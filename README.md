# 🚀 OpsPilot — DevOps Operations Platform

![OpsPilot_Architecture.png](images/OpsPilot_Architecture.png)
A production-grade DevOps platform for CI/CD pipeline management, automated deployments, runbook automation, and infrastructure monitoring.

**Tech Stack:** Vue 3 · FastAPI · PostgreSQL · Redis · Celery · Kubernetes · GitHub Actions

---

## Features

| Module | Description |
|---|---|
| **Dashboard** | System-wide health overview — servers, deployments, alerts, recent activity |
| **CI/CD Pipelines** | GitHub Actions integration — trigger, monitor, and sync workflow runs |
| **Deployment Center** | Kubernetes deployment management — rolling deploy, rollback, scale |
| **Task Automation** | Runbook library — write bash/python scripts, execute with approval workflow |
| **Alert Manager** | Rule-based alerting engine with severity levels and resolve/acknowledge |
| **Asset Inventory** | Server CMDB — track CPU/memory/OS, filter by env/role/provider |

---

## Quick Start

### Local Development (Docker Compose)

```bash
# 1. Clone and copy env
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY

# 2. Start everything
docker compose up -d

# 3. Create admin user
curl -X POST http://localhost:8000/api/auth/users \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","email":"admin@example.com","password":"admin123","role":"admin"}'

# 4. Open the UI
open http://localhost:3000
```

Services available:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **Celery Flower**: http://localhost:5555

### Backend Only (Dev Mode)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Apply DB migrations
alembic upgrade head

# Run API server
uvicorn app.main:app --reload --port 8000

# Run Celery worker (separate terminal)
celery -A app.workers.task_worker.celery_app worker --loglevel=info
```

### Frontend Only

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

---

## CI/CD Pipeline

```
Push to main ─► GitHub Actions CI
                  ├─ Backend tests (pytest + ruff lint)
                  ├─ Frontend build (vite build + eslint)
                  └─ Docker build & push to GHCR
                        └─► CD workflow
                              ├─ Deploy to Staging (auto)
                              └─ Deploy to Production (manual approval)
```

### Secrets Required

| Secret | Description |
|---|---|
| `GITHUB_TOKEN` | Auto-provided by GitHub Actions |
| `KUBE_CONFIG_STAGING` | Base64-encoded kubeconfig for staging cluster |
| `KUBE_CONFIG_PROD` | Base64-encoded kubeconfig for production cluster |

---

## Kubernetes Deployment

```bash
# Create namespace and secrets
kubectl create namespace opspilot
kubectl create secret generic opspilot-secrets \
  --from-literal=DATABASE_URL="postgresql+asyncpg://..." \
  --from-literal=REDIS_URL="redis://..." \
  --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=CELERY_BROKER_URL="redis://..." \
  --from-literal=CELERY_RESULT_BACKEND="redis://..." \
  --from-literal=POSTGRES_USER="opspilot" \
  --from-literal=POSTGRES_PASSWORD="<strong-password>" \
  -n opspilot

# Apply manifests
kubectl apply -f k8s/postgres/
kubectl apply -f k8s/backend/
kubectl apply -f k8s/frontend/
```

---

## API Reference

Full interactive docs at **http://localhost:8000/docs**

Key endpoints:

```
POST  /api/auth/token                    Login
GET   /api/dashboard/overview            System overview

GET   /api/pipelines                     List pipelines
POST  /api/pipelines/{id}/trigger        Trigger workflow

GET   /api/deployments                   List deployments
POST  /api/deployments/{id}/deploy       Deploy new image
POST  /api/deployments/{id}/rollback     Rollback to previous
POST  /api/deployments/{id}/scale        Scale replicas

GET   /api/tasks/runbooks                List runbooks
POST  /api/tasks/runbooks/{id}/execute   Execute a runbook
POST  /api/tasks/executions/{id}/approve Approve pending execution

GET   /api/alerts                        List alerts
GET   /api/servers                       List servers
```

---

## Project Structure

```
OpsPilot/
├── .github/workflows/
│   ├── ci.yml          # Test → Build → Push to GHCR
│   └── cd.yml          # Deploy to Staging / Production
├── backend/
│   ├── app/
│   │   ├── api/routes/ # FastAPI routers
│   │   ├── models/     # SQLAlchemy models
│   │   ├── services/   # GitHub, K8s integrations
│   │   ├── workers/    # Celery task runner
│   │   └── main.py
│   ├── alembic/        # DB migrations
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── api/        # Axios API layer
│   │   ├── views/      # Page components
│   │   ├── store/      # Pinia stores
│   │   └── router/
│   └── Dockerfile
├── k8s/                # Kubernetes manifests
└── docker-compose.yml
```

---

## Role-Based Access

| Role | Permissions |
|---|---|
| `viewer` | Read-only — view dashboards, logs, history |
| `operator` | Execute tasks, trigger pipelines, deploy |
| `admin` | Full access including user management |
