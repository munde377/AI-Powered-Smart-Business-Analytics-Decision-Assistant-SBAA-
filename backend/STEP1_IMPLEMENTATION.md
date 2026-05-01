# Backend Step 1: Complete Auth + DB + Models - Implementation Guide

## Overview
This document describes the complete Step 1 backend implementation including JWT authentication, database models, and data processing pipeline.

## Architecture

### 1. Authentication System

#### Features:
- **JWT Authentication** with access and refresh tokens
- **Password Hashing** using bcrypt
- **Role-Based Access Control** (admin/user)
- **Token Refresh** mechanism for long-lived sessions
- **Protected Routes** with automatic user extraction

#### Key Files:
- `app/core/security.py` - Token creation, validation, and user extraction
- `app/services/auth.py` - Business logic for auth operations
- `app/routers/auth.py` - API endpoints

#### Endpoints:
```
POST   /api/auth/register       - Register new user
POST   /api/auth/login          - Login and get tokens
POST   /api/auth/refresh        - Refresh access token
GET    /api/auth/me             - Get current user profile
PUT    /api/auth/me             - Update user profile
```

#### Usage Example:
```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"secure_pass","role":"user"}'

# Login
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=secure_pass"

# Refresh Token
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token":"YOUR_REFRESH_TOKEN"}'

# Get Current User
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### 2. Database Models

#### Users Table
- `id` (PK) - User ID
- `email` (UNIQUE) - Email address
- `hashed_password` - bcrypt hashed password
- `full_name` - User's full name
- `role` - 'admin' or 'user'
- `is_active` - Account status
- `created_at` - Registration timestamp
- `updated_at` - Last update timestamp
- **Indexes**: email, role

#### Datasets Table
- `id` (PK) - Dataset ID
- `user_id` (FK) - Owner's user ID
- `name` - Dataset display name
- `filename` - Stored filename
- `file_path` - Full file path
- `file_size` - File size in bytes
- `row_count` - Number of rows after processing
- `column_count` - Number of columns
- `columns_list` (JSON) - List of column names
- `dtypes` (JSON) - Data types per column
- `missing_values` (JSON) - Missing value counts
- `metadata` (JSON) - Additional metadata
- `summary_stats` (JSON) - Summary statistics
- `status` - 'received', 'processing', 'processed', 'failed'
- `notes` - Processing notes
- `created_at` - Upload timestamp
- `updated_at` - Last update timestamp
- **Indexes**: user_id, status, created_at

#### ModelMeta Table
- `id` (PK) - Model ID
- `user_id` (FK) - Model creator
- `dataset_id` (FK) - Training dataset
- `name` - Model display name
- `model_type` - 'regression', 'classification', 'lstm', etc.
- `algorithm` - Specific algorithm used
- `accuracy`, `precision`, `recall`, `f1_score`, `rmse` - Performance metrics
- `model_path` - Path to saved model file
- `params` (JSON) - Hyperparameters
- `feature_names` (JSON) - List of features used
- `target_column` - Target variable
- `training_samples`, `test_samples`, `training_time_seconds`
- `status` - Model status
- `created_at`, `updated_at`
- **Indexes**: user_id, dataset_id, model_type

#### PredictionLog Table
- `id` (PK) - Log entry ID
- `user_id`, `model_id`, `dataset_id` (FKs)
- `input_data` (JSON) - Input features
- `output_data` (JSON) - Prediction output
- `prediction_value` - Numeric prediction
- `confidence_score` - Prediction confidence
- `status` - 'success', 'failed'
- `error_message` - Error details if failed
- `created_at` - Prediction timestamp
- **Indexes**: user_id, model_id, dataset_id, created_at

#### AlertRule Table
- `id` (PK)
- `name` - Alert name
- `description` - Alert description
- `alert_type` - Type of alert
- `metric` - Metric to monitor
- `condition` - 'greater_than', 'less_than', etc.
- `threshold` - Trigger threshold
- `active` - Alert status
- `cooldown_minutes` - Minimum time between alerts
- `created_at`, `updated_at`
- **Indexes**: active, alert_type

#### ChatHistory Table
- `id` (PK)
- `user_id` (FK) - User asking
- `dataset_id` (FK) - Dataset context
- `user_query` - Natural language query
- `ai_response` - LLM response
- `generated_sql` - Generated SQL if applicable
- `metadata` (JSON) - Context and tokens used
- `created_at`
- **Indexes**: user_id, dataset_id, created_at

#### APILog Table
- `id` (PK)
- `method` - HTTP method
- `endpoint` - API endpoint
- `status_code` - Response status
- `user_id` - User making request
- `response_time_ms` - Response time
- `error_message` - Error if any
- `created_at`
- **Indexes**: user_id, endpoint, created_at

### 3. Data Processing Pipeline

#### Features:
- **File Format Validation** - CSV, XLSX, XLS support
- **Column Name Normalization** - Standardize naming conventions
- **Duplicate Removal** - Remove duplicate rows
- **Missing Value Handling** - Multiple strategies
- **Type Conversion** - Intelligent type detection
- **Outlier Detection** - Statistical outlier removal
- **Metadata Extraction** - Column stats, data types, missing values

#### Data Processor Flow:
```
1. Load File (CSV/Excel)
2. Normalize Column Names
3. Remove Duplicates
4. Handle Missing Values
5. Convert Data Types
6. Remove Outliers
7. Extract Statistics
8. Store Metadata
```

#### Configuration:
- `MAX_FILE_SIZE`: 50 MB (can be changed)
- `OUTLIER_THRESHOLD`: 3.0 (z-score)
- Supported strategies: drop, fill_numeric, forward_fill

### 4. Error Handling

#### Exception Types:
- `APIError` - Base exception
- `ValidationError` - 422 Unprocessable Entity
- `NotFoundError` - 404 Not Found
- `UnauthorizedError` - 401 Unauthorized
- `ForbiddenError` - 403 Forbidden
- `ConflictError` - 409 Conflict
- `InternalServerError` - 500 Internal Server Error

#### Middleware:
- `APILoggingMiddleware` - Log all requests/responses
- `RequestValidationMiddleware` - Validate request sizes

### 5. Data Upload & Processing

#### Endpoints:
```
POST   /api/data/upload           - Upload dataset file
GET    /api/data/                 - List user's datasets
GET    /api/data/{dataset_id}     - Get dataset details
GET    /api/data/{dataset_id}/preview - Get data preview
DELETE /api/data/{dataset_id}     - Delete dataset
```

#### Upload Flow:
```
1. User uploads CSV/Excel file
2. File is saved to storage directory
3. Dataset record created with status='received'
4. Background task queued via Celery
5. Background task processes file
6. Metadata and statistics extracted
7. Status updated to 'processed' or 'failed'
```

## Configuration

### Environment Variables (.env)
```
DATABASE_URL=mysql+pymysql://user:pass@host:3306/dbname
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REDIS_URL=redis://localhost:6379/0
GROQ_API_KEY=
GROQ_MODEL=llama3-8b-8192
OLLAMA_URL=http://localhost:11434
USE_LOCAL_LLM=false
```

## Running the Backend

### 1. Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Initialize Database
```bash
# Create all tables
python -c "from app.database import engine, Base; Base.metadata.create_all(engine)"
```

### 3. Start FastAPI Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Start Celery Worker (in separate terminal)
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

### 5. Access Docs
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

### Run Tests
```bash
pytest tests/ -v --cov=app
```

### Create Test Data
```python
from app.database import SessionLocal
from app.services.auth import AuthService
from app.schemas.auth import UserCreate

db = SessionLocal()
user = AuthService.create_user(db, UserCreate(email="test@example.com", password="test123"))
db.close()
```

## Performance Considerations

1. **Database Indexing**: All foreign keys and frequently queried columns are indexed
2. **Pagination**: List endpoints support skip/limit parameters
3. **Background Processing**: Heavy tasks (data cleaning) run via Celery
4. **Connection Pooling**: SQLAlchemy uses connection pooling
5. **Request Logging**: Optional request logging for performance monitoring

## Security Features

1. **JWT Authentication**: Secure token-based auth
2. **Password Hashing**: Bcrypt with salt
3. **CORS Protection**: Configured trusted origins
4. **Rate Limiting**: Can be added via FastAPI middleware
5. **Input Validation**: Pydantic models validate all inputs
6. **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
7. **HTTPS**: Enable in production

## Next Steps

After Step 1 is complete:
1. **Step 2**: ML Pipeline with model training
2. **Step 3**: Deep Learning with LSTM forecasting
3. **Step 4**: GenAI Chat system
4. **Step 5**: Frontend integration
5. **Step 6**: Docker deployment
6. **Step 7**: Testing suite

## Troubleshooting

### Common Issues

**1. Database Connection Error**
- Check DATABASE_URL in .env
- Ensure MySQL/SQLite server is running
- Verify database credentials

**2. Celery Tasks Not Processing**
- Ensure Redis is running
- Check Celery worker logs
- Verify Celery configuration

**3. File Upload Failing**
- Check storage directory permissions
- Verify file size under 50 MB
- Check supported file types

**4. JWT Token Issues**
- Ensure SECRET_KEY is set in .env
- Check token expiration time
- Verify ALGORITHM matches configuration

## API Response Format

### Success Response
```json
{
  "status": "success",
  "data": { },
  "message": "Operation completed"
}
```

### Error Response
```json
{
  "detail": "Error description",
  "status_code": 400
}
```

## Database Migration

### Using Alembic
```bash
# Create new migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

This completes Step 1: Full backend with authentication, database models, and data processing!
