[![GitHub Actions Workflow Status](https://github.com/PaulDuvall/vibecoding/actions/workflows/vibe-coding-digest.yml/badge.svg)](https://github.com/PaulDuvall/vibecoding/actions/workflows/vibe-coding-digest.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![GitHub last commit](https://img.shields.io/github/last-commit/PaulDuvall/vibecoding)
[![LinkedIn-Follow](https://img.shields.io/badge/LinkedIn-Follow-blue)](https://www.linkedin.com/in/paulduvall/)

# Rules, Workflows, and Memories in Windsurf

This project uses **Windsurf** to manage and automate development standards, workflows, and persistent project knowledge. This approach ensures consistency, scalability, and rapid onboarding for all contributors.

---

## Vibe Digest Automation & Quality Workflow

### Overview

**Vibe Digest** is an automated content aggregation and summarization tool that delivers curated, daily email digests of the most relevant developments in AI, developer tools, and emerging technology. See [`docs/prd.md`](docs/prd.md) for the Product Requirements Document (PRD), goals, and acceptance criteria.

### Key Features
- Aggregates RSS feeds from multiple sources
- Summarizes content using OpenAI's API
- Formats and sends a daily HTML digest via SendGrid
- Designed for tech founders, engineers, and AI practitioners

### Quality & CI/CD Workflow
- **Linting:** Enforced via Flake8 (`./run.sh lint`)
- **Testing:** Comprehensive pytest suite (`./run.sh test`)
- **CI/CD:** Automated with GitHub Actions ([`.github/workflows/vibe-coding-digest.yml`](.github/workflows/vibe-coding-digest.yml))
- **All code and tests are PEP 8 compliant** as of the latest update
- **Traceability:**
  - Implementation: [`.github/scripts/vibe_digest.py`](.github/scripts/vibe_digest.py)
  - Tests: [`tests/test_vibe_digest.py`](tests/test_vibe_digest.py)
  - Product requirements: [`docs/prd.md`](docs/prd.md)

### Required Secrets for Deployment
Set the following secrets in your GitHub repository for the workflow to function:
- `OPENAI_API_KEY`: OpenAI API access
- `SENDGRID_API_KEY`: SendGrid email service
- `EMAIL_FROM`: Verified sender email address
- `EMAIL_TO`: Recipient email address

---

### Setting Up SendGrid for Email Delivery

1. **Create a SendGrid Account**  
   Sign up at [https://sendgrid.com/](https://sendgrid.com/).

2. **Verify a Sender or Domain**  
   - Go to **Settings > Sender Authentication** in the SendGrid dashboard.
   - For testing, use **Single Sender Verification** (enter and verify your email).
   - For production, use **Domain Authentication** (add DNS records and verify your domain).

3. **Generate an API Key**  
   - Go to **Settings > API Keys**.
   - Click **Create API Key** (give it a name, e.g., `VibeDigest`).
   - Select "Full Access" or at least "Mail Send" permissions.
   - Click **Create & View** and **copy the API key** (you won't see it again).

4. **Set GitHub Secrets**  
   Use the [`scripts/set_github_secrets.sh`](scripts/set_github_secrets.sh) script or set secrets manually in your GitHub repository:
   ```bash
   ./scripts/set_github_secrets.sh <owner/repo>
   ```
   - `SENDGRID_API_KEY`: Your SendGrid API key
   - `EMAIL_FROM`: Your verified sender email
   - `EMAIL_TO`: Recipient email address

5. **Test Your Setup**  
   Trigger the workflow or run the script locally. Check your inbox for the digest.

**Tip:** For best deliverability, use domain authentication and a sender address at your own domain.

---

### Running Locally
```bash
# Run linting
./run.sh lint

# Run tests
./run.sh test
```

---

## How to Create an RSS Feed for a Google Alert

You can use Google Alerts to track news, blogs, and forum posts for any search term, and receive updates via RSS. Here’s how to set up an RSS feed for a Google Alert:

1. **Go to Google Alerts:**
   - Visit [https://www.google.com/alerts](https://www.google.com/alerts) and sign in with your Google account.

2. **Create a New Alert:**
   - In the search box, enter your desired query (e.g., `AI coding`, `GitHub Copilot`, `Vibe Coding`).
   - Click “Show options” to adjust frequency, sources, language, and region as needed.
   - For “Deliver to,” select **RSS feed** from the dropdown menu.
   - Click **Create Alert**.

3. **Copy the RSS Feed URL:**
   - After creating the alert, you’ll see it listed with an RSS icon next to it.
   - Right-click the RSS icon and copy the link address (it will look like `https://www.google.com/alerts/feeds/XXXXXXXX/XXXXXXXX`).

4. **Add the Feed to Your Digest:**
   - Add the RSS URL to your `FEEDS` list in `vibe_digest.py`.
   - Add a human-friendly name to `FEED_SOURCES` in the same file for clarity.

**Example:**
```python
FEEDS = [
    # ...other feeds...
    "https://www.google.com/alerts/feeds/11805205268710618137/2009129731931801714",  # Google Alerts: Vibe Coding
]
FEED_SOURCES = {
    # ...other sources...
    "https://www.google.com/alerts/feeds/11805205268710618137/2009129731931801714": "Google Alerts: Vibe Coding",
}
```

---

## Windsurf Vibe Coding vs. Cursor: Conceptual Analogs

Both **Windsurf Vibe Coding** (Cascade) and **Cursor** are advanced AI-powered coding environments, but they use different terminology for similar concepts. Here’s how their core features map to each other:

### 1. Memories

- **Windsurf Vibe:**  
  - “Memories” are persistent, workspace-specific records of context, user stories, architecture decisions, and more. Cascade (the AI agent) can generate or retrieve these to provide continuity and context-aware assistance.
- **Cursor Analogs:**  
  - **Codebase Indexing & Contextual Awareness:** Cursor indexes your codebase for deep contextual understanding.
  - **Chat Context:** Cursor’s chat considers your current file, cursor, and explicit `@file` or `@symbol` mentions.
  - **Project Rules as Persistent Context:** You can save summaries or procedures as Project Rules in `.cursor/rules` to provide future context—mimicking Windsurf’s Memories.
  - **Agent Mode:** Cursor’s agent remembers the context of ongoing tasks, providing operational memory.

### 2. Rules

- **Windsurf Vibe:**  
  - “Rules” are user-defined instructions (e.g., `global_rules.md`, `.windsurfrules.md`) that guide the AI’s behavior, enforce standards, and ensure consistency.
- **Cursor Analogs:**  
  - **Project Rules:** Located in `.cursor/rules`, these are version-controlled, support file pattern matching, git commit messages, and can be auto-attached or manually invoked.
  - **User Rules:** Global, user-level rules set in Cursor’s settings, applying across all projects.
  - **Generating Rules from Chat:** You can use `/Generate Cursor Rules` to create rules from conversations, similar to how Windsurf lets you persist learnings as rules.

### 3. Workflows

- **Windsurf Vibe:**  
  - “Workflows” are declarative, AI-driven automation units that orchestrate multi-step processes (e.g., build, test, deploy) and can reference rules and memories for context-aware execution.
- **Cursor Analogs:**  
  - **Agent Mode & Composer:** Cursor’s agent can plan and execute multi-step tasks, perform multi-file edits, run terminal commands, and loop on errors.
  - **Multi-File Edits & Codebase Actions:** Supports complex refactoring and feature implementation.
  - **Ctrl+K (Edit/Generate):** Enables in-place code modification or generation.
  - **Terminal Integration:** Cursor can help script and run terminal commands.
  - **Automated Error Detection:** Cursor can fix lint errors and automate debugging steps.
  - **Customizable Rules for Workflow Automation:** Project Rules can automate and enforce workflow steps.

---

### Summary Table

| Concept            | Windsurf Vibe Coding (Cascade)           | Cursor Analog(s)                                 |
|--------------------|------------------------------------------|--------------------------------------------------|
| **Memories**       | Persistent workspace/project context      | Codebase indexing, chat context, Project Rules    |
| **Rules**          | `global_rules.md`, `.windsurfrules.md`   | Project Rules, User Rules, `.cursor/rules`        |
| **Workflows**      | Declarative, AI-driven, multi-step flows | Agent Mode, Composer, multi-file/terminal actions |

---

**Tip:**  
To translate your workflow from Windsurf to Cursor:
- Store persistent context as Project Rules in `.cursor/rules`
- Use Cursor’s Agent Mode for multi-step, context-aware automation
- Leverage file pattern rules and chat context for granular control

Both platforms aim to make coding more collaborative and efficient by deeply integrating AI into the development process. Understanding these analogs helps teams move between environments while retaining best practices.

---

## 1. Rules: Definition, Structure, and Reuse

### a. `global_rules.md`
- **Purpose:** Defines global standards and best practices (e.g., naming, security, CI/CD, Python style).
- **Default Location:** User home directory: `~/.codeium/windsurf/memories/global_rules.md`
- **Project Override (optional):** Project root: `./global_rules.md`
- **Scaling/Reuse:**
  - Update the global file for organization-wide standards.
  - Add or override with a project-specific file as needed.
  - Reference both in your `README.md` for clarity.

### b. `.windsurfrules.md`
- **Purpose:** Repository-specific rules and overrides.
- **Default Location:** Project root: `./.windsurfrules.md`
- **Scaling/Reuse:**
  - Use as a template for new projects.
  - Document project-specific exceptions to global rules.

### c. Additional Rules Files
- **Purpose:** Define rules for submodules or components (e.g., `lambda_rules.md`).
- **Default Location:** Project root: `./lambda_rules.md`
- **Scaling/Reuse:**
  - Reference these files in the main `README.md` and in related documentation.
  - Use a consistent naming convention and document precedence.

### d. Referencing and Adding New Rules Files
- List all rules files in this `README.md`.
- Clearly state the scope and precedence of each file.
- When adding a new component, create a rules file if unique standards are needed for that component.

---

## 2. Workflows: Windsurf Capability, Documentation, and Scaling

- **Definition:**
  - **Windsurf Workflows** are a first-class, declarative automation capability built into Windsurf. They orchestrate sequences of actions (build, test, deploy, audit, etc.) in a context-aware, AI-assisted manner.
  - Unlike traditional scripts or CI/CD pipelines, Windsurf Workflows are explicitly defined, versioned, and can reference project rules and memories for dynamic, intelligent automation.

- **Key Features:**
  - Declarative YAML/JSON or markdown-based definitions (not just shell scripts)
  - AI understands and adapts workflows based on current context, rules, and memories
  - Can trigger on events (e.g., code push, PR, scheduled, manual)
  - Integrated with rules enforcement and memory retrieval for traceable, compliant automation

- **Location:**
  - Define workflows in `windsurf_workflows/`, `workflows/`, or a dedicated section in your documentation (e.g., `docs/workflows.md`).
  - Reference all active workflows in this `README.md` for discoverability.
  - **Example:** See [`windsurf_workflows/test_and_lint.yaml`](./windsurf_workflows/test_and_lint.yaml) for a reusable, documented workflow that sets up Python, installs dependencies, lints, and tests your codebase.

- **Creating and Reusing Workflows:**
  - Use existing workflow templates or compose new ones using Windsurf’s declarative syntax.
  - Parameterize workflows for reuse across projects or teams.
  - Reference relevant rules (`global_rules.md`, `.windsurfrules.md`, etc.) and memories for context-aware execution.

- **Scaling Workflows:**
  - Maintain a central library of reusable workflows for your organization.
  - Share, fork, and adapt workflows as your team or project grows.
  - Use workflow inheritance or composition for complex automation scenarios.

- **Best Practice:**
  - Document each workflow’s purpose, triggers, and rule/memory dependencies.
  - Regularly review and refactor workflows to align with evolving standards and project needs.

---

## 3. Memories: Persistent Project Knowledge

- **Definition:** Structured, persistent records of user stories, architectural decisions, traceability, and implementation details.
- **Default Location:** User home directory: `~/.codeium/windsurf/memories/`
- **Surfaced In:** Documentation (e.g., `user_stories.md`, `traceability_matrix.md`).
- **Scaling/Reuse:**
  - Use memories to automate onboarding and provide historical context.
  - Update memories as the project evolves.
  - Share or export memories to new projects for rapid knowledge transfer.

---

## 4. Best Practices for Reuse and Scaling

- **Hierarchy:**
  1. `global_rules.md` (organization-wide)
  2. `.windsurfrules.md` (project-specific)
  3. Component/module rules files (most specific)
- **Documentation:**
  - Always update this `README.md` with references to all rules, workflows, and memories.
  - Maintain a traceability matrix linking user stories, rules, and implementation.
- **Change Management:**
  - Document rationale for rule changes in commit messages and memories.
  - Communicate updates to the team.
- **Automation:**
  - Integrate rules and workflows into CI/CD pipelines for enforcement.
  - Use memories to surface relevant context in code reviews and onboarding.

---

## 5. Cursor (AI-Assisted IDE) Analogs

- **Rules Files:** Like `.editorconfig` or `CONTRIBUTING.md`, but AI-enforced and context-aware.
- **Workflows:** Analogous to IDE build/run/debug tasks, but with AI-driven suggestions and updates.
- **Memories:** Comparable to a persistent, searchable project knowledge base, with AI surfacing relevant context as you work.

---

## 6. Scaling Across Teams and Projects

- **Reuse rules and workflows** by templating and sharing across repositories.
- **Centralize global rules** for consistency, and allow project/component overrides for flexibility.
- **Leverage memories** to retain and transfer knowledge as teams grow or projects fork.
- **Automate enforcement** using CI/CD and Windsurf’s AI capabilities.

---

**For further details, see:**
- [`global_rules.md`](./global_rules.md)
- [`.windsurfrules.md`](./.windsurfrules.md)
- (Add links to any additional rules files as needed)
- `user_stories.md`, `traceability_matrix.md`, and other docs for memories and workflows.