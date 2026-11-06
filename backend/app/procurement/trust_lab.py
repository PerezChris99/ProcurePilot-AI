"""Read-only purchasing trust lab.

Each scenario constructs *labelled synthetic fixture data* and executes the
same deterministic evaluate_offer() production policy used by PO creation.
No real catalogue data, AI calls, PayPal actions, database writes or invented
live-protection metrics are performed.
"""
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.integrations.channel3.schemas import (
    Channel3Offer, Channel3Price, Channel3Product,
)
from app.procurement.policy import evaluate_offer

# One positive control and negative controls for independently enforced gates.
_SCENARIOS = (
    {
        "id": "valid_offer",
        "name": "Valid 27-inch office monitor",
        "intent": "Two 27-inch monitors",
        "title": "27-inch office monitor",
        "attributes": {"screen_size": "27 inch"},
        "unit_price": "140.00",
        "quantity": 2,
        "budget": "350.00",
        "currency": "USD",
        "availability": "InStock",
        "url": "https://approved.example/item",
        "policy": {},
        "expected_allowed": True,
    },
    {
        "id": "wrong_diagonal",
        "name": "Wrong monitor diagonal",
        "intent": "Four 72-inch monitors",
        "title": "24-inch office monitor",
        "attributes": {"screen_size": "24 inch"},
        "unit_price": "180.00",
        "quantity": 4,
        "budget": "3000.00",
        "currency": "USD",
        "availability": "InStock",
        "url": "https://approved.example/item",
        "policy": {},
        "expected_allowed": False,
    },
    {
        "id": "unknown_diagonal",
        "name": "Unverifiable monitor diagonal",
        "intent": "Four 72-inch monitors",
        "title": "Office monitor (size unspecified)",
        "attributes": {},
        "unit_price": "180.00",
        "quantity": 4,
        "budget": "3000.00",
        "currency": "USD",
        "availability": "InStock",
        "url": "https://approved.example/item",
        "policy": {},
        "expected_allowed": False,
    },
    {
        "id": "accessory",
        "name": "Accessory masquerading as a display",
        "intent": "Four 72-inch monitors",
        "title": "72-inch Monitor Arm",
        "attributes": {"screen_size": "72 inch"},
        "unit_price": "60.00",
        "quantity": 4,
        "budget": "3000.00",
        "currency": "USD",
        "availability": "InStock",
        "url": "https://approved.example/item",
        "policy": {},
        "expected_allowed": False,
    },
    {
        "id": "out_of_stock",
        "name": "Item with no confirmed stock",
        "intent": "Two office monitors",
        "title": "Office monitor",
        "attributes": {},
        "unit_price": "120.00",
        "quantity": 2,
        "budget": "500.00",
        "currency": "USD",
        "availability": "OutOfStock",
        "url": "https://approved.example/item",
        "policy": {},
        "expected_allowed": False,
    },
    {
        "id": "over_budget",
        "name": "Quantity exceeds total budget",
        "intent": "Four office monitors",
        "title": "Office monitor",
        "attributes": {},
        "unit_price": "850.00",
        "quantity": 4,
        "budget": "3000.00",
        "currency": "USD",
        "availability": "InStock",
        "url": "https://approved.example/item",
        "policy": {},
        "expected_allowed": False,
    },
    {
        "id": "wrong_currency",
        "name": "Offer priced in another currency",
        "intent": "Two office monitors",
        "title": "Office monitor",
        "attributes": {},
        "unit_price": "120.00",
        "quantity": 2,
        "budget": "500.00",
        "currency": "EUR",
        "request_currency": "USD",
        "availability": "InStock",
        "url": "https://approved.example/item",
        "policy": {},
        "expected_allowed": False,
    },
    {
        "id": "unapproved_merchant",
        "name": "Merchant outside the buyer allowlist",
        "intent": "Two office monitors",
        "title": "Office monitor",
        "attributes": {},
        "unit_price": "120.00",
        "quantity": 2,
        "budget": "500.00",
        "currency": "USD",
        "availability": "InStock",
        "url": "https://unapproved.example/item",
        "policy": {"allowed_merchants": ["approved.example"]},
        "expected_allowed": False,
    },
    {
        "id": "insecure_offer",
        "name": "Merchant offer is not HTTPS",
        "intent": "Two office monitors",
        "title": "Office monitor",
        "attributes": {},
        "unit_price": "120.00",
        "quantity": 2,
        "budget": "500.00",
        "currency": "USD",
        "availability": "InStock",
        "url": "http://approved.example/item",
        "policy": {},
        "expected_allowed": False,
    },
    {
        "id": "expired_mandate",
        "name": "Buyer mandate has expired",
        "intent": "Two office monitors",
        "title": "Office monitor",
        "attributes": {},
        "unit_price": "120.00",
        "quantity": 2,
        "budget": "500.00",
        "currency": "USD",
        "availability": "InStock",
        "url": "https://approved.example/item",
        "policy": {"expires_at": "2020-01-01T00:00:00+00:00"},
        "expected_allowed": False,
    },
)


def trust_lab_scenarios():
    results = []
    for case in _SCENARIOS:
        product = Channel3Product(
            id="synthetic-" + case["id"],
            title=case["title"],
            structured_attributes=case["attributes"],
        )
        offer = Channel3Offer(
            url=case["url"],
            domain=case["url"].split("/")[2],
            price=Channel3Price(amount=Decimal(case["unit_price"]),
                                currency=case["currency"]),
            availability=case["availability"],
        )
        request = SimpleNamespace(
            request_text=case["intent"],
            quantity=case["quantity"],
            currency=case.get("request_currency", case["currency"]),
            budget=Decimal(case["budget"]),
            policy_json=case["policy"],
        )
        # This function also governs real creation of immutable purchase orders.
        reasons = evaluate_offer(request, product, offer)
        allowed = not reasons
        results.append({
            "id": case["id"],
            "name": case["name"],
            "intent": case["intent"],
            "product_title": product.title,
            "quantity": request.quantity,
            "unit_price": case["unit_price"],
            "quoted_total": str(Decimal(case["unit_price"]) * request.quantity),
            "budget": case["budget"],
            "offer_currency": case["currency"],
            "request_currency": request.currency,
            "availability": case["availability"],
            "merchant": offer.domain,
            "expected_allowed": case["expected_allowed"],
            "allowed": allowed,
            "passed": allowed == case["expected_allowed"],
            "violations": reasons,
        })
    return {
        "source": "synthetic_policy_fixtures",
        "verified_by": "app.procurement.policy.evaluate_offer",
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "never_contacts": ["Channel3", "Gemini", "PayPal"],
        "payment_calls": 0,
        "scenarios": results,
        "passed": sum(case["passed"] for case in results),
        "total": len(results),
        "note": (
            "Read-only checks against the actual server purchase policy "
            "with labelled synthetic inputs. This is NOT a penetration test "
            "or proof that live payment providers are reachable."
        ),
    }
