import httpx
from pydantic import ValidationError
from app.core.config import get_settings
from app.integrations.channel3.schemas import Channel3SearchResponse

class Channel3ConfigurationError(RuntimeError):
    pass

class Channel3Unavailable(RuntimeError):
    pass

class Channel3Client:
    def __init__(self,api_key: str | None=None,base_url: str | None=None,transport=None):
        settings=get_settings()
        self.api_key=api_key or settings.channel3_api_key
        self.base_url=(base_url or settings.channel3_base_url or 'https://api.trychannel3.com/v1').rstrip('/')+'/'
        self.transport=transport

    async def search_products(self,query: str,*,limit: int=20,filters: dict | None=None,user_id: str | None=None,page_token: str | None=None) -> Channel3SearchResponse:
        if not self.api_key: raise Channel3ConfigurationError('Channel3 API key is not configured')
        if not query.strip(): raise ValueError('Search query cannot be empty')
        if not 1<=limit<=50: raise ValueError('Search limit must be between 1 and 50')
        headers={'x-api-key':self.api_key,'Content-Type':'application/json','Accept':'application/json'}
        if user_id: headers['x-user-id']=user_id
        payload={'query':query.strip(),'limit':limit}
        if filters: payload['filters']=filters
        if page_token: payload['page_token']=page_token
        try:
            async with httpx.AsyncClient(base_url=self.base_url,timeout=httpx.Timeout(12.0,connect=3.0),transport=self.transport) as client:
                response=await client.post('search',headers=headers,json=payload)
                response.raise_for_status()
                return Channel3SearchResponse.model_validate(response.json())
        except (httpx.HTTPError,ValidationError,ValueError) as exc:
            raise Channel3Unavailable('Channel3 product search failed or returned an invalid response') from exc
