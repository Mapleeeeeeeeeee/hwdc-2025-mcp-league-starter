# Backend Development Guide

FastAPI backend development guide, including project structure, environment setup, and development tools configuration.

## 🏗️ Project Structure

We adopt the `src` layout structure, organized by architectural layers according to Clean Architecture principles.

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py             # FastAPI application instance and startup logic
│   │
│   ├── api/                # API Layer (HTTP entry points)
│   ├── core/               # Core configurations (logging, middleware)
│   ├── domain/             # Core business models and logic
│   ├── usecases/           # Application-specific business flows
│   ├── models/             # API Models (DTOs / Schemas)
│   ├── integrations/       # External services (DB, LLM clients)
│   └── shared/             # Code shared across layers (exceptions, responses)
│
├── tests/                  # Test files
├── docs/                   # Project documentation
├── pyproject.toml
└── README.md
```

For a detailed explanation of each directory's role, please see the [Backend Folder Structure documentation](docs/FOLDER_STRUCTURE.md).

### Benefits of `src` layout
- Clear separation between source code and other project files
- Better import organization and package discovery
- Easier testing and deployment configuration

## 🚀 Quick Start

### Requirements
- Python 3.12+
- uv (Python package management tool)

### Installation & Running
```bash
# From project root directory
cd backend

# Install dependencies
uv sync

# Start development server
uv run dev
```

### IDE Setup (VS Code)
For proper Python intellisense and import resolution:

1. **Select Python Interpreter**:
   - Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
   - Type "Python: Select Interpreter"
   - Choose "Enter interpreter path..."
   - Enter: `./backend/.venv/bin/python` (from project root) or `./.venv/bin/python` (from backend directory)

### Development Commands
```bash
# Code formatting
uv run ruff format

# Code linting
uv run ruff check

# Auto-fix fixable issues
uv run ruff check --fix

# Run tests
uv run pytest

# Type checking
uv run mypy src/
```

### Logging
- Application startup automatically calls `setup_logging()` from `src.core` to configure formatters, handlers, and levels based on `settings`.
- Use `from src.core import get_logger, get_audit_logger` in modules instead of `print()` so logs honour the central configuration.
- Provide context via the `extra` kwarg (e.g. `extra={"user_id": user.id}`) and use `get_audit_logger()` for authentication, permission, or data-access events that require audit trails.
- See [Coding Standards](docs/CODING_STANDARDS.md#8-logging) for detailed guidance and examples.

## 🔧 Development Tools Configuration

### Ruff
We use Ruff for code formatting and linting, configured in `pyproject.toml`:

```toml
[tool.ruff]
# Basic configuration
line-length = 88
target-version = "py312"

# Lint rules
lint.select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "C4",   # flake8-comprehensions
    "UP",   # pyupgrade
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### Pre-commit Hooks
Project has configured pre-commit hooks that run automatically on commit:
- Ruff formatting and linting
- MyPy type checking
- End-of-file newline checks

### MyPy
Type checking configuration in `pyproject.toml`:

```toml
[tool.mypy]
python_version = "3.12"
ignore_missing_imports = true
files = ["src/"]
```

## 📋 Development Standards

### Coding Standards
For detailed coding standards, see: [CODING_STANDARDS.md](docs/CODING_STANDARDS.md)

Key highlights:
- Use type hints for type annotation
- Follow PEP 585 for built-in generic types
- Semantic naming (variables, functions, classes)
- Timezone-aware datetime handling

### Directory Responsibilities
- **`api/`**: Defines API endpoints, handles HTTP requests/responses, and calls use cases.
- **`usecases/`**: Orchestrates application-specific business logic flows.
- **`domain/`**: Contains core, independent business logic and models (Entities).
- **`integrations/`**: Manages communication with all external services (e.g., database, third-party APIs).
- **`models/`**: Defines Pydantic models (DTOs) for API data contracts.
- **`core/`**: Holds shared configurations like logging, middleware, etc.

For a complete guide to the architecture, see the [architecture documentation](docs/architecture/).

### Dependency Management
- Use `uv add <package>` to add production dependencies
- Use `uv add --dev <package>` to add development dependencies
- Use `uv remove <package>` to remove dependencies
- Use `uv sync` to install all dependencies from lock file
- Lock file: `uv.lock` (auto-generated, should be committed)

**Examples:**
```bash
# Add production dependency
uv add fastapi

# Add development dependency
uv add --dev pytest

# Remove dependency
uv remove requests

# Install all dependencies
uv sync
```

## 🧪 Testing

### Test Structure
```
tests/
├── unit/           # Unit tests
├── integration/    # Integration tests
├── conftest.py     # Pytest configuration
└── fixtures/       # Test data
```

### Running Tests
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_example.py

# Generate coverage report
uv run pytest --cov=src --cov-report=html
```

## 📚 Related Resources

- [Project Overview](../README.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [Coding Standards](docs/CODING_STANDARDS.md)
- [FastAPI Official Documentation](https://fastapi.tiangolo.com/)
- [uv Usage Guide](https://docs.astral.sh/uv/)
