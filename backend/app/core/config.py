"""
Application configuration, loaded from environment variables / .env file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "GovernX"
    DATABASE_URL: str = "postgresql://governx:governx@db:5432/governx"
    REDIS_URL: str = "redis://redis:6379/0"

    JWT_SECRET_KEY: str = "insecure-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    USE_MOCK_AWS: bool = True

    # Risk quantification defaults
    MONTE_CARLO_ITERATIONS: int = 10000


settings = Settings()
