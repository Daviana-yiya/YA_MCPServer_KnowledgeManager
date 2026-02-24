"""
网页内容抓取模块
- fetch_url: 抓取指定 URL 的网页标题和正文内容
"""

from typing import Dict


async def fetch_url(url: str) -> Dict[str, str]:
    """抓取指定 URL 的网页标题和正文内容。

    Args:
        url (str): 要抓取的网页 URL

    Returns:
        Dict[str, str]: 包含网页标题和正文内容
            - title (str): 网页标题
            - content (str): 提取的正文文本

    Raises:
        RuntimeError: 网络请求失败或内容解析失败

    Example:
        {
            "title": "Python 装饰器详解",
            "content": "装饰器是 Python 中一种强大的语法糖..."
        }
    """
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError as e:
        raise RuntimeError(
            f"无法导入依赖模块，请确认已安装 httpx 和 beautifulsoup4: {e}"
        )

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                    "Referer": "https://www.google.com/",
                },
            )
            response.raise_for_status()
    except httpx.HTTPStatusError as e:
        raise RuntimeError(f"HTTP 请求失败 ({e.response.status_code}): {url}")
    except httpx.RequestError as e:
        raise RuntimeError(f"网络请求失败: {e}")

    try:
        soup = BeautifulSoup(response.text, "html.parser")

        # 提取标题
        title = ""
        if soup.title and soup.title.string:
            title = soup.title.string.strip()

        # 移除脚本、样式、导航等无关标签
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        # 提取正文
        content = soup.get_text(separator="\n", strip=True)
        # 合并多余空行
        lines = [line for line in content.splitlines() if line.strip()]
        content = "\n".join(lines)

    except Exception as e:
        raise RuntimeError(f"网页内容解析失败: {e}")

    return {"title": title, "content": content}
