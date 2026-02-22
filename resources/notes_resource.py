"""
笔记列表资源
- knowledge://notes: 返回知识库中所有笔记的列表
"""

from resources import YA_MCPServer_Resource


@YA_MCPServer_Resource(
    "knowledge://notes",
    name="knowledge_notes",
    title="Knowledge Notes",
    description="返回知识库中所有笔记的列表，包含 id、标题、标签和创建时间",
    mime_type="application/json",
)
async def get_all_notes():
    """返回知识库中所有笔记的列表。

    Returns:
        list: 笔记列表，每条包含 id、title、tags、created_at、updated_at

    Raises:
        RuntimeError: 获取失败

    Example:
        [
            {
                "id": "abc123",
                "title": "Python装饰器",
                "tags": ["Python"],
                "created_at": "2025-01-01T10:00:00",
                "updated_at": "2025-01-01T10:00:00"
            }
        ]
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
        notes = await km.get_all_notes()

        return [
            {
                "id": n.id,
                "title": n.title,
                "tags": n.tags,
                "created_at": n.created_at.isoformat(),
                "updated_at": n.updated_at.isoformat(),
            }
            for n in notes
        ]
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"获取笔记列表失败: {e}")
