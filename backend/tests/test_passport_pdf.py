"""Decision Passport PDF output is valid, safe to render, and keeps disclaimers.

No real provider credentials or payments are used in these tests.
"""
from app.procurement.passport_pdf import passport_pdf_bytes


def test_passport_pdf_has_valid_signature_and_financial_disclosures():
    report={
        'order_number':'PP-20261105-TEST',
        'status':'paid',
        'created_at':'2026-11-05T10:00:00+00:00',
        'evidence':{
            'request':{'text':'Two 27 inch monitors for the team','quantity':2,'currency':'USD','budget':'300.00'},
            'discovered_at':'2026-11-05T09:00:00+00:00',
            'policy':{'mandatory_attributes':{'size':'27 inch'},'max_unit_price':'150.00'},
            'selected':{'title':'Sample monitor','merchant':'retailer.example','product_id':'item-one','unit_price':'120.00'},
            'ai':{'source':'gemini','model':'gemini-3.8-flash','explanation':'The sample was in stock.'},
            'limitations':['No retailer settlement','Delivery is unverified'],
        },
        'comparison':{'selected_total':'240.00','least_cost_eligible_total':'230.00','premium_vs_least_cost':'10.00','note':'No realized savings claimed'},
        'buyer_decision':{'approved_at':'2026-11-05T10:05:00+00:00','approval_model':'Human-controlled approval','entries':[{'at':'2026-11-05T10:05:00+00:00','decision':'approved','comment':'Budget accepted'}]},
        'payment_proof':{'status':'completed','amount':'240.00','currency':'USD','paypal_order_id':'SANDBOX-ORDER','capture_id':'SANDBOX-CAPTURE','signed_webhook_correlated':False},
        'audit_timeline':[{'at':'2026-11-05T10:00:00+00:00','action':'purchase_order.created'}],
        'snapshot_sha256':'abc'*21+'d',
        'integrity_note':'Checksum, not notarization',
    }
    pdf=passport_pdf_bytes(report)
    assert pdf.startswith(b'%PDF-')
    assert b'%%EOF' in pdf[-512:]
    assert len(pdf)>1500
    assert b'backend-only-secret-value' not in pdf


def test_passport_pdf_handles_long_untrusted_catalogue_text_with_page_breaks():
    report={
        'order_number':'PP-LONG','status':'draft','created_at':'2026-11-05',
        'evidence':{'request':{'text':'Long procurement description '*120,'quantity':1,'currency':'USD','budget':None},
                    'selected':{},'policy':{},'ai':{'explanation':'Supplier narrative '*140},
                    'limitations':['Shipping unknown']},
        'comparison':{},
        'buyer_decision':{},
        'payment_proof':{},
        'audit_timeline':[{'at':'2026-11-05','action':'event.'+str(i)} for i in range(100)],
        'snapshot_sha256':'x'*64,'integrity_note':'Source may change',
    }
    pdf=passport_pdf_bytes(report)
    assert pdf.startswith(b'%PDF-')
    assert b'%%EOF' in pdf[-512:]
    assert len(pdf)>2500
