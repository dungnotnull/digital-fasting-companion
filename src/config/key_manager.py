"""
API key management via OS keychain (keyring).

Securely stores API keys for Claude, OpenAI, and Garmin
in the operating system's native credential store.

Never stores keys in plain text files.
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

KEYRING_AVAILABLE = False
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    logger.warning("keyring not available — API keys stored in environment only")

SERVICE_NAME = "digital-fasting-companion"
KEY_NAMES = {
    "claude": "CLAUDE_API_KEY",
    "openai": "OPENAI_API_KEY",
    "garmin_username": "GARMIN_USERNAME",
    "garmin_password": "GARMIN_PASSWORD",
}


class APIKeyManager:
    """
    Manage API keys via OS keychain or environment variables.

    Priority:
    1. OS keychain (keyring library)
    2. Environment variables
    3. None (backend disabled)

    Keys are NEVER written to disk in plain text.
    """

    def __init__(self, service_name: str = SERVICE_NAME):
        self.service = service_name

    def get_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a provider.

        Args:
            provider: 'claude', 'openai', 'garmin_username', 'garmin_password'

        Returns:
            API key string or None
        """
        # Try keyring first
        if KEYRING_AVAILABLE:
            try:
                key = keyring.get_password(self.service, provider)
                if key:
                    return key
            except Exception as e:
                logger.debug("Keyring get failed for %s: %s", provider, e)

        # Fall back to environment
        env_key = KEY_NAMES.get(provider)
        if env_key:
            return os.environ.get(env_key)

        return None

    def set_key(self, provider: str, key: str) -> bool:
        """
        Store API key in OS keychain.

        Args:
            provider: 'claude', 'openai', 'garmin_username', 'garmin_password'
            key: The API key to store

        Returns:
            True if stored successfully
        """
        if not KEYRING_AVAILABLE:
            logger.warning("keyring not available — cannot store key")
            return False

        try:
            keyring.set_password(self.service, provider, key)
            logger.info("Stored API key for %s in OS keychain", provider)
            return True
        except Exception as e:
            logger.error("Failed to store key for %s: %s", provider, e)
            return False

    def delete_key(self, provider: str) -> bool:
        """Remove an API key from the keychain."""
        if not KEYRING_AVAILABLE:
            return False
        try:
            keyring.delete_password(self.service, provider)
            logger.info("Deleted API key for %s", provider)
            return True
        except keyring.errors.PasswordDeleteError:
            return False
        except Exception as e:
            logger.error("Failed to delete key for %s: %s", provider, e)
            return False

    def get_all_providers(self) -> list:
        """Get list of providers with stored keys."""
        available = []
        for provider in KEY_NAMES:
            if self.get_key(provider):
                available.append(provider)
        return available

    def has_key(self, provider: str) -> bool:
        return self.get_key(provider) is not None


# Global singleton
_key_manager: Optional[APIKeyManager] = None


def get_key_manager() -> APIKeyManager:
    global _key_manager
    if _key_manager is None:
        _key_manager = APIKeyManager()
    return _key_manager
