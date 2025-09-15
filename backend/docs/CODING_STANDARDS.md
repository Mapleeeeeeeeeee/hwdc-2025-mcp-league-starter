# Backend Coding Standards

This document outlines the coding standards and best practices for the backend development of this project. Adhering to these guidelines ensures code consistency, readability, and maintainability.

## 0. Project Structure

We follow the `src` layout structure for better organization and packaging:

```
backend/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── utils/
│   │   ├── __init__.py
│   │   └── datetime_utils.py # Timezone-aware datetime utilities
│   ├── models/              # Data models and schemas
│   ├── services/            # Business logic layer
│   ├── repositories/        # Data access layer
│   └── api/                 # API routes and controllers
├── tests/                   # Test files
├── docs/                    # Documentation
├── pyproject.toml
└── README.md
```

**Benefits of `src` layout:**
- Clear separation between source code and other project files
- Better import organization and package discovery
- Easier testing and deployment configuration

## 1. General Principles

- **KISS (Keep It Simple, Stupid)**: Prefer simple, straightforward solutions over complex ones.
- **DRY (Don't Repeat Yourself)**: Avoid duplicating code. Use functions, classes, and modules to promote reusability.
- **YAGNI (You Aren't Gonna Need It)**: Don't add functionality until it's actually needed. Avoid over-engineering and premature optimization.
- **Readability Counts**: Write code that is easy for other developers to understand.

### 1.1. The Three Rules of Simple Design

Follow Kent Beck's three rules for simple design (in order of priority):

1. **Tests Pass**: The code must work correctly and all tests must pass.
2. **Expresses Intent**: The code clearly communicates what it does. Use meaningful names, clear structure, and appropriate abstractions.
3. **No Duplication (DRY)**: Eliminate redundant code and knowledge. Extract common functionality into reusable components.
4. **Minimal Elements**: Use the fewest number of classes, methods, and other elements necessary. Remove unnecessary complexity.

*Note: Some variations include "Fewest Elements" as the fourth rule, emphasizing minimalism.*

### 1.2. SOLID Principles (Core Focus)

We focus on the following three SOLID principles for better software architecture:

- **Single Responsibility Principle (S)**: A class should have only one reason to change. Each class or module should focus on a single responsibility or functionality.
- **Open/Closed Principle (O)**: Software entities should be open for extension but closed for modification. Use inheritance, composition, and dependency injection to extend functionality without modifying existing code.
- **Dependency Inversion Principle (D)**: High-level modules should not depend on low-level modules. Both should depend on abstractions. Use interfaces and dependency injection to achieve loose coupling.

## 2. Naming Conventions

Clear and consistent naming is crucial for readable code.

### 2.1. General Naming

- **Variables, Functions, and Modules**: Use `snake_case` (e.g., `user_profile`, `calculate_total_price`).
- **Classes**: Use `PascalCase` (e.g., `UserProfile`, `DatabaseConnection`).
- **Constants**: Use `UPPER_SNAKE_CASE` (e.g., `MAX_CONNECTIONS`, `API_TIMEOUT`).
- **Private members**: Prefix with a single underscore (e.g., `_internal_state`).

### 2.1.1. Semantic Naming

- **Be Descriptive**: Choose names that clearly express intent and purpose. Prefer longer, descriptive names over short, ambiguous ones.
- **Avoid Ambiguity**: Make clear distinctions between similar concepts:
  - **DO**: `get_agent_by_id()` vs `list_agents_by_criteria()`
  - **DON'T**: `get_agent()` vs `get_agents()` (unclear what the difference is)
- **Context Matters**: Include sufficient context to make the purpose clear:
  - **DO**: `calculate_monthly_revenue()`, `validate_user_email()`
  - **DON'T**: `calc()`, `validate()` (too generic)
- **Consistency**: Use the same terminology throughout the codebase for the same concepts.

### 2.2. Function Naming Prefixes

Use prefixes to indicate the function's primary action and return type.

- **`get_`**: Use for functions that retrieve a **single object** by a unique identifier. This function should return the object directly or `None` if not found.
  - **Use case**: Service/DAO layer where the caller has the ability to decide how to handle "not found" scenarios.
  - Example: `get_user_by_id(user_id: int) -> User | None`

- **`require_`** (or **`fetch_`**): Use for functions that retrieve a **single object** and are expected to find it. If the object is not found, this function **must raise an exception** (e.g., `NotFoundError`).
  - **Use case**: Controller/handler layer where the object "must exist" (often directly corresponds to HTTP 404).
  - Example: `require_user_by_id(user_id: int) -> User`

- **`list_`**: Use for functions that retrieve a **collection of objects**. This function **must always return a list** (or an iterable), even if no objects are found (return an empty list). It often includes parameters for filtering, sorting, and pagination.
  - Example: `list_users(is_active: bool = True, page: int = 1) -> list[User]`

- **`create_`**: For creating and saving a new object.
  - Example: `create_user(data: UserCreate) -> User`

- **`update_`**: For modifying an existing object.
  - Example: `update_user(user_id: int, data: UserUpdate) -> User`

- **`delete_`**: For removing an object.
  - Example: `delete_user(user_id: int) -> None`

- **`is_` / `has_`**: For functions that return a boolean value. **Must always return `bool`**, never `None` or three-state values.
  - Example: `is_user_active(user: User) -> bool`

- **`count_`** (optional): For counting objects, returns `int`.
  - Example: `count_active_users() -> int`

- **`exists_`** (optional): For existence checks, returns `bool`. Use this for dedicated existence checking to avoid semantic confusion with `has_*`.
  - Example: `exists_user_by_email(email: str) -> bool`

#### Why `require_` instead of `find_`?

The semantics of `find_` are inconsistent across different frameworks and ORMs (sometimes returns `None`, sometimes returns multiple records). Using `require_` is more intuitive—when you read it, you immediately know the object "must exist".

## 3. Type Hinting

- **Mandatory Typing**: All new code **must** include type hints for function arguments and return values.
- **Modern Syntax (Python 3.10+)**: Always use the modern, built-in generic types as standardized in PEP 585 and PEP 604.
  - **DO**: `list[str]`, `dict[int, str]`, `int | None`
  - **DON'T**: `typing.List[str]`, `typing.Dict[int, str]`, `typing.Union[int, None]`, `typing.Optional[int]`
- **PEP 695 Generics (Python 3.12+)**: For generic classes and functions, prefer the new syntax when supported by type checkers and third-party libraries:
  - **DO**: `class Container[T]: ...` and `def process[T](item: T) -> T: ...`
  - **Fallback**: Use traditional `TypeVar` if the new syntax is not yet supported by tools or libraries.
- **Docstring Guidelines**: Avoid repeating type information in docstrings that is already captured by type hints. Focus docstrings on semantics, behavior, and contracts rather than types.
- Our pre-commit hooks with Ruff will automatically enforce and correct these typings.

## 4. Code Formatting & Linting

- **Tool**: We use `Ruff` for both code formatting and linting to ensure a single, consistent style.
- **Enforcement**: This is automatically enforced by pre-commit hooks. Before committing, `ruff format` and `ruff check --fix` will run, standardizing the code.
- **Configuration**: All rules are defined in `backend/pyproject.toml` under the `[tool.ruff]` section.

## 5. Docstrings and Comments

- **Docstrings**: Use them for **public modules, classes, and complex functions**. For simple utility functions with clear names and type hints, docstrings may be omitted if the function's purpose is self-evident.
  - **Required**: Public APIs, business logic, complex algorithms, or functions with non-obvious behavior.
  - **Optional**: Simple utility functions where the name, parameters, and return type clearly express the intent.
- **Google Style**: When writing docstrings, follow the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html#3.8-comments-and-docstrings).
- **Comments**: Use inline comments (`#`) to explain complex logic, workarounds, or "why" something is done a certain way, not "what" it does.

## 6. Imports

- **Ordering**: Imports should be grouped in the following order:
  1. Standard library imports (e.g., `os`, `sys`).
  2. Third-party library imports (e.g., `fastapi`, `pydantic`).
  3. Local application imports.
- **Local Imports**: Use relative imports within the `src` package to avoid hardcoding the package name:
  - **DO**: `from utils.datetime_utils import utc_now`
  - **DO**: `from .utils.datetime_utils import utc_now` (when in same package)
  - **DON'T**: `from src.utils.datetime_utils import utc_now`
- **Forbidden Practices**:
  - **No wildcard imports**: Never use `from module import *`. Always import specific names or use qualified imports.
  - **No confusing aliases**: Avoid aliases that conflict with standard library or well-known third-party names (e.g., don't use `import json as ujson`).
- **Automation**: `Ruff` (`I` rule) will automatically check and help fix import order during the pre-commit phase.

## 8. Date and Time Handling

- **Timezone-Aware Datetimes**: All datetime objects **must** be timezone-aware and use UTC.
  - **DO**: `datetime.now(timezone.utc)`, `datetime.fromisoformat("2023-01-01T00:00:00+00:00")`
  - **DON'T**: `datetime.now()` (naive datetime)
- **Serialization**: Always serialize datetimes to ISO-8601 format with timezone information.
- **Consistency**: Never mix naive and timezone-aware datetimes in the same codebase.

### 8.1. Utility Functions

Use the provided utility functions in `utils.datetime_utils` for consistent datetime handling:

```python
from utils.datetime_utils import utc_now, to_iso_string, from_iso_string, ensure_utc

# Get current UTC time
now = utc_now()

# Convert to ISO string
iso_string = to_iso_string(now)

# Parse from ISO string
parsed_dt = from_iso_string("2023-01-01T00:00:00+00:00")

# Ensure a value is UTC datetime (useful for validation)
validated_dt = ensure_utc(some_datetime_value)
```

**Available utility functions:**
- `utc_now()`: Get current UTC datetime
- `to_utc(dt)`: Convert any datetime to UTC
- `from_iso_string(iso_string)`: Parse ISO-8601 string to datetime
- `to_iso_string(dt)`: Convert datetime to ISO-8601 string
- `ensure_utc(value)`: Validate and convert various inputs to UTC datetime

## 9. Commit Messages

- **Format**: We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.
- **Enforcement**: A pre-commit hook is in place to validate the format of your commit messages.
- **Common Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`.
  - Example: `feat: add user authentication endpoint`
  - Example: `fix: correct pagination logic in list_users`
