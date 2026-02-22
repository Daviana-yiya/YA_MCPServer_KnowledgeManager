"""
标签列表资源
- knowledge://tags: 返回知识库中所有标签的列表
"""

from resources import YA_MCPServer_Resource


@YA_MCPServer_Resource(
    "knowledge://tags",
    name="knowledge_tags",
    title="Knowledge Tags",
    description="返回知识库中所有已使用的标签列表",
    mime_type="application/json",
)
async def get_all_tags():
    """返回知识库中所有已使用的标签列表。

    Returns:
        list: 标签字符串列表

    Raises:
        RuntimeError: 获取失败

    Example:
        ["Python", "算法", "数据结构", "机器学习"]
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
        return await km.get_all_tags()
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"获取标签列表失败: {e}")
