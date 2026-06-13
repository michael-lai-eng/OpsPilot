from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "OpsPilot"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql+asyncpg://opspilot:opspilot@localhost:5432/opspilot"
    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "changeme-in-production-use-openssl-rand-hex-32"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8
    ALGORITHM: str = "HS256"

    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # GitHub integration
    GITHUB_TOKEN: str = ""
    GITHUB_OWNER: str = ""

    # Kubernetes
    K8S_IN_CLUSTER: bool = False
    K8S_KUBECONFIG: str = ""

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    class Config:
        env_file = ".env"


settings = Settings()
