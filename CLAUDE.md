# Project Context for Claude Code: CLAUDE.md

This file provides Claude Code with essential project context, rules, and implementation details. This is derived from the Windsurf-specific `.windsurfrules.md` but adapted for Claude Code workflow.

## Project Overview

**Vibe Coding Digest** is an automated content aggregation and summarization tool that delivers curated, daily email digests of the most relevant developments in AI, developer tools, and emerging technology.

### Key Components
- **RSS Feed Aggregation**: Multi-source content collection with concurrent processing from 29+ feeds
- **External Configuration**: JSON/YAML feed management with categorization and enable/disable controls
- **AI Summarization**: OpenAI-powered content summarization with error handling
- **Email Delivery**: SendGrid integration for HTML digest delivery
- **AWS Blog Search**: Targeted search functionality for AWS-specific content
- **ATDD Test Suite**: Comprehensive unit, integration, and acceptance testing with user story traceability

## Project Structure

```
vibecoding/
├── src/                    # Main source package
│   ├── __init__.py        # Package exports and metadata
│   ├── vibe_digest.py     # Main orchestration and entry point
│   ├── models.py          # Data models (DigestItem)
│   ├── feeds.py           # RSS feed management and fetching
│   ├── config_loader.py   # External configuration management
│   ├── summarize.py       # OpenAI summarization logic
│   ├── email_utils.py     # SendGrid email functionality
│   └── aws_blog_search.py # AWS blog search functionality
├── tests/                 # Comprehensive test suite
│   ├── test_vibe_digest.py     # Core functionality tests
│   ├── test_aws_blog_search.py # AWS search tests
│   ├── test_integration.py     # End-to-end pipeline tests
│   ├── test_optimizations.py   # Performance optimization tests
│   └── features/              # ATDD feature specifications
│       ├── digest_workflow.feature      # Main digest scenarios
│       ├── externalized_config.feature  # Configuration scenarios
│       ├── environment.py               # Behave setup
│       └── steps/                       # Step definitions
│           ├── digest_steps.py          # Main workflow steps
│           └── config_steps.py          # Configuration steps
├── docs/                  # Project documentation
│   ├── user_stories.md    # User stories with acceptance criteria
│   ├── traceability_matrix.md # ATDD traceability documentation
│   └── prd.md            # Product Requirements Document
├── .github/
│   └── workflows/
│       └── vibe-coding-digest.yml # CI/CD automation
├── feeds_config.json      # Default external feed configuration
├── .attdrules.md         # ATDD/BDD development guidelines
├── pyproject.toml         # Modern Python package configuration
├── requirements.txt       # Runtime dependencies (includes PyYAML)
└── run.sh                # Development utility script
```

## Development Standards

### Python Environment
- **Required Version**: Python 3.11 (enforced via `run.sh`)
- **Virtual Environment**: All operations use `.venv` managed by `run.sh`
- **Package Management**: Uses modern `pyproject.toml` configuration
- **Import Strategy**: Absolute imports (`from src.module import ...`)

### Code Quality Requirements
- **Type Hints**: Full type annotation coverage required
- **Linting**: Flake8 compliance enforced (PEP8)
- **Testing**: Pytest with coverage reporting
- **Documentation**: Comprehensive docstrings and comments

### Testing Standards
- **ATDD-Driven Development**: Write Gherkin feature specifications before implementation
- **Test Coverage**: Pytest-cov integration with HTML reports  
- **Test Types**: Unit, integration, and acceptance tests with user story traceability
- **Mock Strategy**: Comprehensive external service mocking
- **User Story Mapping**: Each test maps to specific user stories (US-001 through US-305)

## Development Workflow

### Setup and Execution
```bash
# Environment setup
./run.sh setup

# Run all checks (lint + test + coverage)
./run.sh all

# Individual operations
./run.sh lint    # Flake8 linting
./run.sh test    # Tests with coverage
./run.sh clean   # Environment cleanup
```

### Running the Digest
```bash
# As module (development)
export PYTHONPATH=$PYTHONPATH:$(pwd)
python -m src.vibe_digest

# Via package installation
pip install -e .
vibe-digest
```

## Environment Configuration

### Required Environment Variables
```bash
OPENAI_API_KEY      # OpenAI API access for summarization
SENDGRID_API_KEY    # SendGrid email service API key
EMAIL_FROM          # Verified sender email address
EMAIL_TO            # Recipient email address
```

### Feed Configuration

**External Configuration System (Recommended)**
- **Configuration Files**: Support for JSON and YAML formats (`feeds_config.json`, `feeds_config.yaml`)
- **Environment Variables**: `VIBE_CONFIG_PATH` for custom configuration file paths
- **Feed Management**: Individual enable/disable controls without removal
- **Categorization**: Organize feeds by AI, DevTools, Community, YouTube, Blogs
- **Validation**: Comprehensive error checking with helpful error messages

**Default Configuration**
- 29 pre-configured feeds across all categories in `feeds_config.json`
- Includes Google Alerts, RSS feeds, GitHub releases, YouTube channels
- Backward compatible fallback to hardcoded feeds in `src/feeds.py`

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

## Testing Strategy

### Test Organization
- **Unit Tests**: Individual component testing with mocks
- **Integration Tests**: End-to-end pipeline validation
- **Coverage Reporting**: HTML and terminal coverage reports
- **CI/CD Integration**: Automated testing on all pushes

### Mock Patterns
- External APIs (OpenAI, SendGrid) fully mocked
- Feed parsing with controlled test data
- Environment variable injection for testing
- Date/time mocking for consistent outputs

## CI/CD Pipeline

### GitHub Actions Workflow
1. **Security Checks**: Secrets scanning and SAST
2. **Environment Setup**: Python 3.11 + dependency installation
3. **Quality Checks**: Linting (flake8) and testing (pytest)
4. **Digest Execution**: Automated daily digest generation
5. **Email Delivery**: SendGrid integration for distribution

### Quality Gates
- All tests must pass before deployment
- Linting compliance required
- Coverage reporting included
- No secrets in codebase (automated scanning)

## Architectural Improvements Implemented

### Recent Enhancements
✅ **Module Structure**: Moved from `.github/scripts/` to proper `src/` package  
✅ **Type Safety**: Added comprehensive type hints throughout  
✅ **Package Management**: Modern `pyproject.toml` configuration  
✅ **Testing Infrastructure**: Integration tests and coverage reporting  
✅ **Development Tools**: Enhanced `run.sh` with coverage integration  

### Code Organization
- **Proper Imports**: Absolute imports for all internal modules
- **Package Exports**: Clean `__init__.py` with defined `__all__`
- **Error Handling**: Granular OpenAI API error catching
- **Modular Design**: Clear separation of concerns

## Documentation Standards

### Code Documentation
- **Docstrings**: Comprehensive function and class documentation
- **Type Hints**: Full typing coverage for better IDE support
- **Comments**: Clear explanations for complex logic
- **Examples**: Usage patterns documented in docstrings

### Project Documentation
- **Architecture Overview**: `ARCHITECTURE.md` for technical details
- **User Stories**: `docs/user_stories.md` for requirements
- **Traceability**: `docs/traceability_matrix.md` for implementation tracking

## Security Practices

### Secret Management
- No credentials in codebase
- Environment variable injection
- `.gitignore` properly configured
- Automated secrets scanning in CI/CD

### API Security
- Proper error handling for API failures
- Rate limiting considerations
- Timeout configurations
- Retry logic with exponential backoff

## Performance Considerations

### Optimization Strategies
- **Concurrent Processing**: ThreadPoolExecutor for feed fetching
- **Connection Pooling**: HTTP connection reuse
- **Caching**: Potential for feed caching implementation
- **Rate Limiting**: Respectful API usage patterns

## Troubleshooting Common Issues

### Import Errors
- Ensure `PYTHONPATH` includes project root
- Use absolute imports: `from src.module import ...`
- Verify virtual environment activation

### Test Failures
- Check environment variable setup in tests
- Ensure mocks are properly configured
- Verify test isolation (no shared state)

### API Issues
- Validate environment variables are set
- Check network connectivity for external APIs
- Review rate limiting and timeout settings

## Future Enhancement Areas

### Medium Priority
- Configuration externalization
- Enhanced error monitoring
- Performance optimization
- CLI interface expansion

### Low Priority
- Docker containerization
- Template customization
- Multi-format output support
- Advanced caching strategies

---

**Last Updated**: 2025-01-06  
**Python Version**: 3.11  
**Package Version**: 1.0.0