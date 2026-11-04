from functools import lru_cache
from urllib.parse import urlsplit
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = 'ProcurePilot AI'
    app_env: str = 'development'
    api_v1_prefix: str = '/api/v1'
    frontend_url: str = 'http://localhost:5173'
    database_url: str = 'sqlite:///./procurepilot.db'
    jwt_secret_key: str = 'development-only-change-this-secret'
    access_token_expire_minutes: int = 30
    google_api_key: str | None = None
    ai_model: str | None = None
    ai_max_output_tokens: int = Field(default=900, ge=256, le=2048)
    ai_timeout_seconds: int = Field(default=35, ge=10, le=90)
    ai_daily_user_runs: int = Field(default=12, ge=1, le=500)
    ai_daily_global_runs: int = Field(default=100, ge=1, le=5000)
    ai_evidence_candidates: int = Field(default=4, ge=1, le=8)
    channel3_api_key: str | None = None
    channel3_base_url: str | None = None
    paypal_client_id: str | None = None
    paypal_client_secret: str | None = None
    paypal_base_url: str = 'https://api-m.sandbox.paypal.com'
    paypal_webhook_id: str | None = None
    model_config = SettingsConfigDict(env_file=('.env','../.env'),env_file_encoding='utf-8',case_sensitive=False,extra='ignore')

    @model_validator(mode='after')
    def validate_production_secrets(self):
        environment = self.app_env.strip().lower()
        if environment not in ('development','test','testing','staging','production'):
            raise ValueError('APP_ENV must be development, test, testing, staging, or production')
        self.app_env = environment
        if environment in ('staging','production'):
            if (len(self.jwt_secret_key)<32 or self.jwt_secret_key in
                    ('development-only-change-this-secret','replace-with-a-long-random-secret')
                    or len(set(self.jwt_secret_key))<12):
                raise ValueError('Production requires a unique JWT_SECRET_KEY of at least 32 characters')
            if self.database_url == 'postgresql+psycopg://postgres:postgres@localhost:5432/procurepilot':
                raise ValueError('Public environments must replace the example PostgreSQL credentials')
            if not self.database_url.startswith('postgresql+psycopg://'):
                raise ValueError('Production DATABASE_URL must use postgresql+psycopg:// and a persistent PostgreSQL database')
            url = urlsplit(self.frontend_url)
            if (url.scheme != 'https' or not url.hostname
                    or url.hostname in ('localhost', '127.0.0.1', '::1')
                    or url.username or url.password or url.query or url.fragment
                    or url.path not in ('', '/')):
                raise ValueError('Production FRONTEND_URL must be a public HTTPS origin without path or query')
            self.frontend_url = self.frontend_url.rstrip('/')
        return self

@lru_cache
def get_settings() -> Settings:
    return Settings()
