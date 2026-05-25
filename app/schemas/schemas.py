"""
schemas/schemas.py — 请求/响应数据验证（Pydantic v2）
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, field_validator



# ─────────────────────────────────────────────
# 通用响应
# ─────────────────────────────────────────────
class Resp(BaseModel):
    code: int = 0
    msg: str = "ok"
    data: Any = None


# ─────────────────────────────────────────────
# 认证
# ─────────────────────────────────────────────
class LoginReq(BaseModel):
    username: str
    password: str

class TokenResp(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    user_name: str
    role: str


# ─────────────────────────────────────────────
# 用户
# ─────────────────────────────────────────────
class UserCreate(BaseModel):
    id: str
    name: str
    role: str = "user"
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserOut(BaseModel):
    id: str
    name: str
    role: str
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# 字段定义
# ─────────────────────────────────────────────
class FieldCreate(BaseModel):
    id: Optional[str] = None
    label: str
    field_type: str = "text"
    is_required: bool = False
    options: Optional[str] = None
    sort_order: int = 0

class FieldOut(BaseModel):
    id: str
    label: str
    field_type: str
    is_required: bool
    is_core: bool
    options: Optional[str] = None
    sort_order: int

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# 库存物资
# ─────────────────────────────────────────────
class ItemCreate(BaseModel):
    name: str
    code: str
    category: Optional[str] = None
    spec: Optional[str] = None
    unit: Optional[str] = None
    qty: int
    location: Optional[str] = None
    supplier: Optional[str] = None
    price: Optional[float] = None
    expire_date: Optional[str] = None
    extra_data: Optional[str] = None # JSON 字符串
    note: Optional[str] = None

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    spec: Optional[str] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    supplier: Optional[str] = None
    price: Optional[float] = None
    expire_date: Optional[str] = None
    extra_data: Optional[str] = None
    note: Optional[str] = None

class ItemOut(BaseModel):
    id: str
    name: str
    code: str
    category: Optional[str] = None
    spec: Optional[str] = None
    unit: Optional[str] = None
    stock: int
    location: Optional[str] = None
    supplier: Optional[str] = None
    price: Optional[float] = None
    expire_date: Optional[str] = None
    extra_data: Optional[str] = None
    note: Optional[str] = None
    created_by: Optional[str] = None   # ★ 录入人 user.id，前端用于权限判断
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# 出入库记录
# ─────────────────────────────────────────────
class StockIn(BaseModel):
    item_id: Optional[str] = None    # 已有物资 ID（追加入库）
    qty: int
    note: Optional[str] = None

class StockOut(BaseModel):
    item_id: str
    qty: int
    receiver: Optional[str] = None
    note: Optional[str] = None

class RecordOut(BaseModel):
    id: str
    item_id: str
    item_name: Optional[str] = None
    item_code: Optional[str] = None
    record_type: str
    qty: int
    operator_name: Optional[str] = None
    receiver: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# 日志
# ─────────────────────────────────────────────
class LogOut(BaseModel):
    id: int
    operator_name: Optional[str] = None
    action: str
    ip_address: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
# 分析统计
# ─────────────────────────────────────────────
class AnalysisSummary(BaseModel):
    total_types: int
    total_stock: int
    warn_count: int
    today_ops: int
    total_value: float
    total_in: int
    total_out: int

class BarChartItem(BaseModel):
    label: str
    value: float

class TrendItem(BaseModel):
    date: str
    in_qty: int
    out_qty: int


# ─────────────────────────────────────────────
# 系统配置
# ─────────────────────────────────────────────
class ConfigUpdate(BaseModel):
    warehouse_name: Optional[str] = None
    warn_threshold: Optional[int] = None
    stock_unit: Optional[str] = None


# ─────────────────────────────────────────────
# 变更申请
# ─────────────────────────────────────────────
class ChangeRequestCreate(BaseModel):
    description: str

class ChangeRequestUpdate(BaseModel):
    status: str                        # approved / rejected
    admin_note: Optional[str] = None
    expires_hours: Optional[int] = None  # 批准时有效期（小时），0=永久

class ChangeRequestOut(BaseModel):
    id: int
    user_id: str
    user_name: str
    description: str
    status: str
    admin_note: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
