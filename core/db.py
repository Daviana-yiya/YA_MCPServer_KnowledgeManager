"""
SQLite 数据库接口封装
- init_db: 初始化数据库表结构
- insert_note: 插入新笔记
- get_note_by_id: 按 ID 查询笔记
- update_note: 更新笔记字段
- delete_note: 删除笔记
- get_all_notes: 获取所有笔记
- get_all_tags: 获取所有标签
- search_notes_by_keyword: 按关键词搜索笔记（标题或内容）
- search_notes_by_title_keyword: 按关键词搜索标题命中的笔记
- search_notes_by_content_keyword: 按关键词搜索内容命中的笔记
- search_notes_by_tag_keyword: 按关键词搜索标签命中的笔记
"""

import json
import uuid
from datetime import datetime
from typing import List, Optional

import aiosqlite

from core.models import Note, NoteCreate, NoteUpdate


async def init_db(db_path: str) -> None:
    """初始化数据库，创建 notes 表。

    Args:
        db_path (str): SQLite 数据库文件路径

    Raises:
        RuntimeError: 数据库初始化失败
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS notes (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    tags TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """
            )
            await db.commit()
    except Exception as e:
        raise RuntimeError(f"数据库初始化失败: {e}")


async def insert_note(db_path: str, note_create: NoteCreate) -> Note:
    """插入新笔记到数据库。

    Args:
        db_path (str): SQLite 数据库文件路径
        note_create (NoteCreate): 创建笔记的输入数据

    Returns:
        Note: 创建成功的完整笔记对象

    Raises:
        RuntimeError: 插入失败

    Example:
        {
            "id": "abc123",
            "title": "Python装饰器",
            "content": "装饰器是...",
            "tags": ["Python"],
            "created_at": "2025-01-01T10:00:00",
            "updated_at": "2025-01-01T10:00:00"
        }
    """
    now = datetime.now()
    note = Note(
        id=str(uuid.uuid4()),
        title=note_create.title,
        content=note_create.content,
        tags=note_create.tags,
        created_at=now,
        updated_at=now,
    )
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "INSERT INTO notes (id, title, content, tags, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    note.id,
                    note.title,
                    note.content,
                    json.dumps(note.tags, ensure_ascii=False),
                    note.created_at.isoformat(),
                    note.updated_at.isoformat(),
                ),
            )
            await db.commit()
    except Exception as e:
        raise RuntimeError(f"插入笔记失败: {e}")
    return note


async def get_note_by_id(db_path: str, note_id: str) -> Optional[Note]:
    """按 ID 查询笔记。

    Args:
        db_path (str): SQLite 数据库文件路径
        note_id (str): 笔记 ID

    Returns:
        Optional[Note]: 找到则返回笔记对象，否则返回 None

    Raises:
        RuntimeError: 查询失败
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM notes WHERE id = ?", (note_id,)
            ) as cursor:
                row = await cursor.fetchone()
    except Exception as e:
        raise RuntimeError(f"查询笔记失败: {e}")

    if row is None:
        return None
    return _row_to_note(row)


async def update_note(
    db_path: str, note_id: str, note_update: NoteUpdate
) -> Optional[Note]:
    """更新笔记字段。

    Args:
        db_path (str): SQLite 数据库文件路径
        note_id (str): 笔记 ID
        note_update (NoteUpdate): 要更新的字段

    Returns:
        Optional[Note]: 更新后的笔记对象，ID 不存在则返回 None

    Raises:
        RuntimeError: 更新失败
    """
    note = await get_note_by_id(db_path, note_id)
    if note is None:
        return None

    new_title = note_update.title if note_update.title is not None else note.title
    new_content = (
        note_update.content if note_update.content is not None else note.content
    )
    new_tags = note_update.tags if note_update.tags is not None else note.tags
    new_updated_at = datetime.now()

    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute(
                "UPDATE notes SET title=?, content=?, tags=?, updated_at=? WHERE id=?",
                (
                    new_title,
                    new_content,
                    json.dumps(new_tags, ensure_ascii=False),
                    new_updated_at.isoformat(),
                    note_id,
                ),
            )
            await db.commit()
    except Exception as e:
        raise RuntimeError(f"更新笔记失败: {e}")

    return await get_note_by_id(db_path, note_id)


async def delete_note(db_path: str, note_id: str) -> bool:
    """删除笔记。

    Args:
        db_path (str): SQLite 数据库文件路径
        note_id (str): 笔记 ID

    Returns:
        bool: 删除成功返回 True，ID 不存在返回 False

    Raises:
        RuntimeError: 删除失败
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("DELETE FROM notes WHERE id = ?", (note_id,))
            await db.commit()
            return cursor.rowcount > 0
    except Exception as e:
        raise RuntimeError(f"删除笔记失败: {e}")


async def get_all_notes(db_path: str) -> List[Note]:
    """获取所有笔记，按创建时间倒序排列。

    Args:
        db_path (str): SQLite 数据库文件路径

    Returns:
        List[Note]: 所有笔记列表

    Raises:
        RuntimeError: 查询失败
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM notes ORDER BY created_at DESC"
            ) as cursor:
                rows = await cursor.fetchall()
    except Exception as e:
        raise RuntimeError(f"获取所有笔记失败: {e}")

    return [_row_to_note(row) for row in rows]


async def get_all_tags(db_path: str) -> List[str]:
    """获取所有不重复的标签。

    Args:
        db_path (str): SQLite 数据库文件路径

    Returns:
        List[str]: 去重后的标签列表

    Raises:
        RuntimeError: 查询失败
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            async with db.execute("SELECT tags FROM notes") as cursor:
                rows = await cursor.fetchall()
    except Exception as e:
        raise RuntimeError(f"获取标签失败: {e}")

    tag_set = set()
    for (tags_json,) in rows:
        for tag in json.loads(tags_json):
            tag_set.add(tag)
    return sorted(tag_set)


async def search_notes_by_keyword(db_path: str, keyword: str) -> List[Note]:
    """按关键词搜索笔记（标题和内容的模糊匹配）。

    Args:
        db_path (str): SQLite 数据库文件路径
        keyword (str): 搜索关键词

    Returns:
        List[Note]: 匹配的笔记列表

    Raises:
        RuntimeError: 搜索失败
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? ORDER BY updated_at DESC",
                (f"%{keyword}%", f"%{keyword}%"),
            ) as cursor:
                rows = await cursor.fetchall()
    except Exception as e:
        raise RuntimeError(f"关键词搜索失败: {e}")

    return [_row_to_note(row) for row in rows]


async def search_notes_by_title_keyword(db_path: str, keyword: str) -> List[Note]:
    """按关键词搜索标题命中的笔记。

    Args:
        db_path (str): SQLite 数据库文件路径
        keyword (str): 搜索关键词

    Returns:
        List[Note]: 标题中包含关键词的笔记列表

    Raises:
        RuntimeError: 搜索失败
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM notes WHERE title LIKE ? ORDER BY updated_at DESC",
                (f"%{keyword}%",),
            ) as cursor:
                rows = await cursor.fetchall()
    except Exception as e:
        raise RuntimeError(f"标题关键词搜索失败: {e}")

    return [_row_to_note(row) for row in rows]


async def search_notes_by_content_keyword(db_path: str, keyword: str) -> List[Note]:
    """按关键词搜索内容命中的笔记。

    Args:
        db_path (str): SQLite 数据库文件路径
        keyword (str): 搜索关键词

    Returns:
        List[Note]: 内容中包含关键词的笔记列表（含标题也命中的）

    Raises:
        RuntimeError: 搜索失败
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM notes WHERE content LIKE ? ORDER BY updated_at DESC",
                (f"%{keyword}%",),
            ) as cursor:
                rows = await cursor.fetchall()
    except Exception as e:
        raise RuntimeError(f"内容关键词搜索失败: {e}")

    return [_row_to_note(row) for row in rows]


async def search_notes_by_tag_keyword(db_path: str, keyword: str) -> List[Note]:
    """按关键词搜索标签命中的笔记。

    Args:
        db_path (str): SQLite 数据库文件路径
        keyword (str): 搜索关键词

    Returns:
        List[Note]: 标签中包含关键词的笔记列表

    Raises:
        RuntimeError: 搜索失败
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM notes WHERE tags LIKE ? ORDER BY updated_at DESC",
                (f"%{keyword}%",),
            ) as cursor:
                rows = await cursor.fetchall()
    except Exception as e:
        raise RuntimeError(f"标签关键词搜索失败: {e}")

    return [_row_to_note(row) for row in rows]


def _row_to_note(row: aiosqlite.Row) -> Note:
    """将数据库行转换为 Note 对象（内部辅助函数）。"""
    return Note(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        tags=json.loads(row["tags"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
    )
