# PayPal capture-response mismatch: diagnosis, correction and recovery

**Date:** 8 November 2026  
**System:** ProcurePilot AI (React/Vite + FastAPI + Neon + PayPal Sandbox Orders v2)  
**Issue:** After the Personal Sandbox buyer approved checkout, ProcurePilot's `Confirm buyer approval & capture` returned **"PayPal capture response does not match the approved purchase order."**

## 1. Root cause — confirmed from production source and PayPal's API contract

The previous capture path was:

1. GET `/v2/checkout/orders/{id}`; verify `id`, `status`, `purchase_units[0].custom_id`, `purchase_units[0].amount.currency_code` and `purchase_units[0].amount.value` against the approved PO. **This is the correct strict pre-payment check.**
2. POST `/v2/checkout/orders/{id}/capture` with stable idempotency key.
3. **BUG:** Apply that *same strict pre-capture order matcher* to the immediate POST capture response. It required `custom_id` and the original unit-level `amount` again.
4. PayPal's documented completed capture response can include `id`, `status=COMPLETED`, `purchase_units[].reference_id`, `purchase_units[].payments.captures[0].id`, `status`, `amount`, **without** repeating `purchase_units[].custom_id` or `purchase_units[].amount`. The previous code returned HTTP 502 **after PayPal may already have completed the capture**.

Official PayPal examples:
- https://developer.paypal.com/platforms/checkout/standard/integrate
- https://developer.paypal.com/api/orders-v2/track-orders/use/
- https://developer.paypal.com/api/orders/v2/definitions/purchase_unit

**Do not confuse a server-side validation 502 with an unsuccessful PayPal capture.** The specific real payment cannot be classified conclusively until the same order's actual provider state and saved PO are reconciled.

## 2. Corrected invariant / design

- **Before payment:** GET the saved, merchant-bound PayPal order; strictly check saved order ID, PO `custom_id`, exact approved amount/currency and approved state. Do not send POST capture if this fails.
- **After capture:** Validate the actual Orders v2 capture shape separately. Require *the same PayPal order ID*, one purchase unit, **exactly one** completed capture, a valid capture ID, and precise `capture.amount` and `capture.currency_code` matching the approved PO. When `reference_id`, `custom_id`, or original purchase-unit amount are present, check them for contradictions. They are not mandatory in the capture representation. Reject NaN, wrong/missing capture evidence, wrong currency, extra captures or conflicting IDs.
- **Recovery after the old 502:** If GET now reports `status=COMPLETED`, verify exact completed capture evidence and reconcile the saved payment and PO to `paid`, **without issuing another POST /capture**. This works even when completed GET omits the original unit-level metadata.
- **Sparse immediate POST response:** If PayPal reports COMPLETED but omits detailed capture evidence, a strictly non-contradictory payload may be reconciled with **one read-only GET** for the same order. Contradictory evidence is never overridden or silently accepted.
- **Idempotency and concurrent webhooks:** Preserve the same saved PayPal order and PayPal-Request-Id for valid unfinished attempts; re-check the database after provider I/O; if a verified webhook has already finalized the order, return the saved paid status, never replace its existing capture ID.
- **Merchant rotation:** The previously added REST-app fingerprint check remains: no old seller checkout can be captured after changing Business seller credentials.
- **No fake paid state:** A buyer return alone, an authenticated OAuth token, or a PayPal order `APPROVED` state never marks the PO `paid`. Only exact verified completed capture evidence does.

## 3. Changed source

- `backend/app/api/purchase_orders.py`: keep strict `_paypal_order_matches` for pre-capture GET; introduce `_paypal_completed_capture` and `_paypal_capture_response_noncontradictory`; route successful capture and already-completed reconciliation through correct validators; preserve refusal on contradictory transaction evidence.
- `backend/tests/test_purchase_orders.py`: pytest API regressions for PayPal-shaped POST, read-only reconciliation, already-completed GET with and without original unit metadata, wrong/duplicate/nonfinite captures, strict no-capture on PO mismatch and zero repeat POST.
- `backend/scripts/verify_paypal_capture.py`: dependency-free, no-network **16-test** standard-library contract and actual FastAPI workflow suite, using in-memory SQLite, mocked Channel3 and mocked PayPal, with zero external provider calls.
- `backend/scripts/release_schema_gate.py`: optional Preview-only regression check, enabled by `PROCUREPILOT_STAGING_CAPTURE_TESTS=1`, never run on Production; no new CI workflow.

No database migration, PayPal order creation, capture, refund, webhook subscription mutation, or production payment record changes were made by this correction.

## 4. QA evidence and limitations

- **Preview Services release:** `dpl_5zTq6WPg46GHqoCdvpD5XZY4NiwD` reached **READY** with the Preview-only no-network standard-library suite enabled. The suite verifies the actual capture matcher and four FastAPI endpoint workflows. Successful release means the test command exited zero.
- **Full pytest suite:** Authored and retained. The Vercel build environment does not provide `pytest` at runtime; the initial pytest-only gate returned explicit code 107, so full pytest execution is **not claimed**. Local command from `backend/`: `python -m pytest -q tests/test_purchase_orders.py` (requires dev dependencies). An isolated Preview QA gate uses only the standard library.
- **Actual existing Sandbox transaction:** Status is **unknown** to this investigation. The connected Neon database access was pinned to a role that does not permit querying the Production owner's role, and no authorized user's order session or provider receipt is accessible here. Nothing has been claimed about an actual capture ID or actual merchant receipt.
- **Signed webhook delivery:** Separate provider acceptance gate; the three registered PayPal events must include `CHECKOUT.ORDER.APPROVED`, `PAYMENT.CAPTURE.COMPLETED`, and `PAYMENT.CAPTURE.DENIED`.

## 5. Operator recovery of the existing failed checkout

1. After deployment, **reload** https://procurepilotai.vercel.app/orders.
2. Locate the **same approved/pending purchase order** from the successful Personal Sandbox checkout. **Do not create a new purchase order or another checkout.**
3. Check its `Payment` and `PayPal order` information. If already `Paid`, do not press capture.
4. If still pending, select **Confirm buyer approval & capture** **on that same PO only**. The server first GETs the saved PayPal order:
   - If PayPal already completed the capture, it validates its capture evidence and records the PO as paid **without any new capture POST**.
   - If PayPal has only approved the order, it may perform the original authorized capture using the existing idempotency key.
   - If the provider reports a mismatch or uncertain state, it fails closed; retain the same PO and inspect the PayPal order before retrying.
5. Verify `Paid`, a nonempty capture ID, the matching exact USD amount and PO audit timeline, and the dashboard's signed webhook status. A delivered webhook is separately required for 100% acceptance.

Never disclose Sandbox REST secrets, wallet passwords, PayPal approval tokens, or buyer details in public issue/PR logs.

## 6. Acceptance remaining

- [x] Distinct PayPal response shapes handled in backend source
- [x] Safe recovery path when PayPal is already COMPLETED
- [x] Strict amount/currency/order binding and anti-duplicate validation retained
- [x] In-memory no-network contract and endpoint regression test suite Preview READY
- [ ] Full workstation pytest and browser-level E2E
- [ ] Confirm the user's **actual** previously failing Sandbox PO reconciles to Paid
- [ ] Confirm actual signed Webhook Events delivery and idempotency in the PayPal Developer dashboard
