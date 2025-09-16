# Backend Development Guide

FastAPI backend development guide, including project structure, environment setup, and development tools configuration.

## 🏗️ Project Structure

We adopt the `src` layout structure for better organization and packaging:

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── utils/
│   │   ├── __init__.py
│   │   └── time.py          # Timezone-aware time utilities
│   ├── models/              # Data models and schemas
│   ├── services/            # Business logic layer
│   ├── repositories/        # Data access layer
│   └── api/                 # API routes and controllers
├── tests/                   # Test files
├── docs/                    # Documentation
├── pyproject.toml
└── README.md
```

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
- **`api/`**: FastAPI route definitions and HTTP handling
- **`services/`**: Business logic implementation, no direct HTTP handling
- **`repositories/`**: Data access layer, abstracts database operations
- **`models/`**: Pydantic models and data structure definitions
- **`utils/`**: Common utility functions

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
