"""
routers/auth.py — 认证接口
POST /api/auth/login  登录，返回 JWT Token
GET  /api/auth/me     获取当前用户信息
POST /api/auth/logout 退出（记录日志）
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import verify_password, create_access_token
from app.core.deps import get_current_user
from app.models.models import User, OperationLog
from app.schemas.schemas import LoginReq, TokenResp, UserOut, Resp

router = APIRouter(prefix="/api/auth", tags=["认证"])


def _add_log(db: Session, user: User, action: str, ip: str = None):
    db.add(OperationLog(operator_id=user.id, operator_name=user.name, action=action, ip_address=ip))
    db.commit()


@router.post("/login", response_model=TokenResp)
def login(req: LoginReq, request: Request, db: Session = Depends(get_db)):
    user = db.get(User, req.username)
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已停用，请联系管理员")

    user.last_login = datetime.now(timezone.utc)
    db.commit()
    ip = request.client.host if request.client else None
    _add_log(db, user, "登录系统", ip)

    token = create_access_token({"sub": user.id})
    return TokenResp(access_token=token, user_id=user.id, user_name=user.name, role=user.role)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout", response_model=Resp)
def logout(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ip = request.client.host if request.client else None
    _add_log(db, current_user, "退出登录", ip)
    return Resp(msg="已退出")
