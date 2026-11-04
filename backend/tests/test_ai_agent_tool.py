import asyncio
from decimal import Decimal

from app.agents.procurement_agent.agent import discover_and_rank_products
from app.integrations.channel3.client import Channel3Client
from app.integrations.channel3.schemas import Channel3Product, Channel3Offer, Channel3Price, Channel3SearchResponse


def test_optional_tool_agent_limits_catalogue_context_size(monkeypatch):
    async def search(self, query, *, limit=20, filters=None, user_id=None, page_token=None):
        return Channel3SearchResponse(products=[
            Channel3Product(
                id=f'item-{i}', title='Office monitor', description='Untrusted supplier narrative ' * 1000,
                offers=[Channel3Offer(url='https://seller.example/item', domain='seller.example',
                                      availability='InStock',price=Channel3Price(amount=Decimal('99'),currency='USD'))],
            )
            for i in range(20)
        ])
    monkeypatch.setattr(Channel3Client,'search_products',search)
    data=asyncio.run(discover_and_rank_products('office monitor'))
    assert data['status']=='success'
    assert len(data['results'])==5
    assert all('description' not in entry and 'offers' not in entry for entry in data['results'])
    assert all('best_unit_price' in entry for entry in data['results'])
    assert 'Untrusted supplier narrative' not in str(data)


def test_gemini_38_config_avoids_deprecated_temperature_and_caps_thinking():
    from app.agents.procurement_agent.agent import _generation_config
    config = _generation_config('gemini-3.8-flash')
    assert config.temperature is None
    assert config.max_output_tokens >= 256
    assert config.thinking_config is not None
    assert str(config.thinking_config.thinking_level).lower() == 'low'


def test_legacy_gemini_models_do_not_receive_unsupported_3x_thinking_level():
    from app.agents.procurement_agent.agent import _generation_config
    config = _generation_config('gemini-2.5-flash')
    assert config.temperature is None
    assert config.thinking_config is None
