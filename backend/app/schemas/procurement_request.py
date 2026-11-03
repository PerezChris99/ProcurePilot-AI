from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel,ConfigDict,Field,field_validator

class ProcurementRequestCreate(BaseModel):
    request_text: str = Field(min_length=12,max_length=5000)
    quantity: int = Field(default=1,ge=1,le=100000)
    budget: Decimal | None = Field(default=None,gt=0,max_digits=14,decimal_places=2)
    currency: str = Field(default='USD',pattern=r'^[A-Z]{3}$')
    @field_validator('request_text')
    @classmethod
    def normalize_request(cls,value: str) -> str:
        normalized=' '.join(value.split())
        if len(normalized)<12: raise ValueError('Request must contain at least 12 non-space characters')
        return normalized

class ProcurementRequestResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: str
    request_text: str
    quantity: int
    budget: Decimal | None
    currency: str
    status: str
    analysis_json: dict | None
    created_at: datetime
    updated_at: datetime
