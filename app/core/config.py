"""
core/config.py — 应用配置，读取 .env 文件
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "库房管理系统"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = "sqlite:///./data/wms.db"

    SECRET_KEY: str = "change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    CORS_ORIGINS: str = "http://localhost,http://localhost:8080,http://127.0.0.1"

    DEFAULT_ADMIN_ID: str = "admin"
    DEFAULT_ADMIN_NAME: str = "管理员"
    DEFAULT_ADMIN_PASSWORD: str = "125521"

    DEFAULT_WARN_THRESHOLD: int = 10

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
