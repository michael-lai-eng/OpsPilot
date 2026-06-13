from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
from app.db.session import get_db
from app.models.task import Runbook, TaskExecution
from app.models.user import User
from app.api.deps import get_current_user, require_operator

router = APIRouter(prefix="/tasks", tags=["tasks"])


class RunbookCreate(BaseModel):
    name: str
    category: str = "misc"
    description: str = ""
    script: str
    script_type: str = "bash"
    params_schema: dict = {}
    timeout_seconds: int = 300
    requires_approval: bool = False


class ExecutePayload(BaseModel):
    title: str = ""
    params: dict = {}
    target_servers: list = []


@router.get("/runbooks")
async def list_runbooks(category: Optional[str] = None, db: AsyncSession = Depends(get_db),
                        user: User = Depends(get_current_user)):
    q = select(Runbook).order_by(Runbook.name)
    if category:
        q = q.where(Runbook.category == category)
    result = await db.execute(q)
    books = result.scalars().all()
    return [{"id": b.id, "name": b.name, "category": b.category,
             "description": b.description, "script_type": b.script_type,
             "params_schema": b.params_schema, "requires_approval": b.requires_approval,
             "timeout_seconds": b.timeout_seconds} for b in books]


@router.post("/runbooks", status_code=201)
async def create_runbook(payload: RunbookCreate, db: AsyncSession = Depends(get_db),
                         user: User = Depends(require_operator)):
    book = Runbook(**payload.model_dump(), created_by=user.id)
    db.add(book)
    await db.flush()
    return {"id": book.id, "name": book.name}


@router.get("/runbooks/{book_id}")
async def get_runbook(book_id: int, db: AsyncSession = Depends(get_db),
                      user: User = Depends(get_current_user)):
    result = await db.execute(select(Runbook).where(Runbook.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Runbook not found")
    return book


@router.post("/runbooks/{book_id}/execute", status_code=202)
async def execute_runbook(book_id: int, payload: ExecutePayload,
                          db: AsyncSession = Depends(get_db),
                          user: User = Depends(require_operator)):
    result = await db.execute(select(Runbook).where(Runbook.id == book_id))
    book = result.scalar_one_or_none()
    if not book:
        raise HTTPException(status_code=404, detail="Runbook not found")

    initial_status = "pending" if book.requires_approval else "running"
    execution = TaskExecution(
        runbook_id=book_id,
        title=payload.title or book.name,
        params=payload.params,
        target_servers=payload.target_servers,
        status=initial_status,
        triggered_by=user.id,
    )
    db.add(execution)
    await db.flush()

    if initial_status == "running":
        from app.workers.task_worker import run_task
        run_task.delay(execution.id)

    return {"execution_id": execution.id, "status": initial_status}


@router.get("/executions")
async def list_executions(runbook_id: Optional[int] = None, limit: int = 30,
                          db: AsyncSession = Depends(get_db),
                          user: User = Depends(get_current_user)):
    q = select(TaskExecution).order_by(desc(TaskExecution.created_at)).limit(limit)
    if runbook_id:
        q = q.where(TaskExecution.runbook_id == runbook_id)
    result = await db.execute(q)
    execs = result.scalars().all()
    return [{"id": e.id, "runbook_id": e.runbook_id, "title": e.title,
             "status": e.status, "exit_code": e.exit_code,
             "started_at": e.started_at, "finished_at": e.finished_at,
             "created_at": e.created_at} for e in execs]


@router.get("/executions/{exec_id}")
async def get_execution(exec_id: int, db: AsyncSession = Depends(get_db),
                        user: User = Depends(get_current_user)):
    result = await db.execute(select(TaskExecution).where(TaskExecution.id == exec_id))
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    return ex


@router.post("/executions/{exec_id}/approve")
async def approve_execution(exec_id: int, db: AsyncSession = Depends(get_db),
                            user: User = Depends(require_operator)):
    result = await db.execute(select(TaskExecution).where(TaskExecution.id == exec_id))
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    if ex.status != "pending":
        raise HTTPException(status_code=400, detail="Execution is not pending approval")
    ex.status = "running"
    ex.approved_by = user.id
    from app.workers.task_worker import run_task
    run_task.delay(ex.id)
    return {"message": "Approved and queued"}


@router.post("/executions/{exec_id}/cancel")
async def cancel_execution(exec_id: int, db: AsyncSession = Depends(get_db),
                           user: User = Depends(require_operator)):
    result = await db.execute(select(TaskExecution).where(TaskExecution.id == exec_id))
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="Execution not found")
    if ex.status not in ("pending", "running"):
        raise HTTPException(status_code=400, detail="Cannot cancel")
    ex.status = "cancelled"
    return {"message": "Cancelled"}
