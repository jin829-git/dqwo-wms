"""
routers/analysis.py — 数据分析统计接口
GET /api/analysis/summary    汇总数据
GET /api/analysis/stock-top  库存量 Top N
GET /api/analysis/category   类别分布
GET /api/analysis/trend      近 N 日趋势
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.models import InventoryItem, StockRecord, SystemConfig, User
from app.schemas.schemas import AnalysisSummary, BarChartItem, TrendItem

router = APIRouter(prefix="/api/analysis", tags=["数据分析"])

def _thresh(db):
    row = db.get(SystemConfig, "warn_threshold")
    return int(row.value) if row else 10


@router.get("/summary", response_model=AnalysisSummary)
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    thresh = _thresh(db)
    items = db.query(InventoryItem).all()
    total_types = len(items)
    total_stock = sum(i.stock for i in items)
    warn_count  = sum(1 for i in items if i.stock <= thresh)
    total_value = sum((i.stock * (i.price or 0)) for i in items)

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_ops = db.query(StockRecord).filter(StockRecord.created_at >= today_start).count()

    total_in  = db.query(func.sum(StockRecord.qty)).filter_by(record_type="in").scalar() or 0
    total_out = db.query(func.sum(StockRecord.qty)).filter_by(record_type="out").scalar() or 0

    return AnalysisSummary(
        total_types=total_types, total_stock=total_stock,
        warn_count=warn_count, today_ops=today_ops,
        total_value=total_value, total_in=total_in, total_out=total_out,
    )


@router.get("/stock-top", response_model=List[BarChartItem])
def stock_top(n: int = Query(8, ge=1, le=50), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    items = db.query(InventoryItem).order_by(InventoryItem.stock.desc()).limit(n).all()
    return [BarChartItem(label=i.name, value=i.stock) for i in items]


@router.get("/category", response_model=List[BarChartItem])
def category_dist(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = (db.query(InventoryItem.category, func.sum(InventoryItem.stock))
              .group_by(InventoryItem.category)
              .order_by(func.sum(InventoryItem.stock).desc()).all())
    return [BarChartItem(label=(r[0] or "未分类"), value=r[1] or 0) for r in rows]


@router.get("/trend", response_model=List[TrendItem])
def trend(days: int = Query(7, ge=1, le=90), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    result = []
    now = datetime.now(timezone.utc)
    for d in range(days - 1, -1, -1):
        day_start = (now - timedelta(days=d)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end   = day_start + timedelta(days=1)
        in_qty  = db.query(func.sum(StockRecord.qty)).filter(
            StockRecord.record_type == "in",
            StockRecord.created_at >= day_start,
            StockRecord.created_at < day_end
        ).scalar() or 0
        out_qty = db.query(func.sum(StockRecord.qty)).filter(
            StockRecord.record_type == "out",
            StockRecord.created_at >= day_start,
            StockRecord.created_at < day_end
        ).scalar() or 0
        result.append(TrendItem(date=day_start.strftime("%m/%d"), in_qty=in_qty, out_qty=out_qty))
    return result
