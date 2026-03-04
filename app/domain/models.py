# app/domain/models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class Post(BaseModel):
    """Доменная сущность постов"""

    id: Optional[int] = None
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # вместо orm_mode

    def update(self, title: Optional[str] = None, content: Optional[str] = None) -> None:
        """Бизнес-правила обновления поста"""
        
        if title is not None:
            if len(title.strip()) == 0:
                raise ValueError("Title cannot be empty")
            self.title = title.strip()
        
        if content is not None:
            if len(content.strip()) == 0:
                raise ValueError("Content cannot be empty")
            self.content = content.strip()
        
        self.updated_at = datetime.utcnow()
