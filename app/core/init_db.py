"""
core/init_db.py — 首次启动初始化数据库
- 创建所有表
- 写入核心字段定义
- 创建默认管理员账号
- 写入默认系统配置
"""
import uuid
from sqlalchemy.orm import Session
from app.core.database import engine, Base
from app.core.security import hash_password
from app.core.config import settings
from app.models.models import User, FieldDefinition, SystemConfig


CORE_FIELDS = [
    dict(id="name",     label="物资名称", field_type="text",   is_required=True,  is_core=True,  options=None,                                          sort_order=1),
    dict(id="code",     label="物资编码", field_type="text",   is_required=True,  is_core=True,  options=None,                                          sort_order=2),
    dict(id="category", label="物资类别", field_type="select", is_required=True,  is_core=True,  options="办公用品,电子设备,工具,原材料,耗材,备件,劳保用品", sort_order=3),
    dict(id="spec",     label="规格型号", field_type="text",   is_required=False, is_core=False, options=None,                                          sort_order=4),
    dict(id="unit",     label="单位",     field_type="text",   is_required=True,  is_core=False, options=None,                                          sort_order=5),
    dict(id="qty",      label="入库数量", field_type="number", is_required=True,  is_core=True,  options=None,                                          sort_order=6),
    dict(id="location", label="存放位置", field_type="text",   is_required=False, is_core=False, options=None,                                          sort_order=7),
    dict(id="supplier", label="供应商",   field_type="text",   is_required=False, is_core=False, options=None,                                          sort_order=8),
    dict(id="price",    label="单价(元)", field_type="number", is_required=False, is_core=False, options=None,                                          sort_order=9),
    dict(id="expire",   label="保质期至", field_type="date",   is_required=False, is_core=False, options=None,                                          sort_order=10),
    dict(id="note",     label="备注",     field_type="text",   is_required=False, is_core=False, options=None,                                          sort_order=11),
]

DEFAULT_CONFIG = {
    "warehouse_name": "主仓库",
    "warn_threshold": str(settings.DEFAULT_WARN_THRESHOLD),
    "stock_unit": "件",
}


def init_db():
    """创建表 + 初始化数据（幂等，重复运行安全）"""
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        # 写入核心字段（已存在则跳过）
        for fd in CORE_FIELDS:
            if not db.get(FieldDefinition, fd["id"]):
                db.add(FieldDefinition(**fd))

        # 创建默认管理员（已存在则跳过）
        if not db.get(User, settings.DEFAULT_ADMIN_ID):
            db.add(User(
                id=settings.DEFAULT_ADMIN_ID,
                name=settings.DEFAULT_ADMIN_NAME,
                role="admin",
                password=hash_password(settings.DEFAULT_ADMIN_PASSWORD),
            ))

        # 写入默认配置（已存在则跳过）
        for key, val in DEFAULT_CONFIG.items():
            if not db.get(SystemConfig, key):
                db.add(SystemConfig(key=key, value=val))

        db.commit()
    print("✅ 数据库初始化完成")
