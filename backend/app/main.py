import time
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, make_asgi_app, CONTENT_TYPE_LATEST, generate_latest
from app.core.config import settings
from app.db.session import engine, Base

# ── Structured JSON logging ───────────────────────────────────────────────────
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger()

# ── Prometheus metrics ────────────────────────────────────────────────────────
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["endpoint"],
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (use Alembic in production)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("startup", app=settings.APP_NAME, version=settings.APP_VERSION)
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


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    endpoint = request.url.path
    HTTP_REQUESTS_TOTAL.labels(request.method, endpoint, response.status_code).inc()
    HTTP_REQUEST_DURATION.labels(endpoint).observe(duration)
    if response.status_code >= 500:
        logger.error("request_error", method=request.method, path=endpoint, status=response.status_code, duration=round(duration, 4))
    return response


@app.get("/metrics", include_in_schema=False)
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

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
