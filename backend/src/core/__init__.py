from .exceptions import (
    BadGatewayError,
    # 4XX Client Errors
    BadRequestError,
    BaseAppException,
    ClientError,
    ConflictError,
    ForbiddenError,
    GatewayTimeoutError,
    # 5XX Server Errors
    InternalServerError,
    NotFoundError,
    ServerError,
    ServiceUnavailableError,
    TooManyRequestsError,
    UnauthorizedError,
    UnprocessableEntityError,
)
from .middleware import TraceMiddleware

__all__ = [
    # Base exceptions
    "BaseAppException",
    "ClientError",
    "ServerError",
    # 4XX errors
    "BadRequestError",
    "UnauthorizedError",
    "ForbiddenError",
    "NotFoundError",
    "ConflictError",
    "UnprocessableEntityError",
    "TooManyRequestsError",
    # 5XX errors
    "InternalServerError",
    "BadGatewayError",
    "ServiceUnavailableError",
    "GatewayTimeoutError",
    # Middleware
    "TraceMiddleware",
]
