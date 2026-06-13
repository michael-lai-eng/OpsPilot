from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.models.pipeline import Pipeline, PipelineRun
from app.models.user import User
from app.api.deps import get_current_user, require_operator
from app.services.github_service import GitHubService

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


class PipelineCreate(BaseModel):
    name: str
    repo: str
    branch: str = "main"
    workflow_file: str
    description: str = ""
    tags: list = []


class TriggerPayload(BaseModel):
    ref: str = "main"
    inputs: dict = {}


@router.get("")
async def list_pipelines(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Pipeline).order_by(desc(Pipeline.created_at)))
    pipelines = result.scalars().all()
    return [{"id": p.id, "name": p.name, "repo": p.repo, "branch": p.branch,
             "workflow_file": p.workflow_file, "description": p.description, "tags": p.tags} for p in pipelines]


@router.post("", status_code=201)
async def create_pipeline(payload: PipelineCreate, db: AsyncSession = Depends(get_db),
                          user: User = Depends(require_operator)):
    pipeline = Pipeline(**payload.model_dump(), created_by=user.id)
    db.add(pipeline)
    await db.flush()
    return {"id": pipeline.id, "name": pipeline.name}


@router.get("/{pipeline_id}/runs")
async def get_runs(pipeline_id: int, limit: int = 20, db: AsyncSession = Depends(get_db),
                   user: User = Depends(get_current_user)):
    result = await db.execute(
        select(PipelineRun)
        .where(PipelineRun.pipeline_id == pipeline_id)
        .order_by(desc(PipelineRun.created_at))
        .limit(limit)
    )
    runs = result.scalars().all()
    return [{"id": r.id, "run_number": r.run_number, "github_run_id": r.github_run_id,
             "status": r.status, "conclusion": r.conclusion, "triggered_by": r.triggered_by,
             "commit_sha": r.commit_sha, "commit_msg": r.commit_msg,
             "duration_seconds": r.duration_seconds, "logs_url": r.logs_url,
             "started_at": r.started_at, "finished_at": r.finished_at} for r in runs]


@router.post("/{pipeline_id}/trigger")
async def trigger_pipeline(pipeline_id: int, payload: TriggerPayload,
                           background_tasks: BackgroundTasks,
                           db: AsyncSession = Depends(get_db),
                           user: User = Depends(require_operator)):
    result = await db.execute(select(Pipeline).where(Pipeline.id == pipeline_id))
    pipeline = result.scalar_one_or_none()
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    github = GitHubService()
    run_id = await github.trigger_workflow(pipeline.repo, pipeline.workflow_file, payload.ref, payload.inputs)

    run = PipelineRun(
        pipeline_id=pipeline_id,
        run_number=0,
        github_run_id=run_id,
        status="queued",
        triggered_by=user.username,
    )
    db.add(run)
    await db.flush()
    return {"run_id": run.id, "github_run_id": run_id, "status": "queued"}


@router.get("/{pipeline_id}/runs/{run_id}/sync")
async def sync_run(pipeline_id: int, run_id: int, db: AsyncSession = Depends(get_db),
                   user: User = Depends(get_current_user)):
    """Pull latest status from GitHub and update local record."""
    result = await db.execute(
        select(PipelineRun, Pipeline)
        .join(Pipeline, Pipeline.id == PipelineRun.pipeline_id)
        .where(PipelineRun.id == run_id)
    )
    row = result.one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Run not found")
    run, pipeline = row

    if run.github_run_id:
        github = GitHubService()
        data = await github.get_run_status(pipeline.repo, run.github_run_id)
        run.status = data.get("status", run.status)
        run.conclusion = data.get("conclusion")
        run.run_number = data.get("run_number", run.run_number)
    return {"status": run.status, "conclusion": run.conclusion}
