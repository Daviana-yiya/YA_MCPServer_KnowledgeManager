"""
tools 层集成测试
- test_add_note_tool: 测试添加笔记工具
- test_search_notes_tool: 测试搜索笔记工具
- test_update_note_tool: 测试更新笔记工具
- test_update_note_tool_not_found: 测试更新不存在的笔记
- test_delete_note_tool: 测试删除笔记工具
- test_delete_note_tool_not_found: 测试删除不存在的笔记
- test_summarize_topic_tool_with_notes: 测试有笔记时的主题总结
- test_summarize_topic_tool_empty: 测试无笔记时的主题总结
- test_fetch_url_tool: 测试网页抓取工具（mock httpx）
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    """patch get_config，返回临时目录路径。"""
    paths = {
        "knowledge.database.path": str(tmp_path / "test.db"),
        "knowledge.vector_store.path": str(tmp_path / "vector"),
        "knowledge.vector_store.collection_name": "test",
    }
    from modules.YA_Common.utils import config as _cfg_mod

    monkeypatch.setattr(_cfg_mod, "get_config", lambda key: paths[key])
    return paths


async def test_add_note_tool(cfg):
    from tools.add_note_tool import add_note

    result = await add_note(
        title="Python装饰器", content="装饰器是语法糖", tags=["Python"]
    )

    assert "id" in result
    assert result["title"] == "Python装饰器"
    assert result["content"] == "装饰器是语法糖"
    assert result["tags"] == ["Python"]
    assert "created_at" in result


async def test_search_notes_tool(cfg):
    from tools.add_note_tool import add_note
    from tools.search_notes_tool import search_notes

    await add_note(title="Python装饰器", content="装饰器是语法糖", tags=["Python"])
    result = await search_notes(query="Python装饰器", top_k=5)

    assert "results" in result
    assert "total" in result
    assert result["total"] > 0
    titles = [r["title"] for r in result["results"]]
    assert "Python装饰器" in titles


async def test_update_note_tool(cfg):
    from tools.add_note_tool import add_note
    from tools.update_note_tool import update_note

    added = await add_note(title="原标题", content="原内容", tags=[])
    result = await update_note(note_id=added["id"], title="新标题")

    assert result["title"] == "新标题"
    assert result["id"] == added["id"]
    assert "updated_at" in result


async def test_update_note_tool_not_found(cfg):
    from tools.update_note_tool import update_note

    with pytest.raises(RuntimeError, match="笔记不存在"):
        await update_note(note_id="不存在的id", title="新标题")


async def test_delete_note_tool(cfg):
    from tools.add_note_tool import add_note
    from tools.delete_note_tool import delete_note

    added = await add_note(title="待删除", content="内容", tags=[])
    result = await delete_note(note_id=added["id"])

    assert result["success"] is True
    assert result["note_id"] == added["id"]


async def test_delete_note_tool_not_found(cfg):
    from tools.delete_note_tool import delete_note

    with pytest.raises(RuntimeError, match="笔记不存在"):
        await delete_note(note_id="不存在的id")


async def test_summarize_topic_tool_with_notes(cfg):
    from tools.add_note_tool import add_note
    from tools.summarize_topic_tool import summarize_topic

    await add_note(
        title="动态规划", content="背包问题是经典的动态规划算法", tags=["算法"]
    )
    result = await summarize_topic(topic="动态规划", top_k=5)

    assert result["topic"] == "动态规划"
    assert result["note_count"] > 0
    assert "combined_content" in result
    assert "动态规划" in result["combined_content"]


async def test_summarize_topic_tool_empty(cfg):
    from tools.summarize_topic_tool import summarize_topic

    result = await summarize_topic(topic="量子计算", top_k=5)

    assert result["note_count"] == 0
    assert "量子计算" in result["combined_content"]


async def test_fetch_url_tool():
    from tools.fetch_url_tool import fetch_url

    fake_html = (
        "<html><head><title>测试页面</title></head><body><p>正文内容</p></body></html>"
    )

    mock_response = MagicMock()
    mock_response.text = fake_html
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)

    with patch("httpx.AsyncClient", return_value=mock_client):
        result = await fetch_url(url="https://example.com")

    assert result["title"] == "测试页面"
    assert "正文内容" in result["content"]
