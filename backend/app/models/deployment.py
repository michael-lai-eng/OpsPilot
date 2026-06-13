from sqlalchemy import String, Integer, Text, DateTime, JSON, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.session import Base


class Environment(Base):
    __tablename__ = "environments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64))       # dev | staging | prod
    cluster: Mapped[str] = mapped_column(String(128))   # k8s cluster name
    namespace: Mapped[str] = mapped_column(String(128))
    description: Mapped[str] = mapped_column(Text, default="")
    is_protected: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    environment_id: Mapped[int] = mapped_column(ForeignKey("environments.id"), index=True)
    service: Mapped[str] = mapped_column(String(128))   # k8s deployment name
    image: Mapped[str] = mapped_column(String(512))     # full image:tag
    replicas: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(32))     # running | pending | failed | stopped
    health: Mapped[str] = mapped_column(String(32), default="unknown")  # healthy | degraded | unhealthy
    ready_replicas: Mapped[int] = mapped_column(Integer, default=0)
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    deployed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    deployed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class DeploymentHistory(Base):
    __tablename__ = "deployment_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    deployment_id: Mapped[int] = mapped_column(ForeignKey("deployments.id"), index=True)
    action: Mapped[str] = mapped_column(String(32))      # deploy | rollback | scale | restart
    prev_image: Mapped[str] = mapped_column(String(512), nullable=True)
    new_image: Mapped[str] = mapped_column(String(512), nullable=True)
    prev_replicas: Mapped[int] = mapped_column(Integer, nullable=True)
    new_replicas: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(32))      # success | failed | in_progress
    performed_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    note: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
