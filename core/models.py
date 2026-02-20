"""
知识库数据模型定义
- Note: 笔记数据模型
- NoteCreate: 创建笔记时的输入模型
- NoteUpdate: 更新笔记时的输入模型
- SearchResult: 搜索结果模型
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class Note(BaseModel):
    """笔记完整数据模型"""

    id: str = Field(..., description="笔记唯一ID")
    title: str = Field(..., description="笔记标题")
    content: str = Field(..., description="笔记内容")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="最后更新时间")


class NoteCreate(BaseModel):
    """创建笔记的输入模型"""

    title: str = Field(..., description="笔记标题")
    content: str = Field(..., description="笔记内容")
    tags: List[str] = Field(default_factory=list, description="标签列表")


class NoteUpdate(BaseModel):
    """更新笔记的输入模型"""

    title: Optional[str] = Field(None, description="新标题，不传则不修改")
    content: Optional[str] = Field(None, description="新内容，不传则不修改")
    tags: Optional[List[str]] = Field(None, description="新标签列表，不传则不修改")


class SearchResult(BaseModel):
    """搜索结果模型"""

    note: Note = Field(..., description="匹配的笔记")
    score: float = Field(..., description="相关性得分，越高越相关")
