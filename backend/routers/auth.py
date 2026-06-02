from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.models.health_profile import HealthProfile
from backend.models.user import User
from backend.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
)

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Cookie is secure=True in production (HTTPS only), False in dev (HTTP allowed)
COOKIE_SECURE = settings.is_production
COOKIE_NAME = "nutriguide_refresh"
COOKIE_MAX_AGE = settings.jwt_refresh_expire_days * 24 * 60 * 60  # seconds


def _set_refresh_cookie(response: Response, refresh_token: str):
    """
    Store refresh token in httpOnly cookie.
    - httpOnly=True  → JavaScript cannot read it (blocks XSS theft)
    - secure=True    → browser only sends over HTTPS (production only)
    - samesite=lax   → sent on same-site requests + top-level navigations
    """
    response.set_cookie(
        key=COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/auth",  # cookie only sent to /auth/* routes
    )


def _clear_refresh_cookie(response: Response):
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/auth",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
    )


def _make_access_token_response(user: User, response: Response) -> dict:
    """
    - Access token: in JSON response body (frontend stores in memory)
    - Refresh token: in httpOnly cookie (frontend never sees it)
    """
    refresh_token = create_refresh_token({"sub": str(user.id)})
    _set_refresh_cookie(response, refresh_token)

    return {
        "access_token": create_access_token({"sub": str(user.id)}),
        "token_type": "bearer",
        "expires_in": settings.jwt_expire_minutes * 60,
        "user": UserResponse.model_validate(user),
    }


# ── Endpoints ─────────────────────────────────────────


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new account",
    description=(
        "Returns an access token in the response body. "
        "A refresh token is set as an httpOnly cookie automatically."
    ),
)
def register(
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()

    profile = HealthProfile(user_id=user.id)
    db.add(profile)
    db.commit()
    db.refresh(user)

    return _make_access_token_response(user, response)


@router.post(
    "/login",
    summary="Login",
    description=(
        "Returns an access token in the response body. "
        "A refresh token is set as an httpOnly cookie — "
        "never exposed to JavaScript."
    ),
)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive",
        )

    return _make_access_token_response(user, response)


@router.post(
    "/refresh",
    summary="Get a new access token using the refresh cookie",
    description=(
        "Reads the refresh token from the httpOnly cookie set at login. "
        "No body needed — the browser sends the cookie automatically. "
        "Returns a new access token in the response body and rotates the refresh cookie."
    ),
)
def refresh(
    response: Response,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = Cookie(default=None, alias=COOKIE_NAME),
):
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token cookie found — please log in again",
        )

    token_data = decode_refresh_token(refresh_token)
    if not token_data:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or expired — please log in again",
        )

    user = db.query(User).filter(User.id == int(token_data["sub"])).first()
    if not user or not user.is_active:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Rotate: issue a brand new refresh token (invalidates old one implicitly)
    return _make_access_token_response(user, response)


@router.post(
    "/logout",
    summary="Logout — clears the refresh token cookie",
)
def logout(response: Response):
    _clear_refresh_cookie(response)
    return {"message": "Logged out successfully"}


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
