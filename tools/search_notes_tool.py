"""
笔记搜索工具
- search_notes: 通过语义搜索和关键词混合搜索笔记
"""

from typing import Dict, List

from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="search_notes",
    title="Search Notes",
    description="搜索知识库中的笔记，支持语义搜索和关键词匹配",
)
async def search_notes(query: str, top_k: int = 5) -> Dict:
    """搜索知识库中的笔记。

    Args:
        query (str): 搜索查询文本，支持自然语言描述
        top_k (int): 返回最相关的结果数量，默认 5

    Returns:
        Dict: 包含搜索结果列表，每条结果含笔记信息和相关性得分

    Raises:
        RuntimeError: 搜索失败

    Example:
        {
            "results": [
                {
                    "id": "abc123",
                    "title": "Python装饰器",
                    "content": "...",
                    "tags": ["Python"],
                    "score": 0.95
                }
            ],
            "total": 1
        }
    """
    try:
        from core.knowledge_manager import KnowledgeManager
        from modules.YA_Common.utils.config import get_config
    except ImportError as e:
        raise RuntimeError(f"无法导入依赖模块: {e}")

    try:
        db_path = get_config("knowledge.database.path")
        vector_path = get_config("knowledge.vector_store.path")
        collection = get_config("knowledge.vector_store.collection_name")

        km = KnowledgeManager(db_path, vector_path, collection)
        await km.initialize()
        results = await km.search_notes(query, top_k=top_k)

        return {
            "results": [
                {
                    "id": r.note.id,
                    "title": r.note.title,
                    "content": r.note.content,
                    "tags": r.note.tags,
                    "score": r.score,
                }
                for r in results
            ],
            "total": len(results),
        }
    except Exception as e:
        raise RuntimeError(f"搜索笔记失败: {e}")
