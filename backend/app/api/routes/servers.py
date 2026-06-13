from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.models.server import Server, ServerMetric
from app.models.user import User
from app.api.deps import get_current_user, require_operator

router = APIRouter(prefix="/servers", tags=["servers"])


class ServerCreate(BaseModel):
    name: str
    hostname: str
    ip: str
    port: int = 22
    os: str = ""
    cpu_cores: int = 0
    memory_gb: float = 0.0
    disk_gb: float = 0.0
    environment: str = "prod"
    role: str = "app"
    region: str = ""
    provider: str = ""
    tags: dict = {}


@router.get("")
async def list_servers(environment: Optional[str] = None, role: Optional[str] = None,
                       db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(Server).order_by(Server.name)
    if environment:
        q = q.where(Server.environment == environment)
    if role:
        q = q.where(Server.role == role)
    result = await db.execute(q)
    servers = result.scalars().all()
    return [{"id": s.id, "name": s.name, "hostname": s.hostname, "ip": s.ip,
             "os": s.os, "cpu_cores": s.cpu_cores, "memory_gb": s.memory_gb,
             "environment": s.environment, "role": s.role, "region": s.region,
             "provider": s.provider, "status": s.status, "last_seen": s.last_seen} for s in servers]


@router.post("", status_code=201)
async def create_server(payload: ServerCreate, db: AsyncSession = Depends(get_db),
                        user: User = Depends(require_operator)):
    server = Server(**payload.model_dump())
    db.add(server)
    await db.flush()
    return {"id": server.id, "name": server.name}


@router.get("/{server_id}")
async def get_server(server_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Server).where(Server.id == server_id))
    server = result.scalar_one_or_none()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return server


@router.get("/{server_id}/metrics")
async def get_metrics(server_id: int, hours: int = 1, db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    from datetime import datetime, timedelta
    since = datetime.utcnow() - timedelta(hours=hours)
    result = await db.execute(
        select(ServerMetric)
        .where(ServerMetric.server_id == server_id, ServerMetric.recorded_at >= since)
        .order_by(ServerMetric.recorded_at)
    )
    metrics = result.scalars().all()
    return [{"recorded_at": m.recorded_at, "cpu_usage": m.cpu_usage,
             "mem_usage": m.mem_usage, "disk_usage": m.disk_usage,
             "net_in_mbps": m.net_in_mbps, "net_out_mbps": m.net_out_mbps,
             "load_avg": m.load_avg} for m in metrics]


@router.get("/stats/summary")
async def server_summary(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    total = await db.scalar(select(func.count(Server.id)))
    online = await db.scalar(select(func.count(Server.id)).where(Server.status == "online"))
    offline = await db.scalar(select(func.count(Server.id)).where(Server.status == "offline"))
    maintenance = await db.scalar(select(func.count(Server.id)).where(Server.status == "maintenance"))
    return {"total": total, "online": online, "offline": offline, "maintenance": maintenance}
