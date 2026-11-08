"""Registration and login with explicit, fail-closed database errors.

Never mislabel an unavailable database as an invalid password or a duplicate
account. A production database failure is a 503, not an unhandled 500.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.security.passwords import hash_password, verify_password
from app.security.tokens import create_access_token, get_current_user
from app.security.rate_limits import throttle_login, throttle_registration

router = APIRouter(prefix='/auth', tags=['authentication'])


def _database_unavailable(exc: SQLAlchemyError) -> HTTPException:
    # No exception text, SQL, connection URI, or database credentials in HTTP.
    return HTTPException(
        status_code=503,
        detail='Authentication database is temporarily unavailable. Please try again later.',
        headers={'Retry-After': '15'},
    )


def _find_user(db: Session, email: str) -> User | None:
    try:
        return db.scalar(select(User).where(User.email == email))
    except SQLAlchemyError as exc:
        raise _database_unavailable(exc) from exc


def _token_response(user: User | UserResponse) -> TokenResponse:
    settings = get_settings()
    response_user = user if isinstance(user, UserResponse) else UserResponse.model_validate(user)
    return TokenResponse(
        access_token=create_access_token(response_user.id),
        expires_in=settings.access_token_expire_minutes * 60,
        user=response_user,
    )


@router.post('/register', response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
    _throttle: None = Depends(throttle_registration),
):
    email = str(payload.email).strip().lower()
    if _find_user(db, email):
        raise HTTPException(status_code=409, detail='An account with this email already exists')
    user = User(
        email=email,
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
    )
    try:
        db.add(user)
        # Assign the UUID and client-side created_at default on INSERT.
        # Take a complete user snapshot before commit so auth doesn't need a
        # second SELECT after the write on a remote Neon connection.
        db.flush()
        response_user = UserResponse.model_validate(user)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        # An integrity violation could be a non-unique constraint. Only report
        # a duplicate when a subsequent lookup actually confirms one.
        if _find_user(db, email):
            raise HTTPException(
                status_code=409, detail='An account with this email already exists'
            ) from exc
        raise _database_unavailable(exc) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise _database_unavailable(exc) from exc
    return _token_response(response_user)


@router.post('/login', response_model=TokenResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    _throttle: None = Depends(throttle_login),
):
    email = str(payload.email).strip().lower()
    user = _find_user(db, email)
    if user is None or not user.is_active or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail='Invalid email or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    return _token_response(user)


@router.get('/me', response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user
