"""
OAuth 2.0 — Authorization Code Flow

How it works:
1. User clicks "Login with Google" in the frontend
2. Frontend calls GET /auth/google/login → redirected to Google consent screen
3. User approves → Google redirects to GET /auth/google/callback?code=...
4. We exchange the code for a Google access token
5. We fetch the user's profile from Google
6. We find or create the user in our DB
7. We return our own JWT tokens to the frontend

Facebook follows the same pattern.
"""

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.core.security import create_access_token, create_refresh_token
from backend.database import get_db
from backend.models.health_profile import HealthProfile
from backend.models.user import User, UserRole

settings = get_settings()
router = APIRouter(prefix="/auth", tags=["OAuth"])

# ── Google OAuth URLs ─────────────────────────────────
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
GOOGLE_SCOPES = "openid email profile"

# ── Facebook OAuth URLs ───────────────────────────────
FACEBOOK_AUTH_URL = "https://www.facebook.com/v19.0/dialog/oauth"
FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"
FACEBOOK_USERINFO_URL = "https://graph.facebook.com/me?fields=id,name,email,picture"


# ── Shared helpers ────────────────────────────────────


def _get_or_create_oauth_user(
    db: Session,
    email: str,
    full_name: str,
    provider: str,
) -> User:
    """
    Find an existing user by email or create a new one from OAuth data.
    OAuth users have no password (hashed_password set to provider identifier).
    """
    user = db.query(User).filter(User.email == email).first()

    if not user:
        user = User(
            email=email,
            full_name=full_name,
            hashed_password=f"oauth:{provider}",  # no real password
            role=UserRole.patient,
            is_active=True,
        )
        db.add(user)
        db.flush()

        # Auto-create empty health profile
        profile = HealthProfile(user_id=user.id)
        db.add(profile)
        db.commit()
        db.refresh(user)

    return user


def _build_redirect(user: User) -> RedirectResponse:
    """
    After OAuth, redirect to the frontend with tokens in query params.
    The frontend reads them and stores in memory / secure storage.

    In production: use httpOnly cookies instead of query params.
    """
    access = create_access_token({"sub": str(user.id)})
    refresh = create_refresh_token({"sub": str(user.id)})

    frontend_url = (
        f"{settings.frontend_url}/auth/callback"
        f"?access_token={access}"
        f"&refresh_token={refresh}"
        f"&provider=oauth"
    )
    return RedirectResponse(url=frontend_url)


# ── Google ────────────────────────────────────────────


@router.get(
    "/google/login",
    summary="Redirect user to Google consent screen",
    description="Initiate Google OAuth flow. Frontend should redirect the user to this URL.",
)
def google_login():
    if not settings.google_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.",
        )

    params = (
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={settings.google_redirect_uri}"
        f"&response_type=code"
        f"&scope={GOOGLE_SCOPES.replace(' ', '%20')}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return RedirectResponse(url=GOOGLE_AUTH_URL + params)


@router.get(
    "/google/callback",
    summary="Google OAuth callback — exchanges code for user profile",
)
async def google_callback(code: str, db: Session = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    async with httpx.AsyncClient() as client:
        # Step 1: Exchange code for access token
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=400, detail="Failed to exchange Google token"
            )

        token_data = token_response.json()
        google_access_token = token_data.get("access_token")

        # Step 2: Fetch user profile from Google
        profile_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {google_access_token}"},
        )

        if profile_response.status_code != 200:
            raise HTTPException(
                status_code=400, detail="Failed to fetch Google user profile"
            )

        profile = profile_response.json()

    email = profile.get("email")
    full_name = profile.get("name", email)

    if not email:
        raise HTTPException(
            status_code=400, detail="Google account has no email address"
        )

    # Step 3: Get or create user
    user = _get_or_create_oauth_user(db, email, full_name, provider="google")

    # Step 4: Redirect to frontend with tokens
    return _build_redirect(user)


# ── Facebook ──────────────────────────────────────────


@router.get(
    "/facebook/login",
    summary="Redirect user to Facebook consent screen",
    description="Initiate Facebook OAuth flow. Frontend should redirect the user to this URL.",
)
def facebook_login():
    if not settings.facebook_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Facebook OAuth is not configured. Set FACEBOOK_CLIENT_ID and FACEBOOK_CLIENT_SECRET.",
        )

    params = (
        f"?client_id={settings.facebook_client_id}"
        f"&redirect_uri={settings.facebook_redirect_uri}"
        f"&response_type=code"
        f"&scope=email,public_profile"
    )
    return RedirectResponse(url=FACEBOOK_AUTH_URL + params)


@router.get(
    "/facebook/callback",
    summary="Facebook OAuth callback — exchanges code for user profile",
)
async def facebook_callback(code: str, db: Session = Depends(get_db)):
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    async with httpx.AsyncClient() as client:
        # Step 1: Exchange code for access token
        token_response = await client.get(
            FACEBOOK_TOKEN_URL,
            params={
                "client_id": settings.facebook_client_id,
                "client_secret": settings.facebook_client_secret,
                "redirect_uri": settings.facebook_redirect_uri,
                "code": code,
            },
        )

        if token_response.status_code != 200:
            raise HTTPException(
                status_code=400, detail="Failed to exchange Facebook token"
            )

        fb_access_token = token_response.json().get("access_token")

        # Step 2: Fetch user profile from Facebook
        profile_response = await client.get(
            FACEBOOK_USERINFO_URL,
            params={"access_token": fb_access_token},
        )

        if profile_response.status_code != 200:
            raise HTTPException(
                status_code=400, detail="Failed to fetch Facebook user profile"
            )

        profile = profile_response.json()

    email = profile.get("email")
    full_name = profile.get("name", "Facebook User")

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Facebook account has no email. Enable email permission in your Facebook App settings.",
        )

    # Step 3: Get or create user
    user = _get_or_create_oauth_user(db, email, full_name, provider="facebook")

    # Step 4: Redirect to frontend with tokens
    return _build_redirect(user)


# ── OAuth status endpoint ─────────────────────────────


@router.get(
    "/providers",
    summary="List configured OAuth providers",
)
def list_providers():
    """Shows clients which OAuth providers are available"""
    return {
        "providers": [
            {
                "name": "google",
                "enabled": bool(settings.google_client_id),
                "login_url": "/auth/google/login",
            },
            {
                "name": "facebook",
                "enabled": bool(settings.facebook_client_id),
                "login_url": "/auth/facebook/login",
            },
        ]
    }
