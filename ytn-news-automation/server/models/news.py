from typing import Optional
from datetime import datetime

from pydantic import BaseModel, HttpUrl


class NewsBase(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    published_at: Optional[str] = None
    reporter_name: Optional[str] = None
    reporter_email: Optional[str] = None
    category: Optional[str] = None
    source_url: Optional[str] = None
    blog_url: Optional[str] = None
    status: Optional[str] = None


class NewsCreate(NewsBase):
    pass


class NewsUpdate(NewsBase):
    pass


class NewsOut(NewsBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None





