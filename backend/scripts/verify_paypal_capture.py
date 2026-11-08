"""No-network, no-pytest PayPal capture contract acceptance for Vercel Preview.

The test suite makes ZERO real PayPal/Channel3 HTTP requests, never touches
Neon (in-memory SQLite), and never creates a real charge. This complements
pytest tests/test_purchase_orders.py, which developers run locally.
"""
from __future__ import annotations

import io
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from app.api.purchase_orders import (
    _paypal_order_matches, _paypal_completed_capture,
    _paypal_capture_response_noncontradictory,
)
from app.integrations.paypal.client import PayPalClient

ORDER=SimpleNamespace(id="11111111-2222-3333-4444-555555555555",
                      po_number="PP-20261108-ABCDEF01",
                      total_amount=Decimal("240.00"),currency="USD")
PAYMENT=SimpleNamespace(paypal_order_id="PAYPAL-TEST-ORDER-123",
                        capture_id=None)


def approved_get():
    return {
        "id":PAYMENT.paypal_order_id,"status":"APPROVED",
        "purchase_units":[{
            "reference_id":ORDER.po_number,"custom_id":ORDER.id,
            "amount":{"value":"240.00","currency_code":"USD"},
        }],
    }


def captured_response():
    # Modeled after the official PayPal Orders v2 capture example: the
    # original custom_id and purchase-unit amount are absent.
    return {
        "id":PAYMENT.paypal_order_id,"status":"COMPLETED",
        "purchase_units":[{
            "reference_id":ORDER.po_number,
            "payments":{"captures":[{
                "id":"CAPTURE-RESULT-987654321","status":"COMPLETED",
                "amount":{"currency_code":"USD","value":"240.00"},
            }]},
        }],
    }


class CaptureContract(unittest.TestCase):
    def test_approved_order_identity_and_amount_before_capture(self):
        self.assertTrue(_paypal_order_matches(approved_get(),ORDER,PAYMENT))
        missing=approved_get()
        del missing["purchase_units"][0]["custom_id"]
        self.assertFalse(_paypal_order_matches(missing,ORDER,PAYMENT))

    def test_capture_response_accepts_omitted_original_metadata(self):
        capture=_paypal_completed_capture(captured_response(),ORDER,PAYMENT)
        self.assertEqual(capture["id"],"CAPTURE-RESULT-987654321")
        self.assertFalse(_paypal_order_matches(captured_response(),ORDER,PAYMENT))

    def test_completed_get_can_reconcile_without_recapture(self):
        self.assertEqual(_paypal_completed_capture(captured_response(),ORDER,PAYMENT)["status"],"COMPLETED")

    def test_wrong_amount_fails(self):
        result=captured_response()
        result["purchase_units"][0]["payments"]["captures"][0]["amount"]["value"]="239.99"
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))
        self.assertFalse(_paypal_capture_response_noncontradictory(result,ORDER,PAYMENT))

    def test_wrong_currency_fails(self):
        result=captured_response()
        result["purchase_units"][0]["payments"]["captures"][0]["amount"]["currency_code"]="EUR"
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))

    def test_wrong_order_id_fails(self):
        result=captured_response();result["id"]="WRONG-ORDER-123"
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))

    def test_wrong_explicit_custom_id_fails(self):
        result=captured_response()
        result["purchase_units"][0]["custom_id"]="unrelated-po"
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))

    def test_wrong_reference_id_fails(self):
        result=captured_response()
        result["purchase_units"][0]["reference_id"]="WRONG-PO"
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))

    def test_duplicate_capture_fails(self):
        result=captured_response()
        capture=result["purchase_units"][0]["payments"]["captures"][0]
        result["purchase_units"][0]["payments"]["captures"].append(capture.copy())
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))

    def test_nan_capture_fails(self):
        result=captured_response()
        result["purchase_units"][0]["payments"]["captures"][0]["amount"]["value"]="NaN"
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))

    def test_existing_other_capture_id_fails(self):
        result=captured_response()
        payment=SimpleNamespace(paypal_order_id=PAYMENT.paypal_order_id,
                                capture_id="ANOTHER-CAPTURE")
        self.assertIsNone(_paypal_completed_capture(result,ORDER,payment))

    def test_sparse_completed_response_allows_read_only_follow_up(self):
        result=captured_response()
        result["purchase_units"][0]["payments"]={}
        self.assertIsNone(_paypal_completed_capture(result,ORDER,PAYMENT))
        self.assertTrue(_paypal_capture_response_noncontradictory(result,ORDER,PAYMENT))


def run() -> int:
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(CaptureContract)
    result=unittest.TextTestRunner(stream=io.StringIO(),verbosity=0).run(suite)
    if not result.wasSuccessful():
        # Tests contain only hardcoded synthetic values. Even so, print only
        # testcase method names and do not print exception traces/credentials.
        for case,_ in result.failures+result.errors:
            print("[paypal-capture] FAIL "+case._testMethodName)
        return 1
    print("[paypal-capture] PASS "+str(result.testsRun)+" no-network contract tests")
    return 0


if __name__=="__main__":
    raise SystemExit(run())
