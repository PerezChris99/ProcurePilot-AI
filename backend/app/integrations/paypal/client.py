import re
import httpx

from urllib.parse import urlsplit
from app.core.config import get_settings


class PayPalConfigurationError(RuntimeError):
    pass


class PayPalUnavailable(RuntimeError):
    pass


class PayPalClient:
    def __init__(self, transport=None):
        settings = get_settings()
        self.client_id = settings.paypal_client_id
        self.client_secret = settings.paypal_client_secret
        self.base_url = settings.paypal_base_url.rstrip("/")
        self.webhook_id = settings.paypal_webhook_id
        self.transport = transport
        try:
            parsed = urlsplit(self.base_url)
            valid = (
                parsed.scheme == "https"
                and parsed.hostname in ("api-m.sandbox.paypal.com", "api-m.paypal.com")
                and parsed.path in ("", "/")
                and parsed.username is None
                and parsed.password is None
                and parsed.port is None
                and not parsed.query
                and not parsed.fragment
            )
        except ValueError:
            valid = False
        if not valid:
            raise PayPalConfigurationError(
                "PayPal API base URL must be an official PayPal Sandbox or Live API host"
            )

    @staticmethod
    def is_valid_order_id(value):
        return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", value) is not None

    @staticmethod
    def is_approval_url(value):
        try:
            if not isinstance(value, str):
                return False
            parsed = urlsplit(value)
            return (
                parsed.scheme == "https"
                and parsed.hostname in ("www.sandbox.paypal.com", "www.paypal.com")
                and not parsed.username
                and not parsed.password
                and parsed.port is None
            )
        except ValueError:
            return False

    def ensure_configured(self):
        if not self.client_id or not self.client_secret:
            raise PayPalConfigurationError("PayPal API credentials are not configured")

    async def _access_token(self):
        self.ensure_configured()
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(15, connect=4), transport=self.transport
            ) as client:
                response = await client.post(
                    self.base_url + "/v1/oauth2/token",
                    auth=(self.client_id, self.client_secret),
                    data={"grant_type": "client_credentials"},
                    headers={"Accept": "application/json", "Accept-Language": "en_US"},
                )
                response.raise_for_status()
                token = response.json().get("access_token")
                if not token:
                    raise PayPalUnavailable("PayPal did not issue an access token")
                return token
        except (httpx.HTTPError, ValueError) as exc:
            raise PayPalUnavailable("PayPal authentication failed") from exc

    async def _request(self, method, path, *, payload=None, request_id=None):
        token = await self._access_token()
        headers = {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if request_id:
            headers["PayPal-Request-Id"] = request_id
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(20, connect=4), transport=self.transport
            ) as client:
                response = await client.request(
                    method, self.base_url + path, headers=headers, json=payload
                )
                response.raise_for_status()
                return response.json() if response.content else {}
        except (httpx.HTTPError, ValueError) as exc:
            raise PayPalUnavailable("PayPal transaction request failed") from exc

    async def create_order(
        self,
        *,
        po_id,
        po_number,
        amount,
        currency,
        description,
        quantity,
        unit_price,
        idempotency_key,
        return_url,
        cancel_url,
    ):
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "reference_id": po_number,
                    "custom_id": po_id,
                    "description": description[:127],
                    "amount": {
                        "currency_code": currency,
                        "value": amount,
                        "breakdown": {
                            "item_total": {"currency_code": currency, "value": amount}
                        },
                    },
                    "items": [
                        {
                            "name": description[:127],
                            "quantity": str(quantity),
                            "unit_amount": {"currency_code": currency, "value": unit_price},
                            "category": "PHYSICAL_GOODS",
                        }
                    ],
                }
            ],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "return_url": return_url,
                        "cancel_url": cancel_url,
                        "user_action": "PAY_NOW",
                        "shipping_preference": "NO_SHIPPING",
                    }
                }
            },
        }
        return await self._request(
            "POST",
            "/v2/checkout/orders",
            payload=payload,
            request_id=idempotency_key,
        )

    async def get_order(self, order_id):
        if not self.is_valid_order_id(order_id):
            raise ValueError("Invalid PayPal order ID")
        return await self._request("GET", "/v2/checkout/orders/" + order_id)

    async def capture_order(self, order_id, idempotency_key):
        if not self.is_valid_order_id(order_id):
            raise ValueError("Invalid PayPal order ID")
        return await self._request(
            "POST",
            "/v2/checkout/orders/" + order_id + "/capture",
            payload={},
            request_id=idempotency_key,
        )

    async def verify_webhook(self, headers, event):
        self.ensure_configured()
        if not self.webhook_id:
            raise PayPalConfigurationError("PayPal webhook ID is not configured")
        required = (
            "paypal-auth-algo",
            "paypal-cert-url",
            "paypal-transmission-id",
            "paypal-transmission-sig",
            "paypal-transmission-time",
        )
        if any(not headers.get(name) for name in required):
            return False
        payload = {
            "auth_algo": headers["paypal-auth-algo"],
            "cert_url": headers["paypal-cert-url"],
            "transmission_id": headers["paypal-transmission-id"],
            "transmission_sig": headers["paypal-transmission-sig"],
            "transmission_time": headers["paypal-transmission-time"],
            "webhook_id": self.webhook_id,
            "webhook_event": event,
        }
        result = await self._request(
            "POST", "/v1/notifications/verify-webhook-signature", payload=payload
        )
        return result.get("verification_status") == "SUCCESS"
