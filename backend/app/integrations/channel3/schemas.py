from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, HttpUrl

class Channel3Brand(BaseModel):
    model_config=ConfigDict(extra='ignore')
    id: str | None = None
    name: str | None = None

class Channel3Image(BaseModel):
    model_config=ConfigDict(extra='ignore')
    url: HttpUrl | None = None
    cleaned_url: HttpUrl | None = None
    is_main_image: bool = False
    alt_text: str | None = None

class Channel3Offer(BaseModel):
    model_config=ConfigDict(extra='ignore')
    url: HttpUrl
    domain: str
    price: Decimal = Field(ge=0)
    currency: str = Field(min_length=3,max_length=3)
    availability: str
    condition: str | None = None
    max_commission_rate: Decimal | None = None

class Channel3Product(BaseModel):
    model_config=ConfigDict(extra='ignore')
    id: str
    title: str
    description: str | None = None
    brands: list[Channel3Brand] = Field(default_factory=list)
    images: list[Channel3Image] = Field(default_factory=list)
    key_features: list[str] = Field(default_factory=list)
    structured_attributes: dict[str,str] = Field(default_factory=dict)
    offers: list[Channel3Offer] = Field(default_factory=list)

class Channel3SearchResponse(BaseModel):
    model_config=ConfigDict(extra='ignore')
    products: list[Channel3Product] = Field(default_factory=list)
    next_page_token: str | None = None
