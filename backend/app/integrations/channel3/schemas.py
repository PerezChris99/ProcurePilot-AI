from decimal import Decimal
from pydantic import AliasChoices,BaseModel,ConfigDict,Field,HttpUrl,model_validator

class Channel3Brand(BaseModel):
    model_config=ConfigDict(extra='ignore')
    id: str | None = None
    name: str | None = None

class Channel3Image(BaseModel):
    model_config=ConfigDict(extra='ignore')
    url: HttpUrl
    cleaned_url: HttpUrl | None = None
    is_main_image: bool = False
    alt_text: str | None = None

class Channel3Price(BaseModel):
    model_config=ConfigDict(extra='ignore')
    amount: Decimal = Field(ge=0,validation_alias=AliasChoices('amount','price'))
    currency: str = Field(min_length=3,max_length=3,pattern=r'^[A-Z]{3}$')
    compare_at_price: Decimal | None = Field(default=None,ge=0)

class Channel3Offer(BaseModel):
    model_config=ConfigDict(extra='ignore')
    url: HttpUrl
    domain: str = ''
    price: Channel3Price
    availability: str = 'Unknown'
    condition: str | None = None
    max_commission_rate: Decimal | None = None

class Channel3Product(BaseModel):
    model_config=ConfigDict(extra='ignore')
    id: str
    title: str
    description: str | None = None
    brands: list[Channel3Brand] = Field(default_factory=list)
    images: list[Channel3Image] = Field(default_factory=list)
    key_features: list[str] | None = None
    structured_attributes: dict[str,str] = Field(default_factory=dict)
    offers: list[Channel3Offer] = Field(default_factory=list)

class Channel3SearchResponse(BaseModel):
    """Normalize documented paged catalogue responses without treating errors as empty results."""

    model_config=ConfigDict(extra='ignore')
    products: list[Channel3Product]
    next_page_token: str | None = None

    @model_validator(mode='before')
    @classmethod
    def normalize_page(cls, value):
        if not isinstance(value, dict):
            raise ValueError('Channel3 response must be an object')
        products = value.get('products')
        if products is None:
            products = value.get('data', value.get('items'))
        if not isinstance(products, list):
            raise ValueError('Channel3 response is missing a product list')
        pagination = value.get('pagination')
        if not isinstance(pagination, dict):
            pagination = {}
        token = (
            value.get('next_page_token') or value.get('nextPageToken')
            or value.get('next_cursor') or value.get('nextCursor')
            or pagination.get('next_cursor') or pagination.get('next_page_token')
        )
        return {**value, 'products': products, 'next_page_token': token}

