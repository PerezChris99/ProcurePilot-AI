from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.security.tokens import get_current_user

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/status", summary="Show integration configuration without exposing credentials")
def integration_status(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Return safe configuration/readiness metadata for the signed-in operator.

    This endpoint deliberately reports booleans and model/environment labels only.
    It never returns API keys, client secrets, database URLs, or webhook IDs.
    """
    settings = get_settings()

    try:
        db.execute(text("SELECT 1"))
        database_connected = True
    except SQLAlchemyError:
        db.rollback()
        database_connected = False

    paypal_base_url = (settings.paypal_base_url or "").rstrip("/")
    paypal_environment = (
        "sandbox"
        if paypal_base_url == "https://api-m.sandbox.paypal.com"
        else "live"
        if paypal_base_url == "https://api-m.paypal.com"
        else "unknown"
    )

    return {
        "database": {"connected": database_connected},
        "ai": {
            "provider": "Google Gemini",
            "configured": bool(settings.google_api_key),
            "model": settings.ai_model or "gemini-flash-latest",
        },
        "channel3": {
            "provider": "Channel3",
            "configured": bool(settings.channel3_api_key),
            "base_url_configured": bool(settings.channel3_base_url),
        },
        "paypal": {
            "provider": "PayPal",
            "credentials_configured": bool(
                settings.paypal_client_id and settings.paypal_client_secret
            ),
            "webhook_configured": bool(settings.paypal_webhook_id),
            "environment": paypal_environment,
        },
    }
