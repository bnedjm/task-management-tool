# 🚀 Quick Start Guide

Get up and running with the Task Management System in less than 5 minutes!

## Table of Contents
- [Prerequisites](#prerequisites)
- [Setup Options](#setup-options)
  - [Option 1: Automated Setup (Recommended)](#option-1-automated-setup-recommended)
  - [Option 2: Docker Setup](#option-2-docker-setup)
  - [Option 3: Manual Setup](#option-3-manual-setup)
- [Verify Installation](#verify-installation)
- [Your First API Calls](#your-first-api-calls)
- [Next Steps](#next-steps)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** - [Download here](https://www.python.org/downloads/)
- **Git** - [Download here](https://git-scm.com/downloads)
- **Docker** (Optional) - [Download here](https://docs.docker.com/get-docker/)

**Check your Python version:**
```bash
python3 --version
# Should show Python 3.11.x or higher

```
If your Python version is lower than 3.11, you should update it:

- **macOS**:  
  ```bash
  brew install python@3.11
  ```

- **Ubuntu/Debian**:  
  ```bash
  sudo apt update
  sudo apt install python3.11
  ```

- **Windows**:  
  [Download Python 3.11+ from the official website](https://www.python.org/downloads/), run the installer, and make sure to check "Add Python to PATH" during installation.

After installing, you may need to restart your terminal and use `python3.1x` instead of `python3` on some systems.

---

## Setup Options

Choose the setup method that works best for you:

### Option 1: Automated Setup (Recommended)

**Best for:** First-time setup, beginners

The automated setup script handles everything for you.

```bash
# 1. Clone the repository
git clone <repository-url>
cd task-management-tool

# 2. Run the setup script
./setup.sh

# Or use make
make setup
```

The script will:
- ✅ Verify Python version
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Create configuration files
- ✅ Set up project directories
- ✅ Run verification tests

**Follow the prompts** - the script will guide you through the process!

---

### Option 2: Docker Setup

**Best for:** Quick deployment, production-like environment

Docker provides the fastest way to run the application without any local setup.

```bash
# 1. Clone the repository
git clone <repository-url>
cd task-management-tool

# 2. Configure environment
cp env.template .env
nano .env  # Edit database credentials

# 3. Start with Docker
make docker-dev

# Or directly with docker-compose
docker-compose up -d
```

**That's it!** The API is now running at http://localhost:8000

---

### Option 3: Manual Setup

**Best for:** Developers who want full control

If you prefer a manual setup or the automated script doesn't work:

```bash
# 1. Clone the repository
git clone <repository-url>
cd task-management-tool

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install dependencies
pip install -r requirements.txt

# 5. Install development dependencies (optional)
pip install -r requirements-dev.txt

# 6. Configure environment
cp env.template .env
nano .env  # Edit with your settings

# 7. Create directories
mkdir -p data logs

# 8. Run the application
uvicorn src.api.main:app --reload
```

---

## Verify Installation

Once setup is complete, verify everything is working:

### 1. Check Health Endpoint

```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy"
}
```

### 2. Access API Documentation

Open your browser and visit:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc  <!-- recommended for better UI -->

You should see the interactive API documentation!

### 3. Run Tests (Optional)

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest

# Or use make
make test
```

---

## Your First API Calls

Let's create a project and some tasks using the API!

### Step 1: Create a Project

```bash
curl -X POST "http://localhost:8000/projects" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Project",
    "description": "Learning the Task Management System",
    "deadline": "2025-12-31T23:59:59"
  }'
```

**Response:**
```json
{
  "id": "proj_abc123...",
  "title": "My First Project",
  "description": "Learning the Task Management System",
  "deadline": "2025-12-31T23:59:59",
  "completed": false,
  "total_task_count": 0,
  "completed_task_count": 0,
  "created_at": "2025-12-15T10:00:00",
  "updated_at": "2025-12-15T10:00:00"
}
```

**💡 Save the project ID** - you'll need it for creating tasks!

### Step 2: Create a Task

Replace `<PROJECT_ID>` with the ID from Step 1:

```bash
curl -X POST "http://localhost:8000/tasks" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Complete the Quick Start guide",
    "description": "Follow all steps in the Quick Start guide",
    "deadline": "2025-12-20T18:00:00",
    "project_id": "<PROJECT_ID>"
  }'
```

**Response:**
```json
{
  "id": "task_xyz789...",
  "title": "Complete the Quick Start guide",
  "description": "Follow all steps in the Quick Start guide",
  "deadline": "2025-12-20T18:00:00",
  "completed": false,
  "project_id": "<PROJECT_ID>",
  "is_overdue": false,
  "created_at": "2025-12-15T10:00:00",
  "updated_at": "2025-12-15T10:00:00"
}
```

### Step 3: List All Tasks

```bash
curl http://localhost:8000/tasks
```

### Step 4: Complete a Task

Replace `<TASK_ID>` with your task ID:

```bash
curl -X PATCH "http://localhost:8000/tasks/<TASK_ID>/complete"
```

### Step 5: View Project Progress

Replace `<PROJECT_ID>` with your project ID:

```bash
curl http://localhost:8000/projects/<PROJECT_ID>
```

**🎉 Congratulations!** You've successfully:
- ✅ Created a project
- ✅ Added a task
- ✅ Completed a task
- ✅ Tracked project progress

---

## Using the Interactive API Documentation

The easiest way to explore the API is through the **Swagger UI**:

1. Open http://localhost:8000/docs
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"
6. See the response!

**No curl commands needed!** The interactive docs let you test everything directly in your browser.

---

## Common Queries

### Filter Tasks

**Get completed tasks:**
```bash
curl "http://localhost:8000/tasks?completed=true"
```

**Get incomplete tasks:**
```bash
curl "http://localhost:8000/tasks?completed=false"
```

**Get overdue tasks:**
```bash
curl "http://localhost:8000/tasks?overdue=true"
```

**Get tasks that are not overdue:**
```bash
curl "http://localhost:8000/tasks?overdue=false"
```

**Get tasks for a specific project:**
```bash
curl "http://localhost:8000/tasks?project_id=<PROJECT_ID>"
```

**Combine multiple filters** (all filters work together):
```bash
# Get completed, non-overdue tasks for a specific project
curl "http://localhost:8000/tasks?completed=true&overdue=false&project_id=<PROJECT_ID>"
```

### Update Operations

**Update a task:**
```bash
curl -X PUT "http://localhost:8000/tasks/<TASK_ID>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated title",
    "description": "Updated description",
    "deadline": "2025-12-25T18:00:00"
  }'
```

**Reopen a completed task:**
```bash
curl -X PATCH "http://localhost:8000/tasks/<TASK_ID>/reopen"
```

### Delete Operations

**Delete a task:**
```bash
curl -X DELETE "http://localhost:8000/tasks/<TASK_ID>"
```

**Delete a project:**
```bash
curl -X DELETE "http://localhost:8000/projects/<PROJECT_ID>"
```

---

## Next Steps

Now that you're up and running, explore these topics:

### 📚 Learn more
- Read the main [README.md](../README.md)

### 🧪 Run Tests
```bash
# All tests
make test

# Unit tests (domain logic)
make test-unit

# Integration tests (API + database)
make test-integration

# With coverage report
make coverage
```

### 🎨 Code Quality
```bash
# Format code
make format

# Run linter
make lint

# Type check
make type-check
```

### 🐳 Docker Commands
```bash
# Start development mode
make docker-dev

# Start production mode
make docker-prod

# View logs
make docker-logs

# Stop containers
make docker-down
```

### 📖 Explore Business Rules

The system enforces these business rules automatically:

1. **Task deadlines ≤ Project deadline**
   - Try creating a task with a deadline after the project deadline
   - The API will reject it!

2. **Auto-complete projects**
   - Complete all tasks in a project
   - The project automatically completes!

3. **Smart reopening**
   - Reopen a task in a completed project
   - The project automatically reopens!

**Test these rules** using the API documentation!

---

## Configuration

### Environment Variables

Edit `.env` to configure the application:

```bash
# Development Database (Neon PostgreSQL)
DEV_DATABASE_URL=postgresql://user:pass@host.neon.tech/db?sslmode=require

# Production Database
PROD_DATABASE_URL=postgresql://user:pass@host:5432/db

# Features
AUTO_COMPLETE_PROJECTS=true  # Enable auto-completion

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### Database Options

**Option 1: Neon PostgreSQL (Recommended for dev)**
```bash
DEV_DATABASE_URL=postgresql://user:pass@ep-xxx.neon.tech/db?sslmode=require
```
Get a free database at [neon.tech](https://neon.tech)

**Option 2: Local SQLite (Quick testing)**
```bash
DEV_DATABASE_URL=sqlite:///./data/tasks.db
```

**Option 3: Self-hosted PostgreSQL**
```bash
PROD_DATABASE_URL=postgresql://user:pass@localhost:5432/taskmanager
```

---

## Troubleshooting

### Python version error

**Problem:** `Python 3.11 or higher is required`

**Solution:**
```bash
# Install Python 3.11+
# Visit https://www.python.org/downloads/

# Or use pyenv
pyenv install 3.11
pyenv local 3.11
```

### Database connection error

**Problem:** `Could not connect to database`

**Solution:**
1. Check your `.env` file has correct credentials
2. Verify database is accessible
3. For SQLite, check `data/` directory exists

```bash
# Test database URL
python3 -c "from sqlalchemy import create_engine; create_engine('your-database-url').connect()"
```

### Port already in use

**Problem:** `Port 8000 is already in use`

**Solution:**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn src.api.main:app --reload --port 8001
```

### Module not found error

**Problem:** `ModuleNotFoundError: No module named 'fastapi'`

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Tests failing

**Problem:** Tests fail on first run

**Solution:**
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Clean and rerun
make clean
pytest
```

### Docker issues

**Problem:** Docker containers won't start

**Solution:**
```bash
# Check Docker is running
docker --version

# Rebuild containers
make docker-down
docker-compose build --no-cache
make docker-dev

# Check logs
make docker-logs
```

---

## Need Help?

### Documentation
- 📖 [README.md](../README.md) - Complete documentation
- 📝 [CONTRIBUTING.md](../CONTRIBUTING.md) - Development guide
- 📋 [CHANGELOG.md](../CHANGELOG.md) - Version history

### Interactive Help
- 🌐 API Docs: http://localhost:8000/docs (when running)
- 🔍 ReDoc: http://localhost:8000/redoc

### Commands Reference
```bash
make help  # Show all available commands
```
