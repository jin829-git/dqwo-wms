"""
routers/config.py  — 系统配置 & 操作日志接口
GET  /api/config         获取所有配置
PUT  /api/config         更新配置（管理员）
GET  /api/logs           操作日志列表（管理员）
DELETE /api/logs         清空日志（管理员）
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.models import SystemConfig, OperationLog, User
from app.schemas.schemas import ConfigUpdate, LogOut, Resp

router = APIRouter(tags=["配置与日志"])


# ── 系统配置 ────────────────────────────────
@router.get("/api/config")
def get_config(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = db.query(SystemConfig).all()
    return {r.key: r.value for r in rows}


@router.put("/api/config", response_model=Resp)
def update_config(req: ConfigUpdate, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    def _set(key, val):
        if val is None:
            return
        row = db.get(SystemConfig, key)
        if row:
            row.value = str(val)
        else:
            db.add(SystemConfig(key=key, value=str(val)))
    _set("warehouse_name", req.warehouse_name)
    _set("warn_threshold", req.warn_threshold)
    _set("stock_unit", req.stock_unit)
    db.add(OperationLog(operator_id=current.id, operator_name=current.name, action="修改系统配置"))
    db.commit()
    return Resp(msg="配置已保存")


# ── 操作日志 ────────────────────────────────
@router.get("/api/logs")
def list_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    total = db.query(OperationLog).count()
    logs  = db.query(OperationLog).order_by(OperationLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "logs": [LogOut.model_validate(l) for l in logs]}


@router.delete("/api/logs", response_model=Resp)
def clear_logs(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    db.query(OperationLog).delete()
    db.commit()
    return Resp(msg="日志已清空")
