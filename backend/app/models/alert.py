from sqlalchemy import String, Text, DateTime, JSON, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.db.session import Base


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128))
    resource_type: Mapped[str] = mapped_column(String(32))   # server | deployment | pipeline
    metric: Mapped[str] = mapped_column(String(64))          # cpu_usage | mem_usage | error_rate
    operator: Mapped[str] = mapped_column(String(8))         # > | < | >= | <=
    threshold: Mapped[float] = mapped_column(Float)
    duration_seconds: Mapped[int] = mapped_column(default=60)
    severity: Mapped[str] = mapped_column(String(16), default="warning")  # info | warning | critical
    channels: Mapped[list] = mapped_column(JSON, default=list)            # slack | email | webhook
    is_active: Mapped[bool] = mapped_column(default=True)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("alert_rules.id"), index=True)
    resource_id: Mapped[int] = mapped_column(default=None, nullable=True)
    resource_name: Mapped[str] = mapped_column(String(128))
    title: Mapped[str] = mapped_column(String(256))
    message: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="firing")  # firing | resolved | silenced
    labels: Mapped[dict] = mapped_column(JSON, default=dict)
    resolved_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    acknowledged_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=True)
    fired_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
