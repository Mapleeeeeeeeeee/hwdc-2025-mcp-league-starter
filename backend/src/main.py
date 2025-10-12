import tomllib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.exception_handlers import register_exception_handlers
from src.api.v1.conversation_router import router as conversation_router
from src.api.v1.mcp_router import router as mcp_router
from src.config import settings
from src.core import TraceMiddleware, setup_logging
from src.integrations.mcp import (
    graceful_mcp_cleanup,
    initialize_mcp_system,
    mcp_server,
)
from src.shared.response import create_success_response


# Read version from pyproject.toml
def get_version() -> str:
    with open("pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)
    return pyproject["project"]["version"]


setup_logging()

# Create FastMCP server http_app first (before FastAPI app)
# This allows us to access its lifespan
mcp_http_app = mcp_server.http_app(path="/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Start FastMCP lifespan
    async with mcp_http_app.lifespan(app):
        # Initialize MCP system on startup
        await initialize_mcp_system()

        try:
            yield
        finally:
            await graceful_mcp_cleanup()


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

# Mount FastMCP server at /mcp endpoint for peer-to-peer MCP communication
# Authentication is configured in mcp_server initialization
# (see src/integrations/mcp/server.py)
# IMPORTANT: MCP_SERVER_AUTH_TOKEN is REQUIRED
# FastMCP will enforce bearer token authentication
# path="/" tells FastMCP to serve at the mount root, not at /mcp/mcp/
# Note: mcp_http_app is created at the top of this file before FastAPI app
# initialization
app.mount("/mcp", mcp_http_app)


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
