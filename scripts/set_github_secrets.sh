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

read -s -p "Enter your OPENAI_API_KEY: " OPENAI_API_KEY; echo
read -p "Enter your EMAIL_TO address: " EMAIL_TO
read -p "Enter your EMAIL_FROM address: " EMAIL_FROM
read -s -p "Enter your SENDGRID_API_KEY: " SENDGRID_API_KEY; echo

gh secret set OPENAI_API_KEY -b"$OPENAI_API_KEY" -R "$REPO"
gh secret set EMAIL_TO -b"$EMAIL_TO" -R "$REPO"
gh secret set EMAIL_FROM -b"$EMAIL_FROM" -R "$REPO"
gh secret set SENDGRID_API_KEY -b"$SENDGRID_API_KEY" -R "$REPO"

echo "✅ All secrets set successfully for $REPO"
