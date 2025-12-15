# Task Management System

A task and project management system built with love.

[![Python 3.11-3.13](https://img.shields.io/badge/python-3.11--3.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [Roadmap](#roadmap)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## Overview

This Task Management System is a **production-ready application** built to demonstrate advanced software engineering practices.

### Technology Stack

- **Backend Framework:** FastAPI 0.115+
- **Language:** Python 3.11+
- **Database:** PostgreSQL (Neon) / SQLite
- **ORM:** SQLAlchemy 2.0
- **Validation:** Pydantic 2.9
- **Testing:** Pytest
- **Containerization:** Docker & Docker Compose

---

## Features

### Task Management

- ✅ **Create, read, update, delete tasks** - Full CRUD operations
- ✅ **Task completion tracking** - Mark tasks as completed or reopen them
- ✅ **Deadline management** - Track task deadlines with automatic overdue detection
- ✅ **Project assignment** - Assign tasks to projects with validation
- ✅ **Advanced filtering** - Filter by completion status, project, or overdue status
- ✅ **Automatic validation** - Task deadlines cannot exceed project deadlines

### Project Management

- ✅ **Create, read, update, delete projects** - Full project lifecycle management
- ✅ **Task association** - Group related tasks under projects
- ✅ **Automatic completion** - Projects auto-complete when all tasks are done (configurable)
- ✅ **Smart reopening** - Reopening a task automatically reopens completed projects
- ✅ **Progress tracking** - Real-time count of total and completed tasks
- ✅ **Deadline enforcement** - Task deadlines must be within project deadline

### Business Rules (Domain Layer)

All business rules are enforced at the domain level and **cannot be bypassed**:

1. **Deadline Constraints** - Task deadlines must be ≤ project deadline
2. **Completion Rules** - Projects can only be marked complete when all tasks are done
3. **Cascade Reopening** - Reopening a task automatically reopens its completed project
4. **Auto-Completion** - Completing the last task auto-completes the project (optional)
5. **Deadline Propagation** - Deadline changes cascade with proper event handling

### API Features

- 🔍 **Advanced Querying** - Filter, sort, and search capabilities
- 📊 **Health Checks** - Built-in health endpoint for monitoring
- 🔒 **CORS Support** - Configurable CORS for frontend integration
- 🎯 **Error Handling** - Structured error responses with proper HTTP status codes
- 📝 **Request Validation** - Automatic validation using Pydantic schemas

---

## Architecture

This system implements **Hexagonal Architecture** (Ports & Adapters) with **Domain-Driven Design** principles:

```
┌─────────────────────────────────────────────────────┐
│                   API Layer (FastAPI)               │
│           HTTP/REST Interface to the world          │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              Application Layer                      │
│   Commands, Queries, Services (Use Cases)           │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│               Domain Layer (Core)                   │
│  Entities, Value Objects, Events, Business Rules    │
│         NO framework dependencies                   │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│           Infrastructure Layer                      │
│  Database, Event Bus, External Dependencies         │
└─────────────────────────────────────────────────────┘
```

### Architectural Layers

#### 1. Domain Layer (Core Business Logic)
- **Entities:** `Task`, `Project` (rich domain models with business logic)
- **Value Objects:** `TaskId`, `ProjectId`, `Deadline` (immutable, validated types)
- **Domain Events:** `TaskCompletedEvent`, `ProjectDeadlineChangedEvent`, etc.
- **Repository Interfaces:** Abstract contracts (no implementation details)
- **Domain Exceptions:** Business-specific exceptions
- **Zero Dependencies:** No framework or infrastructure dependencies

#### 2. Application Layer (Use Cases)
- **Commands:** `CreateTask`, `CompleteTask`, `UpdateProject`, etc.
- **Queries:** `GetTaskById`, `ListProjects`, `FilterTasks`, etc.
- **Services:** `TaskService`, `ProjectService` (orchestration logic)
- **DTOs:** Data Transfer Objects for layer boundaries

#### 3. Infrastructure Layer (External Concerns)
- **Persistence:** SQLAlchemy implementations of repositories
- **Database Models:** ORM models mapping to database tables
- **Event Bus:** In-memory event dispatcher
- **Unit of Work:** Transaction management
- **Configuration:** Environment variable management

#### 4. API Layer (HTTP Interface)
- **Routes:** RESTful endpoints for tasks and projects
- **Schemas:** Pydantic models for request/response validation
- **Middleware:** Error handling, CORS
- **Dependencies:** Dependency injection for services

### Key Design Patterns

1. **Hexagonal Architecture** - Complete separation of concerns
2. **Repository Pattern** - Abstract data access
3. **Unit of Work** - Transaction management at boundaries
4. **Domain Events** - Decoupled business rule enforcement
5. **Dependency Injection** - Loose coupling at API layer
6. **Value Objects** - Immutable domain concepts
7. **Factory Pattern** - Entity creation with proper initialization
8. **Command Query Separation** - Clear separation of reads and writes

### Project Structure

```
task-management-tool/
├── src/
│   ├── domain/              # Core business logic (NO dependencies)
│   │   ├── entities/        # Task, Project (rich domain models)
│   │   ├── value_objects/   # TaskId, ProjectId, Deadline
│   │   ├── events/          # Domain events
│   │   ├── exceptions/      # Domain-specific exceptions
│   │   └── repositories/    # Repository INTERFACES
│   ├── application/         # Use cases & orchestration
│   │   ├── commands/        # Write operations
│   │   ├── queries/         # Read operations
│   │   ├── services/        # Application services
│   │   └── dto/             # Data Transfer Objects
│   ├── infrastructure/      # External dependencies
│   │   ├── persistence/     # Database implementation
│   │   │   ├── models/      # SQLAlchemy models
│   │   │   ├── repositories/# Repository implementations
│   │   │   ├── database.py  # Database setup
│   │   │   └── unit_of_work.py
│   │   ├── events/          # Event bus implementation
│   │   └── config.py        # Configuration management
│   └── api/                 # FastAPI layer
│       ├── routes/          # API endpoints
│       ├── schemas/         # Pydantic request/response models
│       ├── middleware/      # Error handling, CORS
│       ├── dependencies.py  # Dependency injection
│       └── main.py          # Application entry point
├── tests/
│   ├── unit/               # Domain logic tests (no DB)
│   └── integration/        # API & database tests
├── docs/
│   └── QUICKSTART.md       # Detailed setup guide
├── data/                   # SQLite database (if used)
├── logs/                   # Application logs
├── docker-compose.yml      # Docker orchestration
├── Dockerfile              # Container definition
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── setup.sh               # Automated setup script
├── Makefile               # Development commands
└── README.md              # This file
```

---

## Installation

### Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** (tested up to 3.13) - [Download here](https://www.python.org/downloads/)
- **Git** - [Download here](https://git-scm.com/downloads)
- **Docker** (Optional, recommended) - [Download here](https://docs.docker.com/get-docker/)

**Check your Python version:**
```bash
python3 --version  # Should show 3.11 or higher
```

> **Note for Python 3.13 users:** This project has been updated for full Python 3.13 compatibility with updated versions of FastAPI, Pydantic, and psycopg.

### Option 1: Automated Setup (Recommended)

The easiest way to get started. Run the automated setup script:

```bash
# Clone the repository
git clone <repository-url>
cd task-management-tool

# Run the setup script
./setup.sh

# Or use make
make setup
```

The script will automatically:
- ✅ Verify Python 3.11+ is installed
- ✅ Create and activate virtual environment
- ✅ Upgrade pip to latest version
- ✅ Install production dependencies
- ✅ Optionally install development dependencies
- ✅ Create `.env` file from template
- ✅ Set up data and logs directories
- ✅ Run tests to verify installation

### Option 2: Docker Setup (Fastest)

Perfect for quick deployment or production-like environment:

```bash
# Clone the repository
git clone <repository-url>
cd task-management-tool

# Configure environment
cp env.template .env
nano .env  # Edit with your database credentials

# Start with Docker
make docker-dev

# Or directly
docker-compose up -d
```

**Access the API:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/health

### Option 3: Manual Setup

For developers who want full control:

```bash
# Clone the repository
git clone <repository-url>
cd task-management-tool

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies (optional)
pip install -r requirements-dev.txt

# Configure environment
cp env.template .env
nano .env  # Edit with your settings

# Create directories
mkdir -p data logs

# Run the application
uvicorn src.api.main:app --reload

# Access at http://localhost:8000/docs
```

### Verification

Verify your installation is working:

```bash
# Check health endpoint
curl http://localhost:8000/health

# Should return: {"status":"healthy"}

# Run tests
make test
# or
pytest
```

### Troubleshooting Installation

#### Error: `pydantic-core` build failure (Python 3.13)

**Problem:** Older versions of Pydantic don't support Python 3.13.

**Solution:** This project has been updated to use Python 3.13-compatible versions. If you cloned an older version:

```bash
# Ensure you have the latest requirements
git pull origin main

# Remove old venv
rm -rf venv

# Reinstall
./setup.sh
```

**Manual fix:**
```bash
pip install --upgrade "pydantic>=2.9.0" "fastapi>=0.115.0"
```

#### Error: `pg_config executable not found` (Python 3.13)

**Problem:** `psycopg2-binary` doesn't support Python 3.13 yet.

**Solution:** This project uses `psycopg` version 3 instead:

```bash
pip install "psycopg[binary]>=3.2.13"
```

#### Error: `Python version too old`

**Solution:** Install Python 3.11 or higher:
- macOS: `brew install python@3.11` or download from [python.org](https://www.python.org/downloads/)
- Ubuntu: `sudo apt install python3.11`
- Windows: Download from [python.org](https://www.python.org/downloads/)

#### Error: `ModuleNotFoundError`

**Solution:** Ensure virtual environment is activated:
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

#### Error: Port 8000 already in use

**Solution:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn src.api.main:app --reload --port 8001
```

> 📖 **Need help?** Check our detailed [QUICKSTART.md](docs/QUICKSTART.md) guide for troubleshooting.

---

## Usage

### Starting the Application

**Local Development:**
```bash
# Activate virtual environment
source venv/bin/activate

# Start the server
make run
# or
uvicorn src.api.main:app --reload
```

**With Docker:**
```bash
# Development mode
make docker-dev

# Production mode
make docker-prod

# View logs
make docker-logs

# Stop
make docker-down
```

### Quick Start Example

Here's a complete workflow to get you started:

#### 1. Create a Project

```bash
curl -X POST "http://localhost:8000/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Website Redesign",
    "description": "Complete redesign of company website",
    "deadline": "2025-12-31T23:59:59"
  }'
```

**Response:**
```json
{
  "id": "proj_abc123...",
  "title": "Website Redesign",
  "description": "Complete redesign of company website",
  "deadline": "2025-12-31T23:59:59",
  "completed": false,
  "total_task_count": 0,
  "completed_task_count": 0
}
```

#### 2. Create Tasks

```bash
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Design new homepage",
    "description": "Create mockups and get approval",
    "deadline": "2025-11-30T18:00:00",
    "project_id": "proj_abc123..."
  }'
```

#### 3. List All Tasks

```bash
# Get all tasks
curl "http://localhost:8000/tasks"

# Filter completed tasks
curl "http://localhost:8000/tasks?completed=true"

# Filter overdue tasks
curl "http://localhost:8000/tasks?overdue=true"

# Filter by project
curl "http://localhost:8000/tasks?project_id=proj_abc123..."
```

#### 4. Complete a Task

```bash
curl -X PATCH "http://localhost:8000/tasks/{task_id}/complete"
```

#### 5. Update a Task

```bash
curl -X PUT "http://localhost:8000/tasks/{task_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated title",
    "description": "Updated description",
    "deadline": "2025-12-15T18:00:00"
  }'
```

#### 6. Delete a Task

```bash
curl -X DELETE "http://localhost:8000/tasks/{task_id}"
```

#### 7. View Project Progress

```bash
curl "http://localhost:8000/projects/{project_id}"
```

### Using the Interactive Documentation

The easiest way to explore the API:

1. **Open Swagger UI:** http://localhost:8000/docs
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"
6. See the response!

No curl commands needed - test everything directly in your browser.

### Common Operations

**Get a specific task:**
```bash
curl "http://localhost:8000/tasks/{task_id}"
```

**Get a specific project:**
```bash
curl "http://localhost:8000/projects/{project_id}"
```

**Reopen a completed task:**
```bash
curl -X PATCH "http://localhost:8000/tasks/{task_id}/reopen"
```

**Delete a project:**
```bash
curl -X DELETE "http://localhost:8000/projects/{project_id}"
```

---

## Configuration

Configuration is managed via environment variables loaded from a `.env` file.

### Setup

```bash
# Copy the template
cp env.template .env

# Edit with your values
nano .env
```

### Environment Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `DEV_DATABASE_URL` | Development database connection | `sqlite:///./data/tasks.db` | `postgresql://user:pass@host.neon.tech/db` |
| `PROD_DATABASE_URL` | Production database connection | `sqlite:///./data/tasks.db` | `postgresql://user:pass@host:5432/db` |
| `AUTO_COMPLETE_PROJECTS` | Auto-complete projects when all tasks done | `true` | `true` or `false` |
| `LOG_LEVEL` | Logging verbosity | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `API_TITLE` | API title in documentation | `Task Management API` | Any string |
| `API_VERSION` | API version | `1.0.0` | Semantic version string |
| `API_DESCRIPTION` | API description | Empty | Any string |

### Database Configuration

#### Option 1: Neon PostgreSQL (Recommended for Development)

Free serverless PostgreSQL in the cloud:

```bash
DEV_DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/db?sslmode=require
```

**Get a free database:** [neon.tech](https://neon.tech)

#### Option 2: Local PostgreSQL (Production)

Self-hosted PostgreSQL:

```bash
PROD_DATABASE_URL=postgresql://user:pass@localhost:5432/taskmanager
```

#### Option 3: SQLite (Quick Testing)

File-based database (not for production):

```bash
DEV_DATABASE_URL=sqlite:///./data/tasks.db
```

### Feature Flags

**AUTO_COMPLETE_PROJECTS:**
- `true` - Projects automatically complete when all tasks are done
- `false` - Projects must be manually completed

### Example Configuration

```bash
# .env file
DEV_DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/db?sslmode=require
PROD_DATABASE_URL=postgresql://user:pass@localhost:5432/taskmanager
AUTO_COMPLETE_PROJECTS=true
LOG_LEVEL=INFO
API_TITLE=Task Management API
API_VERSION=1.0.0
API_DESCRIPTION=Production-grade task management system
```

---

## API Documentation

### Interactive Documentation

Once the application is running, access the interactive documentation:

- **Swagger UI (Recommended):** http://localhost:8000/docs
  - Interactive API testing
  - "Try it out" functionality
  - Request/response examples
  
- **ReDoc:** http://localhost:8000/redoc
  - Clean, readable documentation
  - Three-panel layout
  - Better for browsing

- **OpenAPI Schema:** http://localhost:8000/openapi.json
  - Raw OpenAPI 3.0 specification
  - Use with code generators

### API Endpoints

#### Health Check

```
GET /health
```
Returns the health status of the application.

#### Projects

```
POST   /projects              # Create a new project
GET    /projects              # List all projects
GET    /projects/{id}         # Get a specific project
PUT    /projects/{id}         # Update a project
DELETE /projects/{id}         # Delete a project
PATCH  /projects/{id}/complete # Complete a project
POST   /projects/{id}/tasks/{task_id}/link   # Link task to project
DELETE /projects/{id}/tasks/{task_id}/unlink # Unlink task from project
GET    /projects/{id}/tasks   # Get all tasks for a project
```

#### Tasks

```
POST   /tasks                 # Create a new task
GET    /tasks                 # List all tasks (with filters)
GET    /tasks/{id}            # Get a specific task
PUT    /tasks/{id}            # Update a task
DELETE /tasks/{id}            # Delete a task
PATCH  /tasks/{id}/complete   # Complete a task
PATCH  /tasks/{id}/reopen     # Reopen a task
```

### Query Parameters

**GET /tasks:**
- `completed` (boolean) - Filter by completion status
- `overdue` (boolean) - Filter overdue tasks
- `project_id` (string) - Filter by project

### Request/Response Examples

See the [Usage](#usage) section for complete curl examples, or use the interactive Swagger UI for live examples.

### Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Error message here"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request (validation error)
- `404` - Not Found
- `409` - Conflict (business rule violation)
- `500` - Internal Server Error

---

## Testing

The project includes comprehensive unit and integration tests.

### Running Tests

**Using Make (Recommended):**
```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests only
make test-integration

# Run with coverage report
make coverage

# View coverage report in browser
open htmlcov/index.html
```

**Using Pytest Directly:**
```bash
# Install dev dependencies first
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_task.py

# Run specific test
pytest tests/unit/test_task.py::test_complete_task

# Run with coverage
pytest --cov=src --cov-report=html --cov-report=term
```

### Test Structure

#### Unit Tests (`tests/unit/`)
Tests domain logic in complete isolation (no database, no API):

- `test_task.py` - Task entity business rules
- `test_project.py` - Project entity business rules
- `test_value_objects.py` - Value object behavior

**Example:** Testing that a task cannot be completed twice:
```python
def test_cannot_complete_already_completed_task():
    task = Task.create(...)
    task.complete()
    
    with pytest.raises(TaskAlreadyCompletedError):
        task.complete()
```

#### Integration Tests (`tests/integration/`)
Tests the full stack (API → Application → Domain → Database):

- `test_api_tasks.py` - Task API endpoints
- `test_api_projects.py` - Project API endpoints

**Example:** Testing auto-completion of projects:
```python
def test_project_auto_completes_when_all_tasks_done(client):
    # Create project
    project = client.post("/projects", json={...})
    
    # Create task
    task = client.post("/tasks", json={...})
    
    # Complete task
    client.patch(f"/tasks/{task['id']}/complete")
    
    # Verify project is completed
    project = client.get(f"/projects/{project['id']}")
    assert project["completed"] is True
```

### Test Coverage

Current coverage: Check with `make coverage`

**Coverage Goals:**
- Domain Layer: 100% (business logic is critical)
- Application Layer: >90%
- Infrastructure Layer: >80%
- API Layer: >80%

### Continuous Testing

**Watch mode (requires pytest-watch):**
```bash
pip install pytest-watch
ptw
```

**Pre-commit testing:**
```bash
# Add to .git/hooks/pre-commit
#!/bin/bash
make test || exit 1
```

---

## Deployment

### Docker Deployment

#### Development Mode

Uses Neon PostgreSQL cloud database:

```bash
# Start
make docker-dev

# View logs
make docker-logs

# Stop
make docker-down
```

#### Production Mode

Uses production database configuration:

```bash
# Start
make docker-prod

# View logs
docker-compose logs -f

# Stop
make docker-down
```

#### Custom Docker Build

```bash
# Build image
docker build -t task-management-api:latest .

# Run container
docker run -d \
  --name task-management-api \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e AUTO_COMPLETE_PROJECTS=true \
  -e LOG_LEVEL=INFO \
  -v $(pwd)/data:/data \
  -v $(pwd)/logs:/app/logs \
  task-management-api:latest

# Check logs
docker logs -f task-management-api

# Stop
docker stop task-management-api
```

### Production Deployment

#### 1. Environment Configuration

Create production `.env` file:

```bash
# Production database (use strong credentials)
PROD_DATABASE_URL=postgresql://prod_user:strong_password@db.example.com:5432/taskmanager

# Production settings
AUTO_COMPLETE_PROJECTS=true
LOG_LEVEL=INFO

# API metadata
API_TITLE=Task Management API
API_VERSION=1.0.0
API_DESCRIPTION=Production task management system
```

#### 2. Security Considerations

- ✅ Use HTTPS in production
- ✅ Configure CORS appropriately (not `allow_origins=["*"]`)
- ✅ Use strong database credentials
- ✅ Never commit `.env` files
- ✅ Keep dependencies updated
- ✅ Add authentication/authorization middleware
- ✅ Enable rate limiting
- ✅ Set up proper logging and monitoring

#### 3. Database Setup

**PostgreSQL Production Setup:**
```bash
# Create database
createdb taskmanager

# Create user
psql -c "CREATE USER taskmanager WITH PASSWORD 'strong_password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE taskmanager TO taskmanager;"

# Test connection
psql postgresql://taskmanager:strong_password@localhost:5432/taskmanager
```

#### 4. Monitoring

**Health Checks:**
```bash
# Add to monitoring system
curl http://your-domain.com/health

# Expected response
{"status":"healthy"}
```

**Logging:**
- Logs are written to `logs/` directory
- Configure log aggregation (ELK, Datadog, CloudWatch)
- Set up alerts for ERROR level logs

**Metrics to Monitor:**
- Response times
- Error rates
- Database connection pool
- Memory usage
- CPU usage

#### 5. Scaling

**Horizontal Scaling:**
```bash
# Run multiple instances behind load balancer
docker-compose up -d --scale api=3
```

**Best Practices:**
- Use PostgreSQL connection pooling
- Add Redis for caching
- Implement rate limiting
- Use CDN for static assets
- Set up auto-scaling policies

#### 6. Backup Strategy

**Database Backups:**
```bash
# Automated daily backups
pg_dump taskmanager > backup_$(date +%Y%m%d).sql

# Restore
psql taskmanager < backup_20251213.sql
```

### Platform-Specific Deployment

#### Heroku

```bash
# Create app
heroku create task-management-api

# Add PostgreSQL
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set AUTO_COMPLETE_PROJECTS=true
heroku config:set LOG_LEVEL=INFO

# Deploy
git push heroku main

# Open
heroku open
```

#### AWS EC2

```bash
# SSH into EC2 instance
ssh -i key.pem ubuntu@ec2-xxx.compute.amazonaws.com

# Clone and setup
git clone <repository-url>
cd task-management-tool
./setup.sh

# Run with supervisor/systemd
sudo systemctl start task-management-api
```

#### DigitalOcean App Platform

Use the provided `docker-compose.yml` and deploy via App Platform interface.

---

## Contributing

We welcome contributions! This project is a demonstration of best practices, and we're happy to review PRs that maintain or improve code quality.

### Getting Started

1. **Fork the repository**
2. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/task-management-tool.git
   cd task-management-tool
   ```
3. **Set up development environment**
   ```bash
   ./setup.sh
   ```
4. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Development Workflow

#### 1. Make Your Changes

Follow the architectural principles:
- **Domain Layer** - Add entities, value objects, events (no dependencies)
- **Application Layer** - Add commands, queries, services
- **Infrastructure Layer** - Add repositories, database models
- **API Layer** - Add routes, schemas

#### 2. Write Tests

**Test-Driven Development:**
```bash
# Write failing test first
pytest tests/unit/test_new_feature.py -v

# Implement feature

# Verify test passes
pytest tests/unit/test_new_feature.py -v
```

**Coverage Requirements:**
```bash
# Ensure coverage doesn't decrease
make coverage
```

#### 3. Code Quality

**Format code:**
```bash
make format
# or
black src/ tests/
isort src/ tests/
```

**Lint code:**
```bash
make lint
# or
flake8 src/ tests/
```

**Type check:**
```bash
make type-check
# or
mypy src/
```

**Run all quality checks:**
```bash
make format lint type-check test
```

#### 4. Commit Changes

**Commit Message Format:**
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, etc.)
- `refactor` - Code refactoring
- `test` - Adding or updating tests
- `chore` - Maintenance tasks

**Example:**
```bash
git commit -m "feat(domain): add task priority value object"
```

#### 5. Submit Pull Request

1. Push your branch
   ```bash
   git push origin feature/your-feature-name
   ```
2. Create Pull Request on GitHub
3. Fill in the PR template
4. Wait for review

### Code Review Process

All PRs must:
- ✅ Pass all tests
- ✅ Maintain or improve code coverage
- ✅ Follow code style (black, isort)
- ✅ Pass linting (flake8)
- ✅ Pass type checking (mypy)
- ✅ Include documentation updates
- ✅ Follow architectural principles

### Development Guidelines

**Do:**
- ✅ Write tests first (TDD)
- ✅ Keep domain logic in entities
- ✅ Use value objects for domain concepts
- ✅ Emit domain events for important changes
- ✅ Follow SOLID principles
- ✅ Write clear commit messages
- ✅ Document public APIs

**Don't:**
- ❌ Add framework dependencies to domain layer
- ❌ Put business logic in services
- ❌ Use primitive types for domain concepts
- ❌ Bypass domain rules via repositories
- ❌ Skip tests
- ❌ Decrease code coverage

### Adding New Features

**Example: Adding Task Priority**

1. **Domain Layer** - Add value object
   ```python
   # src/domain/value_objects/priority.py
   class Priority(ValueObject):
       def __init__(self, value: int):
           if not 1 <= value <= 5:
               raise ValueError("Priority must be 1-5")
           self._value = value
   ```

2. **Update Entity**
   ```python
   # src/domain/entities/task.py
   class Task:
       def __init__(self, ..., priority: Priority):
           self._priority = priority
   ```

3. **Application Layer** - Update DTOs
   ```python
   # src/application/dto/task_dto.py
   class TaskDTO:
       priority: int
   ```

4. **Infrastructure** - Update model
   ```python
   # src/infrastructure/persistence/models/task_model.py
   class TaskModel(Base):
       priority = Column(Integer, nullable=False)
   ```

5. **API Layer** - Update schemas
   ```python
   # src/api/schemas/task_schemas.py
   class TaskCreate(BaseModel):
       priority: int = Field(ge=1, le=5)
   ```

6. **Write Tests**
   ```python
   # tests/unit/test_priority.py
   # tests/integration/test_api_tasks.py
   ```

### Questions?

- 📖 Read [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines
- 💬 Open an issue for discussion
- 📧 Contact maintainers

---

## Roadmap

### Version 1.1 (Current)
- ✅ Core task management
- ✅ Project management
- ✅ Domain-driven design implementation
- ✅ Hexagonal architecture
- ✅ Event-driven patterns
- ✅ Comprehensive testing
- ✅ Docker deployment

### Version 1.2 (Planned)
- 🔲 Task priority levels
- 🔲 Task tags/labels
- 🔲 Task comments
- 🔲 User assignment
- 🔲 Due date notifications
- 🔲 Search functionality

### Version 2.0 (Future)
- 🔲 User authentication & authorization
- 🔲 Multi-tenant support
- 🔲 Task templates
- 🔲 Recurring tasks
- 🔲 Email notifications
- 🔲 Webhooks
- 🔲 GraphQL API
- 🔲 Real-time updates (WebSockets)

### Infrastructure Improvements
- 🔲 Database migrations with Alembic
- 🔲 Redis caching layer
- 🔲 Message queue (Celery/RabbitMQ)
- 🔲 API rate limiting
- 🔲 Metrics and monitoring (Prometheus)
- 🔲 Distributed tracing (OpenTelemetry)

### Developer Experience
- 🔲 CLI tool for task management
- 🔲 Python client library
- 🔲 Frontend demo application
- 🔲 API client code generators
- 🔲 Development Docker compose setup
- 🔲 VS Code dev container

### Suggestions?

Have ideas for new features? [Open an issue](../../issues) with the `enhancement` label!

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**What this means:**
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use
- ⚠️ License and copyright notice required
- ❌ Liability and warranty excluded

---

## Acknowledgements

### Inspiration

This project demonstrates architectural patterns and principles from:

- **Domain-Driven Design** by Eric Evans
  - Rich domain models
  - Ubiquitous language
  - Bounded contexts

- **Hexagonal Architecture** by Alistair Cockburn
  - Ports and adapters
  - Dependency inversion
  - Testability

- **Clean Architecture** by Robert C. Martin
  - Dependency rule
  - Layer separation
  - Framework independence

- **Enterprise Integration Patterns** by Gregor Hohpe
  - Event-driven architecture
  - Message-based communication

### Technologies

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit and ORM
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [Pytest](https://pytest.org/) - Testing framework
- [Docker](https://www.docker.com/) - Containerization
- [Neon](https://neon.tech/) - Serverless PostgreSQL

### Community

Special thanks to:
- The FastAPI community for excellent documentation
- The DDD community for architectural guidance
- All contributors who help improve this project

### Learning Resources

Want to learn more about the patterns used here?

**Books:**
- "Domain-Driven Design" - Eric Evans
- "Implementing Domain-Driven Design" - Vaughn Vernon
- "Clean Architecture" - Robert C. Martin
- "Patterns of Enterprise Application Architecture" - Martin Fowler

**Online:**
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Domain-Driven Design Reference](https://domainlanguage.com/ddd/)

---

<div align="center">

**Built with senior-level engineering practices** 🚀

[⬆ Back to Top](#task-management-system)

</div>
