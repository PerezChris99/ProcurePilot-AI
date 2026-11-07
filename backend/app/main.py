from urllib.parse import urlsplit

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.health import router as health_router
from app.api.integrations import router as integrations_router
from app.api.paypal_webhooks import router as paypal_webhooks_router
from app.api.procurement_requests import router as procurement_router
from app.api.purchase_orders import router as purchase_orders_router
from app.api.trust_lab import router as trust_lab_router
from app.core.config import get_settings
from app.security.http import SecurityMiddleware

settings = get_settings()


def allowed_frontend_origins(frontend_url: str, app_env: str) -> list[str]:
    """Allow only the configured origin and its loopback alias in local development.

    Browsers treat localhost and 127.0.0.1 as different origins even when they
    reach the same Vite server. Never add these aliases in staging/production.
    """
    primary = frontend_url.rstrip("/")
    origins = [primary]
    if app_env not in ("development", "test", "testing"):
        return origins

    parsed = urlsplit(primary)
    if parsed.scheme not in ("http", "https") or parsed.hostname not in ("localhost", "127.0.0.1"):
        return origins
    if parsed.path or parsed.query or parsed.fragment or parsed.username or parsed.password:
        return origins

    try:
        port = parsed.port
    except ValueError:
        return origins

    alternative = "127.0.0.1" if parsed.hostname == "localhost" else "localhost"
    alias = f"{parsed.scheme}://{alternative}"
    if port is not None:
        alias += f":{port}"
    origins.append(alias)
    return origins


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    description="AI-assisted procurement workflow API.",
    docs_url="/docs" if settings.app_env != "production" else None,
    redoc_url="/redoc" if settings.app_env != "production" else None,
)
# Central guard for database exceptions outside the auth-specific handlers:
# missing relations, lost Neon sessions, and failed connection acquisitions must
# never become opaque 500 responses or expose a driver connection URL to clients.
@app.exception_handler(SQLAlchemyError)
async def database_exception_handler(_request: Request, exc: SQLAlchemyError):
    logging.getLogger('procurepilot.database').error(
        'Database request failed; class=%s', type(exc).__name__
    )
    return JSONResponse(
        status_code=503,
        content={'detail': 'Database is temporarily unavailable. Please retry shortly.'},
        headers={'Retry-After': '15', 'Cache-Control': 'no-store'},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_frontend_origins(settings.frontend_url, settings.app_env),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)
# Installed last so every CORS preflight, error and authenticated response is guarded.
app.add_middleware(SecurityMiddleware, max_body_bytes=settings.max_request_body_bytes, production=settings.app_env=='production')
app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(dashboard_router, prefix=settings.api_v1_prefix)
app.include_router(integrations_router, prefix=settings.api_v1_prefix)
app.include_router(procurement_router, prefix=settings.api_v1_prefix)
app.include_router(purchase_orders_router, prefix=settings.api_v1_prefix)
app.include_router(trust_lab_router, prefix=settings.api_v1_prefix)
app.include_router(paypal_webhooks_router, prefix=settings.api_v1_prefix)


@app.get("/", include_in_schema=False)
def root():
    return {"name": settings.app_name, "status": "running", "version": "0.2.0"}
