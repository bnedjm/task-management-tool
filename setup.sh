#!/bin/bash

# Task Management System - Complete Setup Script
# This script sets up the entire development environment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Main setup
print_header "🚀 Task Management System - Complete Setup"

echo "This script will:"
echo "  1. Check system requirements (Python 3.11+)"
echo "  2. Create and configure virtual environment"
echo "  3. Install dependencies"
echo "  4. Configure environment variables"
echo "  5. Create necessary directories"
echo "  6. Run tests to verify installation"
echo ""

# Check if we're in the project root
if [ ! -f "pyproject.toml" ]; then
    print_error "Error: pyproject.toml not found!"
    echo "Please run this script from the project root directory."
    exit 1
fi

print_success "Project directory verified"

# ============================================
# STEP 1: Check Python version
# ============================================
print_header "📋 Step 1: Checking Python Version"

if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed!"
    echo "Please install Python 3.11 or higher from https://www.python.org/downloads/"
    exit 1
fi

python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.11"

# Version comparison
if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then 
    print_error "Python $required_version or higher is required. Found: $python_version"
    echo "Please upgrade Python from https://www.python.org/downloads/"
    exit 1
fi

print_success "Python $python_version detected"

# ============================================
# STEP 2: Virtual Environment
# ============================================
print_header "📦 Step 2: Setting Up Virtual Environment"

if [ -d "venv" ]; then
    print_warning "Virtual environment already exists"
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Removing existing virtual environment..."
        rm -rf venv
        python3 -m venv venv
        print_success "Virtual environment recreated"
    else
        print_info "Using existing virtual environment"
    fi
else
    python3 -m venv venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# ============================================
# STEP 3: Upgrade pip
# ============================================
print_header "⬆️  Step 3: Upgrading pip"

pip install --upgrade pip --quiet
print_success "pip upgraded to latest version"

# ============================================
# STEP 4: Install Dependencies
# ============================================
print_header "📥 Step 4: Installing Dependencies"

print_info "Installing production dependencies..."
pip install -r requirements.txt --quiet
print_success "Production dependencies installed"

# Ask about development dependencies
echo ""
read -p "Install development dependencies (pytest, black, mypy, etc.)? (Y/n): " install_dev
if [[ ! $install_dev =~ ^[Nn]$ ]]; then
    print_info "Installing development dependencies..."
    pip install -r requirements-dev.txt --quiet
    print_success "Development dependencies installed"
else
    print_info "Skipping development dependencies"
fi

# ============================================
# STEP 5: Environment Configuration
# ============================================
print_header "🔧 Step 5: Environment Configuration"

if [ -f ".env" ]; then
    print_warning ".env file already exists!"
    echo ""
    read -p "Do you want to overwrite it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -f "env.template" ]; then
            cp env.template .env
            print_success "Created new .env file from template"
        else
            print_error "env.template not found!"
            exit 1
        fi
    else
        print_info "Keeping existing .env file"
    fi
else
    if [ -f "env.template" ]; then
        cp env.template .env
        print_success "Created .env file from template"
    else
        print_error "env.template not found!"
        exit 1
    fi
fi

# ============================================
# STEP 6: Create Directories
# ============================================
print_header "📁 Step 6: Creating Project Directories"

mkdir -p data logs
print_success "Created data/ and logs/ directories"

# ============================================
# STEP 7: Docker Check (Optional)
# ============================================
print_header "🐳 Step 7: Docker Configuration Check"

if command -v docker &> /dev/null; then
    print_success "Docker is installed"
    
    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null 2>&1; then
        print_success "Docker Compose is available"
        print_info "You can use Docker with: make docker-dev"
    else
        print_warning "Docker Compose not found"
        print_info "Install docker-compose to use Docker deployment"
    fi
else
    print_warning "Docker not installed"
    print_info "Install Docker from https://docs.docker.com/get-docker/ for containerized deployment"
fi

# ============================================
# STEP 8: Run Tests (Optional)
# ============================================
print_header "🧪 Step 8: Verification Tests"

if command -v pytest &> /dev/null; then
    echo ""
    read -p "Run tests to verify installation? (Y/n): " run_tests
    if [[ ! $run_tests =~ ^[Nn]$ ]]; then
        print_info "Running test suite..."
        echo ""
        
        if pytest -q 2>&1 | tee /tmp/pytest_output.log; then
            print_success "All tests passed!"
        else
            print_warning "Some tests failed (this might be expected on first run)"
            print_info "Check the output above for details"
        fi
    else
        print_info "Skipping tests"
    fi
else
    print_warning "pytest not available (install dev dependencies to run tests)"
fi

# ============================================
# SETUP COMPLETE - Show Summary
# ============================================
print_header "🎉 Setup Complete!"

echo "Your Task Management System is ready to use!"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📝 IMPORTANT NEXT STEPS:${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "1. Configure your database credentials:"
echo -e "   ${BLUE}nano .env${NC}  (or use your preferred editor)"
echo ""
echo "   Update these values:"
echo "   - DEV_DATABASE_URL  (SQLite for development)"
echo "   - PROD_DATABASE_URL (PostgreSQL for production)"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🚀 QUICK START COMMANDS:${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Activate virtual environment:"
echo -e "  ${BLUE}source venv/bin/activate${NC}"
echo ""
echo "Run locally (after configuring .env):"
echo -e "  ${BLUE}make run${NC}"
echo "  or"
echo -e "  ${BLUE}uvicorn src.api.main:app --reload${NC}"
echo ""
echo "Run with Docker:"
echo -e "  ${BLUE}make docker-dev${NC}     # Development mode"
echo -e "  ${BLUE}make docker-prod${NC}    # Production mode"
echo ""
echo "Run tests:"
echo -e "  ${BLUE}make test${NC}           # All tests"
echo -e "  ${BLUE}make test-unit${NC}      # Unit tests only"
echo -e "  ${BLUE}make test-integration${NC} # Integration tests only"
echo ""
echo "Code quality:"
echo -e "  ${BLUE}make format${NC}         # Format code (black + isort)"
echo -e "  ${BLUE}make lint${NC}           # Run linter (flake8)"
echo -e "  ${BLUE}make type-check${NC}     # Type check (mypy)"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}📚 RESOURCES:${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "Documentation:"
echo "  - README.md            # Complete project documentation"
echo "  - docs/QUICKSTART.md   # Quick start guide"
echo "  - docs/CONTRIBUTING.md # Contribution guidelines"
echo ""
echo "API Documentation (once running):"
echo "  - http://localhost:8000/docs      # Swagger UI"
echo "  - http://localhost:8000/redoc     # ReDoc"
echo "  - http://localhost:8000/health    # Health check"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${YELLOW}🔒 SECURITY REMINDERS:${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "  ⚠️  Never commit .env to version control"
echo "  ✅ .env is already in .gitignore"
echo "  🔐 Keep your database credentials secret"
echo "  📝 Use different credentials for dev/prod"
echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${PURPLE}Happy coding! 🚀${NC}"
echo ""
