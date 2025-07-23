"""
Database package for Vibe Coding Digest persistence.
US-004-002: Create Database Package Structure
"""

from .client import DynamoDBClient

__all__ = ['DynamoDBClient']
__version__ = '0.1.0'