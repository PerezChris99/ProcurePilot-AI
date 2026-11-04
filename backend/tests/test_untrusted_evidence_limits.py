"""Untrusted catalogue/webhook evidence cannot bypass money and size bounds."""
import asyncio
from decimal import Decimal

import httpx
import pytest
from pydantic import ValidationError

from app.integrations.channel3.client import Channel3Client, Channel3Unavailable
from app.integrations.channel3.schemas import Channel3Price


@pytest.mark.parametrize('amount',['NaN','Infinity','-Infinity','1E+1000'])
def test_catalogue_prices_reject_non_finite_or_unbounded_values(amount):
    with pytest.raises(ValidationError):
        Channel3Price(amount=Decimal(amount), currency='USD')


def test_channel3_rejects_oversized_upstream_json_before_deserializing():
    huge_description='x'*2_100_000
    transport=httpx.MockTransport(lambda _:httpx.Response(
        200,json={'products':[{'id':'product','title':'Long listing','description':huge_description}]}
    ))
    async def call():
        client=Channel3Client(api_key='configured-for-test',transport=transport)
        return await client.search_products('Office equipment')
    with pytest.raises(Channel3Unavailable,match='safe size limit'):
        asyncio.run(call())


@pytest.mark.parametrize('bad_id',[123,{'nested':'invalid'},'x'*129,'bad\nidentifier'])
def test_webhook_rejects_invalid_identifiers_before_outbound_provider_verification(client,bad_id):
    result=client.post('/api/v1/webhooks/paypal',json={
        'id':bad_id,'event_type':'PAYMENT.CAPTURE.COMPLETED',
    })
    assert result.status_code==400


def test_webhook_rejects_too_long_event_type(client):
    result=client.post('/api/v1/webhooks/paypal',json={
        'id':'id-short','event_type':'e'*129,
    })
    assert result.status_code==400
