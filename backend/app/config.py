from pydantic import BaseSettings, Field, validator
from typing import Optional

class Settings(BaseSettings):
    # Core
    environment: str = Field('development', env='ENVIRONMENT')
    debug: bool = Field(False, env='DEBUG')
    
    # Database
    database_url: str = Field('sqlite:///./local.db', env='DATABASE_URL')
    db_pool_size: int = Field(10, env='DB_POOL_SIZE')
    db_max_overflow: int = Field(20, env='DB_MAX_OVERFLOW')
    db_pool_recycle: int = Field(3600, env='DB_POOL_RECYCLE')
    db_echo: bool = Field(False, env='DB_ECHO')
    
    # Security
    secret_key: str = Field('change-me-super-secret-key-minimum-32-chars', env='SECRET_KEY')
    jwt_secret: str = Field('change-me-jwt-secret-key-minimum-32-chars', env='JWT_SECRET')
    algorithm: str = Field('HS256', env='ALGORITHM')
    access_token_expire_minutes: int = Field(60, env='ACCESS_TOKEN_EXPIRE_MINUTES')
    
    # Redis/Celery
    redis_url: str = Field('redis://localhost:6379/0', env='REDIS_URL')
    
    # Groq / LLM
    groq_api_key: str = Field(..., env='GROQ_API_KEY')
    groq_model: str = Field('llama3-8b-8192', env='GROQ_MODEL')
    use_local_llm: bool = Field(False, env='USE_LOCAL_LLM')
    ollama_url: str = Field('http://localhost:11434', env='OLLAMA_URL')
    
    # Frontend
    frontend_url: str = Field('http://localhost:3000', env='FRONTEND_URL')
    
    # Storage
    storage_path: str = Field('./storage', env='STORAGE_PATH')
    max_upload_size_mb: int = Field(50, env='MAX_UPLOAD_SIZE_MB')
    
    # Logging
    log_level: str = Field('INFO', env='LOG_LEVEL')
    
    # Optional error tracking
    sentry_dsn: Optional[str] = Field(None, env='SENTRY_DSN')

    @validator('database_url')
    def validate_database_url(cls, v):
        if not v:
            raise ValueError('DATABASE_URL must be set')
        return v

    @validator('secret_key')
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError('SECRET_KEY must be at least 32 characters long')
        return v

    @validator('jwt_secret')
    def validate_jwt_secret(cls, v):
        if len(v) < 32:
            raise ValueError('JWT_SECRET must be at least 32 characters long')
        return v

    @validator('groq_api_key')
    def validate_groq_api_key(cls, v):
        if not v:
            raise ValueError('GROQ_API_KEY must be set')
        return v

    @property
    def broker_url(self) -> str:
        """Get Celery broker URL from REDIS_URL."""
        return self.redis_url

    @property
    def result_backend(self) -> str:
        """Get Celery result backend from REDIS_URL."""
        return self.redis_url

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() in ('production', 'prod')

    class Config:
        env_file = '.env'
        case_sensitive = False
        
settings = Settings()
