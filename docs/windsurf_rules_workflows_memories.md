# Using Windsurf Rules, Workflows, and Memories

Over the past two decades, I’ve been obsessed with making software delivery faster, safer, and more repeatable. From my early days automating builds with CruiseControl to authoring “[Continuous Integration](https://www.amazon.com/Continuous-Integration-Improving-Software-Reducing/dp/0321336380),” I’ve seen firsthand how the right practices and tools can transform teams. Today, we stand at the threshold of a new era: AI-powered development environments. Tools like [Windsurf](https://windsurf.com/editor) and [Cursor](https://www.cursor.com/) are not just changing how we write code—they’re fundamentally reshaping how we capture knowledge, enforce standards, and automate workflows.

In this post, I’ll walk through how to use Rules, Workflows, and Memories in Windsurf to create a living, breathing software system. I’ll also compare these concepts to Cursor’s approach, so you can translate practices between environments and scale your own delivery pipelines—no matter which AI-powered IDE you choose.

## Why Rules, Workflows, and Memories Matter

Let’s face it: most teams struggle with consistency, onboarding, and the loss of tribal knowledge. How many times have you joined a project and spent days (or weeks) figuring out which standards to follow, where the deployment scripts live, or why a certain architectural decision was made? Multiply that by the number of teams, and you get a productivity drain that no amount of heroics can fix.

Windsurf’s answer is to make these practices explicit, discoverable, and—crucially—enforced by AI. Here’s how:

- **Rules** codify your standards and best practices, from naming conventions to security requirements.
- **Workflows** automate the build, test, and deploy cycle, leveraging AI to adapt as your project evolves.
- **Memories** capture the context, decisions, and user stories that make your project unique, providing continuity across contributors and time.

## Rules: The Foundation of Consistency

In Windsurf, rules are more than just guidelines—they’re living documents that the AI agent (Cascade) actively enforces and references.

### Types of Rules

- **Global Rules** (`global_rules.md`):  
  These live at `~/.codeium/windsurf/memories/global_rules.md` and define organization-wide standards. Think of them as your “constitution”—they set the tone for every project.
- **Project Rules** (`.windsurfrules.md`):  
  Each repository can have its own `.windsurfrules.md` at the project root. These override or extend global rules for local needs. For example, maybe your API project requires stricter security checks than your static site.
- **Component Rules** ([`.cicdrules.md`](../.cicdrules.md), [`.iamrolerules.md`](../.iamrolerules.md), etc.):  
  For CI/CD, IAM, or other major components, place dedicated rules files at the project root (e.g., `.cicdrules.md` for CI/CD pipeline standards, `.iamrolerules.md` for IAM and security practices). Reference these files in your workflows and documentation for clarity and enforcement. For additional submodules or microservices, add rules files to the relevant subdirectory as needed.

- **Workflow YAML:** The repository includes a Windsurf workflow definition at `windsurf_workflows/test_and_lint.yaml`. Note: This workflow exists, but as of now, it has not worked exactly as intended for my local or IDE-based automation needs. Ongoing troubleshooting and improvements are in progress.

### Best Practices

- **Document the hierarchy** in your `README.md`, so contributors know which rules apply.
- **Update rules as you learn.** When you discover a better way, encode it in the rules file and let the AI enforce it.
- **Reference rules in your workflows.** This ensures that every build, test, or deploy step is aligned with your standards.

## Workflows: Automating the Rhythm of Delivery

If rules are the “what” and “why,” then workflows are the “how.” Windsurf Workflows are declarative, AI-assisted automation units that orchestrate everything from environment setup to deployment and compliance checks.

### Anatomy of a Windsurf Workflow

A typical workflow might:

- Set up a Python 3.11 virtual environment
- Install dependencies from `requirements.txt`
- Run linting (`flake8`)
- Execute tests (`pytest`)
- Summarize results and link to relevant rules and memories

Here’s a simplified example (see `windsurf_workflows/test_and_lint.yaml` in this repo):

```yaml
name: Test & Lint
on:
  manual: true
  push: true
  pull_request: true

jobs:
  setup:
    steps:
      - name: Setup Python 3.11 venv
        run: |
          python3.11 -m venv .venv
          source .venv/bin/activate
      - name: Install dependencies
        run: |
          pip install --upgrade pip
          pip install -r requirements.txt
  lint:
    needs: setup
    steps:
      - name: Run flake8 linter
        run: |
          source .venv/bin/activate
          flake8 .
  test:
    needs: lint
    steps:
      - name: Run pytest
        run: |
          source .venv/bin/activate
          pytest
  report:
    needs: test
    steps:
      - name: Summarize results and link rules/memories
        run: |
          echo "Lint and test results above."
          echo "Refer to project rules in global_rules.md and .windsurfrules.md for compliance."
          echo "Consult user_stories.md and traceability_matrix.md for context."
```

### Scaling Workflows

- **Centralize reusable workflows** in a directory like `windsurf_workflows/`.
- **Parameterize** where possible, so workflows can be reused across projects or teams.
- **Document triggers and dependencies**—make it clear when and how each workflow runs, and which rules/memories it references.

### Windsurf Workflows vs. GitHub Actions or other CI/CD workflow tools

> The following comparison helps you choose the right automation tool for each stage of delivery—and shows how Windsurf and GitHub Actions can work together for end-to-end automation.

Windsurf Workflows and GitHub Actions or other CI/CD workflow tools both automate software delivery, but they serve different roles and complement each other:

- **Purpose & Scope:**
  - *Windsurf Workflows* are AI-assisted and context-aware, automating not just CI/CD but also code generation, documentation, compliance, and more directly within the developer environment.
  - *GitHub Actions or other CI/CD workflow tools* focus on CI/CD automation in the cloud, triggered by repository events and running on GitHub-hosted infrastructure.

- **Context Awareness:**
  - *Windsurf* leverages project rules and memories, allowing workflows to dynamically adapt to coding standards, security, and architectural patterns.
  - *GitHub Actions* operate with repository and environment context, but lack native AI-driven adaptation.

- **Extensibility:**
  - *Windsurf* workflows can be parameterized and reused, and the AI can compose or modify them based on project needs.
  - *GitHub Actions* are highly extensible via marketplace actions and custom scripts, but are statically defined in YAML.

- **Execution Location:**
  - *Windsurf* runs workflows in the local development environment, orchestrated by the AI.
  - *GitHub Actions* run in isolated cloud runners, focusing on repository state and deployment.

- **Best Practice:**
  Use Windsurf Workflows for local, AI-driven automation and codebase health, and GitHub Actions for cloud-based CI/CD and deployment. Together, they provide end-to-end automation from code to production.

## Memories: Institutionalizing Knowledge

This is where Windsurf really shines. Memories are not just notes—they’re structured, persistent records of important project knowledge. Examples include user stories, architectural decisions, process changes, technical standards, troubleshooting steps, and more.

### Default Location

- **Memories are stored at:**  
  `~/.codeium/windsurf/memories/`

### How We Use Memories

- **User Stories:**  
  We maintain a `user_stories.md` that captures requirements in a testable format. Each story is linked to implementation and test files in a traceability matrix.
- **Traceability:**  
  The `docs/traceability_matrix.md` links user stories to code and tests, providing an audit trail.
- **Architectural Decisions:**  
  Whenever we make a significant design choice, it’s recorded as a memory. This means new team members can see not just what we did, but why.

### Benefits

- **Onboarding:**  
  New contributors ramp up in hours, not weeks.
- **Auditability:**  
  We can answer “why did we do this?” months after the fact.
- **AI Assistance:**  
  Cascade surfaces relevant memories during code reviews, refactoring, and even in chat.

## Cursor: A Comparative Lens

If you’ve used Cursor, you’ll notice some familiar concepts—but with different terminology and mechanics.

### Cursor Analogs

- **Memories:**  
  Cursor achieves contextual understanding through codebase indexing, chat context, and “Project Rules” that can store persistent information.
- **Rules:**  
  Cursor’s “Project Rules” (in `.cursor/rules`) and “User Rules” (global) provide granular control, including file pattern matching and even git commit message checks.
- **Workflows:**  
  Cursor’s Agent Mode and Composer can orchestrate multi-step tasks, including multi-file edits and terminal commands.

### Key Takeaway

Both platforms aim to make coding more collaborative and efficient by deeply integrating AI into the development process. The key is to understand the underlying capabilities and how to leverage them effectively within each specific editor’s paradigm.

## Putting It All Together: A Day in the Life

Here’s how these concepts come together in my daily workflow:

1. **Start with the Rules:**  
   I review (and sometimes update) `global_rules.md` and `.windsurfrules.md` to ensure I’m working with the latest standards.
2. **Kick Off a Workflow:**  
   I trigger the `Test & Lint` workflow before pushing changes. If something fails, Cascade surfaces the relevant rule or memory to help me fix it.
3. **Capture New Knowledge:**  
   When I solve a tricky problem or make a key decision, I add it as a memory. This might be as simple as updating a user story or as detailed as documenting a new architectural pattern.
4. **Traceability:**  
   I link new code and tests to user stories in the traceability matrix, closing the loop between requirements and implementation.

## Best Practices for Scaling AI-Driven Delivery

- **Be explicit.**  
  Don’t assume tribal knowledge—write it down as a rule or memory.
- **Automate everything.**  
  If you do it more than once, make it a workflow.
- **Review and refactor.**  
  Rules, workflows, and memories are living artifacts—keep them up to date.
- **Cross-pollinate ideas.**  
  Borrow best practices from Cursor or other tools and adapt them to your environment.

## Conclusion

The future of software delivery is AI-driven, but it’s still up to us to provide the right guardrails and context. By codifying rules, automating workflows, and capturing memories, we can build systems that are not just faster and safer, but also more resilient to change.

If you’re looking to scale your team or accelerate delivery, start by making your rules, workflows, and memories explicit. Your future self—and your team—will thank you.

---

## Appendix: Further Reading and References

Below are official and community resources that provide additional detail and validation for the concepts described in this post:

- **Cascade Memories (Official Docs):**  [Cascade Memories](https://docs.windsurf.com/windsurf/cascade/memories) Explains how Windsurf’s Cascade agent uses "Memories" to persist user stories, architectural decisions, and project context for context-aware automation and onboarding.
- **Getting Started: Rules, Workflows, and Memories (Official Docs):**  [Getting Started](https://docs.windsurf.com/windsurf/getting-started) Introduces the core concepts of Rules, Workflows, and Memories, showing their interaction and importance in automating and enforcing standards throughout the software delivery lifecycle.
- **Rules for AI Assistants (Windsurf & Cursor Interoperability):**  [rules-for-ai GitHub](https://github.com/hashiiiii/rules-for-ai) Explains how to structure global and project-specific rules in Windsurf (`global_rules.md`, `.windsurfrules`) and Cursor, reinforcing best practices described above.

These resources provide further technical details and official guidance, supporting the definitions and practices described in this document. For direct references to mechanisms and definitions, see the "Cascade Memories" and "Getting Started" documentation.[^1]

[^1]: Official Windsurf documentation, see Appendix above.