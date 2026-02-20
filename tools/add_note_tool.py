"""
笔记添加工具
- add_note: 添加新笔记到知识库
"""

from typing import Dict, List

from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="add_note",
    title="Add Note",
    description="添加一条新笔记到知识库，支持标题、内容和标签",
)
async def add_note(title: str, content: str, tags: List[str] = []) -> Dict:
    """添加新笔记到知识库。

    Args:
        title (str): 笔记标题
        content (str): 笔记内容
        tags (List[str]): 标签列表，默认为空

    Returns:
        Dict: 创建成功的笔记信息，包含 id、title、content、tags、created_at

    Raises:
        RuntimeError: 添加失败

    Example:
        {
            "id": "abc123",
            "title": "Python装饰器",
            "content": "装饰器是...",
            "tags": ["Python"],
            "created_at": "2025-01-01T10:00:00"
        }
    """
    try:
        from core.knowledge_manager import KnowledgeManager
        from core.models import NoteCreate
        from modules.YA_Common.utils.config import get_config
    except ImportError as e:
        raise RuntimeError(f"无法导入依赖模块: {e}")

    try:
        db_path = get_config("knowledge.database.path")
        vector_path = get_config("knowledge.vector_store.path")
        collection = get_config("knowledge.vector_store.collection_name")

        km = KnowledgeManager(db_path, vector_path, collection)
        await km.initialize()
        note = await km.add_note(NoteCreate(title=title, content=content, tags=tags))

        return {
            "id": note.id,
            "title": note.title,
            "content": note.content,
            "tags": note.tags,
            "created_at": note.created_at.isoformat(),
        }
    except Exception as e:
        raise RuntimeError(f"添加笔记失败: {e}")
