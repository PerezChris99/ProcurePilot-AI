from functools import lru_cache
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
    channel3_api_key: str | None = None
    channel3_base_url: str | None = None
    paypal_client_id: str | None = None
    paypal_client_secret: str | None = None
    paypal_base_url: str = 'https://api-m.sandbox.paypal.com'
    paypal_webhook_id: str | None = None
    model_config = SettingsConfigDict(env_file='.env',env_file_encoding='utf-8',case_sensitive=False,extra='ignore')

@lru_cache
def get_settings() -> Settings:
    return Settings()
