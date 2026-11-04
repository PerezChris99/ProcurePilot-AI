"""Distributed auth attempt throttling. Redis is mandatory for public environments.

No client-supplied X-Forwarded-For parsing: the trusted ASGI proxy must provide a
validated request.client address, and the edge must limit aggregate traffic.
"""
import hashlib
import hmac
from functools import lru_cache

from fastapi import HTTPException, Request
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings

# Atomic increment + first-hit expiry, with a bounded fixed window.
_SCRIPT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('EXPIRE', KEYS[1], ARGV[2]) end
local ttl = redis.call('TTL', KEYS[1])
return {count, ttl}
"""


@lru_cache(maxsize=4)
def _redis(url: str) -> Redis:
    return Redis.from_url(
        url, max_connections=24, socket_connect_timeout=1.0,
        socket_timeout=1.0, health_check_interval=30,
        decode_responses=True,
    )


def _anonymous_key(secret: str, namespace: str, value: str) -> str:
    digest=hmac.new(secret.encode('utf-8'),
                    (namespace+':'+value).encode('utf-8'),
                    hashlib.sha256).hexdigest()
    return 'procurepilot:auth:'+namespace+':'+digest


async def _identity(request: Request) -> str:
    # FastAPI/Starlette reuses request.json() in the subsequent Pydantic parser.
    try:
        body=await request.json()
    except (ValueError,UnicodeDecodeError):
        return ''
    if not isinstance(body, dict):
        return ''
    value=body.get('email')
    return value.strip().casefold()[:320] if isinstance(value,str) else ''


async def _guard(request: Request, action: str):
    settings=get_settings()
    if settings.app_env not in ('staging','production'):
        # Local development must work offline; do not mistake this for a
        # distributed production limiter.
        return
    if not settings.rate_limit_redis_url:
        raise HTTPException(status_code=503, detail='Authentication protection service is not configured')
    source=(request.client.host if request.client else 'unknown') or 'unknown'
    identifier=await _identity(request)
    buckets=[
        (_anonymous_key(settings.jwt_secret_key,action+':ip',source),120),
    ]
    if identifier:
        buckets.append((_anonymous_key(settings.jwt_secret_key,action+':identity',identifier),8))
    try:
        redis=_redis(settings.rate_limit_redis_url)
        for key,limit in buckets:
            count,ttl=await redis.eval(_SCRIPT,1,key,limit,60)
            if int(count)>limit:
                raise HTTPException(status_code=429,detail='Too many authentication attempts. Try again shortly.',
                                    headers={'Retry-After':str(max(1,int(ttl)))})
    except HTTPException:
        raise
    except (RedisError,TimeoutError,OSError) as exc:
        # Login/registration cannot continue unthrottled if Redis is lost.
        raise HTTPException(status_code=503,detail='Authentication protection service is unavailable') from exc


async def throttle_login(request: Request):
    await _guard(request,'login')


async def throttle_registration(request: Request):
    await _guard(request,'register')
