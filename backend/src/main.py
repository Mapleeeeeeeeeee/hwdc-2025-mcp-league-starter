import tomllib
from pathlib import Path

from fastapi import FastAPI

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


@app.get("/")
def read_root():
    return {
        "message": "Hello HWDC 2025!",
        "environment": settings.environment,
        "version": get_version(),
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment,
        "host": settings.host,
        "port": settings.port,
    }
