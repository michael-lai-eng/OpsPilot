from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.models.deployment import Environment, Deployment, DeploymentHistory
from app.models.user import User
from app.api.deps import get_current_user, require_operator
from app.services.k8s_service import K8sService

router = APIRouter(prefix="/deployments", tags=["deployments"])


class DeployPayload(BaseModel):
    image: str
    replicas: Optional[int] = None
    note: str = ""


class ScalePayload(BaseModel):
    replicas: int


@router.get("/environments")
async def list_environments(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Environment).order_by(Environment.name))
    envs = result.scalars().all()
    return [{"id": e.id, "name": e.name, "cluster": e.cluster,
             "namespace": e.namespace, "is_protected": e.is_protected} for e in envs]


@router.get("")
async def list_deployments(env_id: Optional[int] = None, db: AsyncSession = Depends(get_db),
                           user: User = Depends(get_current_user)):
    q = select(Deployment).order_by(desc(Deployment.deployed_at))
    if env_id:
        q = q.where(Deployment.environment_id == env_id)
    result = await db.execute(q)
    deps = result.scalars().all()
    return [{"id": d.id, "name": d.name, "service": d.service, "image": d.image,
             "replicas": d.replicas, "ready_replicas": d.ready_replicas,
             "status": d.status, "health": d.health,
             "environment_id": d.environment_id, "deployed_at": d.deployed_at} for d in deps]


@router.get("/{dep_id}")
async def get_deployment(dep_id: int, db: AsyncSession = Depends(get_db),
                         user: User = Depends(get_current_user)):
    result = await db.execute(select(Deployment).where(Deployment.id == dep_id))
    dep = result.scalar_one_or_none()
    if not dep:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return dep


@router.post("/{dep_id}/deploy")
async def deploy(dep_id: int, payload: DeployPayload, db: AsyncSession = Depends(get_db),
                 user: User = Depends(require_operator)):
    result = await db.execute(
        select(Deployment, Environment)
        .join(Environment, Environment.id == Deployment.environment_id)
        .where(Deployment.id == dep_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Deployment not found")
    dep, env = row

    k8s = K8sService(env.cluster)
    await k8s.update_image(env.namespace, dep.service, payload.image)

    history = DeploymentHistory(
        deployment_id=dep.id,
        action="deploy",
        prev_image=dep.image,
        new_image=payload.image,
        status="success",
        performed_by=user.id,
        note=payload.note,
    )
    dep.image = payload.image
    dep.status = "running"
    if payload.replicas:
        dep.replicas = payload.replicas
    db.add(history)
    return {"message": "Deployment triggered", "image": payload.image}


@router.post("/{dep_id}/rollback")
async def rollback(dep_id: int, db: AsyncSession = Depends(get_db),
                   user: User = Depends(require_operator)):
    result = await db.execute(select(Deployment).where(Deployment.id == dep_id))
    dep = result.scalar_one_or_none()
    if not dep:
        raise HTTPException(status_code=404, detail="Deployment not found")

    hist_result = await db.execute(
        select(DeploymentHistory)
        .where(DeploymentHistory.deployment_id == dep_id, DeploymentHistory.action == "deploy")
        .order_by(desc(DeploymentHistory.created_at))
        .limit(2)
    )
    history_list = hist_result.scalars().all()
    if len(history_list) < 2:
        raise HTTPException(status_code=400, detail="No previous version to rollback to")

    prev_image = history_list[1].new_image
    env_result = await db.execute(select(Environment).where(Environment.id == dep.environment_id))
    env = env_result.scalar_one()

    k8s = K8sService(env.cluster)
    await k8s.update_image(env.namespace, dep.service, prev_image)

    rollback_history = DeploymentHistory(
        deployment_id=dep.id,
        action="rollback",
        prev_image=dep.image,
        new_image=prev_image,
        status="success",
        performed_by=user.id,
    )
    dep.image = prev_image
    db.add(rollback_history)
    return {"message": "Rollback triggered", "image": prev_image}


@router.post("/{dep_id}/scale")
async def scale(dep_id: int, payload: ScalePayload, db: AsyncSession = Depends(get_db),
                user: User = Depends(require_operator)):
    result = await db.execute(
        select(Deployment, Environment)
        .join(Environment, Environment.id == Deployment.environment_id)
        .where(Deployment.id == dep_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Deployment not found")
    dep, env = row

    k8s = K8sService(env.cluster)
    await k8s.scale(env.namespace, dep.service, payload.replicas)

    history = DeploymentHistory(
        deployment_id=dep.id,
        action="scale",
        prev_replicas=dep.replicas,
        new_replicas=payload.replicas,
        status="success",
        performed_by=user.id,
    )
    dep.replicas = payload.replicas
    db.add(history)
    return {"message": f"Scaled to {payload.replicas} replicas"}


@router.get("/{dep_id}/history")
async def get_history(dep_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(DeploymentHistory)
        .where(DeploymentHistory.deployment_id == dep_id)
        .order_by(desc(DeploymentHistory.created_at))
        .limit(20)
    )
    return result.scalars().all()
