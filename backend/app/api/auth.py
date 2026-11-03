from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token, get_current_user

router=APIRouter(prefix='/auth',tags=['authentication'])

def _token_response(user: User) -> TokenResponse:
    settings=get_settings()
    return TokenResponse(access_token=create_access_token(user.id),expires_in=settings.access_token_expire_minutes*60,user=UserResponse.model_validate(user))

@router.post('/register',response_model=TokenResponse,status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest,db: Session=Depends(get_db)):
    email=str(payload.email).strip().lower()
    existing=db.scalar(select(User).where(User.email==email))
    if existing: raise HTTPException(status_code=409,detail='An account with this email already exists')
    user=User(email=email,full_name=payload.full_name.strip(),hashed_password=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409,detail='An account with this email already exists') from exc
    return _token_response(user)

@router.post('/login',response_model=TokenResponse)
def login(payload: LoginRequest,db: Session=Depends(get_db)):
    email=str(payload.email).strip().lower()
    user=db.scalar(select(User).where(User.email==email))
    if user is None or not user.is_active or not verify_password(payload.password,user.hashed_password):
        raise HTTPException(status_code=401,detail='Invalid email or password',headers={'WWW-Authenticate':'Bearer'})
    return _token_response(user)

@router.get('/me',response_model=UserResponse)
def me(user: User=Depends(get_current_user)):
    return user
