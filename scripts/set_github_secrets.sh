#!/bin/bash
# set_github_secrets.sh
#
# Usage: ./set_github_secrets.sh <owner/repo>
# Example: ./set_github_secrets.sh PaulDuvall/vibecoding
#
# Prompts for and sets required GitHub repository secrets using the GitHub CLI (gh).
# Requires: gh CLI authenticated and repo admin permissions.

set -e

if [ -z "$1" ]; then
  echo "Usage: $0 <owner/repo>"
  exit 1
fi

REPO="$1"

echo "Setting GitHub secrets for repository: $REPO"

# Get list of existing secrets
EXISTING_SECRETS=$(gh secret list -R "$REPO" | awk '{print $1}')

set_secret() {
  local secret_name="$1"
  local prompt="$2"
  local silent="$3"
  if echo "$EXISTING_SECRETS" | grep -qx "$secret_name"; then
    echo "[SKIP] $secret_name already set."
  else
    if [ "$silent" = "silent" ]; then
      read -s -p "$prompt" secret_value; echo
    else
      read -p "$prompt" secret_value
    fi
    gh secret set "$secret_name" -b"$secret_value" -R "$REPO"
    echo "[SET] $secret_name set."
  fi
}

set_secret "OPENAI_API_KEY" "Enter your OPENAI_API_KEY: " silent
set_secret "EMAIL_TO" "Enter your EMAIL_TO address: "
set_secret "EMAIL_FROM" "Enter your EMAIL_FROM address: "
set_secret "SENDGRID_API_KEY" "Enter your SENDGRID_API_KEY: " silent
set_secret "GITLEAKS_LICENSE" "Enter your GITLEAKS_LICENSE: " silent

echo "✅ All secrets processed for $REPO"
# GITLEAKS_LICENSE is now available as a GitHub Actions secret for use in workflows.
