# scripts/seed.py
import asyncio
import asyncpg
import os
import sys
from pathlib import Path
import time


sys.path.append(str(Path(__file__).parent.parent))

try:
    from app.config import settings
except ImportError:
    class Settings:
        POSTGRES_USER = os.getenv("POSTGRES_USER", "blog_user")
        POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "blog_pass")
        POSTGRES_DB = os.getenv("POSTGRES_DB", "blog_db")
        POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
        POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    
    settings = Settings()

async def wait_for_db(max_attempts=60):
    """Ожидание готовности PostgreSQL"""
    start_time = time.time()
    print(f"Подключение к PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    
    for attempt in range(max_attempts):
        try:
            conn = await asyncpg.connect(
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                timeout=5
            )
            await conn.close()
            elapsed = time.time() - start_time
            print(f"Подключение к БД установлено (через {elapsed:.1f}с)")
            return True
        except Exception as e:
            print(f"Ожидание БД... ({attempt + 1}/{max_attempts}) - {type(e).__name__}: {e}")
            await asyncio.sleep(2)
    
    elapsed = time.time() - start_time
    print(f"Не удалось подключиться к БД после {elapsed:.1f}с")
    return False

async def seed_database():
    """Заполнение базы тестовыми постами"""
    print("Ожидание готовности PostgreSQL...")
    
    if not await wait_for_db():
        print("Не удалось подключиться к БД")
        sys.exit(1)
    
    try:
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT
        )
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS posts (
                id SERIAL PRIMARY KEY,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE
            )
        ''')
        print("Таблица posts создана или уже существует")
        
        count = await conn.fetchval("SELECT COUNT(*) FROM posts")
        
        if count == 0:
            print("Добавляем тестовые посты...")
            posts = [
                ("Первый пост", "Содержание первого поста - этот пост будет часто запрашиваться"),
                ("Второй пост", "Содержание второго поста с интересной информацией"),
                ("Популярный пост", "Этот пост будут часто запрашивать для тестирования кеша"),
                ("Ещё один пост", "И его содержание, которое тоже может быть популярным"),
                ("Технический пост", "О том как работает кеширование в нашем API"),
                ("Новости блога", "Последние обновления и новости нашего блога"),
                ("Туториал по FastAPI", "Как создать API с кешированием на FastAPI и Redis"),
                ("Python советы", "Полезные советы для Python разработчиков"),
                ("Архитектура приложений", "Чистая архитектура и разделение на слои"),
                ("Тестирование API", "Как писать интеграционные тесты для FastAPI"),
            ]
            
            for title, content in posts:
                await conn.execute(
                    "INSERT INTO posts (title, content, created_at) VALUES ($1, $2, NOW())",
                    title, content
                )
            print(f"Добавлено {len(posts)} тестовых постов")
            
            new_count = await conn.fetchval("SELECT COUNT(*) FROM posts")
            print(f"Всего постов в БД: {new_count}")
            
        else:
            print(f"В базе уже есть {count} постов, пропускаем инициализацию")
        
        await conn.close()
        print("Инициализация базы данных завершена успешно")
        return True
        
    except Exception as e:
        print(f"Ошибка при инициализации БД: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(seed_database())
    sys.exit(0 if success else 1)
