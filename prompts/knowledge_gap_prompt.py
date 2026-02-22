"""
知识盲区分析提示词
- knowledge_gap: 分析知识库中某主题的覆盖情况，找出知识盲区
"""

from prompts import YA_MCPServer_Prompt
from prompts.role import BASE_ROLE, SKILL_SEARCH


@YA_MCPServer_Prompt(
    name="knowledge_gap",
    title="Knowledge Gap",
    description="分析指定主题在知识库中的覆盖情况，识别知识盲区并给出学习建议",
)
async def knowledge_gap(topic: str, top_k: int = 9999) -> str:
    """分析知识库中某主题的覆盖情况，找出知识盲区。

    Args:
        topic (str): 要分析的主题关键词
        top_k (int): 检索相关笔记的数量，默认 5

    Returns:
        str: 供 LLM 使用的知识盲区分析提示词文本

    Example:
        "以下是知识库中关于「机器学习」的现有笔记：\n\n...
         请分析这些笔记的覆盖范围，指出哪些重要子主题尚未涉及，并给出针对性的学习建议。"
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
        notes = await km.summarize_topic(topic, top_k=top_k)

        if not notes:
            return (
                f"{BASE_ROLE}{SKILL_SEARCH}\n\n"
                f"知识库中暂无与「{topic}」相关的笔记。\n\n"
                f"请分析「{topic}」这一主题的核心知识体系，列出应该学习的主要子主题，"
                f"并给出一份入门学习路线建议。"
            )

        lines = [f"以下是知识库中关于「{topic}」的现有笔记（共 {len(notes)} 条）：\n"]
        for i, note in enumerate(notes, 1):
            lines.append(f"## 笔记{i}: {note.title}")
            lines.append(note.content)
            if note.tags:
                lines.append(f"标签: {', '.join(note.tags)}\n")

        lines.append(
            f"\n请分析以上笔记对「{topic}」主题的覆盖范围，"
            f"指出哪些重要子主题或知识点尚未涉及（即知识盲区），"
            f"并给出针对性的学习建议和补充方向。"
        )

        return f"{BASE_ROLE}{SKILL_SEARCH}\n\n" + "\n\n".join(lines)
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"生成知识盲区分析提示词失败: {e}")
