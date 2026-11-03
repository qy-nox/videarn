from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    secret_key: str = "change-me"
    database_url: str = "postgresql+asyncpg://videarn:videarn@postgres:5432/videarn"
    redis_url: str = "redis://redis:6379/0"
    jwt_access_minutes: int = 15
    jwt_refresh_days: int = 30
    firebase_project_id: str | None = None
    firebase_service_account_json: str | None = None
    admin_email: str = "admin@example.com"
    admin_password: str = "change-me"
    admin_totp_secret: str | None = None
    s3_endpoint_url: str | None = None
    s3_region: str = "auto"
    s3_bucket: str = "videarn"
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    cdn_base_url: str | None = None
    feed_page_size: int = 20
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
