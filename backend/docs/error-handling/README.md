# Error Handling System

## Overview

The HWDC 2025 MCP League Starter implements a comprehensive error handling system based on HTTP status codes and FastAPI best practices. The system provides:

- **Standardized error responses** with consistent JSON format
- **Request tracing** with unique trace IDs for debugging
- **Hierarchical exception classes** based on HTTP status codes
- **Retry capabilities** for recoverable errors with configurable strategies
- **Internationalization support** for error messages
- **Performance monitoring** with request processing times

## Quick Start

### Basic Usage

```python
from core.exceptions import NotFoundError, ConflictError, ServiceUnavailableError

# Raise specific errors in your services
def get_user(user_id: int):
    user = database.get_user(user_id)
    if not user:
        raise NotFoundError(
            f"User {user_id} not found",
            context={"user_id": user_id}
        )
    return user

def create_user(email: str):
    if database.user_exists(email):
        raise ConflictError(
            f"User with email {email} already exists",
            context={"email": email}
        )
    return database.create_user(email)

def connect_to_service():
    try:
        return external_service.connect()
    except ConnectionError:
        # This error is retryable by default
        raise ServiceUnavailableError(
            "External service temporarily unavailable",
            context={"service": "external_api"}
        )
```

### Error Response Format

All errors return a consistent JSON structure:

```json
{
  "success": false,
  "data": null,
  "message": "Request failed",
  "trace_id": "abc-123-def-456",
  "error": {
    "type": "NotFoundError",
    "message": "User 123 not found",
    "trace_id": "abc-123-def-456",
    "context": {
      "user_id": 123,
      "suggestion": "Check if the user ID is correct"
    }
  },
  "retry_info": {
    "retryable": false,
    "retry_after": null,
    "max_retries": 0,
    "current_attempt": 1
  }
}
```

## System Components

### 1. Trace Middleware

Located in `src/core/middleware.py`, this middleware:
- Generates unique trace IDs for each request
- Tracks request processing time
- Adds trace information to response headers

**Response Headers:**
- `X-Trace-ID`: Unique request identifier
- `X-Process-Time`: Request processing time in seconds

### 2. Exception Classes

Located in `src/core/exceptions.py`, providing:
- `BaseAppException`: Foundation for all custom errors
- `ClientError`: Base for 4XX errors
- `ServerError`: Base for 5XX errors
- Specific error classes for common HTTP status codes

### 3. Request Tracing

Every request gets a unique trace ID that can be used for:
- **Debugging**: Track specific requests across logs
- **Monitoring**: Correlate errors with performance metrics
- **Support**: Users can provide trace ID for issue investigation

## Architecture Design

### Exception Hierarchy

```
BaseAppException (inherits from HTTPException)
├── ClientError (4XX)
│   ├── BadRequestError (400)
│   ├── UnauthorizedError (401)
│   ├── ForbiddenError (403)
│   ├── NotFoundError (404)
│   ├── ConflictError (409)
│   ├── UnprocessableEntityError (422)
│   └── TooManyRequestsError (429)
└── ServerError (5XX)
    ├── InternalServerError (500)
    ├── BadGatewayError (502)
    ├── ServiceUnavailableError (503)
    └── GatewayTimeoutError (504)
```

### Design Principles

1. **HTTP Semantics First**: Error classes map directly to HTTP status codes
2. **Modular Management**: Each service can define its own specific exceptions
3. **Consistent Responses**: All errors follow the same JSON structure
4. **Context Preservation**: Errors can carry additional context information
5. **Security Conscious**: Sensitive information is not exposed in error messages

## Documentation

- **[Development Guide](development.md)**: 開發標準和最佳實踐指南
- **[Best Practices](best-practices.md)**: How to create and use custom exceptions
- **[API Reference](api-reference.md)**: Complete list of available exception classes

## Examples

### Service-Specific Exceptions

```python
# services/mcp/exceptions.py
from core.exceptions import ServiceUnavailableError, UnauthorizedError

class MCPConnectionError(ServiceUnavailableError):
    def __init__(self, service_name: str, **kwargs):
        super().__init__(
            detail=f"Failed to connect to MCP service: {service_name}",
            i18n_key="errors.mcp.connection_failed",
            context={"service": service_name},
            **kwargs
        )

class MCPAuthenticationError(UnauthorizedError):
    def __init__(self, **kwargs):
        super().__init__(
            detail="MCP authentication failed",
            i18n_key="errors.mcp.auth_failed",
            **kwargs
        )
```

### Usage in Endpoints

```python
from fastapi import APIRouter
from services.mcp.exceptions import MCPConnectionError

router = APIRouter()

@router.get("/mcp/status")
async def get_mcp_status():
    try:
        status = await mcp_service.get_status()
        return {"status": status}
    except ConnectionError:
        raise MCPConnectionError("filesystem")
```

## Benefits

- **Developer Experience**: Clear error types and consistent responses
- **Debugging**: Trace IDs make it easy to track issues across logs
- **Monitoring**: Built-in performance tracking
- **Maintenance**: Modular design makes it easy to add new error types
- **Production Ready**: Secure error handling that doesn't leak sensitive information
