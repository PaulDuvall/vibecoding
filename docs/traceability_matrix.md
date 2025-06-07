# Traceability Matrix

This document maps user stories to their implementation files, test files, and ATDD scenarios following the ATDD-driven AI development approach described in [Paul Duvall's blog post](https://www.paulmduvall.com/atdd-driven-ai-development-how-prompting-and-tests-steer-the-code/).

| User Story ID | Requirement / Acceptance Criteria | Implementation File(s) | Test File(s) | ATDD Scenario(s) | Notes |
|--------------|-----------------------------------|------------------------|--------------|------------------|-------|
| US-001 | AI Engineering Content Aggregation | src/feeds.py, src/vibe_digest.py, src/aws_blog_search.py | tests/test_vibe_digest.py, tests/test_aws_blog_search.py | US-001 US-003 - Complete daily digest workflow execution<br>US-001 - Content deduplication across sources<br>US-001 - AWS blog search integration | RSS feed fetching, content aggregation, deduplication |
| US-002 | AI-Powered Summarization with Performance Optimization | src/summarize.py, src/vibe_digest.py | tests/test_vibe_digest.py, tests/test_optimizations.py | US-002 US-007 - OpenAI API rate limiting scenario<br>US-002 US-012 - Performance requirements for digest generation<br>US-002 - Digest content quality validation | OpenAI summarization, async processing, rate limiting |
| US-003 | AI Engineering Weekly Newsletter | src/email_utils.py, src/vibe_digest.py | tests/test_vibe_digest.py, tests/test_acceptance.py | US-001 US-003 - Complete daily digest workflow execution<br>US-003 US-007 - Email delivery failure handling<br>US-003 - Mobile-optimized email formatting | Email generation, mobile optimization, delivery |
| US-007 | Reliability & Monitoring | src/vibe_digest.py, src/feeds.py, src/summarize.py | tests/test_integration.py, tests/test_vibe_digest.py | US-007 - Digest generation with some feed failures<br>US-002 US-007 - OpenAI API rate limiting scenario<br>US-003 US-007 - Email delivery failure handling | Error handling, retry logic, graceful degradation |
| US-012 | Performance & Success Metrics | src/vibe_digest.py, src/summarize.py | tests/test_optimizations.py, tests/test_integration.py | US-002 US-012 - Performance requirements for digest generation | Performance requirements, latency targets |
| US-XXX | CI/CD Security Controls | .github/workflows/vibe-coding-digest.yml | N/A | N/A | Gitleaks scan job blocks workflow on secret detection |

---

## ATDD Implementation Details

### Behave Feature File Structure
- **File**: `tests/features/digest_workflow.feature`
- **Scenarios**: 9 scenarios covering core user stories
- **Step Definitions**: `tests/features/steps/digest_steps.py`
- **Environment Setup**: `tests/features/environment.py`

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

### ATDD Test Execution
- **Command**: `./run.sh all` runs all tests including ATDD scenarios
- **Individual Scenario**: `.venv/bin/python -m behave tests/features/digest_workflow.feature:<line_number>`
- **Coverage**: 41 tests passing with 55% code coverage

---

## CI/CD Security Controls

- **Automated secrets scanning** is implemented using Gitleaks in the GitHub Actions workflow ([`.github/workflows/vibe-coding-digest.yml`](../.github/workflows/vibe-coding-digest.yml)), per `.cicdrules.md` requirements.
- If secrets are found, the workflow fails and downstream jobs are blocked.
- This control satisfies the "build quality in" and security automation requirements outlined in `.cicdrules.md`.

---

## Test Architecture Summary

- **Unit Tests**: 35 pytest tests covering individual components
- **Integration Tests**: 4 pytest tests covering end-to-end workflows  
- **ATDD Tests**: 9 Behave scenarios covering user story acceptance criteria
- **Performance Tests**: OpenAI optimization and async processing tests
- **Coverage**: HTML reports generated in `htmlcov/index.html`

_Last updated: 2025-01-06_
