"""Agent module — challenge generation with pluggable backends and quality tracking."""

from src.agent.static_pool import StaticChallengePool, Challenge
from src.agent.ollama_backend import OllamaBackend
from src.agent.claude_backend import ClaudeBackend, RateLimiter
from src.agent.openai_backend import OpenAIBackend
from src.agent.router import ChallengeGenerator
from src.agent.user_context import UserContext
from src.agent.quality_tracker import ChallengeQualityTracker

__all__ = [
    "StaticChallengePool", "Challenge",
    "OllamaBackend", "ClaudeBackend", "OpenAIBackend",
    "ChallengeGenerator", "RateLimiter",
    "UserContext", "ChallengeQualityTracker",
]
