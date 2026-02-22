"""
笔记搜索工具
- search_notes: 通过语义搜索和关键词混合搜索笔记
"""

from typing import Dict

from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="search_notes",
    title="Search Notes",
    description="搜索知识库中的笔记，支持语义搜索和关键词匹配。一定注意请将用户意图提炼为核心的关键词后再传入 query，请剔除用户输入中的口语化废话，只保留核心的技术名词，而非直接传入完整句子。(如果有多个关键词，请用空格隔开)",
)
async def search_notes(query: str, top_k: int = 5) -> Dict:
    """搜索知识库中的笔记。

    Args:
        query (str): 提炼出的核心搜索关键词。请剔除用户输入中的"我想查询"、"关于"等口语化废话，只保留核心的技术名词（如"动态规划"、"TimeSformer"等）。如果有多个关键词，请用空格隔开
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
