# app/application/services/post_service.py
from typing import Optional, List
from app.domain.models import Post
from app.domain.interfaces.repository import PostRepository
from app.domain.interfaces.cache_service import PostCacheService

class PostService:
    """Сервис с бизнес-логикой работы с постами
    
    Слой содержит всю бизнес-логику приложения.
    
    Основные функции:
    - Кеширование популярных постов
    - Инвалидация кеша при изменениях
    - Валидация бизнес-правил
    """
    
    def __init__(
        self,
        repository: PostRepository,
        cache_service: PostCacheService
    ):
        self._repository = repository
        self._cache_service = cache_service
        self._cache_ttl = 300

    async def get_all_posts(self, skip: int = 0, limit: int = 100) -> List[Post]:
        """Получение списка всех постов с пагинацией
        
        Args:
            skip: Количество пропускаемых постов
            limit: Максимальное количество постов
            
        Returns:
            List[Post]: Список постов
        """
        return await self._repository.get_all(skip=skip, limit=limit)

    async def get_post(self, post_id: int) -> Optional[Post]:
        """Получение поста с кешированием
             
        Args:
            post_id: ID поста
            
        Returns:
            Optional[Post]: Пост или None если не найден
        """
        cached_post = await self._cache_service.get(post_id)
        if cached_post:
            return cached_post

        post = await self._repository.get(post_id)
        if not post:
            return None

        await self._cache_service.set(post, self._cache_ttl)
        return post

    async def create_post(self, title: str, content: str) -> Post:
        """Создание нового поста
        
        Args:
            title: Заголовок поста
            content: Содержание поста
            
        Returns:
            Post: пост
            
        Raises:
            ValueError: Если заголовок или содержание пустые
        """

        post = Post(title=title, content=content)
        saved_post = await self._repository.save(post)

        return saved_post

    async def update_post(self, post_id: int, title: Optional[str] = None, 
                         content: Optional[str] = None) -> Optional[Post]:
        """Обновление поста с инвалидацией кеша
        
        Args:
            post_id: ID поста для обновления
            title: Новый заголовок (опционально)
            content: Новое содержание (опционально)
            
        Returns:
            Optional[Post]: Обновленный пост или None если не найден
        """

        post = await self._repository.get(post_id)
        if not post:
            return None

        post.update(title, content)
        updated_post = await self._repository.update(post)
        await self._cache_service.invalidate(post_id)

        return updated_post

    async def delete_post(self, post_id: int) -> bool:
        """Удаление поста, инвалидация кэша
        
        Args:
            post_id: ID поста для удаления
            
        Returns:
            bool: True если пост удален, False если не найден
        """
        post = await self._repository.get(post_id)
        if not post:
            return False

        deleted = await self._repository.delete(post_id)
        
        if deleted:
            await self._cache_service.invalidate(post_id)
        
        return deleted
