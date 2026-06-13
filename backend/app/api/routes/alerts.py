from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.models.alert import AlertRule, Alert
from app.models.user import User
from app.api.deps import get_current_user, require_operator

router = APIRouter(prefix="/alerts", tags=["alerts"])


class RuleCreate(BaseModel):
    name: str
    resource_type: str
    metric: str
    operator: str
    threshold: float
    duration_seconds: int = 60
    severity: str = "warning"
    channels: list = []


@router.get("/rules")
async def list_rules(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(AlertRule).order_by(AlertRule.name))
    rules = result.scalars().all()
    return [{"id": r.id, "name": r.name, "resource_type": r.resource_type,
             "metric": r.metric, "operator": r.operator, "threshold": r.threshold,
             "severity": r.severity, "is_active": r.is_active} for r in rules]


@router.post("/rules", status_code=201)
async def create_rule(payload: RuleCreate, db: AsyncSession = Depends(get_db),
                      user: User = Depends(require_operator)):
    rule = AlertRule(**payload.model_dump(), created_by=user.id)
    db.add(rule)
    await db.flush()
    return {"id": rule.id, "name": rule.name}


@router.put("/rules/{rule_id}/toggle")
async def toggle_rule(rule_id: int, db: AsyncSession = Depends(get_db),
                      user: User = Depends(require_operator)):
    result = await db.execute(select(AlertRule).where(AlertRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule.is_active = not rule.is_active
    return {"is_active": rule.is_active}


@router.get("")
async def list_alerts(status: Optional[str] = None, severity: Optional[str] = None,
                      limit: int = 50, db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    q = select(Alert).order_by(desc(Alert.fired_at)).limit(limit)
    if status:
        q = q.where(Alert.status == status)
    if severity:
        q = q.where(Alert.severity == severity)
    result = await db.execute(q)
    alerts = result.scalars().all()
    return [{"id": a.id, "title": a.title, "message": a.message,
             "severity": a.severity, "status": a.status,
             "resource_name": a.resource_name,
             "fired_at": a.fired_at, "resolved_at": a.resolved_at} for a in alerts]


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: int, db: AsyncSession = Depends(get_db),
                            user: User = Depends(get_current_user)):
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged_by = user.id
    return {"message": "Acknowledged"}


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: int, db: AsyncSession = Depends(get_db),
                        user: User = Depends(require_operator)):
    from datetime import datetime
    result = await db.execute(select(Alert).where(Alert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.status = "resolved"
    alert.resolved_at = datetime.utcnow()
    return {"message": "Resolved"}


@router.get("/stats/summary")
async def alert_summary(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    firing = await db.scalar(select(func.count(Alert.id)).where(Alert.status == "firing"))
    critical = await db.scalar(
        select(func.count(Alert.id)).where(Alert.status == "firing", Alert.severity == "critical"))
    warning = await db.scalar(
        select(func.count(Alert.id)).where(Alert.status == "firing", Alert.severity == "warning"))
    return {"firing": firing, "critical": critical, "warning": warning}
