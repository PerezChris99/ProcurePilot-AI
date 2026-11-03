from decimal import Decimal
from app.integrations.channel3.schemas import Channel3Product,Channel3Offer
from app.procurement.schemas import ProcurementRequirements
from app.procurement.scoring import rank_products,score_product

def product(product_id,attrs,price='100',availability='InStock'):
    return Channel3Product(id=product_id,title='Business monitor',structured_attributes=attrs,offers=[Channel3Offer(url='https://shop.example/item',domain='shop.example',price=Decimal(price),currency='USD',availability=availability)])

def test_mandatory_attribute_mismatch_makes_product_ineligible():
    requirements=ProcurementRequirements(query='27 inch monitor',mandatory_attributes={'screen_size':'27 inch'})
    result=score_product(product('p1',{'screen_size':'24 inch'}),requirements)
    assert result.eligible is False
    assert result.unmet_requirements==['screen_size']

def test_ranker_prefers_verified_mandatory_match():
    requirements=ProcurementRequirements(query='27 inch monitor',mandatory_attributes={'screen_size':'27 inch'},budget=Decimal('500'))
    ranked=rank_products([product('wrong',{'screen_size':'24 inch'}),product('right',{'screen_size':'27 inch'},'90')],requirements)
    assert ranked[0].product_id=='right'
    assert ranked[0].eligible is True

def test_unknown_delivery_is_not_awarded_points():
    result=score_product(product('p1',{}),ProcurementRequirements(query='monitor'))
    assert 'Delivery suitability is unknown' in result.explanation[-1]
