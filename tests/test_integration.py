# tests/test_integration.py
import pytest
from unittest.mock import AsyncMock, Mock

from app.application.services.post_service import PostService
from app.domain.models import Post

@pytest.mark.asyncio
async def test_get_post_caching_flow():
    """Тест проверяет, что кеширование работает правильно на уровне сервиса"""
    
    # моки для репозитория и кеша
    mock_repo = AsyncMock()
    mock_cache = AsyncMock()
    
    service = PostService(repository=mock_repo, cache_service=mock_cache)
    
    test_post = Post(id=1, title="Test", content="Content")
    
    # Если поста нет в кеше, берём из БД
    mock_cache.get.return_value = None
    mock_repo.get.return_value = test_post
    
    result = await service.get_post(1)
    
    # Проверяем, что сходили в БД и сохранили в кеш
    mock_repo.get.assert_called_once_with(1)
    mock_cache.set.assert_called_once_with(test_post, 300)
    assert result == test_post
    
    # Если пост есть в кеше
    mock_cache.reset_mock()
    mock_repo.reset_mock()
    mock_cache.get.return_value = test_post
    
    result = await service.get_post(1)
    
    # Проверяем, что использовали кеш и не ходили в БД
    mock_repo.get.assert_not_called()
    mock_cache.set.assert_not_called()
    assert result == test_post
    
    # Обновление поста инвалидирует кеш
    mock_cache.reset_mock()
    mock_repo.reset_mock()
    mock_repo.get.return_value = test_post
    mock_repo.update.return_value = test_post
    
    await service.update_post(1, title="Updated")
    
    # Проверяем инвалидацию кеша
    mock_cache.invalidate.assert_called_once_with(1)
