"""
Storage module for digital-fasting-companion.

Handles encrypted SQLite database operations.
"""

from src.storage.local_db import LocalDB, get_db

__all__ = ["LocalDB", "get_db"]
