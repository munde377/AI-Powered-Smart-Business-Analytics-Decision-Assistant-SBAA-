from datetime import datetime
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str
    role: str = 'user'

class UserRead(BaseModel):
    """Schema for user profile response."""
    id: int
    email: EmailStr
    full_name: str | None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    """Schema for access token response."""
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'

class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str

class TokenPayload(BaseModel):
    """Schema for decoded token payload."""
    sub: str | None = None
    type: str | None = None
