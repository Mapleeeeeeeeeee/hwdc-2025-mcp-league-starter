import tomllib
from pathlib import Path

from fastapi import FastAPI

from api.exception_handlers import register_exception_handlers
from core.exceptions import NotFoundError, ServiceUnavailableError
from core.middleware import TraceMiddleware
from shared.response import create_success_response

from .config import settings


# Read version from pyproject.toml
def get_version() -> str:
    try:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
        return pyproject["project"]["version"]
    except Exception:
        return "unknown"


app = FastAPI(
    title="HWDC 2025 Backend",
    version=get_version(),
    description="FastAPI backend for HWDC 2025 MCP League Starter",
)

# Add trace middleware for request tracking and performance monitoring
app.add_middleware(TraceMiddleware)

# Register global exception handlers
register_exception_handlers(app)


@app.get("/")
def read_root():
    return create_success_response(
        data={
            "message": "Hello HWDC 2025!",
            "environment": settings.environment,
            "version": get_version(),
        },
        message="Welcome to HWDC 2025 MCP League Starter Backend",
    )


@app.get("/health")
def health_check():
    return create_success_response(
        data={
            "status": "healthy",
            "environment": settings.environment,
            "host": settings.host,
            "port": settings.port,
            "version": get_version(),
        },
        message="Service is healthy",
    )


# Test endpoints for error handling demonstration
@app.get("/test-error/404")
def test_not_found_error():
    """Test endpoint for demonstrating 404 error handling."""
    raise NotFoundError("This is a test 404 error")


@app.get("/test-error/503")
def test_service_unavailable_error():
    """Test endpoint for demonstrating retryable 503 error handling."""
    raise ServiceUnavailableError(
        "This is a test 503 error with retry capability",
        context={"service": "test", "expected_recovery": "30 seconds"},
    )
