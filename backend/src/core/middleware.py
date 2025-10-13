import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.shared.exceptions.mcp import MCPServerNotAvailableError


class TraceMiddleware(BaseHTTPMiddleware):
    """
    Trace middleware for request tracking and performance monitoring.

    Generates a unique trace ID for each request and adds it to both
    request state and response headers. Also tracks request processing time.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique trace ID for this request
        trace_id = str(uuid.uuid4())
        request.state.trace_id = trace_id

        # Record start time for performance monitoring
        start_time = time.perf_counter()

        # Process the request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.perf_counter() - start_time

        # Add trace ID and processing time to response headers
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Process-Time"] = f"{process_time:.6f}"

        return response


class MCPServerGuardMiddleware(BaseHTTPMiddleware):
    """
    Middleware to guard MCP server endpoints when AS_A_MCP_SERVER is disabled.

    This middleware intercepts requests to /mcp/* endpoints and raises
    MCPServerNotAvailableError when the server is not configured to act as
    an MCP server. The exception is caught and converted to a proper JSON
    response following the application's error handling architecture.
    """

    def __init__(self, app, as_a_mcp_server: bool, enable_mcp_system: bool):
        super().__init__(app)
        self.as_a_mcp_server = as_a_mcp_server
        self.enable_mcp_system = enable_mcp_system

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check if this is a request to the MCP endpoint
        if request.url.path.startswith("/mcp"):
            # If MCP server is disabled, raise exception for proper error handling
            if not self.as_a_mcp_server:
                # Create the exception
                exc = MCPServerNotAvailableError(
                    as_a_mcp_server=self.as_a_mcp_server,
                    enable_mcp_system=self.enable_mcp_system,
                )

                # Get trace_id from request state
                trace_id = getattr(request.state, "trace_id", None)

                # Build response following the error handling architecture
                response_content = {
                    "success": False,
                    "error": {
                        "type": exc.__class__.__name__,
                        "message": exc.get_i18n_message(),
                        "trace_id": trace_id,
                        "context": exc.context if exc.context else None,
                    },
                    "retry_info": {
                        "retryable": exc.retryable,
                        "retry_after": exc.retry_after,
                        "max_retries": exc.max_retries,
                        "current_attempt": 1,
                    },
                }

                return JSONResponse(
                    status_code=exc.status_code,
                    content=response_content,
                    headers=exc.headers or {},
                )

        # Continue with normal request processing
        return await call_next(request)
