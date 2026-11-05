"""Typed procurement request and constrained buyer mandate schemas."""
from datetime import datetime
from decimal import Decimal
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ProcurementPolicy(BaseModel):
    """Hard rules enforced by deterministic server code, not by Gemini."""
    mandatory_attributes: dict[str, str] = Field(default_factory=dict, max_length=8)
    preferred_attributes: dict[str, str] = Field(default_factory=dict, max_length=8)
    allowed_merchants: list[str] = Field(default_factory=list, max_length=12)
    max_unit_price: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    expires_at: datetime | None = None
    approver_email: EmailStr | None = None

    @field_validator('mandatory_attributes', 'preferred_attributes')
    @classmethod
    def valid_attributes(cls, values):
        clean = {}
        for key, value in values.items():
            if not re.fullmatch(r'[A-Za-z0-9_ -]{1,48}', key):
                raise ValueError('Attribute keys must be short plain-text names')
            if not isinstance(value, str) or not 1 <= len(value.strip()) <= 100:
                raise ValueError('Attribute values must be 1–100 characters')
            clean[key.strip()] = value.strip()
        return clean

    @field_validator('allowed_merchants')
    @classmethod
    def valid_domains(cls, values):
        clean = []
        for entry in values:
            if not isinstance(entry, str):
                raise ValueError('Merchant domains must be text')
            domain = entry.strip().lower().rstrip('.')
            if len(domain) > 253 or not re.fullmatch(
                r'[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+',
                domain,
            ):
                raise ValueError('Allowed merchants must be domain names, not URLs')
            if domain not in clean:
                clean.append(domain)
        return clean

    @field_validator('approver_email')
    @classmethod
    def valid_approver(cls,value):
        return str(value).strip().lower() if value else None

    @field_validator('expires_at')
    @classmethod
    def valid_expiry(cls, value):
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError('Mandate expiry must include a timezone offset')
        return value


class ProcurementRequestCreate(BaseModel):
    request_text: str = Field(min_length=12, max_length=5000)
    quantity: int = Field(default=1, ge=1, le=100000)
    budget: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)
    currency: str = Field(default='USD', pattern=r'^[A-Z]{3}$')
    policy_json: ProcurementPolicy = Field(default_factory=ProcurementPolicy)

    @field_validator('request_text')
    @classmethod
    def normalize_request(cls, value: str) -> str:
        normalized = ' '.join(value.split())
        if len(normalized) < 12:
            raise ValueError('Request must contain at least 12 non-space characters')
        return normalized


class ProcurementRequestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    request_text: str
    quantity: int
    budget: Decimal | None
    currency: str
    status: str
    analysis_json: dict | None
    policy_json: dict = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
