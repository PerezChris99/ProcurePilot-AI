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
        return httpx.Response(200,json={'products':[{'id':'prod-1','title':'27 inch monitor','offers':[]}],'next_page_token':None})
    client=Channel3Client(api_key='test-key',base_url='https://api.trychannel3.com/v1',transport=httpx.MockTransport(handler))
    result=asyncio.run(client.search_products('  27 inch monitor  ',limit=5,user_id='user-123'))
    assert result.products[0].id=='prod-1'

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
