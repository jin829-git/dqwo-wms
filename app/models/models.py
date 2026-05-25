"""
models/models.py — 数据库表模型（SQLAlchemy ORM）
新增表：直接在此文件添加 class，然后运行 alembic upgrade head 迁移
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean,
    DateTime, Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from app.core.database import Base


def now_utc():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id          = Column(String(50), primary_key=True)
    name        = Column(String(100), nullable=False)
    role        = Column(Enum("admin", "user"), default="user")
    password    = Column(String(200), nullable=False)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime(timezone=True), default=now_utc)
    last_login  = Column(DateTime(timezone=True), nullable=True)

    logs = relationship("OperationLog", back_populates="operator_user", foreign_keys="OperationLog.operator_id")


class FieldDefinition(Base):
    __tablename__ = "field_definitions"

    id          = Column(String(50), primary_key=True)
    label       = Column(String(100), nullable=False)
    field_type  = Column(String(20), default="text")
    is_required = Column(Boolean, default=False)
    is_core     = Column(Boolean, default=False)
    options     = Column(Text, nullable=True)
    sort_order  = Column(Integer, default=0)
    created_at  = Column(DateTime(timezone=True), default=now_utc)


class InventoryItem(Base):
    __tablename__ = "inventory"

    id          = Column(String(50), primary_key=True)
    name        = Column(String(200), nullable=False, index=True)
    code        = Column(String(100), unique=True, index=True)
    category    = Column(String(100), index=True)
    spec        = Column(String(200))
    unit        = Column(String(20))
    stock       = Column(Integer, default=0)
    location    = Column(String(100))
    supplier    = Column(String(200))
    price       = Column(Float, nullable=True)
    expire_date = Column(String(20), nullable=True)
    extra_data  = Column(Text, nullable=True)
    note        = Column(Text)

    # ★ 新增：记录首次创建者（录入人）
    created_by  = Column(String(50), ForeignKey("users.id"), nullable=True)

    created_at  = Column(DateTime(timezone=True), default=now_utc)
    updated_at  = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)

    records = relationship("StockRecord", back_populates="item", cascade="all, delete-orphan")


class StockRecord(Base):
    __tablename__ = "stock_records"

    id           = Column(String(50), primary_key=True)
    item_id      = Column(String(50), ForeignKey("inventory.id"), nullable=False)
    record_type  = Column(Enum("in", "out"), nullable=False)
    qty          = Column(Integer, nullable=False)
    operator_id  = Column(String(50), ForeignKey("users.id"))
    operator_name= Column(String(100))
    receiver     = Column(String(100))
    note         = Column(Text)
    created_at   = Column(DateTime(timezone=True), default=now_utc)

    item         = relationship("InventoryItem", back_populates="records")


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id           = Column(Integer, primary_key=True, autoincrement=True)
    operator_id  = Column(String(50), ForeignKey("users.id"), nullable=True)
    operator_name= Column(String(100))
    action       = Column(String(500), nullable=False)
    ip_address   = Column(String(50), nullable=True)
    created_at   = Column(DateTime(timezone=True), default=now_utc)

    operator_user = relationship("User", back_populates="logs", foreign_keys=[operator_id])


class SystemConfig(Base):
    __tablename__ = "system_config"

    key         = Column(String(100), primary_key=True)
    value       = Column(Text)
    updated_at  = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)


class ChangeRequest(Base):
    """普通用户提交的设置变更申请，管理员审批"""
    __tablename__ = "change_requests"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(String(50), ForeignKey("users.id"), nullable=False)
    user_name   = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)          # 申请内容描述
    status      = Column(String(20), default="pending") # pending / approved / rejected
    admin_note  = Column(Text, nullable=True)           # 管理员回复
    created_at  = Column(DateTime(timezone=True), default=now_utc)
    updated_at  = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc)
