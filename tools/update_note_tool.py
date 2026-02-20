"""
笔记更新工具
- update_note: 更新知识库中已有笔记的内容
"""

from typing import Dict, List, Optional

from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="update_note",
    title="Update Note",
    description="更新知识库中已有笔记的标题、内容或标签",
)
async def update_note(
    note_id: str,
    title: Optional[str] = None,
    content: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Dict:
    """更新知识库中已有笔记。

    Args:
        note_id (str): 要更新的笔记 ID
        title (Optional[str]): 新标题，不传则保持不变
        content (Optional[str]): 新内容，不传则保持不变
        tags (Optional[List[str]]): 新标签列表，不传则保持不变

    Returns:
        Dict: 更新后的笔记信息

    Raises:
        RuntimeError: 笔记不存在或更新失败

    Example:
        {
            "id": "abc123",
            "title": "Python装饰器（更新）",
            "content": "...",
            "tags": ["Python", "进阶"],
            "updated_at": "2025-01-02T10:00:00"
        }
    """
    try:
        from core.knowledge_manager import KnowledgeManager
        from core.models import NoteUpdate
        from modules.YA_Common.utils.config import get_config
    except ImportError as e:
        raise RuntimeError(f"无法导入依赖模块: {e}")

    try:
        db_path = get_config("knowledge.database.path")
        vector_path = get_config("knowledge.vector_store.path")
        collection = get_config("knowledge.vector_store.collection_name")

        km = KnowledgeManager(db_path, vector_path, collection)
        await km.initialize()
        note = await km.update_note(note_id, NoteUpdate(title=title, content=content, tags=tags))

        if note is None:
            raise RuntimeError(f"笔记不存在: {note_id}")

        return {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "tags": note.tags,
            "updated_at": note.updated_at.isoformat(),
        }
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"更新笔记失败: {e}")
