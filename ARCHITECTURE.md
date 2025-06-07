# Vibe Coding Digest - Architecture Overview

## Project Structure

```
vibecoding/
├── src/                    # Main source code package
│   ├── __init__.py        # Package initialization with exports
│   ├── vibe_digest.py     # Main entry point and orchestration
│   ├── models.py          # Data models (DigestItem)
│   ├── feeds.py           # RSS feed configuration and fetching
│   ├── config_loader.py   # External configuration management
│   ├── summarize.py       # OpenAI summarization logic
│   ├── email_utils.py     # SendGrid email functionality
│   └── aws_blog_search.py # AWS blog search functionality
├── tests/                 # Test suite
│   ├── test_vibe_digest.py     # Core functionality tests
│   ├── test_aws_blog_search.py # AWS blog search tests
│   ├── test_integration.py     # End-to-end integration tests
│   └── features/              # ATDD feature specifications
│       ├── digest_workflow.feature      # Main digest workflow scenarios
│       ├── externalized_config.feature  # Configuration management scenarios
│       ├── environment.py               # Behave test environment setup
│       └── steps/                       # ATDD step definitions
│           ├── digest_steps.py          # Main workflow step definitions
│           └── config_steps.py          # Configuration step definitions
├── docs/                  # Project documentation
│   ├── user_stories.md    # User stories with acceptance criteria
│   ├── traceability_matrix.md # ATDD traceability documentation
│   └── prd.md            # Product Requirements Document
├── .github/
│   └── workflows/
│       └── vibe-coding-digest.yml # CI/CD pipeline
├── feeds_config.json      # Default external feed configuration
├── .attdrules.md         # ATDD/BDD development guidelines
├── pyproject.toml        # Modern Python package configuration
├── requirements.txt      # Runtime dependencies
└── run.sh               # Development utility script
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
   - Feed URL configuration (with external config integration)
   - Concurrent feed fetching
   - Source name mapping
   - Backward compatibility with hardcoded feeds

4. **`config_loader.py`** - Configuration management
   - External JSON/YAML configuration loading
   - Environment variable configuration paths
   - Feed categorization and enable/disable controls
   - Configuration validation and error handling

5. **`summarize.py`** - AI summarization
   - OpenAI API integration
   - Comprehensive error handling
   - Configurable prompts

6. **`email_utils.py`** - Email delivery
   - SendGrid integration
   - HTML email formatting
   - Error handling

### Testing Infrastructure

- **Unit Tests**: Individual component testing with pytest
- **Integration Tests**: End-to-end pipeline testing
- **ATDD Tests**: Behavior-driven acceptance testing with Behave
  - Feature specifications in Gherkin format
  - Comprehensive step definitions
  - User story traceability (US-001 through US-305)
- **Code Coverage**: Pytest-cov integration with HTML reports
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

**External Configuration (Recommended)**
- **Default Configuration**: `feeds_config.json` with 29 pre-configured feeds
- **Format Support**: JSON and YAML configuration files
- **Categorization**: AI, DevTools, Community, YouTube, Blogs
- **Environment Variables**: `VIBE_CONFIG_PATH` for custom configuration paths
- **Enable/Disable Controls**: Individual feed management without removal

**Configuration Structure**
```json
{
  "feeds": [
    {
      "url": "https://openai.com/news/rss.xml",
      "source_name": "OpenAI News",
      "category": "AI",
      "enabled": true
    }
  ]
}
```

**Backward Compatibility**
- Automatic fallback to hardcoded feeds in `src/feeds.py`
- Zero breaking changes for existing deployments
- Seamless migration path from hardcoded to external configuration

**Feed Sources Include**:
- Core AI/Dev feeds (Google Alerts, OpenAI, Anthropic)
- GitHub repositories and releases
- YouTube tech channels  
- Reddit communities (r/MachineLearning, r/programming)
- Developer tool blogs and release notes

## ATDD-Driven Development Approach

This project follows **Acceptance Test-Driven Development (ATDD)** methodology based on [Paul Duvall's ATDD-driven AI development approach](https://www.paulmduvall.com/atdd-driven-ai-development-how-prompting-and-tests-steer-the-code/).

### Key ATDD Principles
- **Specification-First Development**: Gherkin feature files define desired behavior before implementation
- **User Story Traceability**: Each scenario maps to specific user stories (US-001 through US-305)  
- **Real Implementation Testing**: Tests call actual business logic with mocked external dependencies
- **Living Documentation**: Feature files serve as executable specifications

### ATDD Test Structure
```
tests/features/
├── digest_workflow.feature      # Core digest functionality (9 scenarios)
├── externalized_config.feature  # Configuration management (10 scenarios)
├── environment.py               # Behave test environment setup
└── steps/
    ├── digest_steps.py          # Main workflow step definitions
    └── config_steps.py          # Configuration step definitions
```

### User Story Coverage
- **US-001 to US-012**: Core digest functionality
- **US-201 to US-204**: OpenAI usage tracking and cost monitoring
- **US-301 to US-305**: External configuration management

### Traceability Matrix
Complete mapping between user stories, implementation files, test files, and ATDD scenarios documented in [`docs/traceability_matrix.md`](docs/traceability_matrix.md).

## CI/CD Pipeline

The GitHub Actions workflow now:
1. Runs security checks (secrets scanning via Gitleaks)
2. Installs dependencies (including PyYAML for configuration support)
3. Executes linting (flake8 for PEP8 compliance)
4. Runs comprehensive test suite:
   - Unit tests with pytest
   - Integration tests for end-to-end workflows
   - ATDD scenarios with Behave
   - Code coverage reporting
5. Executes the digest generation and email delivery

All tests must pass before the digest script runs, ensuring code quality and reliability. The pipeline enforces the ATDD principle that **failing acceptance tests block deployment**.