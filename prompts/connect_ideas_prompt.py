"""
概念关联提示词
- connect_ideas: 从知识库中找出两个概念的相关笔记，引导 LLM 发现它们之间的联系
"""

from prompts import YA_MCPServer_Prompt


@YA_MCPServer_Prompt(
    name="connect_ideas",
    title="Connect Ideas",
    description="检索两个概念的相关笔记，引导 LLM 发现并阐述它们之间的内在联系",
)
async def connect_ideas(concept_a: str, concept_b: str, top_k: int = 3) -> str:
    """从知识库中找出两个概念的相关笔记，引导 LLM 发现它们之间的联系。

    Args:
        concept_a (str): 第一个概念关键词
        concept_b (str): 第二个概念关键词
        top_k (int): 每个概念检索的笔记数量，默认 3

    Returns:
        str: 供 LLM 使用的概念关联分析提示词文本

    Example:
        "以下是知识库中关于「递归」和「动态规划」的相关笔记：\n\n...
         请分析这两个概念之间的内在联系、相似点与差异，并举例说明如何结合使用。"
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

        notes_a = await km.summarize_topic(concept_a, top_k=top_k)
        notes_b = await km.summarize_topic(concept_b, top_k=top_k)

        lines = []

        if notes_a:
            lines.append(f"## 关于「{concept_a}」的笔记（共 {len(notes_a)} 条）\n")
            for i, note in enumerate(notes_a, 1):
                lines.append(f"### 笔记{i}: {note.title}")
                lines.append(note.content)
                if note.tags:
                    lines.append(f"标签: {', '.join(note.tags)}\n")
        else:
            lines.append(f"## 关于「{concept_a}」的笔记\n知识库中暂无相关笔记。\n")

        if notes_b:
            lines.append(f"## 关于「{concept_b}」的笔记（共 {len(notes_b)} 条）\n")
            for i, note in enumerate(notes_b, 1):
                lines.append(f"### 笔记{i}: {note.title}")
                lines.append(note.content)
                if note.tags:
                    lines.append(f"标签: {', '.join(note.tags)}\n")
        else:
            lines.append(f"## 关于「{concept_b}」的笔记\n知识库中暂无相关笔记。\n")

        lines.append(
            f"\n请基于以上笔记内容，深入分析「{concept_a}」与「{concept_b}」之间的内在联系："
            f"\n1. 两者的相似点和共同原理"
            f"\n2. 两者的主要区别和适用场景"
            f"\n3. 如何将两者结合起来加深理解或解决实际问题"
        )

        return "\n\n".join(lines)
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"生成概念关联提示词失败: {e}")
