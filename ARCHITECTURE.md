# Vibe Coding Digest - Architecture Overview

## Project Structure

```
vibecoding/
├── src/                    # Main source code package
│   ├── __init__.py        # Package initialization with exports
│   ├── vibe_digest.py     # Main entry point and orchestration
│   ├── models.py          # Data models (DigestItem)
│   ├── feeds.py           # RSS feed configuration and fetching
│   ├── summarize.py       # OpenAI summarization logic
│   ├── email_utils.py     # SendGrid email functionality
│   └── aws_blog_search.py # AWS blog search functionality
├── tests/                 # Test suite
│   ├── test_vibe_digest.py     # Core functionality tests
│   ├── test_aws_blog_search.py # AWS blog search tests
│   └── test_integration.py     # End-to-end integration tests
├── .github/
│   └── workflows/
│       └── vibe-coding-digest.yml # CI/CD pipeline
├── pyproject.toml         # Modern Python package configuration
├── requirements.txt       # Runtime dependencies
└── run.sh                # Development utility script
```

## Key Components

### Core Modules

1. **`vibe_digest.py`** - Main orchestrator
   - Environment validation
   - Feed aggregation coordination
   - Content summarization
   - Email dispatch

2. **`models.py`** - Data structures
   - `DigestItem` class with type hints
   - Proper hash/equality implementations

3. **`feeds.py`** - RSS feed management
   - Feed URL configuration
   - Concurrent feed fetching
   - Source name mapping

4. **`summarize.py`** - AI summarization
   - OpenAI API integration
   - Comprehensive error handling
   - Configurable prompts

5. **`email_utils.py`** - Email delivery
   - SendGrid integration
   - HTML email formatting
   - Error handling

### Testing Infrastructure

- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end pipeline testing
- **Code Coverage**: Pytest-cov integration
- **Mocking**: Comprehensive external service mocking

### Development Tools

- **Type Hints**: Full type annotation coverage
- **Linting**: Flake8 with PEP8 compliance
- **Package Management**: Modern pyproject.toml configuration
- **Coverage Reporting**: HTML and terminal coverage reports

## Usage

### Development Setup
```bash
./run.sh setup  # Install dependencies and setup environment
./run.sh all    # Run linting, tests, and coverage
```

### Running the Digest
```bash
# As a module
python -m src.vibe_digest

# Or via package installation
pip install -e .
vibe-digest
```

### Running Tests
```bash
# With coverage
./run.sh test

# Basic pytest
pytest tests/

# Specific test file
pytest tests/test_integration.py -v
```

## Improvements Implemented

### Critical Issues Fixed
✅ Moved core modules from `.github/scripts/` to proper `src/` package structure  
✅ Updated all import statements to use relative imports  
✅ Removed placeholder `sample_module.py`  
✅ Fixed test imports to reference new module locations  

### High Priority Enhancements
✅ Created proper package management with `pyproject.toml`  
✅ Added comprehensive type hints throughout codebase  
✅ Implemented integration tests for full pipeline  
✅ Added code coverage reporting to development workflow  
✅ Updated CI/CD pipeline to use new structure  

### Technical Improvements
- **Better Error Handling**: Granular OpenAI API error catching
- **Type Safety**: Full typing.* annotation coverage
- **Test Coverage**: Integration and unit test expansion
- **Modern Packaging**: pyproject.toml with proper dependencies
- **Development Experience**: Enhanced run.sh with coverage reporting

## Configuration

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API access
- `SENDGRID_API_KEY`: SendGrid email service
- `EMAIL_FROM`: Verified sender email
- `EMAIL_TO`: Recipient email address

### Feed Configuration
RSS feeds and source mappings are configured in `src/feeds.py`:
- Core AI/Dev feeds
- GitHub Copilot related feeds  
- YouTube channels
- Reddit communities
- Blog feeds

## CI/CD Pipeline

The GitHub Actions workflow now:
1. Runs security checks (secrets scanning)
2. Installs dependencies 
3. Executes linting (flake8)
4. Runs full test suite with coverage
5. Executes the digest generation and email delivery

All tests must pass before the digest script runs, ensuring code quality and reliability.