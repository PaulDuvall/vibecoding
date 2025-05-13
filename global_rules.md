# Global Rules for Windsurf Projects

These rules define the organization-wide standards and best practices for all projects using the Windsurf AI IDE. They are intended to be stable, broadly applicable, and serve as the baseline for all repositories. For project-specific rules or exceptions, see `.windsurfrules.md` in each repo.

## Technology Stack & General Principles
- Use Python 3.11 for all Python projects unless otherwise required.
- Leverage AWS services for infrastructure, managed via Infrastructure as Code (CloudFormation preferred).
- Use GitHub Actions or similar CI/CD platforms for automated builds, tests, and deployments.
- Practice Test-Driven Development (TDD) and require comprehensive automated test coverage.
- All code must be reviewed before merging to main branches.

## Naming, Formatting, and Coding Standards
- Use underscores for file, directory, and script names.
- Follow [PEP8](https://peps.python.org/pep-0008/) for Python code style.
- Document all code with clear inline comments and maintain up-to-date README and supporting markdown docs.
- Only include active, necessary dependencies in requirements files.

## Security & Compliance
- Never commit sensitive credentials, API keys, or secrets to repositories.
- Use AWS KMS, encrypted Parameter Store, or AWS Secrets Manager for secret management.
- Apply the principle of least privilege to all IAM roles and policies.
- Enable AWS CloudTrail and schedule regular security audits.
- **All IAM role and policy authoring, review, and least-privilege best practices are defined in [.iamrolerules.md](.iamrolerules.md) and must be followed by all contributors.**

## CI/CD, Testing, and Version Control
- All projects must use automated CI/CD pipelines (e.g., GitHub Actions) for linting, testing, and deployment.
- Require all tests to pass before merging or deploying.
- Use semantic versioning for all tags: `vX.Y.Z` or `vX.Y.Z-description`.
- Commit messages should be clear, descriptive, and follow a consistent convention.
- **All organization-wide CI/CD and automation best practices are defined in [.cicdrules.md](.cicdrules.md) and must be followed by all projects.**

## Infrastructure as Code & Cloud
- Use AWS CloudFormation for all AWS infrastructure.
- S3 bucket names must be globally unique, DNS-compliant, and follow project/environment conventions.
- Automate deployments via bash scripts that invoke CloudFormation (fallback to AWS CLI if needed).
- Follow [Twelve-Factor App](https://twelvefactorapp.com/) principles for SaaS development.

## Documentation & Official References
- All projects must have a comprehensive README and supporting markdown documentation.
- Architecture diagrams should use Mermaid syntax in markdown.
- Always verify code and technical explanations against official documentation for languages, frameworks, and APIs. If conflicts arise, defer to the authoritative source.

  - Review the repository to capture all recent changes and new functionalities.
  - Update the `README.md` with detailed setup, usage, and contribution instructions. Include links to user stories, traceability documents, and versioning information.

### 2.9 Security, Codebase Analysis & Refactoring
- **Security, Privacy, & Compliance Analysis:**
  - Conduct regular code reviews to detect vulnerabilities and privacy or compliance issues.
  - Use automated tools (e.g., Bandit, Prowler, AWS CodeGuru Reviewer) and document findings in a `SECURITY.md` file or equivalent documentation.
- **Analyzing Unused Files & Consolidation:**
  - Use static analysis tools and custom scripts to identify orphaned modules, outdated libraries, and redundant configurations.
  - Evaluate the dependency graph and test coverage to target files for consolidation or removal.
  - Develop and document a refactoring plan, ensuring team collaboration and traceability.
- **Documentation Standards:**
  - **User Stories:**  
    Document each with a unique ID (e.g., `US-XXX`), acceptance criteria, and links to the implementation and tests.
  - **Code Comments & Version Control:**  
    Include references to user story IDs, configuration details, and complex logic in code comments. Use semantic versioning for all documentation changes.
  - **Testing Documentation:**  
    Store test files in `./tests/` and provide execution instructions in a script (e.g., `./tests/run_tests.sh`).

### 2.10 Project Change Log
Maintain a comprehensive, up-to-date change log that documents all project modifications, decision rationales, and contextual details. This log will be automatically referenced in every new chat session to ensure continuity, informed decision-making, and complete historical traceability.

### 2.11 Generating Diagrams
- **Architecture Diagrams:**
  - Create a file named `docs/architecture_diagrams.md` containing instructions for generating diagrams that illustrate:
    1. **Data Processing Architecture:**  
       Flow from data acquisition to HTML generation and the AWS services used (e.g., S3, CloudFront).
    2. **AWS Infrastructure for Static Site:**  
       Configuration of ACM, Route 53, CloudFront, and S3, including security and access flows.
    3. **Scheduled Lambda for HTML Upload:**  
       An overview of the execution cycle (using CloudWatch Events/EventBridge) and the data pipeline.

### 2.12 Fully Automated AWS OIDC Authentication for GitHub Actions
- **One-Step OIDC Setup:**
  - Use the [gha-aws-oidc-bootstrap](https://github.com/PaulDuvall/gha-aws-oidc-bootstrap) tool to automate the configuration of OpenID Connect (OIDC) between GitHub Actions and AWS. This recommended solution:
    - Deploys a CloudFormation stack that creates an IAM OIDC Identity Provider, an IAM Role with a trust policy (scoped to your GitHub organization, repository, and branch), and a managed IAM policy with minimal permissions.
    - Waits for the CloudFormation deployment to complete.
    - Retrieves the IAM Role ARN and automatically sets the GitHub repository variable (`AWS_ROLE_TO_ASSUME`) using the GitHub API.
- **GitHub Actions Workflow Example:**
  ```yaml
  jobs:
    deploy:
      permissions:
        id-token: write   # Required for OIDC
        contents: read
      steps:
        - name: Checkout code
          uses: actions/checkout@v3
        
        - name: Configure AWS credentials
          uses: aws-actions/configure-aws-credentials@v2
          with:
            role-to-assume: ${{ vars.AWS_ROLE_TO_ASSUME }}
            aws-region: us-east-1
        
        # Additional deployment steps...
  ```
- For further details, refer to:  
  - [AWS OIDC Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html)  
  - [GitHub Actions OIDC Documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)

---