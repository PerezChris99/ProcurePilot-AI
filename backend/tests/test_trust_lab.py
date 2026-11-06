"""A policy stress test exercises the real evaluate_offer gate, not mocks."""
from app.procurement.trust_lab import trust_lab_scenarios


def test_threat_scenarios_fully_enforced_by_actual_purchase_policy():
    evidence = trust_lab_scenarios()
    assert evidence["source"] == "synthetic_policy_fixtures"
    assert evidence["verified_by"] == "app.procurement.policy.evaluate_offer"
    assert evidence["payment_calls"] == 0
    assert evidence["total"] == 12
    assert evidence["passed"] == evidence["total"]
    by_id = {item["id"]: item for item in evidence["scenarios"]}
    assert by_id["valid_offer"]["allowed"] is True
    for id_ in (
        "wrong_diagonal", "unknown_diagonal", "accessory", "out_of_stock",
        "over_budget", "wrong_currency", "unapproved_merchant",
        "insecure_offer", "expired_mandate", "unauthorized_approver",
        "tampered_paypal_amount",
    ):
        assert by_id[id_]["allowed"] is False
        assert by_id[id_]["violations"]
    assert "72-inch" in by_id["wrong_diagonal"]["violations"][0]
    assert any("Total exceeds purchasing budget" in reason
               for reason in by_id["over_budget"]["violations"])


def test_trust_lab_requires_login_and_returns_no_real_provider_data(client):
    unauthenticated = client.get("/api/v1/trust-lab/scenarios")
    assert unauthenticated.status_code == 401
    signed = client.post("/api/v1/auth/register", json={
        "email": "trust-lab-testing@example.com",
        "full_name": "Trust Lab QA",
        "password": "correct-horse-battery-staple",
    })
    assert signed.status_code == 201
    headers = {"Authorization": "Bearer " + signed.json()["access_token"]}
    answer = client.get("/api/v1/trust-lab/scenarios", headers=headers)
    assert answer.status_code == 200
    body = answer.json()
    assert body["total"] == 12
    assert body["passed"] == 12
    assert body["payment_calls"] == 0
    assert all(item["id"] and item["expected_allowed"] == item["allowed"]
               for item in body["scenarios"])
    assert "access_token" not in str(body).lower()
    assert "paypal_order_id" not in str(body).lower()


def test_shared_authorization_and_paypal_matching_predicates_fail_closed():
    from types import SimpleNamespace
    from decimal import Decimal
    from app.api.purchase_orders import _can_approve_order, _paypal_order_matches
    order = SimpleNamespace(id="po",user_id="owner",
                            assigned_approver_id="delegate",
                            currency="USD",total_amount=Decimal("300.00"))
    assert _can_approve_order(order,"owner") is False
    assert _can_approve_order(order,"outsider") is False
    assert _can_approve_order(order,"delegate") is True
    order.assigned_approver_id=None
    assert _can_approve_order(order,"owner") is True
    payment=SimpleNamespace(paypal_order_id="SANDBOX-ORDER-CASE")
    valid={"id":"SANDBOX-ORDER-CASE","status":"APPROVED",
           "purchase_units":[{"custom_id":"po",
               "amount":{"value":"300.00","currency_code":"USD"}}]}
    assert _paypal_order_matches(valid,order,payment) is True
    tampered={"id":valid["id"],"status":"APPROVED",
              "purchase_units":[{"custom_id":"po",
                  "amount":{"value":"1.00","currency_code":"USD"}}]}
    assert _paypal_order_matches(tampered,order,payment) is False
