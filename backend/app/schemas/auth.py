from datetime import datetime
from pydantic import BaseModel,EmailStr,Field,ConfigDict,field_validator

class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2,max_length=120)
    password: str = Field(min_length=12,max_length=128)
    @field_validator('full_name')
    @classmethod
    def validate_name(cls,value: str) -> str:
        normalized=' '.join(value.split())
        if len(normalized)<2: raise ValueError('Full name must contain at least two characters')
        return normalized

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1,max_length=128)

class UserResponse(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id: str
    email: EmailStr
    full_name: str
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = 'bearer'
    expires_in: int
    user: UserResponse
