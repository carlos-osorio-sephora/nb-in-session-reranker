from dataclasses import dataclass, field
from typing import List


@dataclass
class SessionFeatures:
    """
    Container for user session features extracted from clickstream data.

    Attributes:
        loved_ids: List of product IDs that were added to loves
        basket_ids: List of product IDs that were added to basket
        viewed_ids: List of product IDs that were viewed (from page view events)
        purchased_ids: List of product IDs that were purchased
        banner_ids: List of banner SIDs from cms viewable impression events
        unloved_ids: List of product IDs that were unloved (from un love events)
        removed_basket_ids: List of product IDs that were removed from basket
    """
    loved_ids: List[str] = field(default_factory=list)
    basket_ids: List[str] = field(default_factory=list)
    viewed_ids: List[str] = field(default_factory=list)
    purchased_ids: List[str] = field(default_factory=list)
    banner_ids: List[str] = field(default_factory=list)
    unloved_ids: List[str] = field(default_factory=list)
    removed_basket_ids: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"SessionFeatures(\n"
            f"  loved_ids={len(self.loved_ids)} items,\n"
            f"  basket_ids={len(self.basket_ids)} items,\n"
            f"  viewed_ids={len(self.viewed_ids)} items,\n"
            f"  purchased_ids={len(self.purchased_ids)} items,\n"
            f"  banner_ids={len(self.banner_ids)} items,\n"
            f"  unloved_ids={len(self.unloved_ids)} items,\n"
            f"  removed_basket_ids={len(self.removed_basket_ids)} items\n"
            f")"
        )


@dataclass
class EnrichedFeatures:
    """
    Container for enriched session features with hierarchy information.
    """
    loved_ids: List[str] = field(default_factory=list)
    basket_ids: List[str] = field(default_factory=list)
    viewed_ids: List[str] = field(default_factory=list)
    purchased_ids: List[str] = field(default_factory=list)
    banner_ids: List[str] = field(default_factory=list)
    unloved_ids: List[str] = field(default_factory=list)
    removed_basket_ids: List[str] = field(default_factory=list)
    loved_brands: List[str] = field(default_factory=list)
    loved_first_level_categories: List[str] = field(default_factory=list)
    loved_second_level_categories: List[str] = field(default_factory=list)
    loved_third_level_categories: List[str] = field(default_factory=list)
    basket_brands: List[str] = field(default_factory=list)
    basket_first_level_categories: List[str] = field(default_factory=list)
    basket_second_level_categories: List[str] = field(default_factory=list)
    basket_third_level_categories: List[str] = field(default_factory=list)
    viewed_brands: List[str] = field(default_factory=list)
    viewed_first_level_categories: List[str] = field(default_factory=list)
    viewed_second_level_categories: List[str] = field(default_factory=list)
    viewed_third_level_categories: List[str] = field(default_factory=list)
    purchased_brands: List[str] = field(default_factory=list)
    purchased_first_level_categories: List[str] = field(default_factory=list)
    purchased_second_level_categories: List[str] = field(default_factory=list)
    purchased_third_level_categories: List[str] = field(default_factory=list)


@dataclass
class BannerPoolItem:
    id: str
    model_score: float


@dataclass
class BannerScore:
    banner_id: str
    model_score: float
    boost_score: float
    boost_multiplier: float
    final_score: float
    loved_boost: float
    cart_boost: float
    viewed_boost: float
