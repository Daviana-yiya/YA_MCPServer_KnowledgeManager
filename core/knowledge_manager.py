"""
知识库管理器，整合 SQLite 与 ChromaDB 的核心业务逻辑
- KnowledgeManager.add_note: 添加笔记
- KnowledgeManager.search_notes: 语义 + 关键词混合搜索（RRF 融合排名）
- KnowledgeManager.update_note: 更新笔记
- KnowledgeManager.delete_note: 删除笔记
- KnowledgeManager.get_all_notes: 获取所有笔记
- KnowledgeManager.get_all_tags: 获取所有标签
- KnowledgeManager.summarize_topic: 按主题汇总相关笔记内容
"""

from typing import List, Optional

from core.models import Note, NoteCreate, NoteUpdate, SearchResult


class KnowledgeManager:
    """知识库管理器，统一管理笔记的增删改查与语义搜索。"""

    def __init__(self, db_path: str, vector_store_path: str, collection_name: str):
        """初始化知识库管理器。

        Args:
            db_path (str): SQLite 数据库文件路径
            vector_store_path (str): ChromaDB 持久化目录路径
            collection_name (str): 向量集合名称
        """
        self.db_path = db_path
        self.vector_store_path = vector_store_path
        self.collection_name = collection_name

    async def initialize(self) -> None:
        """初始化数据库表结构。

        Raises:
            RuntimeError: 初始化失败
        """
        try:
            from core.db import init_db
        except ImportError as e:
            raise RuntimeError(f"无法导入数据库模块: {e}")

        await init_db(self.db_path)

    async def add_note(self, note_create: NoteCreate) -> Note:
        """添加新笔记，同时写入 SQLite 和向量存储。

        Args:
            note_create (NoteCreate): 创建笔记的输入数据

        Returns:
            Note: 创建成功的完整笔记对象

        Raises:
            RuntimeError: 添加失败

        Example:
            {"id": "abc123", "title": "Python装饰器", "content": "...", "tags": ["Python"], ...}
        """
        try:
            from core.db import insert_note
            from core import vector_store
        except ImportError as e:
            raise RuntimeError(f"无法导入依赖模块: {e}")

        note = await insert_note(self.db_path, note_create)
        vector_store.upsert_note(
            self.vector_store_path,
            self.collection_name,
            note.id,
            f"{note.title}\n{note.content}",
        )
        return note

    async def search_notes(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """混合搜索：语义搜索 + 关键词搜索，使用 RRF 融合排名。

        RRF（Reciprocal Rank Fusion）不依赖异构分数的量纲，
        只看每条笔记在各搜索列表中的排名，用 1/(k+rank) 求和后排序。
        标题命中、内容命中、语义命中分别作为独立排名列表参与融合。

        Args:
            query (str): 搜索查询文本
            top_k (int): 返回最相关的前 k 条结果，默认 5

        Returns:
            List[SearchResult]: 搜索结果列表，按 RRF score 降序排列

        Raises:
            RuntimeError: 搜索失败

        Example:
            [{"note": {...}, "score": 0.049}, ...]
        """
        try:
            from core.db import (
                get_note_by_id,
                search_notes_by_title_keyword,
                search_notes_by_content_keyword,
            )
            from core import vector_store
        except ImportError as e:
            raise RuntimeError(f"无法导入依赖模块: {e}")

        RRF_K = 60
        rrf_scores: dict = {}
        note_cache: dict = {}

        def _add_rank(note_id: str, rank: int):
            rrf_scores[note_id] = rrf_scores.get(note_id, 0.0) + 1.0 / (RRF_K + rank)

        # 语义搜索排名列表
        try:
            semantic_hits = vector_store.semantic_search(
                self.vector_store_path, self.collection_name, query, top_k
            )
            for rank, (note_id, _) in enumerate(semantic_hits, start=1):
                _add_rank(note_id, rank)
                note_cache[note_id] = None  # 占位，稍后从 DB 取
        except RuntimeError:
            pass  # 向量库为空时跳过

        # 标题关键词排名列表
        title_hits = await search_notes_by_title_keyword(self.db_path, query)
        for rank, note in enumerate(title_hits, start=1):
            _add_rank(note.id, rank)
            note_cache[note.id] = note

        # 内容关键词排名列表（与标题列表独立，标题也命中的笔记会在两个列表中都得分）
        content_hits = await search_notes_by_content_keyword(self.db_path, query)
        for rank, note in enumerate(content_hits, start=1):
            _add_rank(note.id, rank)
            note_cache[note.id] = note

        # 从 DB 补全语义搜索命中但 note_cache 中还是 None 的笔记
        for note_id, note in note_cache.items():
            if note is None:
                note_cache[note_id] = await get_note_by_id(self.db_path, note_id)

        # 按 RRF score 降序排列，取 top_k
        sorted_ids = sorted(rrf_scores, key=lambda nid: rrf_scores[nid], reverse=True)
        results = []
        for note_id in sorted_ids[:top_k]:
            note = note_cache.get(note_id)
            if note:
                results.append(SearchResult(note=note, score=round(rrf_scores[note_id], 6)))

        return results


    async def update_note(self, note_id: str, note_update: NoteUpdate) -> Optional[Note]:
        """更新笔记，同步更新向量存储。

        Args:
            note_id (str): 笔记 ID
            note_update (NoteUpdate): 要更新的字段

        Returns:
            Optional[Note]: 更新后的笔记，ID 不存在则返回 None

        Raises:
            RuntimeError: 更新失败
        """
        try:
            from core.db import update_note
            from core import vector_store
        except ImportError as e:
            raise RuntimeError(f"无法导入依赖模块: {e}")

        updated = await update_note(self.db_path, note_id, note_update)
        if updated:
            vector_store.upsert_note(
                self.vector_store_path,
                self.collection_name,
                updated.id,
                f"{updated.title}\n{updated.content}",
            )
        return updated

    async def delete_note(self, note_id: str) -> bool:
        """删除笔记，同步删除向量存储中的记录。

        Args:
            note_id (str): 笔记 ID

        Returns:
            bool: 删除成功返回 True，ID 不存在返回 False

        Raises:
            RuntimeError: 删除失败
        """
        try:
            from core.db import delete_note
            from core import vector_store
        except ImportError as e:
            raise RuntimeError(f"无法导入依赖模块: {e}")

        deleted = await delete_note(self.db_path, note_id)
        if deleted:
            vector_store.delete_note_vector(
                self.vector_store_path, self.collection_name, note_id
            )
        return deleted

    async def get_all_notes(self) -> List[Note]:
        """获取所有笔记，按创建时间倒序排列。

        Returns:
            List[Note]: 所有笔记列表

        Raises:
            RuntimeError: 查询失败
        """
        try:
            from core.db import get_all_notes
        except ImportError as e:
            raise RuntimeError(f"无法导入数据库模块: {e}")

        return await get_all_notes(self.db_path)

    async def get_all_tags(self) -> List[str]:
        """获取知识库中所有不重复的标签。

        Returns:
            List[str]: 去重排序后的标签列表

        Raises:
            RuntimeError: 查询失败
        """
        try:
            from core.db import get_all_tags
        except ImportError as e:
            raise RuntimeError(f"无法导入数据库模块: {e}")

        return await get_all_tags(self.db_path)

    async def summarize_topic(self, topic: str, top_k: int = 5) -> List[Note]:
        """按主题搜索相关笔记，供 LLM 进行总结。

        Args:
            topic (str): 主题关键词
            top_k (int): 返回最相关的笔记数量，默认 5

        Returns:
            List[Note]: 与主题最相关的笔记列表

        Raises:
            RuntimeError: 搜索失败
        """
        results = await self.search_notes(topic, top_k=top_k)
        return [r.note for r in results]
