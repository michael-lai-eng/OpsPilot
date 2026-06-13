from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.session import Base


class Runbook(Base):
    """Reusable automation scripts / runbooks."""
    __tablename__ = "runbooks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(64), default="misc")   # deploy | maintain | diagnose | cleanup | misc
    description: Mapped[str] = mapped_column(Text, default="")
    script: Mapped[str] = mapped_column(Text)                            # shell / python script body
    script_type: Mapped[str] = mapped_column(String(16), default="bash") # bash | python | ansible
    params_schema: Mapped[dict] = mapped_column(JSON, default=dict)      # JSON Schema for input params
    timeout_seconds: Mapped[int] = mapped_column(default=300)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TaskExecution(Base):
    """Instance of a runbook execution."""
    __tablename__ = "task_executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    runbook_id: Mapped[int] = mapped_column(ForeignKey("runbooks.id"), index=True)
    title: Mapped[str] = mapped_column(String(256), default="")
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    target_servers: Mapped[list] = mapped_column(JSON, default=list)  # list of server ids
    status: Mapped[str] = mapped_column(String(32))  # pending | approved | running | success | failed | cancelled
    exit_code: Mapped[int] = mapped_column(default=None, nullable=True)
    output: Mapped[str] = mapped_column(Text, default="")
    error: Mapped[str] = mapped_column(Text, default="")
    celery_task_id: Mapped[str] = mapped_column(String(128), nullable=True)
    triggered_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    approved_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
