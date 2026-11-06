from decimal import Decimal
from types import SimpleNamespace

from app.integrations.channel3.schemas import Channel3Offer, Channel3Price, Channel3Product
from app.procurement.policy import evaluate_offer
from app.procurement.schemas import ProcurementRequirements
from app.procurement.scoring import score_product
from app.procurement.specifications import requested_monitor_size, display_size_violations


def offer():
    return Channel3Offer(
        url='https://seller.example/monitor', domain='seller.example',
        availability='InStock', price=Channel3Price(amount='400', currency='USD'),
    )


def test_72_inch_monitor_request_rejects_24_inch_and_monitor_stand():
    req = ProcurementRequirements(query='i need 72 inch monitors', quantity=4,
                                  budget=Decimal('3000'), currency='USD')
    owner = SimpleNamespace(request_text=req.query, quantity=4, budget=req.budget,
                            currency='USD', policy_json={})
    for title in ('HP Series 7 Pro 24 in Monitor', 'Dual Monitor Stand',
                  'Computer Monitor', 'VP348QG'):
        product = Channel3Product(id='bad', title=title, offers=[offer()])
        result = score_product(product, req)
        assert not result.eligible
        assert 'display_size' in result.unmet_requirements
        assert evaluate_offer(owner, product, offer())


def test_explicit_72_inch_size_qualifies_only_with_matching_screen_evidence():
    req = ProcurementRequirements(query='i need 72 inch monitors', quantity=4,
                                  budget=Decimal('3000'), currency='USD')
    product = Channel3Product(
        id='good', title='Commercial monitor',
        structured_attributes={'screen_size':['72 inches']},
        offers=[offer()],
    )
    owner = SimpleNamespace(request_text=req.query, quantity=4, budget=req.budget,
                            currency='USD', policy_json={})
    assert requested_monitor_size(req.query) == Decimal('72')
    assert score_product(product, req).eligible
    assert evaluate_offer(owner, product, offer()) == []
    assert display_size_violations(req.query, product) == []


def test_not_every_free_text_number_becomes_a_screen_constraint():
    assert requested_monitor_size('buy 72 desk chairs') is None
    assert requested_monitor_size('buy 4 office monitors') is None
    assert requested_monitor_size('two 27-inch monitors') == Decimal('27')
    assert requested_monitor_size('need a 72\" display') == Decimal('72')
