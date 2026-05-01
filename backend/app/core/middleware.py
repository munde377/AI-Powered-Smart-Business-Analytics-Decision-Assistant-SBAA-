"""API logging and monitoring middleware."""
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class APILoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log API requests and responses."""

    async def dispatch(self, request: Request, call_next):
        """Log incoming request and outgoing response."""
        start_time = time.time()

        # Log request details
        method = request.method
        url = request.url.path
        client_ip = request.client.host if request.client else 'unknown'

        logger.info(f'Incoming {method} {url} from {client_ip}')

        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(f'Request {method} {url} raised exception: {str(exc)}')
            raise

        # Calculate response time
        process_time = time.time() - start_time
        response.headers['X-Process-Time'] = str(process_time)

        # Log response
        status_code = response.status_code
        log_level = logging.INFO if status_code < 400 else logging.WARNING
        logger.log(
            log_level,
            f'Response {method} {url} completed with status {status_code} in {process_time:.3f}s'
        )

        return response

class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation."""

    async def dispatch(self, request: Request, call_next):
        """Validate request before processing."""
        # Limit request body size
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_length = request.headers.get('content-length')
            if content_length and int(content_length) > 50 * 1024 * 1024:  # 50 MB
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=413,
                    content={'detail': 'Request body too large'}
                )

        response = await call_next(request)
        return response
