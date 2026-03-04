# app/api/dependencies.py
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.post_repository import SQLAlchemyPostRepository
from app.infrastructure.cache.post_cache import RedisPostCache
from app.application.services.post_service import PostService
from app.config import settings


engine = create_async_engine(settings.DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

def get_post_repository(db: AsyncSession = Depends(get_db)) -> SQLAlchemyPostRepository:
    return SQLAlchemyPostRepository(db)

def get_post_cache() -> RedisPostCache:
    return RedisPostCache()

def get_post_service(
    repo: SQLAlchemyPostRepository = Depends(get_post_repository),
    cache: RedisPostCache = Depends(get_post_cache)
) -> PostService:
    return PostService(repository=repo, cache_service=cache)
