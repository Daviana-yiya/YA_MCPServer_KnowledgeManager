"""
主题总结工具
- summarize_topic: 检索与主题相关的笔记，供 LLM 进行总结分析
"""

from typing import Dict

from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="summarize_topic",
    title="Summarize Topic",
    description="检索与指定主题相关的笔记内容，汇总后供 LLM 进行总结分析。请将用户意图提炼为核心的主题关键词后再传入 topic，剔除口语化废话，只保留核心技术名词（如有多个关键词，用空格隔开）。获取结果后，请对 combined_content 进行二次总结归纳，以流畅的自然语言呈现给用户，而非直接返回原文。",
)
async def summarize_topic(topic: str, top_k: int = 5) -> Dict:
    """检索与主题相关的笔记，返回汇总内容供 LLM 总结。

    Args:
        topic (str): 提炼出的核心主题关键词，剔除口语化废话，只保留核心技术名词（如有多个关键词，用空格隔开）
        top_k (int): 检索最相关的笔记数量，默认 5

    Returns:
        Dict: 包含主题、相关笔记列表和拼接后的汇总文本

    Raises:
        RuntimeError: 检索失败

    Example:
        {
            "topic": "Python异步编程",
            "note_count": 3,
            "notes": [{"id": "...", "title": "...", "content": "..."}],
            "combined_content": "# Python异步编程\n\n## 笔记1: ...\n..."
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
        notes = await km.summarize_topic(topic, top_k=top_k)

        if not notes:
            return {
                "topic": topic,
                "note_count": 0,
                "notes": [],
                "combined_content": f"知识库中暂无与「{topic}」相关的笔记。",
            }

        combined_lines = [f"# {topic}\n"]
        for i, note in enumerate(notes, 1):
            combined_lines.append(f"## 笔记{i}: {note.title}")
            combined_lines.append(note.content)
            if note.tags:
                combined_lines.append(f"标签: {', '.join(note.tags)}\n")

        return {
            "topic": topic,
            "note_count": len(notes),
            "notes": [
                {"id": n.id, "title": n.title, "content": n.content} for n in notes
            ],
            "combined_content": "\n\n".join(combined_lines),
        }
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"主题总结失败: {e}")
