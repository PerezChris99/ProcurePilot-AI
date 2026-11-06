import json
import asyncio
import httpx
from pydantic import ValidationError
from app.core.config import get_settings
from app.integrations.channel3.schemas import Channel3SearchResponse,Channel3Product

DEFAULT_CHANNEL3_BASE_URL = 'https://api.trychannel3.com/v1'
MAX_CHANNEL3_SEARCH_LIMIT = 30

class Channel3ConfigurationError(RuntimeError):
    pass

class Channel3Unavailable(RuntimeError):
    pass

class Channel3Client:
    def __init__(self,api_key: str | None=None,base_url: str | None=None,transport=None):
        settings=get_settings()
        self.api_key=api_key if api_key is not None else settings.channel3_api_key
        configured=(base_url or settings.channel3_base_url or DEFAULT_CHANNEL3_BASE_URL).rstrip('/')
        # Support both the documented API root and the full search endpoint.
        # Some .env files set .../v1/search; appending 'search' a second time
        # otherwise produces .../v1/search/search, breaking real discovery.
        if configured.endswith('/v1/search'):
            configured=configured[:-len('/search')]
        self.base_url=configured.rstrip('/')+'/'
        self.transport=transport

    async def search_products(self,query: str,*,limit: int=20,filters: dict | None=None,user_id: str | None=None,page_token: str | None=None) -> Channel3SearchResponse:
        if not self.api_key: raise Channel3ConfigurationError('Channel3 API key is not configured')
        if not query.strip(): raise ValueError('Search query cannot be empty')
        if not 1<=limit<=MAX_CHANNEL3_SEARCH_LIMIT: raise ValueError('Search limit must be between 1 and 30')
        headers={'x-api-key':self.api_key,'Content-Type':'application/json','Accept':'application/json'}
        if user_id: headers['x-user-id']=user_id
        payload={'query':query.strip(),'limit':limit}
        if filters: payload['filters']=filters
        if page_token: payload['page_token']=page_token
        try:
            # Catalogue search is read-only even though Channel3 uses POST.
            # Retry once for transient transport/5xx only; never retry 401,
            # 403, 429, invalid JSON or unsafe payment/order mutations.
            for attempt in range(2):
                try:
                    async with httpx.AsyncClient(
                        base_url=self.base_url,
                        timeout=httpx.Timeout(12.0,connect=3.0),
                        transport=self.transport,
                    ) as client:
                        async with client.stream(
                            'POST','search',headers=headers,json=payload,
                        ) as response:
                            response.raise_for_status()
                            size=0
                            chunks=[]
                            async for chunk in response.aiter_bytes():
                                size+=len(chunk)
                                if size>2_097_152:
                                    raise Channel3Unavailable('Channel3 catalogue response exceeds the safe size limit')
                                chunks.append(chunk)
                            return Channel3SearchResponse.model_validate(json.loads(b''.join(chunks)))
                except (httpx.TransportError,httpx.HTTPStatusError) as exc:
                    transient = isinstance(exc,httpx.TransportError) or (
                        isinstance(exc,httpx.HTTPStatusError)
                        and exc.response.status_code in (502,503,504)
                    )
                    if attempt == 0 and transient:
                        await asyncio.sleep(0.25)
                        continue
                    raise
        except (httpx.HTTPError,ValidationError,ValueError) as exc:
            raise Channel3Unavailable('Channel3 product search failed or returned an invalid response') from exc


    async def get_product(self,product_id: str,*,user_id: str | None=None) -> Channel3Product:
        """Fetch a single canonical product for explicit, on-demand quote checking."""
        from urllib.parse import quote
        if not self.api_key:
            raise Channel3ConfigurationError('Channel3 API key is not configured')
        if not isinstance(product_id,str) or not 1<=len(product_id)<=255:
            raise ValueError('Invalid Channel3 product ID')
        headers={'x-api-key':self.api_key,'Accept':'application/json'}
        if user_id: headers['x-user-id']=user_id
        try:
            for attempt in range(2):
                try:
                    async with httpx.AsyncClient(
                        base_url=self.base_url,timeout=httpx.Timeout(12.0,connect=3.0),
                        transport=self.transport,
                    ) as transport:
                        async with transport.stream(
                            'GET','products/'+quote(product_id,safe=''),headers=headers,
                        ) as response:
                            response.raise_for_status()
                            size=0
                            chunks=[]
                            async for chunk in response.aiter_bytes():
                                size+=len(chunk)
                                if size>2_097_152:
                                    raise Channel3Unavailable('Channel3 product details exceed the safe size limit')
                                chunks.append(chunk)
                            raw=json.loads(b''.join(chunks))
                            if not isinstance(raw,dict):
                                raise ValueError('Invalid Channel3 product object')
                            return Channel3Product.model_validate(raw.get('product',raw))
                except (httpx.TransportError,httpx.HTTPStatusError) as exc:
                    transient = isinstance(exc,httpx.TransportError) or (
                        isinstance(exc,httpx.HTTPStatusError)
                        and exc.response.status_code in (502,503,504)
                    )
                    if attempt == 0 and transient:
                        await asyncio.sleep(0.25)
                        continue
                    raise
        except (httpx.HTTPError,ValidationError,ValueError) as exc:
            raise Channel3Unavailable('Channel3 product verification failed') from exc
