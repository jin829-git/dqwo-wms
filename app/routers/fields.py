"""
routers/fields.py — 自定义字段管理（管理员专用）
GET    /api/fields        获取所有字段定义
POST   /api/fields        添加自定义字段
PUT    /api/fields/{id}   修改字段（仅非核心字段）
DELETE /api/fields/{id}   删除字段（仅非核心字段）
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.models import FieldDefinition, OperationLog, User
from app.schemas.schemas import FieldCreate, FieldOut, Resp

router = APIRouter(prefix="/api/fields", tags=["字段管理"])


def _log(db, user, action):
    db.add(OperationLog(operator_id=user.id, operator_name=user.name, action=action))
    db.commit()


@router.get("", response_model=List[FieldOut])
def list_fields(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(FieldDefinition).order_by(FieldDefinition.sort_order, FieldDefinition.created_at).all()


@router.post("", response_model=FieldOut)
def create_field(req: FieldCreate, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    fid = req.id or ("f_" + uuid.uuid4().hex[:8])
    if db.get(FieldDefinition, fid):
        raise HTTPException(status_code=400, detail="字段ID已存在")
    # 自动排到末尾：取当前最大 sort_order + 1
    max_order = db.query(func.max(FieldDefinition.sort_order)).scalar() or 0
    field = FieldDefinition(
        id=fid, label=req.label, field_type=req.field_type,
        is_required=req.is_required, is_core=False,
        options=req.options, sort_order=max_order + 1
    )
    db.add(field)
    _log(db, current, f"添加字段：{req.label}")
    return field


@router.put("/{field_id}", response_model=FieldOut)
def update_field(field_id: str, req: FieldCreate, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    field = db.get(FieldDefinition, field_id)
    if not field:
        raise HTTPException(status_code=404, detail="字段不存在")
    if field.is_core:
        # 核心字段只允许更新 select 类型的 options（如物资类别的下拉选项）
        if field.field_type != 'select':
            raise HTTPException(status_code=400, detail="核心字段不可修改")
        field.options = req.options
        _log(db, current, f"更新核心字段选项：{field_id}")
        db.commit()
        db.refresh(field)
        return field
    field.label       = req.label
    field.field_type  = req.field_type
    field.is_required = req.is_required
    field.options     = req.options
    field.sort_order  = req.sort_order
    _log(db, current, f"修改字段：{field_id}")
    db.commit()
    db.refresh(field)
    return field


@router.delete("/{field_id}", response_model=Resp)
def delete_field(field_id: str, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    field = db.get(FieldDefinition, field_id)
    if not field:
        raise HTTPException(status_code=404, detail="字段不存在")
    if field.is_core:
        raise HTTPException(status_code=400, detail="核心字段不可删除")
    db.delete(field)
    _log(db, current, f"删除字段：{field.label}")
    return Resp(msg="已删除")
