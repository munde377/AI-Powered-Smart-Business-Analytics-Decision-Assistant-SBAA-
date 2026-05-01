from sqlalchemy.orm import Session
from ..models.user import User
from ..core.security import get_password_hash, verify_password, create_access_token, decode_token
from ..schemas.auth import UserCreate

class AuthService:
    """Authentication service for user registration and login."""

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> User | None:
        """Get user by email address."""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> User | None:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def create_user(db: Session, user_in: UserCreate) -> User:
        """Create new user with hashed password."""
        hashed_password = get_password_hash(user_in.password)
        user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            role=user_in.role,
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, email: str, password: str) -> User | None:
        """Authenticate user with email and password."""
        user = AuthService.get_user_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    @staticmethod
    def create_token_pair(user: User) -> dict[str, str]:
        """Create access and refresh token pair."""
        access_token = create_access_token(subject=str(user.id), token_type='access')
        refresh_token = create_access_token(subject=str(user.id), token_type='refresh')
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer'
        }

    @staticmethod
    def refresh_token(refresh_token: str) -> dict[str, str]:
        """Create new access token from refresh token."""
        token_data = decode_token(refresh_token)
        if token_data['type'] != 'refresh':
            raise ValueError('Invalid token type for refresh')
        
        new_access_token = create_access_token(subject=token_data['subject'], token_type='access')
        return {
            'access_token': new_access_token,
            'token_type': 'bearer'
        }

    @staticmethod
    def update_user(db: Session, user: User, **kwargs) -> User:
        """Update user fields."""
        for key, value in kwargs.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user
