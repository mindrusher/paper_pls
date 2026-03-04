# app/config.py
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database (POSTGRES)
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "blog_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "blog_pass")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "blog_db")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: str = os.getenv("POSTGRES_PORT", "5432")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: str = os.getenv("REDIS_PORT", "6379")
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        env_file = ".env"

settings = Settings()
