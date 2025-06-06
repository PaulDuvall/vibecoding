#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default command if none provided
CMD=${1:-all}

# Function to display usage
show_usage() {
    echo "Usage: $0 [command]"
    echo "Commands:"
    echo "  setup     - Set up the development environment"
    echo "  test      - Run tests"
    echo "  lint      - Run linting"
    echo "  all       - Run setup, lint, and test (default)"
    echo "  clean     - Clean up virtual environment"
    echo "  help      - Show this help message"
}

# Function to setup the environment
setup_env() {
    echo -e "${GREEN}Setting up development environment...${NC}"
    
    # Check for Python 3.11
    if ! command -v python3.11 &> /dev/null; then
        echo -e "${YELLOW}Python 3.11 is required but not installed. Please install it first.${NC}"
        exit 1
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo -e "${GREEN}Creating virtual environment...${NC}"
        python3.11 -m venv .venv
    fi
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Upgrade pip and install dependencies
    echo -e "${GREEN}Installing dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Install development dependencies
    pip install pytest pytest-mock flake8 pytest-cov
    
    echo -e "${GREEN}✓ Development environment is ready!${NC}"
}

# Function to run tests
run_tests() {
    echo -e "${GREEN}Running tests with coverage...${NC}"
    source .venv/bin/activate
    PYTHONPATH=$PYTHONPATH:$(pwd) pytest -v --cov=src --cov-report=html --cov-report=term tests/
    echo -e "${GREEN}✓ Coverage report generated in htmlcov/index.html${NC}"
}

# Function to run linting
run_lint() {
    echo -e "${GREEN}Running linting...${NC}"
    source .venv/bin/activate
    flake8 --exit-zero .
    echo -e "${GREEN}✓ Linting completed (warnings do not fail the build)!${NC}"
}

# Function to clean up
clean() {
    echo -e "${YELLOW}Cleaning up...${NC}"
    if [ -d ".venv" ]; then
        echo "Removing virtual environment..."
        rm -rf .venv
    fi
    echo -e "${GREEN}✓ Clean complete!${NC}"
}

# Main script execution
case $CMD in
    setup)
        setup_env
        ;;
    test)
        run_tests
        ;;
    lint)
        run_lint
        ;;
    all)
        setup_env
        run_lint
        run_tests
        ;;
    clean)
        clean
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        echo -e "${YELLOW}Unknown command: $CMD${NC}"
        show_usage
        exit 1
        ;;
esac

echo -e "${GREEN}✓ Script completed successfully!${NC}"

# 5. Summarize
if [ $? -eq 0 ]; then
    echo "All lint and tests passed!"
else
    echo "Lint or tests failed."
    exit 1
fi
