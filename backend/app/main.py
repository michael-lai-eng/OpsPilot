from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.db.session import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="DevOps Operations Platform — CI/CD · Deployments · Automation · Monitoring",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
from app.api.routes import auth, pipelines, deployments, servers, tasks, alerts, dashboard

app.include_router(auth.router, prefix="/api")
app.include_router(pipelines.router, prefix="/api")
app.include_router(deployments.router, prefix="/api")
app.include_router(servers.router, prefix="/api")
app.include_router(tasks.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}
