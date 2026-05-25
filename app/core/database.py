"""
core/database.py — 数据库连接与会话管理
支持 SQLite / MySQL / PostgreSQL，切换只需改 .env 中的 DATABASE_URL
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

# SQLite 需要特殊参数，其他数据库不需要
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,          # 改为 True 可在控制台看到 SQL 语句（调试用）
    pool_pre_ping=True,  # 自动检测断开的连接
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 依赖注入：获取数据库会话，请求结束后自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
