from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    db_prefix: str = "postgresql+asyncpg://"
    
    DB_HOST: str
    DB_PORT: int
    DB_USER: str
    DB_PASS: str
    DB_NAME: str
    
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"{self.db_prefix}"
            f"{self.DB_USER}:{self.DB_PASS}@"
            f"{self.DB_HOST}:{self.DB_PORT}/"
            f"{self.DB_NAME}"
        )

    @property
    def ALEMBIC_DATABASE_URL(self) -> str:
        return self.DATABASE_URL.replace(
            "+asyncpg",
            "+psycopg",
        )
    
    TEST_DB_HOST: str
    TEST_DB_PORT: int
    TEST_DB_USER: str
    TEST_DB_PASS: str
    TEST_DB_NAME: str

    @property
    def TEST_DATABASE_URL(self) -> str:
        return (
            f"{self.db_prefix}"
            f"{self.TEST_DB_USER}:{self.TEST_DB_PASS}@"
            f"{self.TEST_DB_HOST}:{self.TEST_DB_PORT}/"
            f"{self.TEST_DB_NAME}"
        )
    
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM: str
    SMTP_USE_TLS: bool
    
    TELEGRAM_BOT_TOKEN: str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    RETRY_COUNT: int
    RETRY_INTERVAL_SECONDS: int

    DELIVERY_BATCH_SIZE: int

settings = Settings()
