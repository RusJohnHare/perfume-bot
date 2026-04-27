from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = "test_token"
    database_url: str = "sqlite+aiosqlite:///./perfume_bot.db"
    redis_url: str = "redis://localhost:6379/0"
    anthropic_api_key: str = ""

    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    price_drop_threshold: float = 0.10
    price_check_interval_hours: int = 6


settings = Settings()
