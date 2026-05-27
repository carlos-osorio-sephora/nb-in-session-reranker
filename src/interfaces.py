from abc import ABC, abstractmethod
from typing import Any, Dict, List

from .models import BannerPoolItem, BannerScore, EnrichedFeatures


class BannerBoostScorer(ABC):
    """
    Interface for scoring and ranking banners against session features.

    Implementations can use different strategies (exact matching, embeddings, etc.)
    but all produce BannerScore objects via the same final-score formula:
        Final Score = model_score × min(1 + boost_score, max_boost_multiplier)
    """

    @abstractmethod
    def compute_boost_score(
        self,
        banner_id: str,
        enriched_features: EnrichedFeatures
    ) -> Dict[str, Any]:
        """
        Compute the boost score for a single banner.
        Returned dict must contain 'banner_id' and 'boost_score' keys.
        On failure it may also contain an 'error' key.
        """

    @abstractmethod
    def compute_final_score(
        self,
        banner_id: str,
        model_score: float,
        enriched_features: EnrichedFeatures
    ) -> BannerScore:
        """Combine the model score with the boost to produce the final ranking score."""

    @abstractmethod
    def rank_banners(
        self,
        banner_pool: List[BannerPoolItem],
        enriched_features: EnrichedFeatures
    ) -> List[BannerScore]:
        """Score every banner in the pool and return them sorted descending by final_score."""

    def get_top_banners(
        self,
        banner_pool: List[BannerPoolItem],
        enriched_features: EnrichedFeatures,
        top_n: int = 5
    ) -> List[BannerScore]:
        return self.rank_banners(banner_pool, enriched_features)[:top_n]
