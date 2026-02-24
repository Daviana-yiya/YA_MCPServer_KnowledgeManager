"""
关键词提取模块，基于 jieba.analyse 从文本中自动提取关键词
- extract_tags: 从文本中提取关键词列表
"""

from typing import List


def extract_tags(text: str, top_n: int = 5) -> List[str]:
    """用 jieba.analyse.extract_tags 从文本中提取关键词。

    Args:
        text (str): 待提取关键词的文本（标题 + 内容）
        top_n (int): 返回关键词数量，默认 5

    Returns:
        List[str]: 提取出的关键词列表
    """
    import jieba.analyse

    # allowPOS 只保留名词、动词、形容词，过滤助词/标点等噪声词
    keywords = jieba.analyse.extract_tags(
        text,
        topK=top_n,
        allowPOS=("n", "vn", "v", "a", "an", "nz", "eng"),
    )
    return keywords
