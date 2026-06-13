import subprocess
import asyncio
from datetime import datetime
from celery import Celery
from app.core.config import settings

celery_app = Celery("opspilot", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "UTC"


@celery_app.task(bind=True, name="run_task")
def run_task(self, execution_id: int):
    """Execute a runbook and update the DB record."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.models.task import TaskExecution, Runbook

    sync_url = settings.DATABASE_URL.replace("+asyncpg", "")
    engine = create_engine(sync_url)

    with Session(engine) as db:
        ex = db.get(TaskExecution, execution_id)
        if not ex:
            return
        book = db.get(Runbook, ex.runbook_id)
        if not book:
            return

        ex.status = "running"
        ex.started_at = datetime.utcnow()
        db.commit()

        try:
            # Render script with params
            script = book.script
            for key, val in (ex.params or {}).items():
                script = script.replace(f"{{{{ {key} }}}}", str(val))

            # Choose interpreter
            interpreter = "bash" if book.script_type == "bash" else "python3"

            result = subprocess.run(
                [interpreter, "-c", script],
                capture_output=True,
                text=True,
                timeout=book.timeout_seconds,
            )
            ex.exit_code = result.returncode
            ex.output = result.stdout[-10000:]   # cap to 10k chars
            ex.error = result.stderr[-2000:]
            ex.status = "success" if result.returncode == 0 else "failed"
        except subprocess.TimeoutExpired:
            ex.status = "failed"
            ex.error = f"Timed out after {book.timeout_seconds}s"
        except Exception as e:
            ex.status = "failed"
            ex.error = str(e)
        finally:
            ex.finished_at = datetime.utcnow()
            db.commit()
