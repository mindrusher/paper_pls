# app/domain/interfaces/repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from app.domain.models import Post

class PostRepository(ABC):
    """Абстракция репозитория постов"""
    
    @abstractmethod
    async def get(self, post_id: int) -> Optional[Post]:
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Post]:
        pass
    
    @abstractmethod
    async def save(self, post: Post) -> Post:
        pass
    
    @abstractmethod
    async def update(self, post: Post) -> Post:
        pass
    
    @abstractmethod
    async def delete(self, post_id: int) -> bool:
        pass
