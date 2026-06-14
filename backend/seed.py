"""Seed initial data — run once after first startup.
Usage: python seed.py
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import select
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://opspilot:opspilot@localhost:5432/opspilot"
)

engine = create_async_engine(DATABASE_URL)
Session = async_sessionmaker(engine, expire_on_commit=False)


async def seed():
    from app.db.session import Base
    from app.models.user import User
    from app.models.deployment import Environment
    from app.models.server import Server
    from app.models.alert import AlertRule
    from app.core.security import hash_password

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with Session() as db:
        # ── Admin user ──────────────────────────────────────────
        existing = await db.scalar(select(User).where(User.username == "admin"))
        if not existing:
            db.add(User(
                username="admin", email="admin@opspilot.local",
                hashed_password=hash_password("admin123"),
                full_name="Administrator", role="admin",
            ))
            db.add(User(
                username="operator", email="operator@opspilot.local",
                hashed_password=hash_password("operator123"),
                full_name="Ops Operator", role="operator",
            ))
            print("✓ Users created  (admin/admin123, operator/operator123)")

        # ── Environments ────────────────────────────────────────
        env_exists = await db.scalar(select(Environment))
        if not env_exists:
            db.add(Environment(name="dev",     cluster="local",   namespace="dev",     is_protected=False))
            db.add(Environment(name="staging", cluster="k8s-stg", namespace="staging", is_protected=False))
            db.add(Environment(name="prod",    cluster="k8s-prod",namespace="opspilot",is_protected=True))
            print("✓ Environments created  (dev / staging / prod)")

        # ── Sample servers ──────────────────────────────────────
        svr_exists = await db.scalar(select(Server))
        if not svr_exists:
            for s in [
                dict(name="web-01", hostname="web-01.internal", ip="10.0.1.10",
                     os="Ubuntu 22.04", cpu_cores=8, memory_gb=16, environment="prod",
                     role="app", provider="aws", region="ap-east-1", status="online"),
                dict(name="web-02", hostname="web-02.internal", ip="10.0.1.11",
                     os="Ubuntu 22.04", cpu_cores=8, memory_gb=16, environment="prod",
                     role="app", provider="aws", region="ap-east-1", status="online"),
                dict(name="db-01", hostname="db-01.internal", ip="10.0.2.10",
                     os="Ubuntu 22.04", cpu_cores=16, memory_gb=64, environment="prod",
                     role="db", provider="aws", region="ap-east-1", status="online"),
                dict(name="cache-01", hostname="cache-01.internal", ip="10.0.3.10",
                     os="Ubuntu 22.04", cpu_cores=4, memory_gb=8, environment="prod",
                     role="cache", provider="aws", region="ap-east-1", status="online"),
                dict(name="dev-box", hostname="dev.internal", ip="10.0.9.10",
                     os="Ubuntu 22.04", cpu_cores=4, memory_gb=8, environment="dev",
                     role="app", provider="onprem", status="online"),
            ]:
                db.add(Server(**s))
            print("✓ Sample servers created")

        # ── Sample alert rules ──────────────────────────────────
        rule_exists = await db.scalar(select(AlertRule))
        if not rule_exists:
            admin = await db.scalar(select(User).where(User.username == "admin"))
            for r in [
                dict(name="High CPU", resource_type="server", metric="cpu_usage",
                     operator=">", threshold=85, severity="warning",  created_by=admin.id),
                dict(name="Critical CPU", resource_type="server", metric="cpu_usage",
                     operator=">", threshold=95, severity="critical", created_by=admin.id),
                dict(name="High Memory", resource_type="server", metric="mem_usage",
                     operator=">", threshold=90, severity="warning",  created_by=admin.id),
                dict(name="Disk Full", resource_type="server", metric="disk_usage",
                     operator=">", threshold=85, severity="critical", created_by=admin.id),
            ]:
                db.add(AlertRule(**r))
            print("✓ Default alert rules created")

        await db.commit()
        print("\n🚀 Seed complete! Login: admin / admin123")


asyncio.run(seed())
