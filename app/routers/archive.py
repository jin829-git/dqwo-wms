"""
routers/archive.py — 出入库档案查询
GET /api/archive   全量流水记录（支持筛选/分页）
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import StockRecord, InventoryItem, User
from app.schemas.schemas import RecordOut

router = APIRouter(prefix="/api/archive", tags=["出入库档案"])


@router.get("", response_model=dict)
def list_archive(
    q: Optional[str] = Query(None),
    record_type: Optional[str] = Query(None, description="in/out"),
    date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    query = db.query(StockRecord).join(InventoryItem, StockRecord.item_id == InventoryItem.id, isouter=True)
    if q:
        query = query.filter(or_(
            InventoryItem.name.ilike(f"%{q}%"),
            StockRecord.operator_name.ilike(f"%{q}%"),
            StockRecord.receiver.ilike(f"%{q}%"),
        ))
    if record_type:
        query = query.filter(StockRecord.record_type == record_type)
    if date:
        query = query.filter(StockRecord.created_at.like(f"{date}%"))

    total = query.count()
    records = query.order_by(StockRecord.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    result = []
    for r in records:
        d = RecordOut.model_validate(r)
        if r.item:
            d.item_name = r.item.name
            d.item_code = r.item.code
        result.append(d)
    return {"total": total, "page": page, "page_size": page_size, "records": result}
