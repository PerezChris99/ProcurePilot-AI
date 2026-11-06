"""A policy stress test exercises the real evaluate_offer gate, not mocks."""
from app.procurement.trust_lab import trust_lab_scenarios


def test_threat_scenarios_fully_enforced_by_actual_purchase_policy():
    evidence = trust_lab_scenarios()
    assert evidence["source"] == "synthetic_policy_fixtures"
    assert evidence["verified_by"] == "app.procurement.policy.evaluate_offer"
    assert evidence["payment_calls"] == 0
    assert evidence["total"] >= 10
    assert evidence["passed"] == evidence["total"]
    by_id = {item["id"]: item for item in evidence["scenarios"]}
    assert by_id["valid_offer"]["allowed"] is True
    for id_ in (
        "wrong_diagonal", "unknown_diagonal", "accessory", "out_of_stock",
        "over_budget", "wrong_currency", "unapproved_merchant",
        "insecure_offer", "expired_mandate",
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
    assert body["total"] == 10
    assert body["passed"] == 10
    assert body["payment_calls"] == 0
    assert all(item["id"] and item["expected_allowed"] == item["allowed"]
               for item in body["scenarios"])
    assert "access_token" not in str(body).lower()
    assert "paypal_order_id" not in str(body).lower()
