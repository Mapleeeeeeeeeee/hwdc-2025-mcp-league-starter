# Backend Folder Structure

This document provides a high-level overview of the backend source code structure. It serves as a map for developers to understand the responsibilities of each component and how they interact.

For detailed coding standards and conventions, please refer to [CODING_STANDARDS.md](./CODING_STANDARDS.md).

## Guiding Principles

The structure is designed based on the principles of **Clean Architecture** and **Domain-Driven Design (DDD)**, emphasizing:
- **Separation of Concerns**: Each layer has a single, well-defined responsibility.
- **Dependency Rule**: Inner layers (like `domain`) are independent and know nothing about outer layers (like `api` or `integrations`).
- **High Cohesion & Low Coupling**: Related logic is grouped, and dependencies between components are minimized.

## `src/` Directory Overview

```
src/
├── __init__.py
├── main.py             # FastAPI application instance and startup logic

├── api/                # API Layer (HTTP entry points)
│   ├── v1/
│   └── exception_handlers.py

├── core/               # Core configurations and cross-cutting concerns
│   ├── config.py
│   ├── logging.py
│   └── middleware.py

├── domain/             # (Optional) Domain Layer for core business logic
│   └── conversation/
│       ├── models.py
│       └── services.py

├── usecases/           # Application Use Case Layer
│   └── conversation_usecase.py

├── models/             # API Models (DTOs / Schemas)
│   └── conversation.py

├── integrations/       # Integration with all external services
│   ├── db/
│   └── llm/

└── shared/             # Code shared across the entire application
    ├── exceptions.py
    └── response.py
```

---

## Directory Responsibilities

### `main.py`
- **Role**: Application Entrypoint.
- **Responsibilities**:
  - Create the main FastAPI application instance.
  - Mount middleware from `core/`.
  - Include routers from `api/`.
  - Contains startup and shutdown event logic.
- **Rules**: Should not contain any business logic.

### `api/`
- **Role**: API Layer (Adapter).
- **Responsibilities**:
  - Define API endpoints (routers).
  - Handle HTTP request parsing and validation.
  - Call `usecases` to execute business flows.
  - Format and return HTTP responses using `shared/response.py`.
  - Handle API-specific exceptions via `exception_handlers.py`.
- **For more details, see**: [API Layer Architecture](./architecture/api-layer.md)

### `core/`
- **Role**: Cross-Cutting Concerns.
- **Responsibilities**:
  - Application configuration (`config.py`).
  - Logging setup (`logging.py`).
  - Global FastAPI middleware (`middleware.py`).
- **Rules**: This code is foundational and typically runs once at application startup.

### `domain/`
- **Role**: Domain Layer (Enterprise Business Rules).
- **Responsibilities**:
  - **`models.py`**: Contains **Domain Models (Entities)**, which encapsulate core business data and rules (invariants). These are typically plain Python classes or `@dataclass`. They are the heart of the application.
  - **`services.py`**: Contains **Domain Services**, which orchestrate complex business logic involving multiple domain models that doesn't naturally fit within a single model.
- **Rules**: This layer is completely independent. It **must not** depend on any other layer in the application.

### `usecases/`
- **Role**: Application Use Case Layer.
- **Responsibilities**:
  - Implements a specific application use case (e.g., "Create User", "Generate Conversation Reply").
  - Acts as an orchestrator or "project manager".
  - Calls `domain` services for core logic and `integrations` for external operations (like saving to a database).
- **Rules**: Contains application-specific logic, but not core enterprise rules. It depends on `domain` and `integrations` (via interfaces/abstractions if following strict DI).
- **For more details, see**: `architecture/usecases-layer.md` (formerly `services-layer.md`)

### `models/`
- **Role**: API Model Layer (DTOs / Schemas).
- **Responsibilities**:
  - Defines Pydantic models used for API request and response validation.
  - These models define the public data contract of the API.
- **Rules**: These models are for data transfer and validation at the application boundary. They should not contain business logic.

### `integrations/`
- **Role**: Infrastructure / Integration Layer.
- **Responsibilities**:
  - Contains all logic for communicating with the "outside world".
  - **`db/`**: Implements database interactions, often using the Repository pattern.
  - **`llm/`**: Contains clients for communicating with third-party LLM APIs.
  - Other examples: Email services, payment gateways, file storage.
- **Rules**: This layer handles the "how" of data persistence and external communication. It adapts external resources to a format usable by the application.

### `shared/`
- **Role**: Shared Kernel.
- **Responsibilities**:
  - Contains code that is shared across multiple layers without belonging to a specific one.
  - **`exceptions.py`**: Defines custom, application-wide business exceptions (e.g., `UserNotFoundError`).
  - **`response.py`**: Provides helper functions to create standardized API responses.
- **Rules**: Use with caution. If code is only used by one layer, it should belong to that layer.
