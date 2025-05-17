# User Stories – Vibe Digest

This document defines user stories for the Vibe Digest system, derived from the Product Requirements Document (PRD). Each story includes a unique ID, user story, acceptance criteria, and traceability links (to be updated as implementation progresses).

---

## US-001: Content Aggregation
**As** a busy tech founder, engineer, or AI practitioner,
**I want** the system to fetch and parse content daily from prioritized sources (Cursor Blog, Windsurf Blog, Latent Space, Reddit, Hacker News),
**so that** I receive a curated digest of the most relevant updates.

**Acceptance Criteria:**
- System fetches content from all listed sources at least once per day
- Sources are configurable
- Fetch failures are logged and surfaced in monitoring

---

## US-002: AI-Powered Summarization
**As** a recipient of the Vibe Digest,
**I want** the system to generate concise, context-rich summaries using GPT-4,
**so that** I can quickly understand the key insights from each article.

**Acceptance Criteria:**
- Summaries are generated for each fetched article
- Summaries retain key technical insights and hyperlinks
- Each summary is capped at ~100–150 words

---

## US-003: Daily Email Delivery
**As** a user,
**I want** to receive a daily HTML email digest,
**so that** I can read the latest updates in a mobile-optimized, readable format.

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

## US-008: Performance & Success Metrics
**As** a stakeholder,
**I want** the system to meet key performance and reliability targets,
**so that** it delivers value with high quality.

**Acceptance Criteria:**
- Digest retrieval latency is < 1 second
- Data durability is ≥ 99.9%
- Web “History” page loads in < 500 ms
- Email open rate > 50%, CTR > 10%, daily content freshness > 90%, <1% failure rate in CI/CD

---

_Traceability: Link each user story to its implementation and test files as development progresses._
