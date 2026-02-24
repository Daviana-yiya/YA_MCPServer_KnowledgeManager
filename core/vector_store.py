"""
ChromaDB 向量存储接口封装
- upsert_note: 插入或更新笔记的向量表示
- delete_note_vector: 删除笔记向量
- semantic_search: 语义相似度搜索
"""

from typing import List, Tuple


def _get_collection(store_path: str, collection_name: str):
    """获取 ChromaDB 集合（内部辅助函数）。

    Raises:
        RuntimeError: 无法连接向量存储
    """
    try:
        import chromadb
        from chromadb.utils.embedding_functions import (
            SentenceTransformerEmbeddingFunction,
        )
    except ImportError as e:
        raise RuntimeError(f"无法导入 chromadb，请确认已安装: {e}")

    try:
        ef = SentenceTransformerEmbeddingFunction(
            model_name="paraphrase-multilingual-MiniLM-L12-v2"
        )
        client = chromadb.PersistentClient(path=store_path)
        return client.get_or_create_collection(
            name=collection_name, embedding_function=ef
        )
    except Exception as e:
        raise RuntimeError(f"连接向量存储失败: {e}")


def upsert_note(store_path: str, collection_name: str, note_id: str, text: str) -> None:
    """插入或更新笔记的向量表示。

    Args:
        store_path (str): ChromaDB 持久化目录路径
        collection_name (str): 集合名称
        note_id (str): 笔记 ID，作为向量文档的唯一标识
        text (str): 用于向量化的文本（标题 + 内容）

    Raises:
        RuntimeError: 向量写入失败
    """
    collection = _get_collection(store_path, collection_name)
    try:
        collection.upsert(ids=[note_id], documents=[text])
    except Exception as e:
        raise RuntimeError(f"向量写入失败: {e}")


def delete_note_vector(store_path: str, collection_name: str, note_id: str) -> None:
    """删除笔记的向量表示。

    Args:
        store_path (str): ChromaDB 持久化目录路径
        collection_name (str): 集合名称
        note_id (str): 要删除的笔记 ID

    Raises:
        RuntimeError: 向量删除失败
    """
    collection = _get_collection(store_path, collection_name)
    try:
        collection.delete(ids=[note_id])
    except Exception as e:
        raise RuntimeError(f"向量删除失败: {e}")


def semantic_search(
    store_path: str, collection_name: str, query: str, top_k: int = 5
) -> List[Tuple[str, float]]:
    """语义相似度搜索，返回最相关的笔记 ID 列表。

    Args:
        store_path (str): ChromaDB 持久化目录路径
        collection_name (str): 集合名称
        query (str): 搜索查询文本
        top_k (int): 返回最相关的前 k 条结果，默认 5

    Returns:
        List[Tuple[str, float]]: [(note_id, distance), ...] 按相关性排序，distance 越小越相关

    Raises:
        RuntimeError: 语义搜索失败

    Example:
        [("abc123", 0.12), ("def456", 0.35)]
    """
    collection = _get_collection(store_path, collection_name)
    count = collection.count()
    if count == 0:
        return []
    try:
        results = collection.query(query_texts=[query], n_results=min(top_k, count))
    except Exception as e:
        raise RuntimeError(f"语义搜索失败: {e}")

    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]
    return list(zip(ids, distances))
