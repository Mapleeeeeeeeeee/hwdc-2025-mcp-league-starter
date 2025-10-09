import tomllib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.exception_handlers import register_exception_handlers
from src.api.v1.conversation_router import router as conversation_router
from src.api.v1.mcp_router import router as mcp_router
from src.config import settings
from src.core import TraceMiddleware, setup_logging
from src.integrations.mcp import graceful_mcp_cleanup, initialize_mcp_system
from src.shared.response import create_success_response


# Read version from pyproject.toml
def get_version() -> str:
    with open("pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)
    return pyproject["project"]["version"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Initialize MCP system on startup
    await initialize_mcp_system()

    try:
        yield
    finally:
        await graceful_mcp_cleanup()


setup_logging()

app = FastAPI(
    title="HWDC 2025 Backend",
    version=get_version(),
    description="FastAPI backend for HWDC 2025 MCP League Starter",
    lifespan=lifespan,
)

# Enable CORS for configured client origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

# Add trace middleware for request tracking and performance monitoring
app.add_middleware(TraceMiddleware)

# Register global exception handlers
register_exception_handlers(app)

# Register routers
app.include_router(conversation_router, prefix="/api/v1")
app.include_router(mcp_router, prefix="/api/v1")


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
