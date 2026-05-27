from typing import Dict, List, Any
from .models import SessionFeatures, EnrichedFeatures


class HierarchyEnricher:
    """
    Enriches session features with product hierarchy metadata.
    """

    def __init__(self, product_hierarchy_map: Dict[str, Dict[str, Any]]):
        """
        Initialize hierarchy enricher.
        """
        self.product_hierarchy_map = product_hierarchy_map

    def extract_hierarchies(
        self,
        product_ids: List[str],
        fields: List[str] = None
    ) -> Dict[str, List[str]]:
        """
        Extract hierarchy information for a list of product IDs.
        COUNTS OCCURRENCES - same brand appears multiple times if multiple products have it.

        Args:
            product_ids: List of product IDs
            fields: List of hierarchy fields to extract (default: all important fields)

        Returns:
            Dictionary with hierarchy field names as keys and lists of values (with duplicates for counting)
        """
        if fields is None:
            fields = ['brand_name', 'first_level_category', 'second_level_category', 'third_level_category']

        result = {field: [] for field in fields}

        for product_id in product_ids:
            if product_id in self.product_hierarchy_map:
                product_info = self.product_hierarchy_map[product_id]
                for field in fields:
                    value = product_info.get(field)

                    if value and value.strip():
                        result[field].append(value)

        return result

    def enrich_session_features(
        self,
        session_features: SessionFeatures
    ) -> EnrichedFeatures:
        """
        Enrich session features with hierarchy information.

        Args:
            session_features: SessionFeatures object

        Returns:
            EnrichedFeatures with hierarchy information
        """
        enriched = EnrichedFeatures(
            loved_ids=session_features.loved_ids,
            basket_ids=session_features.basket_ids,
            viewed_ids=session_features.viewed_ids,
            purchased_ids=session_features.purchased_ids,
            banner_ids=session_features.banner_ids,
            unloved_ids=session_features.unloved_ids,
            removed_basket_ids=session_features.removed_basket_ids
        )

        hierarchy_fields = [
            ('brand_name', 'brands'),
            ('first_level_category', 'first_level_categories'),
            ('second_level_category', 'second_level_categories'),
            ('third_level_category', 'third_level_categories'),
        ]

        for prefix in ('loved', 'basket', 'viewed', 'purchased'):
            ids = getattr(session_features, f'{prefix}_ids')
            if ids:
                hierarchies = self.extract_hierarchies(ids)
                for hier_key, attr_suffix in hierarchy_fields:
                    setattr(enriched, f'{prefix}_{attr_suffix}', hierarchies[hier_key])

        return enriched
