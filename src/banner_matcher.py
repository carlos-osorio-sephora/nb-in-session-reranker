from typing import Dict, List, Any
from dataclasses import dataclass
import numpy as np
from .interfaces import BannerBoostScorer
from .models import BannerPoolItem, BannerScore, EnrichedFeatures


@dataclass
class BannerMetadata:
    products: List[str]
    brands: List[str]
    categories: List[str]
    worlds: List[str]


@dataclass
class Weights:
    product: float
    brand: float
    category: float
    world: float


class BannerMatcher(BannerBoostScorer):
    """
    Computes banner scores based on session behavior and model scores.

    Uses multiplicative boosting: Final Score = Model Score × min(1 + Boost, Max Multiplier)
    """
    DEFAULT_WEIGHT_PRODUCT_MATCH = 0.5
    DEFAULT_WEIGHT_BRAND_MATCH = 0.3
    DEFAULT_WEIGHT_CATEGORY_MATCH = 0.15
    DEFAULT_WEIGHT_WORLD_MATCH = 0.1
    DEFAULT_WEIGHT_VIEWED_PRODUCT = 0.05
    DEFAULT_WEIGHT_VIEWED_BRAND = 0.03
    DEFAULT_WEIGHT_VIEWED_CATEGORY = 0.015
    DEFAULT_WEIGHT_VIEWED_WORLD = 0.01
    DEFAULT_MAX_BOOST_MULTIPLIER = 2.0

    def __init__(
        self,
        banner_metadata: Dict[str, Dict[str, Any]],
        weight_product_match: float = None,
        weight_brand_match: float = None,
        weight_category_match: float = None,
        weight_world_match: float = None,
        weight_viewed_product: float = None,
        weight_viewed_brand: float = None,
        weight_viewed_category: float = None,
        weight_viewed_world: float = None,
        max_boost_multiplier: float = None
    ):
        """
        Initialize banner matcher with configurable weights.

        Args:
            banner_metadata: Dictionary mapping banner_id to metadata
            weight_product_match: Weight for exact product match (loved/cart)
            weight_brand_match: Weight for brand match (loved/cart)
            weight_category_match: Weight for category match (loved/cart)
            weight_world_match: Weight for world match (loved/cart)
            weight_viewed_product: Weight for product match (viewed)
            weight_viewed_brand: Weight for brand match (viewed)
            weight_viewed_category: Weight for category match (viewed)
            weight_viewed_world: Weight for world match (viewed)
            max_boost_multiplier: Maximum boost multiplier cap
        """
        self.banner_metadata = banner_metadata
        self.weight_product_match = weight_product_match or self.DEFAULT_WEIGHT_PRODUCT_MATCH
        self.weight_brand_match = weight_brand_match or self.DEFAULT_WEIGHT_BRAND_MATCH
        self.weight_category_match = weight_category_match or self.DEFAULT_WEIGHT_CATEGORY_MATCH
        self.weight_world_match = weight_world_match or self.DEFAULT_WEIGHT_WORLD_MATCH
        self.weight_viewed_product = weight_viewed_product or self.DEFAULT_WEIGHT_VIEWED_PRODUCT
        self.weight_viewed_brand = weight_viewed_brand or self.DEFAULT_WEIGHT_VIEWED_BRAND
        self.weight_viewed_category = weight_viewed_category or self.DEFAULT_WEIGHT_VIEWED_CATEGORY
        self.weight_viewed_world = weight_viewed_world or self.DEFAULT_WEIGHT_VIEWED_WORLD
        self.max_boost_multiplier = max_boost_multiplier or self.DEFAULT_MAX_BOOST_MULTIPLIER

    def _safe_array_to_list(self, arr) -> List[str]:
        """
        Safely convert numpy array or list to list of strings.

        Args:
            arr: Array, list, or None

        Returns:
            List of strings (empty if None)
        """
        if arr is None:
            return []
        if isinstance(arr, np.ndarray):
            return arr.tolist()
        if isinstance(arr, list):
            return arr
        return []

    def _count_matches(self, banner_items: List[str], session_items: List[str]) -> int:
        """
        Count how many session items match banner items.

        Args:
            banner_items: Items from banner metadata
            session_items: Items from session (may contain duplicates for counting)

        Returns:
            Number of matches (counts duplicates)
        """
        banner_set = set(banner_items)
        return sum(1 for item in session_items if item in banner_set)

    def _compute_event_boost(
        self,
        banner: BannerMetadata,
        enriched_features: EnrichedFeatures,
        event_prefix: str,
        weights: Weights
    ) -> float:
        """
        Compute boost for a single event type (loved, basket, or viewed).

        Args:
            banner: Banner metadata
            enriched_features: Enriched session features
            event_prefix: Event prefix ('loved', 'basket', or 'viewed')
            weights: Weights for this event type

        Returns:
            Boost score for this event type
        """
        return (
            self._count_matches(banner.products, getattr(enriched_features, f'{event_prefix}_ids')) * weights.product + # noqa
            self._count_matches(banner.brands, getattr(enriched_features, f'{event_prefix}_brands')) * weights.brand + # noqa
            self._count_matches(banner.categories, getattr(enriched_features, f'{event_prefix}_third_level_categories')) * weights.category + # noqa
            self._count_matches(banner.worlds, getattr(enriched_features, f'{event_prefix}_first_level_categories')) * weights.world # noqa
        )

    def compute_boost_score(
        self,
        banner_id: str,
        enriched_features: EnrichedFeatures
    ) -> Dict[str, Any]:
        """
        Compute boost score for a banner based on session features.

        Args:
            banner_id: Banner identifier
            enriched_features: Enriched session features from HierarchyEnricher

        Returns:
            Dictionary with boost score and breakdown
        """
        if banner_id not in self.banner_metadata:
            return {
                'banner_id': banner_id,
                'boost_score': 0.0,
                'error': 'Banner not found in metadata'
            }

        raw_banner = self.banner_metadata[banner_id]
        banner = BannerMetadata(
            products=self._safe_array_to_list(raw_banner.get('product_ids')),
            brands=self._safe_array_to_list(raw_banner.get('mentioned_brands')),
            categories=self._safe_array_to_list(raw_banner.get('mentioned_categories')),
            worlds=self._safe_array_to_list(raw_banner.get('mentioned_worlds'))
        )

        high_intent_weights = Weights(
            product=self.weight_product_match,
            brand=self.weight_brand_match,
            category=self.weight_category_match,
            world=self.weight_world_match
        )

        viewed_weights = Weights(
            product=self.weight_viewed_product,
            brand=self.weight_viewed_brand,
            category=self.weight_viewed_category,
            world=self.weight_viewed_world
        )

        loved_boost = self._compute_event_boost(banner, enriched_features, 'loved', high_intent_weights)
        cart_boost = self._compute_event_boost(banner, enriched_features, 'basket', high_intent_weights)
        viewed_boost = self._compute_event_boost(banner, enriched_features, 'viewed', viewed_weights)

        return {
            'banner_id': banner_id,
            'boost_score': loved_boost + cart_boost + viewed_boost,
            'loved_boost': loved_boost,
            'cart_boost': cart_boost,
            'viewed_boost': viewed_boost
        }

    def compute_final_score(
        self,
        banner_id: str,
        model_score: float,
        enriched_features: EnrichedFeatures
    ) -> BannerScore:
        """
        Compute final score for a banner using multiplicative boosting.

        Formula: Final Score = Model Score × min(1 + Boost Score, Max Multiplier)

        Args:
            banner_id: Banner identifier
            model_score: Base score from ML model
            enriched_features: Enriched session features from HierarchyEnricher

        Returns:
            BannerScore with final score and details
        """
        boost_result = self.compute_boost_score(banner_id, enriched_features)

        if 'error' in boost_result:
            raise ValueError(f"Banner {banner_id} not found in metadata")

        boost_score = boost_result['boost_score']
        boost_multiplier = min(1 + boost_score, self.max_boost_multiplier)
        final_score = model_score * boost_multiplier

        return BannerScore(
            banner_id=banner_id,
            model_score=model_score,
            boost_score=boost_score,
            boost_multiplier=boost_multiplier,
            final_score=final_score,
            loved_boost=boost_result['loved_boost'],
            cart_boost=boost_result['cart_boost'],
            viewed_boost=boost_result['viewed_boost']
        )

    def rank_banners(
        self,
        banner_pool: List[BannerPoolItem],
        enriched_features: EnrichedFeatures
    ) -> List[BannerScore]:
        """
        Rank a pool of banners based on session features and model scores.

        Args:
            banner_pool: List of BannerPoolItem objects
            enriched_features: Enriched session features from HierarchyEnricher

        Returns:
            List of BannerScore objects, sorted descending by final_score
        """
        scored_banners = []

        for banner in banner_pool:
            result = self.compute_final_score(banner.id, banner.model_score, enriched_features)
            scored_banners.append(result)

        scored_banners.sort(key=lambda x: x.final_score, reverse=True)
        return scored_banners

    def get_top_banners(
        self,
        banner_pool: List[BannerPoolItem],
        enriched_features: EnrichedFeatures,
        top_n: int = 5
    ) -> List[BannerScore]:
        """
        Get top N ranked banners from a pool.

        Args:
            banner_pool: List of BannerPoolItem objects
            enriched_features: Enriched session features
            top_n: Number of top banners to return

        Returns:
            Top N BannerScore objects
        """
        ranked = self.rank_banners(banner_pool, enriched_features)
        return ranked[:top_n]
