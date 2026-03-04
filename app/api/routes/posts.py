# app/api/routes/posts.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

from app.api.dependencies import get_db, get_post_service
from app.application.services.post_service import PostService


class PostCreate(BaseModel):
    """Модель для создания нового поста"""
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        description="Заголовок поста (от 1 до 200 символов)",
        example="Мой первый пост"
    )
    content: str = Field(
        ..., 
        min_length=1,
        description="Содержание поста",
        example="Это содержание моего первого поста в блоге..."
    )

class PostUpdate(BaseModel):
    """Модель для обновления существующего поста"""
    title: Optional[str] = Field(
        None, 
        min_length=1, 
        max_length=200,
        description="Новый заголовок поста (от 1 до 200 символов)",
        example="Обновленный заголовок"
    )
    content: Optional[str] = Field(
        None, 
        min_length=1,
        description="Новое содержание поста",
        example="Обновленное содержание поста..."
    )

class PostResponse(BaseModel):
    """Модель ответа с данными поста"""
    
    id: int = Field(..., description="Уникальный идентификатор поста", example=1)
    title: str = Field(..., description="Заголовок поста", example="Мой первый пост")
    content: str = Field(..., description="Содержание поста", example="Содержание поста...")
    created_at: Optional[datetime] = Field(None, description="Дата и время создания", example="2024-01-01T12:00:00Z")
    updated_at: Optional[datetime] = Field(None, description="Дата и время последнего обновления", example="2024-01-02T12:00:00Z")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Мой первый пост",
                "content": "Это содержание моего первого поста...",
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": None
            }
        }

router = APIRouter(prefix="/posts", tags=["posts"])

@router.get(
    "/all",
    response_model=List[PostResponse],
    summary="Получить все посты",
    description="""
    Возвращает список всех постов с поддержкой пагинации.
    
    **Параметры:**
    * **skip** - количество подгружаемых постов (для пагинации)
    * **limit** - максимальное количество постов в ответе
    
    **Особенности:**
    * Список не кешируется, так как может часто меняться
    * Сортировка по дате создания (новые первыми)
    """,
    response_description="Список постов"
)
async def get_all_posts(
    skip: int = Query(
        0, 
        ge=0, 
        description="Количество подгружаемых постов (для пагинации)",
        example=0
    ),
    limit: int = Query(
        10, 
        ge=1, 
        le=100, 
        description="Максимальное количество постов в ответе (от 1 до 100)",
        example=10
    ),
    service: PostService = Depends(get_post_service)
):
    """Получение списка всех постов с пагинацией"""
    posts = await service.get_all_posts(skip=skip, limit=limit)
    return posts

@router.get(
    "/{post_id}",
    response_model=PostResponse,
    summary="Получить пост по ID",
    description="""
    Возвращает пост по его уникальному идентификатору.
    
    **Кеширование:**
    1. Сначала проверяется наличие поста в Redis
    2. Если пост есть в кеше - возвращается сразу
    3. Если нет - берется из PostgreSQL и сохраняется в Redis на 5 минут
    
    **Инвалидация кеша:**
    * Кеш автоматически удаляется при обновлении или удалении поста
    """,
    response_description="Данные поста",
    responses={
        200: {"description": "Пост успешно найден"},
        404: {"description": "Пост не найден"}
    }
)
async def get_post(
    post_id: int = Path(
        ..., 
        ge=1,
        description="ID поста (целое число больше 0)",
        example=1
    ),
    service: PostService = Depends(get_post_service)
):
    """Получение поста с автоматическим кешированием"""
    post = await service.get_post(post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post

@router.post(
    "/",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Создать новый пост",
    description="""
    Создает новый пост.
    
    **Правила валидации:**
    * Заголовок не может быть пустым
    * Содержание не может быть пустым
    
    **Кеширование:**
    * Новый пост не кешируется автоматически
    * Кеш появится только после первого GET-запроса
    """,
    response_description="Созданный пост"
)
async def create_post(
    post_data: PostCreate,
    service: PostService = Depends(get_post_service)
):
    """Создание нового поста"""
    return await service.create_post(
        title=post_data.title,
        content=post_data.content
    )

@router.put(
    "/{post_id}",
    response_model=PostResponse,
    summary="Обновить пост",
    description="""
    Обновляет существующий пост.
    
    **Особенности:**
    * Можно обновить заголовок, содержание или оба поля
    * При обновлении автоматически проставляется дата updated_at
    * Кеш для этого поста **инвалидируется**
    
    **Инвалидация кеша:**
    После успешного обновления кеш для этого поста удаляется из Redis.
    Следующий GET-запрос загрузит свежие данные в кеш.
    """,
    response_description="Обновленный пост",
    responses={
        200: {"description": "Пост успешно обновлен"},
        404: {"description": "Пост не найден"}
    }
)
async def update_post(
    post_id: int = Path(
        ..., 
        ge=1,
        description="ID поста для обновления",
        example=1
    ),
    post_data: PostUpdate = Body(..., description="Данные для обновления"),  # Исправлено: используем Body вместо Field
    service: PostService = Depends(get_post_service)
):
    """Обновление поста"""
    post = await service.update_post(
        post_id=post_id,
        title=post_data.title,
        content=post_data.content
    )
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return post

@router.delete(
    "/{post_id}",
    summary="Удалить пост",
    description="""
    Удаляет пост из базы данных.
    
    **Важно:**
    * Пост удаляется безвозвратно
    * Кеш для этого поста **инвалидируется**
    * Все последующие GET-запросы к этому ID будут возвращать 404
    """,
    response_description="Результат удаления",
    responses={
        200: {"description": "Пост успешно удален"},
        404: {"description": "Пост не найден"}
    }
)
async def delete_post(
    post_id: int = Path(
        ..., 
        ge=1,
        description="ID поста для удаления",
        example=1
    ),
    service: PostService = Depends(get_post_service)
):
    """Удаление поста"""

    deleted = await service.delete_post(post_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found"
        )
    return {
        "message": "Post deleted successfully",
        "post_id": post_id
    }
