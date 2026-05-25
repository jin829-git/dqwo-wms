"""
routers/inventory.py — 库存物资 CRUD + 出入库
GET    /api/inventory                  查询库存列表（支持搜索/筛选/分页）
POST   /api/inventory                  新增物资并入库
GET    /api/inventory/{id}             获取单个物资详情
PUT    /api/inventory/{id}             更新物资基础信息（不含库存）
DELETE /api/inventory/{id}             删除物资（管理员）
POST   /api/inventory/{id}/stock-in    追加入库
POST   /api/inventory/{id}/stock-out   出库
GET    /api/inventory/{id}/records     该物资的出入库流水

权限说明：
  - PUT（编辑）：管理员 或 该物资的录入人（created_by）均可操作
  - DELETE（删除）：仅管理员
"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.models.models import InventoryItem, StockRecord, OperationLog, User
from app.schemas.schemas import (
    ItemCreate, ItemUpdate, ItemOut,
    StockIn, StockOut, RecordOut, Resp
)

router = APIRouter(prefix="/api/inventory", tags=["库存管理"])


def _log(db, user, action):
    db.add(OperationLog(operator_id=user.id, operator_name=user.name, action=action))
    db.commit()


def _make_record(item, rtype, qty, user, receiver=None, note=None):
    return StockRecord(
        id=uuid.uuid4().hex,
        item_id=item.id,
        record_type=rtype,
        qty=qty,
        operator_id=user.id,
        operator_name=user.name,
        receiver=receiver,
        note=note,
    )


# ── 列表查询 ─────────────────────────────────
@router.get("", response_model=dict)
def list_inventory(
    q: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="ok/low/empty"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    from app.models.models import SystemConfig
    cfg_row = db.get(SystemConfig, "warn_threshold")
    thresh = int(cfg_row.value) if cfg_row else 10

    query = db.query(InventoryItem)
    if q:
        query = query.filter(or_(
            InventoryItem.name.ilike(f"%{q}%"),
            InventoryItem.code.ilike(f"%{q}%"),
            InventoryItem.category.ilike(f"%{q}%"),
            InventoryItem.spec.ilike(f"%{q}%"),
            InventoryItem.supplier.ilike(f"%{q}%"),
            InventoryItem.location.ilike(f"%{q}%"),
        ))
    if category:
        query = query.filter(InventoryItem.category == category)
    if status == "ok":
        query = query.filter(InventoryItem.stock > thresh)
    elif status == "low":
        query = query.filter(InventoryItem.stock > 0, InventoryItem.stock <= thresh)
    elif status == "empty":
        query = query.filter(InventoryItem.stock <= 0)

    total = query.count()
    items = query.order_by(InventoryItem.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    # ★ ItemOut 现在包含 created_by，前端可据此判断是否显示编辑按钮
    return {"total": total, "page": page, "page_size": page_size,
            "items": [ItemOut.model_validate(i) for i in items]}


# ── 新建物资 + 首次入库 ──────────────────────
@router.post("", response_model=ItemOut)
def create_item(req: ItemCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    if req.code and db.query(InventoryItem).filter_by(code=req.code).first():
        raise HTTPException(status_code=400, detail=f"编码 {req.code} 已存在，请用追加入库接口")

    item = InventoryItem(
        id=uuid.uuid4().hex,
        name=req.name, code=req.code, category=req.category,
        spec=req.spec, unit=req.unit, stock=req.qty,
        location=req.location, supplier=req.supplier,
        price=req.price, expire_date=req.expire_date,
        extra_data=req.extra_data, note=req.note,
        created_by=current.id,   # ★ 记录录入人
    )
    db.add(item)
    db.flush()
    db.add(_make_record(item, "in", req.qty, current, note=req.note))
    _log(db, current, f"新建物资并入库：{req.name}（{req.code}）× {req.qty}")
    db.refresh(item)
    return item


# ── 单个物资详情 ────────────────────────────
@router.get("/{item_id}", response_model=ItemOut)
def get_item(item_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物资不存在")
    return item


# ── 更新物资基础信息 ─────────────────────────
# ★ 权限：管理员 或 该物资录入人，后端双重校验
@router.put("/{item_id}", response_model=ItemOut)
def update_item(
    item_id: str,
    req: ItemUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物资不存在")

    # ★ 权限校验：非管理员只能编辑自己录入的物资
    if current.role != "admin" and item.created_by != current.id:
        raise HTTPException(status_code=403, detail="无权限：只能编辑自己录入的物资")

    for field, val in req.model_dump(exclude_none=True).items():
        setattr(item, field, val)
    _log(db, current, f"修改物资信息：{item.name}")
    db.commit()
    db.refresh(item)
    return item


# ── 删除物资（仅管理员）────────────────────
@router.delete("/{item_id}", response_model=Resp)
def delete_item(item_id: str, db: Session = Depends(get_db), current: User = Depends(require_admin)):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物资不存在")
    db.delete(item)
    _log(db, current, f"删除物资：{item.name}（{item.code}）")
    return Resp(msg="已删除")


# ── 追加入库 ────────────────────────────────
@router.post("/{item_id}/stock-in", response_model=ItemOut)
def stock_in(item_id: str, req: StockIn, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物资不存在")
    if req.qty <= 0:
        raise HTTPException(status_code=400, detail="入库数量必须 > 0")
    item.stock += req.qty
    db.add(_make_record(item, "in", req.qty, current, note=req.note))
    _log(db, current, f"入库：{item.name} × {req.qty}")
    db.commit()
    db.refresh(item)
    return item


# ── 出库 ────────────────────────────────────
@router.post("/{item_id}/stock-out", response_model=ItemOut)
def stock_out(item_id: str, req: StockOut, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物资不存在")
    if req.qty <= 0:
        raise HTTPException(status_code=400, detail="出库数量必须 > 0")
    if item.stock < req.qty:
        raise HTTPException(status_code=400, detail=f"库存不足，当前库存：{item.stock}")
    item.stock -= req.qty
    db.add(_make_record(item, "out", req.qty, current, receiver=req.receiver, note=req.note))
    _log(db, current, f"出库：{item.name} × {req.qty}，领用人：{req.receiver or '未填写'}")
    db.commit()
    db.refresh(item)
    return item


# ── 单品流水记录 ────────────────────────────
@router.get("/{item_id}/records", response_model=List[RecordOut])
def item_records(item_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    item = db.get(InventoryItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物资不存在")
    records = db.query(StockRecord).filter_by(item_id=item_id).order_by(StockRecord.created_at.desc()).limit(200).all()
    result = []
    for r in records:
        d = RecordOut.model_validate(r)
        d.item_name = item.name
        d.item_code = item.code
        result.append(d)
    return result
