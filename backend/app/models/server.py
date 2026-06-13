from sqlalchemy import String, Integer, Text, DateTime, JSON, Float, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.session import Base


class Server(Base):
    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True)
    hostname: Mapped[str] = mapped_column(String(256))
    ip: Mapped[str] = mapped_column(String(45))
    port: Mapped[int] = mapped_column(Integer, default=22)
    os: Mapped[str] = mapped_column(String(64), default="")
    arch: Mapped[str] = mapped_column(String(32), default="")
    cpu_cores: Mapped[int] = mapped_column(Integer, default=0)
    memory_gb: Mapped[float] = mapped_column(Float, default=0.0)
    disk_gb: Mapped[float] = mapped_column(Float, default=0.0)
    environment: Mapped[str] = mapped_column(String(32), default="prod")   # dev | staging | prod
    role: Mapped[str] = mapped_column(String(64), default="app")           # app | db | cache | lb | k8s-node
    region: Mapped[str] = mapped_column(String(64), default="")
    provider: Mapped[str] = mapped_column(String(64), default="")          # aws | gcp | azure | onprem
    tags: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="online")      # online | offline | maintenance
    last_seen: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_monitored: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ServerMetric(Base):
    __tablename__ = "server_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    server_id: Mapped[int] = mapped_column(Integer, index=True)
    cpu_usage: Mapped[float] = mapped_column(Float)
    mem_usage: Mapped[float] = mapped_column(Float)
    disk_usage: Mapped[float] = mapped_column(Float)
    net_in_mbps: Mapped[float] = mapped_column(Float, default=0.0)
    net_out_mbps: Mapped[float] = mapped_column(Float, default=0.0)
    load_avg: Mapped[float] = mapped_column(Float, default=0.0)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
