"""Accessible text-only, printable evidence export; no remote assets."""
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas


def passport_pdf_bytes(report):
    output=BytesIO()
    doc=canvas.Canvas(output,pagesize=A4,pageCompression=1)
    width,height=A4
    x=45
    y=height-48

    def line(value='',*,strong=False):
        nonlocal y
        value=' '.join(str(value or '').split())
        value=value.encode('latin-1','replace').decode('latin-1')
        font='Helvetica-Bold' if strong else 'Helvetica'
        size=11 if strong else 9.7
        for part in simpleSplit(value,font,size,width-90) or ['']:
            if y<57:
                doc.showPage()
                y=height-48
            doc.setFont(font,size)
            doc.drawString(x,y,part)
            y-=16
        y-=3

    def label(value):
        nonlocal y
        y-=9
        line(value,strong=True)

    line('PROCUREPILOT | DECISION PASSPORT',strong=True)
    line('Evidence-backed procurement and PayPal Sandbox demonstration')
    line('Purchase order: '+str(report['order_number']))
    line('Status: '+str(report['status']))
    line('Created: '+str(report['created_at']))
    evidence=report.get('evidence') or {}
    request=evidence.get('request') or {}
    label('PURCHASE REQUEST')
    line(request.get('text','Legacy order; original evidence not stored'))
    line('Quantity: '+str(request.get('quantity','Unknown'))+
         ' | Currency: '+str(request.get('currency','Unknown'))+
         ' | Budget: '+str(request.get('budget','Not specified')))
    line('Channel3 snapshot: '+str(evidence.get('discovered_at') or 'Not captured'))
    label('BUYER POLICY')
    policy=evidence.get('policy') or {}
    line('Mandatory specifications: '+str(policy.get('mandatory_attributes') or 'None'))
    line('Approved merchant domains: '+str(policy.get('allowed_merchants') or 'Any'))
    line('Unit price cap: '+str(policy.get('max_unit_price') or 'Not set'))
    line('Expires: '+str(policy.get('expires_at') or 'Not set'))
    label('SELECTED EVIDENCE')
    selected=evidence.get('selected') or {}
    line(str(selected.get('title') or 'Unrecorded product'))
    line('Source: '+str(selected.get('merchant') or 'Unknown')+
         ' | Product ID: '+str(selected.get('product_id') or 'Unknown'))
    line('Unit: '+str(selected.get('unit_price') or '-')+
         ' | Total: '+str(report['comparison'].get('selected_total') or '-'))
    label('COST COMPARISON (NOT REALIZED SAVINGS)')
    comparison=report.get('comparison') or {}
    line('Least-cost eligible snapshot offer: '+str(comparison.get('least_cost_eligible_total') or 'Unknown'))
    line('Selected price premium: '+str(comparison.get('premium_vs_least_cost') or 'Unknown'))
    line('Offers checked: '+str(comparison.get('offers_evaluated_count') or 'Unknown')+
         ' | Policy blocked: '+str(comparison.get('policy_blocked_offer_count', 'Unknown')))
    line('Cheapest rejected same-currency snapshot: '+
         str(comparison.get('cheapest_rejected_total') or 'Not available'))
    blocked=comparison.get('cheapest_rejected_offer') or {}
    if blocked:
        line('Rejected listing: '+str(blocked.get('title') or 'Unknown'))
        for reason in (blocked.get('blocked_by') or [])[:4]:
            line('Policy refusal: '+str(reason)[:180])
    line(comparison.get('note') or '')
    label('EVIDENCE ASSESSMENT — MODEL OR RULE-BASED')
    ai=evidence.get('ai') or {}
    line('Model: '+str(ai.get('model') or 'Unavailable')+
         ' | Source: '+str(ai.get('source') or 'Not analyzed'))
    line(str(ai.get('explanation') or 'No AI conclusion recorded')[:1600])
    label('HUMAN APPROVAL')
    buyer=report.get('buyer_decision') or {}
    line('Approved at: '+str(buyer.get('approved_at') or 'Not approved'))
    line('Model: '+str(buyer.get('approval_model') or ''))
    for approval in (buyer.get('entries') or [])[:12]:
        line(str(approval.get('at'))+' | '+str(approval.get('decision'))+
             ' | '+str(approval.get('comment') or '')[:140])
    label('PAYPAL SANDBOX PROOF (NOT RETAILER SETTLEMENT)')
    payment=report.get('payment_proof') or {}
    line('Status: '+str(payment.get('status'))+
         ' | Amount: '+str(payment.get('amount'))+
         ' '+str(payment.get('currency') or ''))
    line('PayPal order ID: '+str(payment.get('paypal_order_id') or 'Not created'))
    line('Capture ID: '+str(payment.get('capture_id') or 'Not captured'))
    line('Signed webhook correlated: '+str(payment.get('signed_webhook_correlated')))
    label('AUDIT TIMELINE')
    for event in (report.get('audit_timeline') or [])[:100]:
        line(str(event.get('at'))+' | '+str(event.get('action')))
    label('EVIDENCE INTEGRITY')
    line('Snapshot SHA-256: '+str(report.get('snapshot_sha256','')))
    line(report.get('integrity_note',''))
    for note in evidence.get('limitations') or []:
        line('Limit: '+str(note))
    doc.save()
    return output.getvalue()
