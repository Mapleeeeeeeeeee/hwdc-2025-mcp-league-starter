import tomllib

from fastapi import FastAPI

from src.api.exception_handlers import register_exception_handlers
from src.config import settings
from src.core.middleware import TraceMiddleware
from src.shared.response import create_success_response


# Read version from pyproject.toml
def get_version() -> str:
    with open("pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)
    return pyproject["project"]["version"]


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
