import tomllib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.exception_handlers import register_exception_handlers
from src.api.mcp_server import initialize_mcp_server
from src.api.v1.agno_router import router as agno_router
from src.api.v1.conversation_router import router as conversation_router
from src.api.v1.mcp_router import router as mcp_router
from src.config import settings
from src.core import MCPServerGuardMiddleware, TraceMiddleware, setup_logging
from src.integrations.mcp import (
    graceful_mcp_cleanup,
    initialize_mcp_system,
    mcp_settings,
)
from src.shared.response import create_success_response


# Read version from pyproject.toml
def get_version() -> str:
    with open("pyproject.toml", "rb") as f:
        pyproject = tomllib.load(f)
    return pyproject["project"]["version"]


setup_logging()

# Initialize MCP server for internal use (managing other MCP servers)
# This is always needed regardless of AS_A_MCP_SERVER setting
mcp_server = initialize_mcp_server()

# Create FastMCP server http_app only when AS_A_MCP_SERVER is enabled
# This allows external MCP clients to connect to this server
mcp_http_app = None
if settings.as_a_mcp_server:
    mcp_http_app = mcp_server.http_app(path="/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Start FastMCP lifespan for internal MCP server functionality
    # Use the same http_app instance that will be mounted
    mcp_app_for_lifespan = (
        mcp_http_app if mcp_http_app is not None else mcp_server.http_app(path="/")
    )
    async with mcp_app_for_lifespan.lifespan(app):
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

# Add MCP server guard middleware to handle disabled MCP server endpoint
app.add_middleware(
    MCPServerGuardMiddleware,
    as_a_mcp_server=settings.as_a_mcp_server,
    enable_mcp_system=mcp_settings.enable_mcp_system,
)

# Register global exception handlers
register_exception_handlers(app)

# Register routers
app.include_router(conversation_router, prefix="/api/v1")
app.include_router(mcp_router, prefix="/api/v1")
app.include_router(agno_router, prefix="/api/v1")

# Mount FastMCP server at /mcp endpoint for peer-to-peer MCP communication
# Authentication is configured in mcp_server initialization
# (see src/integrations/mcp/server.py)
# IMPORTANT: MCP_SERVER_AUTH_TOKEN is REQUIRED
# FastMCP will enforce bearer token authentication
# path="/" tells FastMCP to serve at the mount root, not at /mcp/mcp/
# Note: mcp_http_app is created at the top of this file before FastAPI app
# initialization
# When AS_A_MCP_SERVER=false, MCPServerGuardMiddleware will handle /mcp requests
# and return 503 with clear error message
if mcp_http_app is not None:
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
