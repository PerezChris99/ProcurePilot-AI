"""Short-lived, audience-scoped JWT bearer tokens; no implicit session cookies."""
import uuid
from datetime import datetime,timedelta,timezone

from jose import JWTError,jwt
from fastapi import Depends,HTTPException,status
from fastapi.security import HTTPAuthorizationCredentials,HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User

bearer_scheme=HTTPBearer(auto_error=False)
TOKEN_ISSUER='procurepilot-ai'
TOKEN_AUDIENCE='procurepilot-api'


def create_access_token(user_id: str) -> str:
    settings=get_settings()
    now=datetime.now(timezone.utc)
    expires=now+timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({
        'sub':user_id,'iss':TOKEN_ISSUER,'aud':TOKEN_AUDIENCE,
        'iat':now,'nbf':now,'exp':expires,'jti':str(uuid.uuid4()),
    },settings.jwt_secret_key,algorithm='HS256')


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None=Depends(bearer_scheme),
    db: Session=Depends(get_db),
) -> User:
    credentials_error=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Invalid or expired authentication token',
        headers={'WWW-Authenticate':'Bearer'},
    )
    if credentials is None or len(credentials.credentials)>4096:
        raise credentials_error
    try:
        payload=jwt.decode(
            credentials.credentials,get_settings().jwt_secret_key,
            algorithms=['HS256'],audience=TOKEN_AUDIENCE,issuer=TOKEN_ISSUER,
            options={'require_exp':True,'require_iat':True,'require_nbf':True},
        )
        user_id=payload.get('sub')
        if not isinstance(user_id,str):
            raise credentials_error
        uuid.UUID(user_id)
    except (JWTError,ValueError,TypeError) as exc:
        raise credentials_error from exc
    user=db.get(User,user_id)
    if user is None or not user.is_active:
        raise credentials_error
    return user
