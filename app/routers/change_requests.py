"""
routers/requests.py — 设置变更申请（普通用户提交，管理员审批）

GET    /api/change-requests          管理员：全部；普通用户：自己的
POST   /api/change-requests          创建申请（每用户最多 3 条待处理）
PUT    /api/change-requests/{id}     管理员批准 / 拒绝
DELETE /api/change-requests/{id}     用户撤销自己的待处理申请
"""
import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.models import ChangeRequest, OperationLog, User
from app.schemas.schemas import (
    ChangeRequestCreate, ChangeRequestUpdate, ChangeRequestOut, Resp
)

router = APIRouter(prefix="/api/change-requests", tags=["变更申请"])

MAX_PENDING = 3   # 每用户最多 3 条待处理申请


def _log(db, user, action):
    db.add(OperationLog(operator_id=user.id, operator_name=user.name, action=action))
    db.commit()


@router.get("", response_model=List[ChangeRequestOut])
def list_requests(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """管理员看全部；普通用户只看自己的"""
    q = db.query(ChangeRequest)
    if current.role != "admin":
        q = q.filter(ChangeRequest.user_id == current.id)
    return q.order_by(ChangeRequest.created_at.desc()).all()


@router.post("", response_model=ChangeRequestOut)
def create_request(
    req: ChangeRequestCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """提交变更申请，管理员无需申请可直接修改"""
    if current.role == "admin":
        raise HTTPException(400, "管理员可直接修改设置，无需申请")

    pending = db.query(ChangeRequest).filter(
        ChangeRequest.user_id == current.id,
        ChangeRequest.status  == "pending",
    ).count()
    if pending >= MAX_PENDING:
        raise HTTPException(
            400,
            f"待处理申请已达上限（{MAX_PENDING} 条），请等待管理员处理后再提交"
        )

    cr = ChangeRequest(
        user_id     = current.id,
        user_name   = current.name,
        description = req.description.strip(),
    )
    db.add(cr)
    db.commit()
    db.refresh(cr)
    _log(db, current, f"提交变更申请：{req.description[:60]}")
    return cr


@router.put("/{req_id}", response_model=ChangeRequestOut)
def handle_request(
    req_id: int,
    req: ChangeRequestUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(require_admin),
):
    """管理员审批"""
    cr = db.get(ChangeRequest, req_id)
    if not cr:
        raise HTTPException(404, "申请不存在")
    if cr.status != "pending":
        raise HTTPException(400, "该申请已处理")
    if req.status not in ("approved", "rejected"):
        raise HTTPException(400, "status 只能是 approved 或 rejected")

    cr.status = req.status
    if req.status == "approved":
        # 将授权信息（备注 + 有效期）存为 JSON，前端解析展示
        meta = {"note": req.admin_note or ""}
        if req.expires_hours and req.expires_hours > 0:
            expires_dt = datetime.now(timezone.utc) + timedelta(hours=req.expires_hours)
            meta["expires_at"] = expires_dt.isoformat()
        # expires_hours == 0 表示永久，不写 expires_at
        cr.admin_note = json.dumps(meta, ensure_ascii=False)
    else:
        cr.admin_note = req.admin_note
    db.commit()
    db.refresh(cr)
    verb = "批准" if req.status == "approved" else "拒绝"
    _log(db, current, f"{verb}变更申请 #{req_id}（{cr.user_name}）：{cr.description[:50]}")
    return cr


@router.delete("/{req_id}", response_model=Resp)
def cancel_request(
    req_id: int,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """用户撤销自己的待处理申请"""
    cr = db.get(ChangeRequest, req_id)
    if not cr:
        raise HTTPException(404, "申请不存在")
    if cr.user_id != current.id and current.role != "admin":
        raise HTTPException(403, "无权限")
    if cr.status != "pending":
        raise HTTPException(400, "只能撤销待处理的申请")
    db.delete(cr)
    db.commit()
    return Resp(msg="已撤销")
