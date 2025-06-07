# User Stories – AI Engineering Platform

This document defines user stories for the AI Engineering platform, derived from the Product Requirements Document (PRD). Each story includes a unique ID, user story, acceptance criteria, and traceability links (to be updated as implementation progresses).

---

## US-001: AI Engineering Content Aggregation
**As** a developer transitioning to AI Engineering,
**I want** the system to fetch and parse content daily from AI Engineering tool sources (Cursor, Windsurf, Claude Code, Copilot, Jules, r/AIDevelopment, Hacker News AI threads),
**so that** I receive curated updates focused on AI development tools and practices.

**Acceptance Criteria:**
- System fetches content from all listed sources at least once per day
- Sources are configurable
- Fetch failures are logged and surfaced in monitoring

---

## US-002: AI-Powered Summarization with Performance Optimization
**As** a recipient of the AI Engineering digest,
**I want** the system to generate concise, context-rich summaries using async processing and smart batching,
**so that** I can quickly understand key AI Engineering insights with 3-5x faster processing and 30-40% cost reduction.

**Acceptance Criteria:**
- Summaries are generated for each fetched article
- Summaries retain key technical insights and hyperlinks
- Each summary is capped at ~100–150 words

---

## US-003: AI Engineering Weekly Newsletter
**As** a developer learning AI Engineering,
**I want** to receive a weekly HTML email digest with tool updates, implementation patterns, and platform development insights,
**so that** I can stay current with AI-assisted development trends and practices.

**Acceptance Criteria:**
- Email is sent daily via SendGrid
- Email contains digest title, date, source attribution, and inline links
- Layout is mobile-optimized

---

## US-004: Data Persistence of Digests
**As** a system operator,
**I want** each day’s fetched feed and website summaries to be persisted in an AWS database (DynamoDB or Aurora),
**so that** historical digests are reliably stored and retrievable.

**Acceptance Criteria:**
- Each digest is stored with a date (YYYY-MM-DD) key
- Schema includes feed source, title, URL, summary, and timestamp
- Data durability is at least 99.9%

---

## US-005: Web UI – History Page
**As** a user,
**I want** a “History” page on the website that displays past digests by date,
**so that** I can review previous summaries easily.

**Acceptance Criteria:**
- Web page lists digests by date
- Supports querying by date or date range
- Page loads in under 500 ms

---

## US-006: API Endpoints for Digest CRUD
**As** a developer or integration,
**I want** Lambda/API endpoints for inserting and retrieving digests,
**so that** the system can be extended and integrated with other services.

**Acceptance Criteria:**
- POST /digest inserts a new digest
- GET /digest/{date} retrieves a digest by date
- GET /digest lists digests over a date range
- Endpoints are secured with least-privilege IAM

---

## US-007: Reliability & Monitoring
**As** an operator,
**I want** robust error handling and monitoring,
**so that** failures are detected, logged, and surfaced promptly.

**Acceptance Criteria:**
- Retry logic for network/API timeouts
- Graceful degradation if a source fails
- Email delivery/reporting failures are logged
- Monitoring includes GitHub Actions status, SendGrid delivery, and API usage metrics

---

## US-008: Tool Comparison Matrix
**As** a developer choosing AI Engineering tools,
**I want** an interactive comparison grid of IDE plugins (Cursor vs. Windsurf vs. Claude Code vs. GitHub Copilot),
**so that** I can make informed decisions based on feature analysis, model performance, and community reviews.

**Acceptance Criteria:**
- Comparison matrix covers autocomplete, refactoring, test generation, debugging features
- Includes model performance comparisons (Claude vs. GPT vs. Gemini)
- Supports community-submitted prompts and performance ratings
- Updates automatically with new tool releases

---

## US-009: AI Engineering Roadmap
**As** a traditional software engineer,
**I want** a structured learning path from SWE to AI Engineer,
**so that** I can systematically develop AI Engineering skills.

**Acceptance Criteria:**
- Roadmap covers foundations (LLMs, tokens, embeddings, prompt engineering)
- Includes tools mastery section (IDE setup, agent workflows, automation)
- Provides advanced topics (custom agents, fine-tuning, production deployment)
- Links to practical examples and starter kits

---

## US-010: Behind-the-Build Devlogs
**As** a developer learning AI-assisted development,
**I want** transparent documentation showing how platform features are built with AI tools,
**so that** I can learn from real implementation examples.

**Acceptance Criteria:**
- Each platform feature documented with prompts → code → results
- Includes real tool usage examples (Windsurf sessions, Claude Code interactions)
- Documents iteration stories, challenges, failures, and AI-assisted solutions
- Shows performance optimization processes

---

## US-011: Starter Kits & Templates
**As** a developer adopting AI Engineering practices,
**I want** AI-built development resources and templates,
**so that** I can quickly start projects using best practices.

**Acceptance Criteria:**
- ATDD + AI pipeline templates for test-driven development with AI agents
- Multi-tool setup guides (Cursor + Claude Code + GitHub Actions)
- Performance monitoring templates for AI cost tracking and optimization
- All templates include implementation documentation

---

## US-012: Performance & Success Metrics
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

## US-201: Log OpenAI Token Usage Per Summarization
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

## US-202: Aggregate and Calculate Total OpenAI Usage and Cost Per Run
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

## US-203: Display OpenAI Usage and Cost in Digest Email
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

## US-204: Document OpenAI Usage and Cost Tracking Feature
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

### Traceability Table

| User Story | Implementation Files         | Test Files                   | Docs/Links                  |
|------------|-----------------------------|------------------------------|-----------------------------|
| US-201     | summarize.py, vibe_digest.py| tests/test_summarize.py      |                             |
| US-202     | vibe_digest.py              | tests/test_vibe_digest.py    |                             |
| US-203     | email_utils.py, vibe_digest.py| tests/test_email_utils.py   |                             |
| US-204     | README.md, user_stories.md  | N/A                          | docs/user_stories.md        |

