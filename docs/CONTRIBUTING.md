# Contributing to Task Management System

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- Docker (optional, for containerized development)

### Setup Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd payback-task-management-tool

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
make install-dev
# Or: pip install -r requirements-dev.txt

# Run tests to verify setup
make test
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 2. Make Your Changes

Follow the architecture guidelines:

- **Domain changes**: Start here for business logic
- **Application changes**: Add use cases and services
- **Infrastructure changes**: Implement repositories or external integrations
- **API changes**: Add or modify endpoints

### 3. Write Tests

**Always write tests for your changes!**

```bash
# Run unit tests
make test-unit

# Run integration tests
make test-integration

# Check coverage
make coverage
```

Maintain minimum 80% coverage for new code.

### 4. Format and Lint

```bash
# Format code
make format

# Run linter
make lint

# Type check
make type-check

# Or run all checks
make all
```

### 5. Commit Your Changes

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add task priority feature"
# or
git commit -m "fix: correct deadline validation logic"
# or
git commit -m "docs: update API documentation"
```

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear description of changes
- Link to related issues
- Screenshots (if UI changes)
- Test results

## Code Style Guidelines

### Python Style

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use Black for formatting
- Use isort for import sorting

### Naming Conventions

- **Classes**: PascalCase (e.g., `TaskService`)
- **Functions/Methods**: snake_case (e.g., `complete_task`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `MAX_TASKS`)
- **Private methods**: prefix with underscore (e.g., `_to_dto`)

### Documentation

- Add docstrings to all public classes and methods
- Use Google-style docstrings
- Document complex business logic
- Update README.md for user-facing changes

Example:
```python
def complete_task(self, command: CompleteTaskCommand) -> TaskDTO:
    """Mark a task as completed.

    Args:
        command: Command containing task ID.

    Returns:
        TaskDTO: Completed task data.

    Raises:
        TaskNotFoundError: If task doesn't exist.
        TaskAlreadyCompletedError: If task is already completed.
    """
```

## Architecture Guidelines

### Domain Layer Rules

✅ **DO**:
- Keep domain pure (no framework dependencies)
- Enforce business rules in entities
- Emit domain events for important state changes
- Use value objects for domain concepts

❌ **DON'T**:
- Import from infrastructure or API layers
- Add database or HTTP concerns
- Use framework decorators
- Make entities anemic

### Application Layer Rules

✅ **DO**:
- Keep services stateless
- Use Unit of Work for transactions
- Publish domain events after persistence
- Map between entities and DTOs

❌ **DON'T**:
- Put business logic in services
- Access database directly (use repositories)
- Expose domain entities to API

### API Layer Rules

✅ **DO**:
- Validate input with Pydantic
- Handle exceptions properly
- Return appropriate HTTP status codes
- Document endpoints

❌ **DON'T**:
- Put business logic in routes
- Expose internal errors to clients
- Access repositories directly

## Testing Guidelines

### Unit Tests

Test domain logic without dependencies:

```python
def test_complete_task():
    """Test that completing a task emits event."""
    task = Task.create(...)
    task.complete()
    
    events = task.collect_events()
    assert isinstance(events[0], TaskCompletedEvent)
```

### Integration Tests

Test API endpoints with database:

```python
def test_complete_task_endpoint(client):
    """Test task completion via API."""
    response = client.post("/tasks", json={...})
    task_id = response.json()["id"]
    
    response = client.patch(f"/tasks/{task_id}/complete")
    assert response.status_code == 200
```

### Test Coverage

- Aim for 80%+ coverage
- Focus on business logic
- Test edge cases and error conditions
- Test domain events

## Pull Request Process

1. **Update Documentation**: README, ARCHITECTURE.md if needed
2. **Add Tests**: Unit and integration tests for changes
3. **Run All Checks**: `make all` should pass
4. **Update CHANGELOG**: Add entry for your changes
5. **Request Review**: Tag appropriate reviewers
6. **Address Feedback**: Respond to review comments
7. **Squash Commits**: If requested by maintainers

## Reporting Bugs

Use GitHub Issues with:

- **Title**: Clear, descriptive summary
- **Description**: Detailed description of the bug
- **Steps to Reproduce**: Exact steps to reproduce
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, etc.
- **Screenshots**: If applicable

## Suggesting Features

Use GitHub Issues with:

- **Title**: Clear feature description
- **Use Case**: Why this feature is needed
- **Proposed Solution**: How it could be implemented
- **Alternatives**: Other approaches considered
- **Architecture Impact**: Which layers affected

## Code Review Guidelines

### As a Reviewer

- Be respectful and constructive
- Focus on code, not the person
- Explain reasoning
- Suggest improvements
- Approve when ready

### As an Author

- Respond to all comments
- Don't take feedback personally
- Ask for clarification if needed
- Make requested changes
- Re-request review

## Community

- Be respectful and inclusive
- Help others learn
- Share knowledge
- Collaborate openly

## Questions?

Feel free to:
- Open an issue for questions
- Start a discussion
- Reach out to maintainers

---

Thank you for contributing! 🎉

