"""Error handling and exception utilities for the backend."""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import traceback

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base class for API exceptions."""
    def __init__(self, status_code: int, detail: str, headers: dict | None = None):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers

class ValidationError(APIError):
    """Validation error."""
    def __init__(self, detail: str):
        super().__init__(status.HTTP_422_UNPROCESSABLE_ENTITY, detail)

class NotFoundError(APIError):
    """Resource not found error."""
    def __init__(self, resource: str = 'Resource'):
        super().__init__(status.HTTP_404_NOT_FOUND, f'{resource} not found')

class UnauthorizedError(APIError):
    """Unauthorized access error."""
    def __init__(self, detail: str = 'Unauthorized'):
        super().__init__(status.HTTP_401_UNAUTHORIZED, detail)

class ForbiddenError(APIError):
    """Forbidden access error."""
    def __init__(self, detail: str = 'Forbidden'):
        super().__init__(status.HTTP_403_FORBIDDEN, detail)

class ConflictError(APIError):
    """Resource conflict error."""
    def __init__(self, detail: str):
        super().__init__(status.HTTP_409_CONFLICT, detail)

class InternalServerError(APIError):
    """Internal server error."""
    def __init__(self, detail: str = 'Internal server error'):
        super().__init__(status.HTTP_500_INTERNAL_SERVER_ERROR, detail)

async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f'Unhandled exception: {str(exc)}', exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={'detail': 'An unexpected error occurred'},
    )

async def api_error_handler(request: Request, exc: APIError):
    """Handle APIError exceptions."""
    logger.warning(f'API Error: {exc.status_code} - {exc.detail}')
    return JSONResponse(
        status_code=exc.status_code,
        content={'detail': exc.detail},
        headers=exc.headers,
    )

async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with detailed feedback."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={'detail': exc.errors()},
    )

class ErrorResponseModel:
    """Standard error response model."""
    
    @staticmethod
    def error_response(status_code: int, detail: str, errors: list | None = None) -> dict:
        """Create standard error response."""
        response = {
            'status': 'error',
            'status_code': status_code,
            'detail': detail,
        }
        if errors:
            response['errors'] = errors
        return response

    @staticmethod
    def success_response(data: dict | list | None = None, message: str = 'Success') -> dict:
        """Create standard success response."""
        return {
            'status': 'success',
            'message': message,
            'data': data,
        }
