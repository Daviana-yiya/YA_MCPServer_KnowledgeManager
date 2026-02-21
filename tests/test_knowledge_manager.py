"""
知识库管理器单元测试
- test_add_note: 测试添加笔记
- test_search_notes: 测试混合搜索
- test_update_note: 测试更新笔记
- test_delete_note: 测试删除笔记
- test_get_all_notes: 测试获取所有笔记
- test_get_all_tags: 测试获取所有标签
"""

import tempfile
import os
import pytest
from core.knowledge_manager import KnowledgeManager
from core.models import NoteCreate, NoteUpdate


def get_km(tmp_path: str) -> KnowledgeManager:
    """创建使用临时目录的 KnowledgeManager 实例。"""
    db_path = os.path.join(tmp_path, "test.db")
    vector_path = os.path.join(tmp_path, "vector_store")
    return KnowledgeManager(db_path, vector_path, "test_notes")


@pytest.fixture
def tmp_path():
    with tempfile.TemporaryDirectory() as d:
        yield d


async def test_add_note(tmp_path):
    km = get_km(tmp_path)
    await km.initialize()

    note = await km.add_note(NoteCreate(title="Python装饰器", content="装饰器是语法糖", tags=["Python"]))

    assert note.id is not None
    assert note.title == "Python装饰器"
    assert note.content == "装饰器是语法糖"
    assert note.tags == ["Python"]
    assert note.created_at is not None


async def test_search_notes(tmp_path):
    km = get_km(tmp_path)
    await km.initialize()

    await km.add_note(NoteCreate(title="Python装饰器", content="装饰器是语法糖", tags=["Python"]))
    await km.add_note(NoteCreate(title="异步编程", content="async await 用法", tags=["Python"]))

    results = await km.search_notes("Python装饰器", top_k=5)

    assert len(results) > 0
    assert results[0].score > 0
    titles = [r.note.title for r in results]
    assert "Python装饰器" in titles


async def test_update_note(tmp_path):
    km = get_km(tmp_path)
    await km.initialize()

    note = await km.add_note(NoteCreate(title="原标题", content="原内容", tags=[]))
    updated = await km.update_note(note.id, NoteUpdate(title="新标题"))

    assert updated is not None
    assert updated.title == "新标题"
    assert updated.content == "原内容"


async def test_update_note_not_found(tmp_path):
    km = get_km(tmp_path)
    await km.initialize()

    result = await km.update_note("不存在的id", NoteUpdate(title="新标题"))
    assert result is None


async def test_delete_note(tmp_path):
    km = get_km(tmp_path)
    await km.initialize()

    note = await km.add_note(NoteCreate(title="待删除", content="内容", tags=[]))
    deleted = await km.delete_note(note.id)
    assert deleted is True

    notes = await km.get_all_notes()
    assert all(n.id != note.id for n in notes)


async def test_delete_note_not_found(tmp_path):
    km = get_km(tmp_path)
    await km.initialize()

    result = await km.delete_note("不存在的id")
    assert result is False


async def test_get_all_notes(tmp_path):
    km = get_km(tmp_path)
    await km.initialize()

    await km.add_note(NoteCreate(title="笔记1", content="内容1", tags=[]))
    await km.add_note(NoteCreate(title="笔记2", content="内容2", tags=[]))

    notes = await km.get_all_notes()
    assert len(notes) == 2


async def test_get_all_tags(tmp_path):
    km = get_km(tmp_path)
    await km.initialize()

    await km.add_note(NoteCreate(title="笔记1", content="内容", tags=["Python", "算法"]))
    await km.add_note(NoteCreate(title="笔记2", content="内容", tags=["Python", "数据库"]))

    tags = await km.get_all_tags()
    assert "Python" in tags
    assert "算法" in tags
    assert "数据库" in tags
    assert len(tags) == len(set(tags))
