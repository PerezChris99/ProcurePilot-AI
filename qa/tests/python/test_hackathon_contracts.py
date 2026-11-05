"""Additional deterministic purchasing tests; no network, DB or credentials."""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.integrations.channel3.schemas import Channel3Offer, Channel3Price, Channel3Product
from app.procurement.passport import build_passport, snapshot_for_order
from app.procurement.policy import evaluate_offer, policy_expired, snapshot_recent


def request(*, budget=Decimal("300.00"), policy=None, quantity=2):
    return SimpleNamespace(
        id="qa-request", user_id="qa-user",
        request_text="Two 27-inch monitors for an office",
        quantity=quantity, currency="USD", budget=budget,
        policy_json=policy or {}, analysis_json=None,
    )


def product_offer(*, amount="120.00", currency="USD", availability="InStock",
                  url="https://approved.example.com/monitor", size="27 inch"):
    offer = Channel3Offer(
        url=url, domain="approved.example.com",
        price=Channel3Price(amount=Decimal(amount), currency=currency),
        availability=availability,
    )
    product = Channel3Product(
        id="monitor-27", title="Office display",
        structured_attributes={"screen_size": [size]}, offers=[offer],
    )
    return product, offer


def test_a_compliant_offer_can_be_evidenced():
    req = request(policy={
        "mandatory_attributes": {"screen_size": "27 inch"},
        "allowed_merchants": ["example.com"],
        "max_unit_price": "125.00",
    })
    product, offer = product_offer()
    assert evaluate_offer(req, product, offer) == []


@pytest.mark.parametrize("change,expected", [
    ({"amount": "160.00"}, "Unit price exceeds buyer mandate"),
    ({"currency": "EUR"}, "Offer currency differs from request"),
    ({"availability": "OutOfStock"}, "Stock is not confirmed"),
    ({"size": "24 inch"}, "Required screen_size is not evidenced"),
    ({"url": "https://evil-example.com/monitor"}, "Merchant is not on the approved domain list"),
    ({"url": "http://example.com/monitor"}, "Offer URL must be a secure merchant link"),
])
def test_buyer_mandates_block_noncompliant_offer(change, expected):
    req = request(policy={
        "mandatory_attributes": {"screen_size": "27 inch"},
        "allowed_merchants": ["example.com"],
        "max_unit_price": "125.00",
    })
    product, offer = product_offer(**change)
    assert any(expected in reason for reason in evaluate_offer(req, product, offer))


def test_budget_applies_to_quantity_not_only_unit_price():
    product, offer = product_offer()
    assert not evaluate_offer(request(budget=Decimal("250.00")), product, offer)
    reasons = evaluate_offer(request(budget=Decimal("200.00")), product, offer)
    assert "Total exceeds purchasing budget" in reasons


def test_expired_mandate_never_authorizes_checkout():
    now = datetime.now(timezone.utc)
    req = request(policy={"expires_at": (now - timedelta(minutes=1)).isoformat()})
    product, offer = product_offer()
    assert policy_expired(req, now=now)
    assert "Buyer mandate expired" in evaluate_offer(req, product, offer, now=now)


def test_only_genuine_recent_channel3_snapshots_can_create_orders():
    now = datetime.now(timezone.utc)
    fresh = {"source": "Channel3", "discovered_at": now.isoformat()}
    assert snapshot_recent(fresh, now=now)
    assert not snapshot_recent({**fresh, "source": "offline_demo"}, now=now)
    assert not snapshot_recent({
        **fresh, "discovered_at": (now - timedelta(days=2)).isoformat()
    }, now=now)
    assert not snapshot_recent({**fresh, "discovered_at": "broken"}, now=now)


def test_decision_passport_keeps_frozen_offer_and_never_claims_retailer_settlement():
    req = request()
    product, offer = product_offer()
    req.analysis_json = {
        "source": "Channel3",
        "discovered_at": datetime.now(timezone.utc).isoformat(),
        "ai_source": "gemini", "ai_model": "mock-model",
        "ai_explanation": "A source-grounded summary.",
        "results": [{
            "product": product.model_dump(mode="json"),
            "ranking": {"eligible": True},
        }],
    }
    evidence = snapshot_for_order(req, product.id, str(offer.url))
    assert evidence["selected"]["unit_price"] == "120.00"
    assert evidence["selected"]["total_price"] == "240.00"
    req.analysis_json["results"][0]["product"]["title"] = "MUTATED"
    assert evidence["selected"]["title"] == "Office display"
    order = SimpleNamespace(
        id="qa-order", po_number="PP-QA", currency="USD",
        total_amount=Decimal("240.00"), status="approved",
        evidence_json=evidence, offer_verification_json=None,
        approved_by="qa-user", approved_at=None,
        created_at=datetime.now(timezone.utc),
    )
    report = build_passport(order, [], [], None, [])
    assert report["comparison"]["least_cost_eligible_total"] == "240.00"
    assert Decimal(report["comparison"]["premium_vs_least_cost"]) == 0
    assert report["payment_proof"]["retailer_settlement"] is False
    assert report["payment_proof"]["status"] == "not_started"
    assert len(report["snapshot_sha256"]) == 64
    assert "not independent proof" in report["integrity_note"]
