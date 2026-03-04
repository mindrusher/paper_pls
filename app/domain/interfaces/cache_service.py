# app/domain/interfaces/cache_service.py
from abc import ABC, abstractmethod
from typing import Optional
from app.domain.models import Post

class PostCacheService(ABC):
    """Абстракция сервиса кеширования"""
    
    @abstractmethod
    async def get(self, post_id: int) -> Optional[Post]:
        pass
    
    @abstractmethod
    async def set(self, post: Post, ttl: int = 300) -> None:
        pass
    
    @abstractmethod
    async def invalidate(self, post_id: int) -> None:
        pass
