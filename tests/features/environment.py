"""
Behave environment configuration for digest workflow tests.
"""
import os
import sys

def before_all(context):
    """Set up test environment before all scenarios."""
    # Add project root to Python path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)


def after_scenario(context, scenario):
    """Clean up after each scenario."""
    # Stop environment variable patcher if it exists
    if hasattr(context, 'env_patcher'):
        context.env_patcher.stop()