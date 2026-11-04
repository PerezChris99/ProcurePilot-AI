from decimal import Decimal
from app.integrations.channel3.schemas import Channel3Product,Channel3Offer,Channel3Price
from app.procurement.schemas import ProcurementRequirements
from app.procurement.scoring import rank_products,score_product

def product(product_id,attrs,price='100',availability='InStock'):
    return Channel3Product(id=product_id,title='Business monitor',structured_attributes=attrs,offers=[Channel3Offer(url='https://shop.example/item',domain='shop.example',price=Channel3Price(amount=Decimal(price),currency='USD'),availability=availability)])

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

def test_budget_ranking_accounts_for_requested_quantity():
    requirements=ProcurementRequirements(query='monitor',quantity=2,budget=Decimal('100'))
    ranked=rank_products([product('expensive',{},'60'),product('affordable',{},'40')],requirements)
    assert ranked[0].product_id=='affordable'

def test_availability_normalizes_documented_values():
    result=score_product(product('p1',{},availability='In Stock'),ProcurementRequirements(query='monitor'))
    assert result.available is True


def test_channel3_attribute_arrays_match_expected_value_without_parser_error():
    item=product('p1',{'colors':['Navy','Sky Blue'],'screen_size':['27 inch','24 inch']})
    requirements=ProcurementRequirements(query='office monitor',mandatory_attributes={'colors':'sky blue'},preferred_attributes={'screen_size':'27 inch'})
    score=score_product(item,requirements)
    assert score.eligible is True
    assert score.matched_attributes==['colors']
    assert score.score is not None


def test_ranker_does_not_reward_out_of_stock_discount_as_buyable_price():
    item=Channel3Product(id='p1',title='Office monitor',offers=[
      Channel3Offer(url='https://shop.example/oos',domain='shop.example',price=Channel3Price(amount=Decimal('10'),currency='USD'),availability='OutOfStock'),
      Channel3Offer(url='https://shop.example/available',domain='shop.example',price=Channel3Price(amount=Decimal('100'),currency='USD'),availability='InStock')
    ])
    result=score_product(item,ProcurementRequirements(query='office monitor',budget=Decimal('150')))
    assert result.best_unit_price==Decimal('100')
    assert result.available is True
    only_oos=product('p2',{},price='10',availability='OutOfStock')
    score=score_product(only_oos,ProcurementRequirements(query='office monitor',budget=Decimal('150')))
    assert score.best_unit_price is None
    assert score.available is False
