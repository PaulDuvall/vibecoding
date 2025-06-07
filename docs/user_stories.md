# User Stories – AI Engineering Platform

This document defines user stories for the AI Engineering platform, derived from the Product Requirements Document (PRD). Each story includes a unique ID, user story, acceptance criteria, and traceability links (to be updated as implementation progresses).

---

## US-001: AI Engineering Content Aggregation ✅ IMPLEMENTED
**As** a developer transitioning to AI Engineering,
**I want** the system to fetch and parse content daily from AI Engineering tool sources (Cursor, Windsurf, Claude Code, Copilot, Jules, r/AIDevelopment, Hacker News AI threads),
**so that** I receive curated updates focused on AI development tools and practices.

**Acceptance Criteria:**
- System fetches content from all listed sources at least once per day
- Sources are configurable
- Fetch failures are logged and surfaced in monitoring

---

## US-002: AI-Powered Summarization with Performance Optimization ✅ IMPLEMENTED
**As** a recipient of the AI Engineering digest,
**I want** the system to generate concise, context-rich summaries using async processing and smart batching,
**so that** I can quickly understand key AI Engineering insights with 3-5x faster processing and 30-40% cost reduction.

**Acceptance Criteria:**
- Summaries are generated for each fetched article
- Summaries retain key technical insights and hyperlinks
- Each summary is capped at ~100–150 words

---

## US-003: AI Engineering Weekly Newsletter ✅ IMPLEMENTED
**As** a developer learning AI Engineering,
**I want** to receive a weekly HTML email digest with tool updates, implementation patterns, and platform development insights,
**so that** I can stay current with AI-assisted development trends and practices.

**Acceptance Criteria:**
- Email is sent daily via SendGrid
- Email contains digest title, date, source attribution, and inline links
- Layout is mobile-optimized

---

## US-004: Data Persistence of Digests ⚠️ NOT IMPLEMENTED
**As** a system operator,
**I want** each day’s fetched feed and website summaries to be persisted in an AWS database (DynamoDB or Aurora),
**so that** historical digests are reliably stored and retrievable.

**Acceptance Criteria:**
- Each digest is stored with a date (YYYY-MM-DD) key
- Schema includes feed source, title, URL, summary, and timestamp
- Data durability is at least 99.9%

---

## US-005: Web UI – History Page ⚠️ NOT IMPLEMENTED
**As** a user,
**I want** a “History” page on the website that displays past digests by date,
**so that** I can review previous summaries easily.

**Acceptance Criteria:**
- Web page lists digests by date
- Supports querying by date or date range
- Page loads in under 500 ms

---

## US-006: API Endpoints for Digest CRUD ⚠️ NOT IMPLEMENTED
**As** a developer or integration,
**I want** Lambda/API endpoints for inserting and retrieving digests,
**so that** the system can be extended and integrated with other services.

**Acceptance Criteria:**
- POST /digest inserts a new digest
- GET /digest/{date} retrieves a digest by date
- GET /digest lists digests over a date range
- Endpoints are secured with least-privilege IAM

---

## US-007: Reliability & Monitoring ✅ IMPLEMENTED
**As** an operator,
**I want** robust error handling and monitoring,
**so that** failures are detected, logged, and surfaced promptly.

**Acceptance Criteria:**
- Retry logic for network/API timeouts
- Graceful degradation if a source fails
- Email delivery/reporting failures are logged
- Monitoring includes GitHub Actions status, SendGrid delivery, and API usage metrics

---

## US-008: Tool Comparison Matrix ⚠️ NOT IMPLEMENTED
**As** a developer choosing AI Engineering tools,
**I want** an interactive comparison grid of IDE plugins (Cursor vs. Windsurf vs. Claude Code vs. GitHub Copilot),
**so that** I can make informed decisions based on feature analysis, model performance, and community reviews.

**Acceptance Criteria:**
- Comparison matrix covers autocomplete, refactoring, test generation, debugging features
- Includes model performance comparisons (Claude vs. GPT vs. Gemini)
- Supports community-submitted prompts and performance ratings
- Updates automatically with new tool releases

---

## US-009: AI Engineering Roadmap ⚠️ NOT IMPLEMENTED
**As** a traditional software engineer,
**I want** a structured learning path from SWE to AI Engineer,
**so that** I can systematically develop AI Engineering skills.

**Acceptance Criteria:**
- Roadmap covers foundations (LLMs, tokens, embeddings, prompt engineering)
- Includes tools mastery section (IDE setup, agent workflows, automation)
- Provides advanced topics (custom agents, fine-tuning, production deployment)
- Links to practical examples and starter kits

---

## US-010: Behind-the-Build Devlogs ⚠️ NOT IMPLEMENTED
**As** a developer learning AI-assisted development,
**I want** transparent documentation showing how platform features are built with AI tools,
**so that** I can learn from real implementation examples.

**Acceptance Criteria:**
- Each platform feature documented with prompts → code → results
- Includes real tool usage examples (Windsurf sessions, Claude Code interactions)
- Documents iteration stories, challenges, failures, and AI-assisted solutions
- Shows performance optimization processes

---

## US-011: Starter Kits & Templates ⚠️ NOT IMPLEMENTED
**As** a developer adopting AI Engineering practices,
**I want** AI-built development resources and templates,
**so that** I can quickly start projects using best practices.

**Acceptance Criteria:**
- ATDD + AI pipeline templates for test-driven development with AI agents
- Multi-tool setup guides (Cursor + Claude Code + GitHub Actions)
- Performance monitoring templates for AI cost tracking and optimization
- All templates include implementation documentation

---

## US-012: Performance & Success Metrics ✅ IMPLEMENTED
**As** a stakeholder,
**I want** the system to meet key performance and reliability targets,
**so that** it delivers value with high quality.

**Acceptance Criteria:**
- Digest retrieval latency is < 1 second
- Data durability is ≥ 99.9%
- Web “History” page loads in < 500 ms
- Newsletter open rate > 50%, website CTR > 10%, time on site > 2 minutes, return visitor rate > 30%
- Monthly active users > 5,000 within 6 months, newsletter subscribers > 1,000 within 3 months
- API response time < 2 seconds, daily content freshness > 90%, <1% failure rate in CI/CD

---

## US-201: Log OpenAI Token Usage Per Summarization ⚠️ PARTIALLY IMPLEMENTED
**As** a system maintainer,
**I want** each OpenAI API call in the summarization process to log the actual prompt, completion, and total token usage,
**so that** I can accurately track usage per item.

**Acceptance Criteria:**
- Each call to the OpenAI API logs:
  - Prompt tokens used
  - Completion tokens used
  - Total tokens used
- Logs are written to the application log and/or a structured in-memory report for aggregation.

**Test Coverage:**
- Unit tests verify that after a summarization call, the returned usage metrics are logged and/or recorded.
- Mock OpenAI responses in tests to ensure logging works without real API calls.

---

## US-202: Aggregate and Calculate Total OpenAI Usage and Cost Per Run ⚠️ PARTIALLY IMPLEMENTED
**As** a system maintainer,
**I want** the system to aggregate total OpenAI token usage and calculate the total cost for each run based on current pricing,
**so that** I can monitor and control operational expenses.

**Acceptance Criteria:**
- The system aggregates all prompt, completion, and total tokens used in a run.
- The system calculates the cost using actual token counts and current model pricing (e.g., gpt-4o).
- The cost calculation logic is encapsulated and unit-testable.

**Test Coverage:**
- Unit tests verify correct aggregation and cost calculation for various token usage scenarios.
- Tests include different pricing rates and edge cases (e.g., zero usage).

---

## US-203: Display OpenAI Usage and Cost in Digest Email ⚠️ PARTIALLY IMPLEMENTED
**As** a digest recipient,
**I want** the total OpenAI usage and cost for the run to be included in the daily digest email,
**so that** I am always aware of the operational cost of each digest.

**Acceptance Criteria:**
- The digest email includes a section at the bottom showing:
  - Total prompt tokens
  - Total completion tokens
  - Total tokens
  - Total cost (USD)
- The information is clearly formatted and easy to find.

**Test Coverage:**
- Automated tests verify that the email includes the correct usage and cost information for a simulated run.
- Tests check for proper formatting and presence of all required fields.

---

## US-204: Document OpenAI Usage and Cost Tracking Feature ⚠️ PARTIALLY IMPLEMENTED
**As** a user or maintainer,
**I want** documentation describing how OpenAI usage and cost tracking works,
**so that** I understand how to interpret the reported values and update pricing if needed.

**Acceptance Criteria:**
- The README and/or user documentation describes:
  - How usage and cost are tracked and reported
  - Where to find the cost in the email
  - How to update pricing logic if OpenAI rates change

**Test Coverage:**
- Documentation review checklist ensures all new features and fields are described.
- Traceability matrix links this story to the relevant documentation files.

---

## US-301: Externalize Feed Configuration for Easy Management ✅ IMPLEMENTED
**As** a content curator or system administrator,
**I want** to configure RSS feeds through external JSON or YAML files instead of hardcoded lists,
**so that** I can easily add, remove, or modify feed sources without changing source code.

**Acceptance Criteria:**
- System supports external configuration files in JSON and YAML formats
- Configuration files include feed URL, source name, category, and enabled/disabled status
- System falls back to hardcoded feeds when no external configuration exists
- Configuration validation prevents malformed files from breaking the system

**Test Coverage:**
- ATDD scenarios verify external configuration loading with valid JSON/YAML files
- Tests validate fallback behavior when configuration files are missing or malformed
- Scenarios ensure disabled feeds are properly excluded from processing

---

## US-302: Support Environment-Based Configuration Paths ✅ IMPLEMENTED
**As** a deployment engineer,
**I want** to specify custom configuration file paths via environment variables,
**so that** I can deploy different feed configurations across environments (dev, staging, prod).

**Acceptance Criteria:**
- `VIBE_CONFIG_PATH` environment variable overrides default configuration file locations
- System searches for configuration files in multiple default locations
- Custom paths support both absolute and relative file paths
- Clear error messages when specified configuration files cannot be found

**Test Coverage:**
- ATDD scenarios verify environment variable configuration path loading
- Tests validate behavior with valid and invalid custom paths
- Scenarios ensure proper error handling for missing custom configuration files

---

## US-303: Categorize and Enable/Disable Individual Feeds ✅ IMPLEMENTED
**As** a content curator,
**I want** to organize feeds by category and selectively enable or disable them,
**so that** I can control content sources without removing them from the configuration.

**Acceptance Criteria:**
- Feed configuration supports categorization (AI, DevTools, Community, YouTube, Blogs)
- Individual feeds can be enabled or disabled via configuration
- System processes only enabled feeds during digest generation
- Categories provide organizational structure for large feed lists

**Test Coverage:**
- ATDD scenarios verify category-based feed organization
- Tests validate that disabled feeds are excluded from processing
- Scenarios ensure enabled feeds from all categories are processed correctly

---

## US-304: Maintain Backward Compatibility with Hardcoded Feeds ✅ IMPLEMENTED
**As** a system maintainer,
**I want** the external configuration system to work seamlessly with existing hardcoded feed lists,
**so that** the system continues to function without any configuration changes.

**Acceptance Criteria:**
- System works identically to before when no external configuration exists
- All existing hardcoded feeds are processed with their original source names
- No breaking changes to existing API or behavior
- Smooth migration path from hardcoded to external configuration

**Test Coverage:**
- ATDD scenarios verify identical behavior with and without external configuration
- Tests validate that all existing feeds continue to work
- Scenarios ensure existing source name mappings remain intact

---

## US-305: Validate Configuration File Format and Provide Clear Error Messages ✅ IMPLEMENTED
**As** a system administrator,
**I want** the system to validate configuration files and provide clear error messages for issues,
**so that** I can quickly identify and fix configuration problems.

**Acceptance Criteria:**
- System validates required fields (url, source_name) in configuration files
- Clear error messages indicate specific validation failures and their locations
- Malformed JSON/YAML files are handled gracefully with helpful error messages
- Configuration validation prevents system crashes from bad configuration data

**Test Coverage:**
- ATDD scenarios verify validation error handling for various malformed configurations
- Tests validate specific error messages for missing required fields
- Scenarios ensure system graceful degradation when configuration validation fails

---

# Traceability Matrix

This document maps user stories to their implementation files, test files, and ATDD scenarios following the ATDD-driven AI development approach described in [Paul Duvall's blog post](https://www.paulmduvall.com/atdd-driven-ai-development-how-prompting-and-tests-steer-the-code/).

| User Story ID | Requirement / Acceptance Criteria | Implementation File(s) | Test File(s) | ATDD Scenario(s) | Notes |
|--------------|-----------------------------------|------------------------|--------------|------------------|-------|
| US-001 | AI Engineering Content Aggregation | [src/feeds.py](../src/feeds.py), [src/vibe_digest.py](../src/vibe_digest.py), [src/aws_blog_search.py](../src/aws_blog_search.py) | [tests/test_vibe_digest.py](../tests/test_vibe_digest.py), [tests/test_aws_blog_search.py](../tests/test_aws_blog_search.py) | US-001 US-003 - Complete daily digest workflow execution<br>US-001 - Content deduplication across sources<br>US-001 - AWS blog search integration | RSS feed fetching, content aggregation, deduplication |
| US-002 | AI-Powered Summarization with Performance Optimization | [src/summarize.py](../src/summarize.py), [src/vibe_digest.py](../src/vibe_digest.py) | [tests/test_vibe_digest.py](../tests/test_vibe_digest.py), [tests/test_optimizations.py](../tests/test_optimizations.py) | US-002 US-007 - OpenAI API rate limiting scenario<br>US-002 US-012 - Performance requirements for digest generation<br>US-002 - Digest content quality validation | OpenAI summarization, async processing, rate limiting |
| US-003 | AI Engineering Weekly Newsletter | [src/email_utils.py](../src/email_utils.py), [src/vibe_digest.py](../src/vibe_digest.py) | [tests/test_vibe_digest.py](../tests/test_vibe_digest.py), [tests/test_acceptance.py](../tests/test_acceptance.py) | US-001 US-003 - Complete daily digest workflow execution<br>US-003 US-007 - Email delivery failure handling<br>US-003 - Mobile-optimized email formatting | Email generation, mobile optimization, delivery |
| US-007 | Reliability & Monitoring | [src/vibe_digest.py](../src/vibe_digest.py), [src/feeds.py](../src/feeds.py), [src/summarize.py](../src/summarize.py) | [tests/test_integration.py](../tests/test_integration.py), [tests/test_vibe_digest.py](../tests/test_vibe_digest.py) | US-007 - Digest generation with some feed failures<br>US-002 US-007 - OpenAI API rate limiting scenario<br>US-003 US-007 - Email delivery failure handling | Error handling, retry logic, graceful degradation |
| US-012 | Performance & Success Metrics | [src/vibe_digest.py](../src/vibe_digest.py), [src/summarize.py](../src/summarize.py) | [tests/test_optimizations.py](../tests/test_optimizations.py), [tests/test_integration.py](../tests/test_integration.py) | US-002 US-012 - Performance requirements for digest generation | Performance requirements, latency targets |
| US-201 | Log OpenAI Token Usage Per Summarization | [src/summarize.py](../src/summarize.py), [src/vibe_digest.py](../src/vibe_digest.py) | [tests/test_summarize.py](../tests/test_summarize.py) | N/A | Token usage tracking |
| US-202 | Aggregate and Calculate Total OpenAI Usage and Cost Per Run | [src/vibe_digest.py](../src/vibe_digest.py) | [tests/test_vibe_digest.py](../tests/test_vibe_digest.py) | N/A | Cost calculation |
| US-203 | Display OpenAI Usage and Cost in Digest Email | [src/email_utils.py](../src/email_utils.py), [src/vibe_digest.py](../src/vibe_digest.py) | [tests/test_email_utils.py](../tests/test_email_utils.py) | N/A | Email cost display |
| US-204 | Document OpenAI Usage and Cost Tracking Feature | [README.md](../README.md), docs/user_stories.md | N/A | N/A | Documentation |
| US-301 | Externalize Feed Configuration for Easy Management | [src/config_loader.py](../src/config_loader.py), [src/feeds.py](../src/feeds.py) | [tests/features/externalized_config.feature](../tests/features/externalized_config.feature), [tests/features/steps/config_steps.py](../tests/features/steps/config_steps.py) | US-301 - Load feed configuration from external JSON file<br>US-301 - Fallback to default configuration when external config is missing<br>US-301 - Validate configuration file format | External JSON/YAML config, feed management, validation |
| US-302 | Support Environment-Based Configuration Paths | [src/config_loader.py](../src/config_loader.py) | [tests/features/externalized_config.feature](../tests/features/externalized_config.feature), [tests/features/steps/config_steps.py](../tests/features/steps/config_steps.py) | US-302 - Load configuration from environment variable path | Environment variable configuration, deployment flexibility |
| US-303 | Categorize and Enable/Disable Individual Feeds | [src/config_loader.py](../src/config_loader.py), [src/feeds.py](../src/feeds.py), [feeds_config.json](../feeds_config.json) | [tests/features/externalized_config.feature](../tests/features/externalized_config.feature), [tests/features/steps/config_steps.py](../tests/features/steps/config_steps.py) | US-303 - Handle disabled feeds in configuration<br>US-303 - Add new feed category via external configuration | Feed categorization, selective enabling/disabling |
| US-304 | Maintain Backward Compatibility with Hardcoded Feeds | [src/config_loader.py](../src/config_loader.py), [src/feeds.py](../src/feeds.py) | [tests/features/externalized_config.feature](../tests/features/externalized_config.feature), [tests/features/steps/config_steps.py](../tests/features/steps/config_steps.py) | US-304 - Preserve backward compatibility with hardcoded feeds | Backward compatibility, migration support |
| US-305 | Validate Configuration File Format and Provide Clear Error Messages | [src/config_loader.py](../src/config_loader.py) | [tests/features/externalized_config.feature](../tests/features/externalized_config.feature), [tests/features/steps/config_steps.py](../tests/features/steps/config_steps.py) | US-305 - Validate configuration file format<br>US-305 - Configuration file hot-reload during development | Configuration validation, error handling, developer experience |
| US-XXX | CI/CD Security Controls | [.github/workflows/vibe-coding-digest.yml](../.github/workflows/vibe-coding-digest.yml) | N/A | N/A | Gitleaks scan job blocks workflow on secret detection |

---

## ATDD Implementation Details

### Behave Feature File Structure
- **Main Digest Workflow**: [`tests/features/digest_workflow.feature`](../tests/features/digest_workflow.feature)
  - **Scenarios**: 9 scenarios covering core user stories
  - **Step Definitions**: [`tests/features/steps/digest_steps.py`](../tests/features/steps/digest_steps.py)
- **External Configuration**: [`tests/features/externalized_config.feature`](../tests/features/externalized_config.feature)
  - **Scenarios**: 10 scenarios covering configuration management
  - **Step Definitions**: [`tests/features/steps/config_steps.py`](../tests/features/steps/config_steps.py)
- **Environment Setup**: [`tests/features/environment.py`](../tests/features/environment.py)

### User Story to ATDD Scenario Mapping

1. **US-001 (Content Aggregation)**:
   - Complete daily digest workflow execution
   - Content deduplication across sources  
   - AWS blog search integration

2. **US-002 (AI-Powered Summarization)**:
   - OpenAI API rate limiting scenario
   - Performance requirements for digest generation
   - Digest content quality validation

3. **US-003 (Newsletter Delivery)**:
   - Complete daily digest workflow execution
   - Email delivery failure handling
   - Mobile-optimized email formatting

4. **US-007 (Reliability & Monitoring)**:
   - Digest generation with some feed failures
   - OpenAI API rate limiting scenario
   - Email delivery failure handling

5. **US-012 (Performance & Success Metrics)**:
   - Performance requirements for digest generation

6. **US-301 (Externalize Feed Configuration)**:
   - Load feed configuration from external JSON file
   - Fallback to default configuration when external config is missing
   - Validate configuration file format

7. **US-302 (Environment-Based Configuration)**:
   - Load configuration from environment variable path

8. **US-303 (Categorize and Enable/Disable Feeds)**:
   - Handle disabled feeds in configuration
   - Add new feed category via external configuration

9. **US-304 (Backward Compatibility)**:
   - Preserve backward compatibility with hardcoded feeds

10. **US-305 (Configuration Validation)**:
    - Validate configuration file format
    - Configuration file hot-reload during development

### ATDD Test Execution
- **All Tests**: `./run.sh all` runs all tests including ATDD scenarios
- **Main Digest ATDD**: `.venv/bin/python -m behave tests/features/digest_workflow.feature`
- **Configuration ATDD**: `.venv/bin/python -m behave tests/features/externalized_config.feature`
- **Individual Scenario**: `.venv/bin/python -m behave tests/features/<feature_file>:<line_number>`
- **Coverage**: HTML reports generated in `htmlcov/index.html`

---

## CI/CD Security Controls

- **Automated secrets scanning** is implemented using Gitleaks in the GitHub Actions workflow ([`.github/workflows/vibe-coding-digest.yml`](../.github/workflows/vibe-coding-digest.yml)), per [`.cicdrules.md`](../.cicdrules.md) requirements.
- If secrets are found, the workflow fails and downstream jobs are blocked.
- This control satisfies the "build quality in" and security automation requirements outlined in `.cicdrules.md`.

---

## Test Architecture Summary

- **Unit Tests**: 35+ pytest tests covering individual components
- **Integration Tests**: 4+ pytest tests covering end-to-end workflows  
- **ATDD Tests**: 19 Behave scenarios covering user story acceptance criteria
  - 9 scenarios for main digest workflow (US-001, US-002, US-003, US-007, US-012)
  - 10 scenarios for external configuration (US-301, US-302, US-303, US-304, US-305)
- **Performance Tests**: OpenAI optimization and async processing tests
- **Configuration Tests**: External configuration validation and loading tests
- **Coverage**: HTML reports generated in `htmlcov/index.html`

_Last updated: 2025-06-07_

