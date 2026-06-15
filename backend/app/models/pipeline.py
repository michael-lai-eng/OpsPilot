from sqlalchemy import String, Integer, BigInteger, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.session import Base


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    repo: Mapped[str] = mapped_column(String(256))           # owner/repo
    branch: Mapped[str] = mapped_column(String(128), default="main")
    workflow_file: Mapped[str] = mapped_column(String(128))  # .github/workflows/ci.yml
    description: Mapped[str] = mapped_column(Text, default="")
    tags: Mapped[dict] = mapped_column(JSON, default=list)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    pipeline_id: Mapped[int] = mapped_column(ForeignKey("pipelines.id"), index=True)
    run_number: Mapped[int] = mapped_column(Integer)
    github_run_id: Mapped[int] = mapped_column(BigInteger, nullable=True)
    status: Mapped[str] = mapped_column(String(32))   # queued | in_progress | success | failure | cancelled
    conclusion: Mapped[str] = mapped_column(String(32), nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(64))
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=True)
    commit_msg: Mapped[str] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    logs_url: Mapped[str] = mapped_column(String(512), nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
