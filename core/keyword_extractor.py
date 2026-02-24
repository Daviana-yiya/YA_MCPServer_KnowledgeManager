"""
关键词提取模块，基于 KeyBERT + jieba 从文本中自动提取关键词
- extract_tags: 从文本中提取关键词列表
"""

from typing import List

# KeyBERT 模块级单例，第一次调用时初始化，之后复用
_kw_model = None


def _get_kw_model():
    global _kw_model
    if _kw_model is None:
        from keybert import KeyBERT

        _kw_model = KeyBERT(model="paraphrase-multilingual-MiniLM-L12-v2")
    return _kw_model


def extract_tags(text: str, top_n: int = 5) -> List[str]:
    """用 KeyBERT + jieba 从文本中提取关键词。

    Args:
        text (str): 待提取关键词的文本（标题 + 内容）
        top_n (int): 返回关键词数量，默认 5

    Returns:
        List[str]: 提取出的关键词列表
    """
    import jieba
    from sklearn.feature_extraction.text import CountVectorizer

    vectorizer = CountVectorizer(tokenizer=jieba.lcut, ngram_range=(1, 2))
    kw_model = _get_kw_model()
    keywords = kw_model.extract_keywords(text, vectorizer=vectorizer, top_n=top_n)
    return [kw for kw, _ in keywords]
