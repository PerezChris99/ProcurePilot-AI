"""Authenticated, secret-safe integration configuration and local readiness state.

Configuration flags reflect the current server environment; no automatic paid or
rate-limited provider requests are made just to paint the dashboard.
"""
from urllib.parse import urlsplit
import re

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.integrations.channel3.client import DEFAULT_CHANNEL3_BASE_URL
from app.models import AiDailyBudget, Payment, User, WebhookEvent
from app.security.tokens import get_current_user

router = APIRouter(prefix="/integrations", tags=["integrations"])


def _set(value: str | None) -> bool:
    """Empty and common template values are not configured credentials."""
    if not isinstance(value, str):
        return False
    trimmed = value.strip()
    if not trimmed or trimmed.lower() in {
        "replace-me", "changeme", "your-api-key", "your_api_key_here",
        "your-client-id", "your-client-secret", "xxx", "placeholder",
    }:
        return False
    return not trimmed.lower().startswith(("your-", "replace-with-", "paste-your-"))


def _https_endpoint(value: str | None) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = urlsplit(value.strip())
        return (
            parsed.scheme == "https" and bool(parsed.hostname)
            and not parsed.username and not parsed.password
            and not parsed.fragment and not parsed.query
        )
    except ValueError:
        return False


def _paypal_mode(value: str | None) -> str:
    host = (value or "").rstrip("/")
    return {
        "https://api-m.sandbox.paypal.com": "sandbox",
        "https://api-m.paypal.com": "live",
    }.get(host, "unknown")


@router.get("/status", summary="Show live server configuration and database readiness, not provider availability")
def integration_status(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Report safely observable settings; never return secrets or claim provider validation."""
    settings = get_settings()
    try:
        dialect = db.get_bind().dialect.name
    except (SQLAlchemyError, AttributeError):
        dialect = "unknown"

    connected = False
    schema_ready = False
    try:
        db.execute(text("SELECT 1"))
        connected = True
        # Unlike SELECT 1 this verifies the latest required migration exists.
        db.scalar(select(AiDailyBudget.scope).limit(1))
        schema_ready = True
    except SQLAlchemyError:
        db.rollback()

    google_key_set = _set(settings.google_api_key)
    channel_key_set = _set(settings.channel3_api_key)
    channel_url_set = _https_endpoint(settings.channel3_base_url or DEFAULT_CHANNEL3_BASE_URL)
    paypal_id_set = _set(settings.paypal_client_id)
    paypal_secret_set = _set(settings.paypal_client_secret)
    paypal_webhook_set = _set(settings.paypal_webhook_id)
    # Only the PayPal-created Webhook ID is masked for client display.
    # This is a configuration claim, not proof of a subscription or delivery.
    webhook_id = settings.paypal_webhook_id or ''
    webhook_id_set = _set(webhook_id)
    webhook_id_valid = bool(re.fullmatch(r'[A-Za-z0-9]{8,40}', webhook_id))
    webhook_hint = '••••' + webhook_id[-4:] if webhook_id_set and webhook_id_valid else None
    webhook_url = getattr(settings, 'paypal_webhook_url', None)
    webhook_url_set = _https_endpoint(webhook_url)
    last_verified_webhook = None
    successful_capture_seen = False
    if connected and schema_ready:
        try:
            last_verified_webhook = db.scalar(
                select(WebhookEvent.processed_at).where(
                    WebhookEvent.verified.is_(True),
                    WebhookEvent.processed_at.is_not(None),
                ).order_by(WebhookEvent.processed_at.desc()).limit(1)
            )
            successful_capture_seen = db.scalar(
                select(Payment.id).where(
                    Payment.provider == 'paypal',
                    Payment.status == 'completed',
                    Payment.capture_id.is_not(None),
                ).limit(1)
            ) is not None
        except SQLAlchemyError:
            db.rollback()
    fallback_enabled = getattr(settings,'ai_fallback_enabled',False)
    return {
        "runtime": {
            "environment": settings.app_env,
            "provider_checks": "configuration_only",
        },
        "database": {
            "connected": connected,
            "schema_ready": schema_ready,
            "engine": dialect,
        },
        "ai": {
            "provider": "Google ADK / LiteLLM",
            "configured": google_key_set or (fallback_enabled and (
                _set(getattr(settings,'groq_api_key',None))
                or _set(getattr(settings,'openrouter_api_key',None))
            )),
            "api_key_set": google_key_set,
            "primary_configured": google_key_set,
            "model": settings.ai_model or "gemini-3.5-flash-lite",
            "fallback_enabled": fallback_enabled,
            "backup_providers": {
                "groq": fallback_enabled and _set(getattr(settings, 'groq_api_key', None)),
                "openrouter": fallback_enabled and _set(getattr(settings, 'openrouter_api_key', None)),
            },
            "provider_checks": "configuration_only",
        },
        "channel3": {
            "provider": "Channel3",
            "configured": channel_key_set and channel_url_set,
            "api_key_set": channel_key_set,
            "base_url_configured": channel_url_set,
        },
        "paypal": {
            "provider": "PayPal",
            "credentials_configured": paypal_id_set and paypal_secret_set,
            "client_id_set": paypal_id_set,
            "client_secret_set": paypal_secret_set,
            "webhook_configured": paypal_webhook_set,
            "webhook_id_valid": webhook_id_valid,
            "webhook_id_hint": webhook_hint,
            "webhook_url_configured": webhook_url_set,
            "webhook_callback_url": webhook_url if webhook_url_set else None,
            "webhook_last_verified_at": last_verified_webhook.isoformat() if last_verified_webhook else None,
            "merchant_checkout_verified": successful_capture_seen,
            "environment": _paypal_mode(settings.paypal_base_url),
        },
    }
