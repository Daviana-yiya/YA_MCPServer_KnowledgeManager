"""
知识库管理器，整合 SQLite 与 ChromaDB 的核心业务逻辑
- KnowledgeManager.add_note: 添加笔记
- KnowledgeManager.search_notes: 语义 + 关键词混合搜索
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
        """混合搜索：语义搜索 + 关键词搜索，结果去重合并。

        Args:
            query (str): 搜索查询文本
            top_k (int): 语义搜索返回的最大条数，默认 5

        Returns:
            List[SearchResult]: 搜索结果列表，按相关性排序

        Raises:
            RuntimeError: 搜索失败

        Example:
            [{"note": {...}, "score": 0.95}, ...]
        """
        try:
            from core.db import get_note_by_id, search_notes_by_keyword
            from core import vector_store
        except ImportError as e:
            raise RuntimeError(f"无法导入依赖模块: {e}")

        results: List[SearchResult] = []
        seen_ids: set = set()

        # 语义搜索
        try:
            semantic_hits = vector_store.semantic_search(
                self.vector_store_path, self.collection_name, query, top_k
            )
            for note_id, distance in semantic_hits:
                if note_id in seen_ids:
                    continue
                note = await get_note_by_id(self.db_path, note_id)
                if note:
                    seen_ids.add(note_id)
                    results.append(SearchResult(note=note, score=round(1 - distance, 4)))
        except RuntimeError:
            pass  # 向量库为空时跳过语义搜索

        # 关键词补充搜索
        keyword_hits = await search_notes_by_keyword(self.db_path, query)
        for note in keyword_hits:
            if note.id not in seen_ids:
                seen_ids.add(note.id)
                results.append(SearchResult(note=note, score=0.5))

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
