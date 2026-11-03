from datetime import datetime,timedelta,timezone
from jose import JWTError,jwt
from fastapi import Depends,HTTPException,status
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User

bearer_scheme=HTTPBearer(auto_error=False)

def create_access_token(user_id: str) -> str:
    settings=get_settings()
    expires=datetime.now(timezone.utc)+timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({'sub':user_id,'exp':expires},settings.jwt_secret_key,algorithm='HS256')

def get_current_user(credentials: HTTPAuthorizationCredentials | None=Depends(bearer_scheme),db: Session=Depends(get_db)) -> User:
    credentials_error=HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail='Invalid or expired authentication token',headers={'WWW-Authenticate':'Bearer'})
    if credentials is None: raise credentials_error
    try:
        payload=jwt.decode(credentials.credentials,get_settings().jwt_secret_key,algorithms=['HS256'])
        user_id=payload.get('sub')
        if not user_id: raise credentials_error
    except JWTError as exc:
        raise credentials_error from exc
    user=db.get(User,user_id)
    if user is None or not user.is_active: raise credentials_error
    return user
