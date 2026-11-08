"""Register or inspect the ProcurePilot PayPal Sandbox webhook idempotently.

This command must run in a TRUSTED backend environment with PAYPAL_CLIENT_ID and
PAYPAL_CLIENT_SECRET loaded privately. Never place credentials in the frontend.

Examples (from backend/):
    python -m scripts.configure_paypal_webhook --check
    python -m scripts.configure_paypal_webhook --register

The returned WEBHOOK ID is the exact PAYPAL_WEBHOOK_ID to configure as a
sensitive environment variable for the SAME merchant REST app. Registration
does not make an ineligible merchant able to accept checkout payments.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import re
from urllib.parse import urlsplit

from app.integrations.paypal.client import PayPalClient, PayPalUnavailable, PayPalConfigurationError

CANONICAL_ENDPOINT = "https://procurepilotai.vercel.app/api/v1/webhooks/paypal"
REQUIRED_EVENTS = frozenset({
    "CHECKOUT.ORDER.APPROVED",
    "PAYMENT.CAPTURE.COMPLETED",
    "PAYMENT.CAPTURE.DENIED",
})
ID_PATTERN = re.compile(r"^[A-Za-z0-9]{8,40}$")


class WebhookSetupError(RuntimeError):
    """Contains only a predetermined category, never provider payloads."""


def _validate_target(url: str) -> str:
    parsed = urlsplit(url)
    if (
        url != CANONICAL_ENDPOINT
        or parsed.scheme != "https"
        or parsed.hostname != "procurepilotai.vercel.app"
        or parsed.path != "/api/v1/webhooks/paypal"
        or parsed.username is not None or parsed.password is not None
        or parsed.port is not None or bool(parsed.query) or bool(parsed.fragment)
    ):
        raise WebhookSetupError("unexpected_webhook_target")
    return url


def _matching_hook(webhooks: list, url: str) -> dict | None:
    matches = [
        hook for hook in webhooks
        if isinstance(hook, dict) and hook.get("url") == url
    ]
    if len(matches) > 1:
        raise WebhookSetupError("duplicate_webhook_urls_require_review")
    if not matches:
        return None
    hook = matches[0]
    if not isinstance(hook.get("id"), str) or not ID_PATTERN.fullmatch(hook["id"]):
        raise WebhookSetupError("invalid_provider_webhook_id")
    events = {
        event.get("name") for event in (hook.get("event_types") or [])
        if isinstance(event, dict) and isinstance(event.get("name"), str)
    }
    if not REQUIRED_EVENTS.issubset(events) and "*" not in events:
        raise WebhookSetupError("webhook_missing_required_events")
    return hook


async def ensure_webhook(*, create: bool = False, client: PayPalClient | None = None) -> dict:
    paypal = client or PayPalClient()
    paypal.ensure_configured()
    target = _validate_target(os.environ.get("PAYPAL_WEBHOOK_URL", CANONICAL_ENDPOINT))
    try:
        # PayPal lists webhooks for the REST app represented by this OAuth
        # token, not for unrelated apps or generic merchant accounts.
        response = await paypal._request("GET", "/v1/notifications/webhooks")
        hooks = response.get("webhooks") if isinstance(response, dict) else None
        if not isinstance(hooks, list):
            raise WebhookSetupError("unexpected_webhooks_list")
        existing = _matching_hook(hooks, target)
        if existing:
            return {"id": existing["id"], "action": "existing", "url": target}
        if not create:
            return {"id": None, "action": "missing", "url": target}
        created = await paypal._request(
            "POST",
            "/v1/notifications/webhooks",
            payload={
                "url": target,
                "event_types": [
                    {"name": event} for event in sorted(REQUIRED_EVENTS)
                ],
            },
        )
        if not isinstance(created, dict):
            raise WebhookSetupError("unexpected_webhook_create_response")
        hook_id = created.get("id")
        if not isinstance(hook_id, str) or not ID_PATTERN.fullmatch(hook_id):
            raise WebhookSetupError("invalid_provider_webhook_id")
        if created.get("url") != target:
            raise WebhookSetupError("webhook_url_mismatch")
        # Verify that this app now lists the exact newly created subscription.
        response = await paypal._request("GET", "/v1/notifications/webhooks")
        confirmed = _matching_hook(response.get("webhooks", []), target)
        if not confirmed or confirmed.get("id") != hook_id:
            raise WebhookSetupError("webhook_registration_not_confirmed")
        return {"id": hook_id, "action": "created", "url": target}
    except (PayPalUnavailable, PayPalConfigurationError) as exc:
        raise WebhookSetupError("sandbox_webhook_api_unavailable") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect or explicitly register the production PayPal Sandbox webhook"
    )
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--check", action="store_true", help="Read-only listing")
    operation.add_argument("--register", action="store_true", help="Create only if absent")
    options = parser.parse_args()
    try:
        result = asyncio.run(ensure_webhook(create=options.register))
        if result["action"] == "missing":
            print("[paypal-webhook] Not registered for this REST app. Use --register.")
            return 2
        print("[paypal-webhook] " + result["action"] + " and verified")
        # The ID is a provider resource identifier, NOT an API secret or token.
        # It must be copied to the private PAYPAL_WEBHOOK_ID environment variable;
        # the application never prints an OAuth token or merchant secret.
        print("PAYPAL_WEBHOOK_ID=" + result["id"])
        print("Webhook URL: " + result["url"])
        return 0
    except WebhookSetupError as exc:
        print("[paypal-webhook] Unable to configure: " + str(exc))
        return 1
    except Exception:
        # Avoid printing raw HTTP errors or response bodies that may contain
        # confidential merchant account/transaction information.
        print("[paypal-webhook] Unable to configure: unexpected_error")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
