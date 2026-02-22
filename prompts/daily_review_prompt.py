"""
每日复习提示词
- daily_review: 生成每日知识复习的提示词，帮助用户回顾近期笔记
"""

from prompts import YA_MCPServer_Prompt
from prompts.role import BASE_ROLE, SKILL_REVIEW


@YA_MCPServer_Prompt(
    name="daily_review",
    title="Daily Review",
    description="生成每日知识复习提示词，列出近期笔记并引导用户进行回顾与巩固",
)
async def daily_review(days: int = 7) -> str:
    """生成每日知识复习的提示词。

    Args:
        days (int): 回顾最近几天的笔记，默认 7 天

    Returns:
        str: 供 LLM 使用的复习提示词文本

    Example:
        "请帮我复习以下笔记内容，并对每条笔记给出简短的要点总结和复习建议：\n\n..."
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

        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        recent_notes = [
            n for n in notes if n.updated_at.replace(tzinfo=timezone.utc) >= cutoff
        ]

        if not recent_notes:
            return f"{BASE_ROLE}{SKILL_REVIEW}\n\n最近 {days} 天内没有新增或更新的笔记。请先通过 add_note 工具添加一些笔记，再进行每日复习。"

        lines = [
            f"请帮我复习以下 {len(recent_notes)} 条笔记内容，对每条笔记给出简短的要点总结和复习建议：\n"
        ]
        for i, note in enumerate(recent_notes, 1):
            lines.append(f"## 笔记{i}: {note.title}")
            lines.append(note.content)
            if note.tags:
                lines.append(f"标签: {', '.join(note.tags)}\n")

        return f"{BASE_ROLE}{SKILL_REVIEW}\n\n" + "\n\n".join(lines)
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"生成每日复习提示词失败: {e}")
