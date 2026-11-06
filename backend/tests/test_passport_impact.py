"""Impact comparisons must be factual and never count rejected listings as savings."""
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

from app.procurement.passport import build_passport


def example_order():
    when = datetime(2026, 11, 6, tzinfo=timezone.utc)
    return SimpleNamespace(
        id="po-impact",po_number="PP-IMPACT",
        status="approved",currency="USD",
        total_amount=Decimal("300.00"),created_at=when,
        approved_at=when,approved_by="buyer",
        assigned_approver_id=None,
        offer_verification_json=None,
        evidence_json={
            "source":"Channel3",
            "request":{"quantity":2,"currency":"USD"},
            "selected":{"product_id":"selected","total_price":"300.00"},
            "compared_offers":[
                {"product_id":"selected","title":"27 inch monitor",
                 "merchant":"approved.example","unit_price":"150.00",
                 "currency":"USD","eligible":True,"blocked_by":[]},
                {"product_id":"more-expensive","title":"27 inch monitor premium",
                 "merchant":"approved.example","unit_price":"170.00",
                 "currency":"USD","eligible":True,"blocked_by":[]},
                {"product_id":"wrong-size","title":"24 inch monitor",
                 "merchant":"blocked.example","unit_price":"45.00",
                 "currency":"USD","eligible":False,
                 "blocked_by":["Required 27-inch screen size not evidenced"]},
                {"product_id":"unavailable","title":"27 inch monitor, out of stock",
                 "merchant":"blocked.example","unit_price":"80.00",
                 "currency":"USD","eligible":False,
                 "blocked_by":["Stock is not confirmed"]},
                {"product_id":"foreign","title":"Monitor in EUR",
                 "merchant":"blocked.example","unit_price":"10.00",
                 "currency":"EUR","eligible":False,
                 "blocked_by":["Offer currency differs from request"]},
            ],
        },
    )


def test_passport_only_uses_eligible_same_currency_prices_for_buyable_baseline():
    report=build_passport(example_order(),[],[],None,[])
    comparison=report["comparison"]
    assert comparison["offers_evaluated_count"]==5
    assert comparison["policy_blocked_offer_count"]==3
    assert comparison["eligible_offer_count"]==2
    assert comparison["least_cost_eligible_total"]=="300.00"
    assert comparison["premium_vs_least_cost"]=="0"
    assert comparison["selected_is_lowest_eligible"] is True
    assert comparison["cheapest_rejected_total"]=="90.00"
    assert comparison["cheapest_rejected_offer"]["product_id"]=="wrong-size"
    assert "27-inch" in comparison["cheapest_rejected_offer"]["blocked_by"][0]
    assert comparison["eligible_vs_rejected_price_gap"]=="210.00"
    assert "not savings" in comparison["note"]
    assert len(report["snapshot_sha256"])==64


def test_passport_never_compares_or_leaks_unknown_and_foreign_currency_prices():
    order=example_order()
    order.evidence_json["compared_offers"]=[
        {"product_id":"bad","unit_price":"1.00","currency":"EUR",
         "eligible":False,"blocked_by":["Wrong currency"]},
        {"product_id":"invalid","unit_price":"0","currency":"USD",
         "eligible":False,"blocked_by":["Zero amount"]},
    ]
    report=build_passport(order,[],[],None,[])
    compare=report["comparison"]
    assert compare["eligible_offer_count"]==0
    assert compare["cheapest_rejected_total"] is None
    assert compare["least_cost_eligible_total"] is None
    assert compare["eligible_vs_rejected_price_gap"] is None
