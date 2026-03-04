# app/main.py
from fastapi import FastAPI
from app.api.routes import posts
from app.infrastructure.database.base import Base
from app.api.dependencies import engine
import asyncpg
from app.config import settings
import logging
import asyncio
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Blog API с кэшированием",
    description="""
    API для блога с кешированием постов
    
    Возможности:
    * CRUD операции для постов
    * Кеширование популярных постов в Redis
    * Инвалидация кеша при обновлении/удалении
    * Пагинация для списка постов
    
    Схема работы кеширования:
    1. При GET /posts/{id} сначала проверяется Redis
    2. Если пост есть в кеше - возвращается сразу
    3. Если нет - берется из PostgreSQL и сохраняется в Redis
    4. При PUT/PATCH/DELETE - кеш инвалидируется
    """,
    version="1.0.0",
    contact={
        "name": "Blog API Support",
        "email": "support@blogapi.com",
    },
    license_info={
        "name": "some info",
    },
    openapi_tags=[
        {
            "name": "posts",
            "description": "Операции с постами блога",
        },
        {
            "name": "health",
            "description": "Проверка состояния сервиса",
        }
    ],
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(posts.router)

@app.get(
    "/",
    tags=["health"],
    summary="Корневой эндпоинт",
    description="Возвращает приветственное сообщение и список доступных эндпоинтов",
    response_description="Информация о API"
)
async def root():
    return {
        "message": "Blog API с кэшированием",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "GET /posts/all": "Список всех постов с пагинацией",
            "GET /posts/{id}": "Получить пост по ID (с кешированием)",
            "POST /posts/": "Создать новый пост",
            "PUT /posts/{id}": "Обновить пост (инвалидирует кеш)",
            "DELETE /posts/{id}": "Удалить пост (инвалидирует кеш)",
            "GET /health": "Проверка здоровья сервиса"
        }
    }

@app.get(
    "/health",
    tags=["health"],
    summary="Проверка работоспособности сервиса",
    description="Проверяет подключение к PostgreSQL и Redis, а также наличие таблиц в БД",
    response_description="Статус всех компонентов системы"
)
async def health_check():
    """Проверка работоспособности сервиса"""

    health_status = {
        "status": "ok",
        "timestamp": time.time(),
        "components": {}
    }
    
    try:
        conn = await asyncpg.connect(
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            database=settings.POSTGRES_DB,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            timeout=3
        )
        
        tables = await conn.fetch("SELECT tablename FROM pg_tables WHERE schemaname='public'")
        await conn.close()
        
        tables_list = [table['tablename'] for table in tables]
        health_status["components"]["postgresql"] = {
            "status": "ok",
            "tables": tables_list,
            "tables_count": len(tables_list)
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["postgresql"] = {
            "status": "error",
            "error": str(e)
        }
    
    try:
        from app.infrastructure.cache.redis_client import redis_client
        await redis_client.ping()
        info = await redis_client.info()
        health_status["components"]["redis"] = {
            "status": "ok",
            "version": info.get("redis_version"),
            "connected_clients": info.get("connected_clients")
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["components"]["redis"] = {
            "status": "error",
            "error": str(e)
        }
    
    return health_status

async def wait_for_db():
    """Ожидание готовности БД и создание таблиц"""

    max_attempts = 60
    attempt = 0
    start_time = time.time()
    
    logger.info(f"Подключение к PostgreSQL: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    logger.info(f"База данных: {settings.POSTGRES_DB}, пользователь: {settings.POSTGRES_USER}")
    
    while attempt < max_attempts:
        try:
            conn = await asyncpg.connect(
                user=settings.POSTGRES_USER,
                password=settings.POSTGRES_PASSWORD,
                database=settings.POSTGRES_DB,
                host=settings.POSTGRES_HOST,
                port=settings.POSTGRES_PORT,
                timeout=5
            )

            result = await conn.fetchval("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'posts'
                )
            """)
            
            await conn.close()
            
            if result:
                elapsed = time.time() - start_time
                logger.info(f"Таблицы уже существуют (через {elapsed:.1f}с)")
                return True
            else:
                logger.warning(f"Таблицы ещё не созданы, ожидаем... (попытка {attempt + 1}/{max_attempts})")
                
        except asyncpg.PostgresError as e:
            logger.warning(f"Ошибка PostgreSQL: {e} (попытка {attempt + 1}/{max_attempts})")
        except ConnectionRefusedError:
            logger.warning(f"Подключение отклонено, PostgreSQL ещё не готов (попытка {attempt + 1}/{max_attempts})")
        except Exception as e:
            logger.warning(f"Неизвестная ошибка: {type(e).__name__}: {e} (попытка {attempt + 1}/{max_attempts})")
        
        attempt += 1
        await asyncio.sleep(2)
    
    elapsed = time.time() - start_time
    logger.error(f"Не удалось дождаться создания таблиц после {elapsed:.1f}с")
    return False

@app.on_event("startup")
async def init_db():
    """Инициализация БД при старте"""

    logger.info("Проверка готовности базы данных...")
    
    db_ready = await wait_for_db()
    if not db_ready:
        logger.error("Критическая ошибка: таблицы не созданы, пробуем создать самостоятельно")
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                logger.info("Таблицы созданы через SQLAlchemy")
        except Exception as e:
            logger.error(f"Не удалось создать таблицы: {e}")
            raise e
