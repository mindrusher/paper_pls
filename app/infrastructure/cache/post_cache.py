# app/infrastructure/cache/post_cache.py
import json
from typing import Optional
from datetime import datetime
from app.domain.models import Post
from app.domain.interfaces.cache_service import PostCacheService
from app.infrastructure.cache.redis_client import redis_client

class RedisPostCache(PostCacheService):
    """Реализация кеш-сервиса через Redis"""
    
    def _key(self, post_id: int) -> str:
        return f"post:{post_id}"

    async def get(self, post_id: int) -> Optional[Post]:
        data = await redis_client.get(self._key(post_id))
        if data:
            post_dict = json.loads(data)
            if post_dict.get('created_at'):
                post_dict['created_at'] = datetime.fromisoformat(post_dict['created_at'])
            if post_dict.get('updated_at'):
                post_dict['updated_at'] = datetime.fromisoformat(post_dict['updated_at'])
            return Post(**post_dict)
        return None

    async def set(self, post: Post, ttl: int = 300) -> None:
        post_dict = post.dict()
        if post_dict.get('created_at'):
            post_dict['created_at'] = post_dict['created_at'].isoformat()
        if post_dict.get('updated_at'):
            post_dict['updated_at'] = post_dict['updated_at'].isoformat()
        await redis_client.setex(
            self._key(post.id),
            ttl,
            json.dumps(post_dict)
        )

    async def invalidate(self, post_id: int) -> None:
        await redis_client.delete(self._key(post_id))
