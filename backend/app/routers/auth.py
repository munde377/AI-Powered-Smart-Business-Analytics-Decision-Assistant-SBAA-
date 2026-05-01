from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.auth import AuthService
from ..schemas.auth import UserCreate, Token, UserRead, RefreshTokenRequest
from ..core.security import get_current_active_user
from ..models.user import User

router = APIRouter()

@router.post('/register', response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register new user."""
    existing = AuthService.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Email already registered'
        )
    user = AuthService.create_user(db, user_in)
    return user

@router.post('/login', response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login user and return access + refresh tokens."""
    user = AuthService.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid email or password',
            headers={'WWW-Authenticate': 'Bearer'}
        )
    return AuthService.create_token_pair(user)

@router.post('/refresh', response_model=Token)
def refresh_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token."""
    try:
        tokens = AuthService.refresh_token(request.refresh_token)
        return Token(
            access_token=tokens['access_token'],
            refresh_token=request.refresh_token,
            token_type=tokens['token_type']
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.get('/me', response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user profile."""
    return current_user

@router.put('/me', response_model=UserRead)
def update_current_user(
    full_name: str | None = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    user = AuthService.update_user(db, current_user, full_name=full_name)
    return user
