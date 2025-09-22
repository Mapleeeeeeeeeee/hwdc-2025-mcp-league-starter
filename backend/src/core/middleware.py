import time
import uuid
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


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
