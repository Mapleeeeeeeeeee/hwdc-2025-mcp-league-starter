#!/usr/bin/env python3
"""
Simple development server runner for HWDC 2025 Backend.
"""

import sys

import uvicorn
from src.config import settings


def main():
    """Start the development server."""
    host = settings.host
    port = settings.port

    # Check if production mode
    is_prod = len(sys.argv) > 1 and sys.argv[1] == "prod"

    uvicorn.run(
        "src.main:app", host=host, port=port, reload=not is_prod, env_file=".env"
    )


if __name__ == "__main__":
    main()
