"""
笔记删除工具
- delete_note: 从知识库中删除指定笔记
"""

from typing import Dict

from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="delete_note",
    title="Delete Note",
    description="从知识库中删除指定 ID 的笔记",
)
async def delete_note(note_id: str) -> Dict:
    """从知识库中删除指定笔记。

    Args:
        note_id (str): 要删除的笔记 ID

    Returns:
        Dict: 删除结果，包含 success 和 note_id 字段

    Raises:
        RuntimeError: 笔记不存在或删除失败

    Example:
        {"success": True, "note_id": "abc123"}
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
        deleted = await km.delete_note(note_id)

        if not deleted:
            raise RuntimeError(f"笔记不存在: {note_id}")

        return {"success": True, "note_id": note_id}
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"删除笔记失败: {e}")
