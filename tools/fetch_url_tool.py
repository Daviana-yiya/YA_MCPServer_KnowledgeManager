"""
网页内容抓取工具
- fetch_url: 抓取指定 URL 的网页标题和正文，供用户确认后存入知识库
"""

from typing import Dict

from tools import YA_MCPServer_Tool


@YA_MCPServer_Tool(
    name="fetch_url",
    title="Fetch URL",
    description="抓取指定网页的标题和正文内容，返回给用户确认后可通过 add_note 存入知识库",
)
async def fetch_url(url: str) -> Dict:
    """抓取指定 URL 的网页标题和正文内容。

    Args:
        url (str): 要抓取的网页 URL

    Returns:
        Dict: 包含网页标题和正文内容，供用户确认后调用 add_note 存入知识库

    Raises:
        RuntimeError: 抓取失败

    Example:
        {
            "title": "Python 装饰器详解",
            "content": "装饰器是 Python 中一种强大的语法糖..."
        }
    """
    try:
        from core.web_fetcher import fetch_url as _fetch_url
    except ImportError as e:
        raise RuntimeError(f"无法导入依赖模块: {e}")

    try:
        return await _fetch_url(url)
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"抓取网页失败: {e}")
