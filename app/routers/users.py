"""
routers/users.py — 用户管理接口（管理员专用）
GET    /api/users          获取用户列表
POST   /api/users          创建用户
PUT    /api/users/{id}     更新用户（改名/角色/密码/状态）
DELETE /api/users/{id}     删除用户
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.core.security import hash_password
from app.models.models import User, OperationLog
from app.schemas.schemas import UserCreate, UserUpdate, UserOut, Resp

router = APIRouter(prefix="/api/users", tags=["用户管理"])


def _log(db, user, action):
    db.add(OperationLog(operator_id=user.id, operator_name=user.name, action=action))
    db.commit()


@router.get("", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return db.query(User).order_by(User.created_at).all()


@router.post("", response_model=UserOut)
def create_user(req: UserCreate, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    if db.get(User, req.id):
        raise HTTPException(status_code=400, detail="账号ID已存在")
    user = User(id=req.id, name=req.name, role=req.role, password=hash_password(req.password))
    db.add(user)
    _log(db, current, f"创建账号：{req.id}（{req.name}）")
    return user


@router.put("/{user_id}", response_model=UserOut)
def update_user(user_id: str, req: UserUpdate, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user_id == "admin" and req.role and req.role != "admin":
        raise HTTPException(status_code=400, detail="不能修改系统管理员角色")
    if req.name is not None:     user.name = req.name
    if req.role is not None:     user.role = req.role
    if req.is_active is not None: user.is_active = req.is_active
    if req.password:             user.password = hash_password(req.password)
    _log(db, current, f"修改账号：{user_id}")
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=Resp)
def delete_user(user_id: str, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    if user_id == "admin":
        raise HTTPException(status_code=400, detail="不能删除系统管理员")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(user)
    _log(db, current, f"删除账号：{user_id}")
    return Resp(msg="已删除")
