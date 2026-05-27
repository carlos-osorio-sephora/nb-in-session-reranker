"""
Sephora Clickstream Analysis Package
"""

from .models import SessionFeatures, EnrichedFeatures, BannerPoolItem, BannerScore
from .session_processor import SessionProcessor
from .hierarchy_enricher import HierarchyEnricher
from .interfaces import BannerBoostScorer
from .banner_matcher import BannerMatcher, Weights, BannerMetadata
from .embedding_matcher import SessionEmbeddingBuilder, EmbeddingBannerMatcher

__all__ = [
    'SessionFeatures',
    'EnrichedFeatures',
    'SessionProcessor',
    'HierarchyEnricher',
    'BannerBoostScorer',
    'BannerMatcher',
    'BannerScore',
    'BannerPoolItem',
    'Weights',
    'BannerMetadata',
    'SessionEmbeddingBuilder',
    'EmbeddingBannerMatcher',
]
