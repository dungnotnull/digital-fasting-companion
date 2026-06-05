"""Knowledge module — automated research paper crawling."""

from src.knowledge.crawler import KnowledgeCrawler
from src.knowledge.relevance_scorer import RelevanceScorer, DOMAIN_KEYWORDS, RELEVANCE_THRESHOLD

__all__ = ["KnowledgeCrawler", "RelevanceScorer", "DOMAIN_KEYWORDS", "RELEVANCE_THRESHOLD"]
