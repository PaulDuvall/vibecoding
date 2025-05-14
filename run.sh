#!/bin/bash
set -e

# Windsurf-style local workflow for test & lint

# 1. Setup Python 3.11 virtual environment
if [ ! -d ".venv" ]; then
    python3.11 -m venv .venv
fi
source .venv/bin/activate

# 2. Install/upgrade pip and dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Lint
flake8 .

# 4. Test
pytest

# 5. Summarize
if [ $? -eq 0 ]; then
    echo "All lint and tests passed!"
else
    echo "Lint or tests failed."
    exit 1
fi
