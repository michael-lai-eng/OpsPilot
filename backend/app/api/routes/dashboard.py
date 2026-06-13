from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.db.session import get_db
from app.models.server import Server
from app.models.deployment import Deployment
from app.models.pipeline import PipelineRun
from app.models.alert import Alert
from app.models.task import TaskExecution
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
async def overview(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    servers_total = await db.scalar(select(func.count(Server.id)))
    servers_online = await db.scalar(select(func.count(Server.id)).where(Server.status == "online"))

    deps_total = await db.scalar(select(func.count(Deployment.id)))
    deps_healthy = await db.scalar(select(func.count(Deployment.id)).where(Deployment.health == "healthy"))

    alerts_firing = await db.scalar(select(func.count(Alert.id)).where(Alert.status == "firing"))
    alerts_critical = await db.scalar(
        select(func.count(Alert.id)).where(Alert.status == "firing", Alert.severity == "critical"))

    recent_runs_result = await db.execute(
        select(PipelineRun).order_by(desc(PipelineRun.created_at)).limit(5)
    )
    recent_runs = recent_runs_result.scalars().all()

    recent_tasks_result = await db.execute(
        select(TaskExecution).order_by(desc(TaskExecution.created_at)).limit(5)
    )
    recent_tasks = recent_tasks_result.scalars().all()

    return {
        "servers": {"total": servers_total, "online": servers_online,
                    "offline": servers_total - servers_online},
        "deployments": {"total": deps_total, "healthy": deps_healthy,
                        "unhealthy": deps_total - deps_healthy},
        "alerts": {"firing": alerts_firing, "critical": alerts_critical,
                   "warning": alerts_firing - alerts_critical},
        "recent_pipeline_runs": [
            {"id": r.id, "pipeline_id": r.pipeline_id, "status": r.status,
             "conclusion": r.conclusion, "triggered_by": r.triggered_by,
             "created_at": r.created_at} for r in recent_runs
        ],
        "recent_task_executions": [
            {"id": t.id, "title": t.title, "status": t.status,
             "created_at": t.created_at} for t in recent_tasks
        ],
    }
