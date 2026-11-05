import asyncio
import httpx
import pytest
from app.integrations.channel3.client import Channel3Client,Channel3ConfigurationError,Channel3Unavailable

def test_search_sends_documented_headers_and_parses_products():
    def handler(request):
        assert request.url.path=='/v1/search'
        assert request.headers['x-api-key']=='test-key'
        assert request.headers['x-user-id']=='user-123'
        assert request.read()==b'{"query":"27 inch monitor","limit":5}'
        return httpx.Response(200,json={'products':[{'id':'prod-1','title':'27 inch monitor','key_features':None,'offers':[{'url':'https://retailer.example/p/1','domain':'retailer.example','price':{'amount':125.50,'currency':'USD'},'availability':'InStock'}]}],'next_page_token':None})
    client=Channel3Client(api_key='test-key',base_url='https://api.trychannel3.com/v1',transport=httpx.MockTransport(handler))
    result=asyncio.run(client.search_products('  27 inch monitor  ',limit=5,user_id='user-123'))
    assert result.products[0].id=='prod-1'
    assert result.products[0].offers[0].price.amount==125.50

def test_search_sends_pagination_token():
    def handler(request):
        assert request.read()==b'{"query":"monitor","limit":20,"page_token":"next-token"}'
        return httpx.Response(200,json={'products':[],'next_page_token':None})
    client=Channel3Client(api_key='test-key',transport=httpx.MockTransport(handler))
    asyncio.run(client.search_products('monitor',page_token='next-token'))

def test_search_requires_api_key():
    client=Channel3Client(api_key='',base_url='https://api.trychannel3.com/v1')
    with pytest.raises(Channel3ConfigurationError): asyncio.run(client.search_products('monitor'))

def test_search_rejects_invalid_response():
    transport=httpx.MockTransport(lambda request:httpx.Response(200,json={'products':[{'title':'missing id'}]}))
    client=Channel3Client(api_key='test-key',transport=transport)
    with pytest.raises(Channel3Unavailable): asyncio.run(client.search_products('monitor'))


@pytest.mark.parametrize('envelope', [
    {'data': [{'id': 'real-1', 'title': 'Monitor'}], 'next_cursor': 'cursor-2'},
    {'items': [{'id': 'real-1', 'title': 'Monitor'}], 'pagination': {'next_cursor': 'cursor-2'}},
    {'products': [{'id': 'real-1', 'title': 'Monitor'}], 'nextPageToken': 'cursor-2'},
])
def test_search_accepts_current_and_legacy_paginated_product_envelopes(envelope):
    transport=httpx.MockTransport(lambda request:httpx.Response(200,json=envelope))
    client=Channel3Client(api_key='test-key',transport=transport)
    result=asyncio.run(client.search_products('monitor'))
    assert [product.id for product in result.products]==['real-1']
    assert result.next_page_token=='cursor-2'


@pytest.mark.parametrize('payload', [
    {'error':'invalid subscription'},
    {'data':{'products':[]}},
    [],
])
def test_search_rejects_unknown_page_shape_instead_of_silently_reporting_no_products(payload):
    transport=httpx.MockTransport(lambda request:httpx.Response(200,json=payload))
    client=Channel3Client(api_key='test-key',transport=transport)
    with pytest.raises(Channel3Unavailable):
        asyncio.run(client.search_products('monitor'))


def test_offer_without_stock_confirmation_does_not_claim_availability():
    from app.integrations.channel3.schemas import Channel3Offer
    offer=Channel3Offer.model_validate({
        'url':'https://retailer.example/item',
        'price':{'amount':'125.00','currency':'USD'},
    })
    assert offer.availability=='Unknown'


def test_search_parses_documented_array_valued_structured_attributes():
    transport=httpx.MockTransport(lambda request:httpx.Response(200,json={
      'data':[{'id':'desk-1','title':'Office chair', 'structured_attributes':{'color':['Navy','Blue'],'material':['Fabric']},'offers':[]}]
    }))
    client=Channel3Client(api_key='test-key',transport=transport)
    result=asyncio.run(client.search_products('desk chair'))
    assert result.products[0].structured_attributes['color']==['Navy','Blue']


def test_documented_search_limit_maximum_is_30_and_rejects_excess_before_network():
    def handler(request):
        raise AssertionError('Search with invalid limit must not make an HTTP call')
    client=Channel3Client(api_key='test-key',transport=httpx.MockTransport(handler))
    with pytest.raises(ValueError,match='between 1 and 30'):
        asyncio.run(client.search_products('monitor',limit=31))


def test_search_normalizes_real_channel3_price_wire_field_and_page_token():
    def handler(request):
        assert request.url.path=='/v1/search'
        assert request.headers['x-api-key']=='test-key'
        return httpx.Response(200,json={
          'products':[{
            'id':'c3-monitor-1',
            'title':'Monitor, 27-inch',
            'structured_attributes':{'color':['Black']},
            'offers':[{
              'url':'https://store.example/monitor',
              'domain':'store.example',
              'price':{'price':219.99,'currency':'USD'},
              'availability':'InStock',
            }],
          }],
          'next_page_token':'c3-next-page',
        })
    client=Channel3Client(api_key='test-key',transport=httpx.MockTransport(handler))
    result=asyncio.run(client.search_products('27 inch monitor',limit=3))
    assert result.products[0].offers[0].price.amount==219.99
    assert result.products[0].offers[0].price.currency=='USD'
    assert result.products[0].offers[0].availability=='InStock'
    assert result.next_page_token=='c3-next-page'
