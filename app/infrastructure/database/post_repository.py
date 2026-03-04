# app/infrastructure/database/post_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.domain.models import Post
from app.domain.interfaces.repository import PostRepository
from app.infrastructure.database.models import PostModel

class SQLAlchemyPostRepository(PostRepository):
    """Реализация репозитория через SQLAlchemy"""
    
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get(self, post_id: int) -> Optional[Post]:
        result = await self._session.execute(
            select(PostModel).where(PostModel.id == post_id)
        )
        db_post = result.scalar_one_or_none()
        return Post.from_orm(db_post) if db_post else None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Post]:
        result = await self._session.execute(
            select(PostModel)
            .order_by(PostModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        db_posts = result.scalars().all()
        return [Post.from_orm(post) for post in db_posts]

    async def save(self, post: Post) -> Post:
        db_post = PostModel(
            title=post.title,
            content=post.content
        )
        self._session.add(db_post)
        await self._session.commit()
        await self._session.refresh(db_post)
        return Post.from_orm(db_post)

    async def update(self, post: Post) -> Post:
        db_post = await self._session.get(PostModel, post.id)
        if post.title:
            db_post.title = post.title
        if post.content:
            db_post.content = post.content
        await self._session.commit()
        await self._session.refresh(db_post)
        return Post.from_orm(db_post)

    async def delete(self, post_id: int) -> bool:
        db_post = await self._session.get(PostModel, post_id)
        if db_post:
            await self._session.delete(db_post)
            await self._session.commit()
            return True
        return False
