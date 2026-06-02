from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator

from backend.models.user import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    @field_validator("full_name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Full name cannot be empty")
        return v.strip()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """
    Only the access token is in the response body.
    The refresh token is in an httpOnly cookie — never in JSON.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds until access token expires
    user: UserResponse
