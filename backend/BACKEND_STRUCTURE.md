# Backend Structure - Quick Reference

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app initialization
│   ├── config.py               # Settings and environment config
│   ├── database.py             # SQLAlchemy session and engine
│   ├── core/
│   │   ├── security.py         # JWT auth, password hashing
│   │   ├── exceptions.py       # Custom exception classes
│   │   ├── middleware.py       # Logging and validation middleware
│   │   ├── utils.py            # Utility functions
│   │   └── data_processor.py   # Data cleaning and validation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User model
│   │   ├── dataset.py          # Dataset model
│   │   ├── model_meta.py       # ML model metadata
│   │   ├── alert.py            # Alert rules model
│   │   ├── log.py              # Prediction logs model
│   │   ├── chat.py             # Chat history model
│   │   └── api_log.py          # API request logs model
│   ├── schemas/
│   │   ├── auth.py             # Auth schemas
│   │   ├── dataset.py          # Dataset schemas
│   │   ├── model.py            # Model schemas
│   │   ├── log.py              # Log schemas
│   │   └── chat.py             # Chat schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication service
│   │   ├── dataset.py          # Dataset service
│   │   ├── ml_pipeline.py      # ML pipeline service
│   │   ├── dl_pipeline.py      # DL pipeline service
│   │   ├── genai.py            # GenAI service
│   │   ├── monitoring.py       # Monitoring service
│   │   └── alerts.py           # Alerts service
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py             # Auth endpoints
│   │   ├── upload.py           # Data upload endpoints
│   │   ├── analytics.py        # Analytics endpoints
│   │   ├── ml.py               # ML endpoints
│   │   ├── dl.py               # DL endpoints
│   │   ├── genai.py            # GenAI endpoints
│   │   ├── dashboard.py        # Dashboard endpoints
│   │   └── alerts.py           # Alert endpoints
│   └── tasks/
│       ├── __init__.py
│       ├── celery_app.py       # Celery configuration
│       └── workers.py          # Background job tasks
├── alembic/                    # Database migrations
│   ├── versions/
│   │   └── 001_initial.py
│   ├── env.py
│   └── README
├── tests/
│   └── test_backend_step1.py  # Test cases
├── storage/                    # Uploaded files
├── .env                        # Environment variables
├── requirements.txt            # Python dependencies
├── .gitignore
├── celery_worker.py           # Celery worker entry point
└── STEP1_IMPLEMENTATION.md    # Step 1 documentation
```

## File Purposes

### Core Files
- **main.py**: FastAPI app setup, middleware, exception handlers, router includes
- **config.py**: Loads environment variables into Settings class
- **database.py**: SQLAlchemy engine, session, and dependency injection

### Security
- **core/security.py**: JWT token creation/validation, password hashing, user extraction
- **core/exceptions.py**: Custom exceptions and error handlers
- **core/middleware.py**: Request logging and validation

### Data Processing
- **core/data_processor.py**: DataValidator, DataCleaner, DataProcessor classes
- **core/utils.py**: File operations, filename generation, storage management

### Database Layer
- **models/*.py**: SQLAlchemy ORM models with relationships
- **services/*.py**: Business logic for each domain

### API Layer
- **schemas/*.py**: Pydantic models for request/response validation
- **routers/*.py**: FastAPI endpoints and route handlers

### Background Jobs
- **tasks/celery_app.py**: Celery broker and configuration
- **tasks/workers.py**: Background job functions
- **celery_worker.py**: Entry point for Celery worker process

## Key Components

### 1. Authentication Flow
```
User Input (email/password)
  ↓
AuthService.authenticate_user()
  ↓
Create JWT tokens (access + refresh)
  ↓
Return tokens to client
  ↓
Client includes access token in Authorization header
  ↓
security.get_current_user() validates token
  ↓
Extract user from database
  ↓
Pass user to protected routes
```

### 2. Data Upload Flow
```
Client uploads file
  ↓
Upload route validates file
  ↓
Save file to storage directory
  ↓
Create Dataset record (status='received')
  ↓
Queue Celery task
  ↓
Worker processes file via DataProcessor
  ↓
Extract metadata and statistics
  ↓
Update Dataset record (status='processed')
  ↓
Frontend polls or receives webhook notification
```

### 3. Error Handling Flow
```
Request → Middleware validation
  ↓
Route handler processes request
  ↓
If error: raise APIError or built-in exception
  ↓
Exception handler catches error
  ↓
Return standardized error response
  ↓
Log error for monitoring
```

## Important Constants

```python
# From config.py
ACCESS_TOKEN_EXPIRE_MINUTES = 60
ALGORITHM = "HS256"

# From routers/upload.py
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.xls']

# From core/data_processor.py
OUTLIER_THRESHOLD = 3.0  # Z-score

# From storage
UPLOAD_DIR = "./storage"
MODEL_DIR = "./storage/models"
```

## Dependencies

Key Python packages:
- **FastAPI**: Web framework
- **SQLAlchemy**: ORM
- **Pydantic**: Data validation
- **python-jose**: JWT tokens
- **passlib**: Password hashing
- **pandas**: Data processing
- **scikit-learn**: ML algorithms
- **tensorflow**: Deep learning
- **celery**: Task queue
- **redis**: Message broker
- **pymysql**: MySQL driver
- **openpyxl**: Excel file support

## Database Relationships

```
User (1) ──→ (Many) Dataset
User (1) ──→ (Many) ModelMeta
User (1) ──→ (Many) PredictionLog
User (1) ──→ (Many) ChatHistory

Dataset (1) ──→ (Many) ModelMeta
Dataset (1) ──→ (Many) PredictionLog
Dataset (1) ──→ (Many) ChatHistory

ModelMeta (1) ──→ (Many) PredictionLog
```

## Status Codes Reference

```
200 OK                       - Request successful
201 Created                  - Resource created
204 No Content               - Success, no content to return
400 Bad Request              - Invalid input
401 Unauthorized             - Authentication required
403 Forbidden                - Insufficient permissions
404 Not Found                - Resource not found
409 Conflict                 - Resource conflict (e.g., duplicate)
413 Payload Too Large        - File too large
422 Unprocessable Entity     - Validation error
500 Internal Server Error    - Server error
503 Service Unavailable      - Service down/unavailable
```

This structure ensures clean separation of concerns, scalability, and maintainability!
