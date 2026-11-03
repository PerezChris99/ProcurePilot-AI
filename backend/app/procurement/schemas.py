from decimal import Decimal
from pydantic import BaseModel,Field,field_validator

class ProcurementRequirements(BaseModel):
    query: str = Field(min_length=3,max_length=5000)
    quantity: int = Field(default=1,ge=1,le=100000)
    budget: Decimal | None = Field(default=None,gt=0)
    currency: str = Field(default='USD',pattern=r'^[A-Z]{3}$')
    mandatory_attributes: dict[str,str] = Field(default_factory=dict)
    preferred_attributes: dict[str,str] = Field(default_factory=dict)

    @field_validator('query')
    @classmethod
    def normalize_query(cls,value: str) -> str:
        normalized=' '.join(value.split())
        if len(normalized)<3: raise ValueError('Search query must contain at least three non-space characters')
        return normalized

class ProductScore(BaseModel):
    product_id: str
    title: str
    eligible: bool
    score: Decimal | None
    matched_attributes: list[str] = Field(default_factory=list)
    unmet_requirements: list[str] = Field(default_factory=list)
    best_unit_price: Decimal | None = None
    currency: str | None = None
    available: bool | None = None
    explanation: list[str] = Field(default_factory=list)
