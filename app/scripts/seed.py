# scripts/seed.py
import asyncio
import asyncpg
from app.config import settings

async def seed_database():
    """Заполнение базы тестовыми постами"""
    
    conn = await asyncpg.connect(
        user=settings.POSTGRES_USER,
        password=settings.POSTGRES_PASSWORD,
        database=settings.POSTGRES_DB,
        host=settings.POSTGRES_HOST,
        port=settings.POSTGRES_PORT
    )

    count = await conn.fetchval("SELECT COUNT(*) FROM posts")
    
    if count == 0:
        print("Добавляем тестовые посты...")
        posts = [
            ("Первый пост", "Содержание первого поста"),
            ("Второй пост", "Содержание второго поста"),
            ("Популярный пост", "Этот пост будут часто запрашивать"),
            ("Ещё один пост", "И его содержание"),
        ]
        
        for title, content in posts:
            await conn.execute(
                "INSERT INTO posts (title, content, created_at) VALUES ($1, $2, NOW())",
                title, content
            )
        print(f"Добавлено {len(posts)} тестовых постов")
    else:
        print(f"В базе уже есть {count} постов, пропускаем инициализацию")
    
    await conn.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
