from typing import Dict, List, Optional

import numpy as np

from .interfaces import BannerBoostScorer
from .models import BannerPoolItem, BannerScore, EnrichedFeatures

# Default weight per interaction type when building the session embedding.
# Higher-intent actions receive higher weights; negative interactions use 0
# by default but can be set negative to subtract those signals.
DEFAULT_INTERACTION_WEIGHTS: Dict[str, float] = {
    'purchased': 1.0,
    'loved': 1.0,
    'basket': 0.8,
    'viewed': 0.3,
    'unloved': 0.0,
    'removed_basket': 0.0,
}


class SessionEmbeddingBuilder:
    """
    Builds a session embedding as a weighted average of item embeddings.

    For each interaction type the weight controls how strongly those items
    pull the session vector. Items missing from item_embeddings are skipped.
    """

    def __init__(
        self,
        item_embeddings: Dict[str, np.ndarray],
        interaction_weights: Optional[Dict[str, float]] = None,
    ):
        self.item_embeddings = item_embeddings
        self.interaction_weights = interaction_weights or DEFAULT_INTERACTION_WEIGHTS

    def build(self, enriched_features: EnrichedFeatures) -> Optional[np.ndarray]:
        """
        Return the weighted-average embedding for the session, or None if no
        known items are present.
        """
        weighted_sum: Optional[np.ndarray] = None
        total_weight = 0.0

        for prefix, weight in self.interaction_weights.items():
            if weight == 0.0:
                continue
            ids = getattr(enriched_features, f'{prefix}_ids', [])
            for item_id in ids:
                emb = self.item_embeddings.get(item_id)
                if emb is None:
                    continue
                weighted_sum = weight * emb if weighted_sum is None else weighted_sum + weight * emb
                total_weight += abs(weight)

        if weighted_sum is None or total_weight == 0.0:
            return None
        return weighted_sum / total_weight


class EmbeddingBannerMatcher(BannerBoostScorer):
    """
    Ranks banners using cosine similarity between a session embedding and
    per-banner embeddings.

    Boost score = cosine similarity ∈ [−1, 1], typically [0, 1] for
    non-negative embedding spaces.
    Final score = model_score × min(1 + boost, max_boost_multiplier)
    """

    DEFAULT_MAX_BOOST_MULTIPLIER = 2.0

    def __init__(
        self,
        banner_embeddings: Dict[str, np.ndarray],
        session_embedding_builder: SessionEmbeddingBuilder,
        max_boost_multiplier: float = None,
    ):
        self.banner_embeddings = banner_embeddings
        self.session_embedding_builder = session_embedding_builder
        self.max_boost_multiplier = max_boost_multiplier or self.DEFAULT_MAX_BOOST_MULTIPLIER

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        denom = np.linalg.norm(a) * np.linalg.norm(b)
        if denom == 0.0:
            return 0.0
        return float(np.dot(a, b) / denom)

    def compute_boost_score(
        self,
        banner_id: str,
        enriched_features: EnrichedFeatures,
    ) -> dict:
        if banner_id not in self.banner_embeddings:
            return {'banner_id': banner_id, 'boost_score': 0.0, 'error': 'Banner not found in embeddings'}

        session_emb = self.session_embedding_builder.build(enriched_features)
        if session_emb is None:
            return {'banner_id': banner_id, 'boost_score': 0.0}

        similarity = self._cosine_similarity(session_emb, self.banner_embeddings[banner_id])
        return {'banner_id': banner_id, 'boost_score': similarity}

    def compute_final_score(
        self,
        banner_id: str,
        model_score: float,
        enriched_features: EnrichedFeatures,
    ) -> BannerScore:
        boost_result = self.compute_boost_score(banner_id, enriched_features)
        if 'error' in boost_result:
            raise ValueError(f"Banner {banner_id} not found in embeddings")

        boost_score = boost_result['boost_score']
        boost_multiplier = min(1 + boost_score, self.max_boost_multiplier)

        return BannerScore(
            banner_id=banner_id,
            model_score=model_score,
            boost_score=boost_score,
            boost_multiplier=boost_multiplier,
            final_score=model_score * boost_multiplier,
            loved_boost=0.0,
            cart_boost=0.0,
            viewed_boost=0.0,
        )

    def rank_banners(
        self,
        banner_pool: List[BannerPoolItem],
        enriched_features: EnrichedFeatures,
    ) -> List[BannerScore]:
        scored = [
            self.compute_final_score(banner.id, banner.model_score, enriched_features)
            for banner in banner_pool
        ]
        return scored
