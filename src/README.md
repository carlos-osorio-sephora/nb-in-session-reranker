# NBC Re-ranking Source Code

This directory contains the core modules for the Next Best Content (NBC) re-ranking system. The implementation follows the exact logic from `NBC_Interactive_Demo.py`.

## Files

### `models.py`
Data models for session features.

- **SessionFeatures**: Dataclass containing user session data (loved_ids, basket_ids, viewed_ids, etc.)

### `session_processor.py`
Processes clickstream events from the online feature store.

- **SessionProcessor**: Extracts product IDs from clickstream events
  - Parses JSON values from PostgreSQL
  - Separates events by type (loved, cart, viewed, purchased, etc.)
  - Returns clean lists of product IDs

### `hierarchy_enricher.py`
Enriches product IDs with hierarchy metadata.

- **HierarchyEnricher**: Maps product IDs to brands, categories, and worlds
  - **Key Change**: Now counts occurrences instead of returning unique values
  - Example: If user views 3 NARS products, the brands list contains ['NARS', 'NARS', 'NARS']
  - This enables count-based accumulation in scoring

### `banner_matcher.py`
Computes banner scores and performs re-ranking.

- **BannerMatcher**: Implements multiplicative boosting with session features
  - **Complete rewrite** to match demo logic exactly
  - Counts occurrences of brands/categories/worlds
  - Applies different weights for loved/cart (high-intent) vs viewed (passive)
  - Formula: `Final Score = Model Score × min(1 + Boost Score, Max Multiplier)`

## Key Differences from Previous Implementation

### 1. Accumulation-Based Counting

**Before:**
```python
# Returned unique values only
['NARS', 'Dior']  # Even if user viewed 5 NARS products
```

**Now:**
```python
# Counts occurrences
['NARS', 'NARS', 'NARS', 'Dior', 'NARS', 'NARS']  # All 5 NARS counted
```

### 2. Separate Weights for Intent Levels

**Before:**
```python
# Single weight for all matches
product_matches['match_count'] * 3.0
brand_matches['match_count'] * 2.0
```

**Now:**
```python
# Different weights for loved/cart vs viewed
# Loved/Cart (high-intent)
loved_boost += weight_brand_match * count  # 0.3 × count
cart_boost += weight_brand_match * count   # 0.3 × count

# Viewed (lower intent)
viewed_boost += weight_viewed_brand * count  # 0.03 × count
```

### 3. Multiplicative Boosting

**Before:**
```python
# Simple match score
total_match_score = sum of weighted matches
```

**Now:**
```python
# Multiplicative with model scores
boost_multiplier = min(1 + boost_score, max_boost_multiplier)
final_score = model_score * boost_multiplier
```

## Usage Example

```python
from src import SessionProcessor, HierarchyEnricher, BannerMatcher, SessionFeatures

# 1. Get session features (from clickstream)
# processor = SessionProcessor(spark)
# session_features = processor.get_session_features(user_id)

# Or create manually for testing
session_features = SessionFeatures(
    loved_ids=['P001', 'P002'],
    basket_ids=['P003'],
    viewed_ids=['P001', 'P002', 'P003', 'P004', 'P005']
)

# 2. Enrich with hierarchy
enricher = HierarchyEnricher(product_hierarchy_map)
enriched_features = enricher.enrich_session_features(session_features)

# 3. Initialize matcher with weights
matcher = BannerMatcher(
    banner_metadata,
    weight_product_match=0.5,
    weight_brand_match=0.3,
    weight_category_match=0.15,
    weight_world_match=0.1,
    weight_viewed_product=0.05,
    weight_viewed_brand=0.03,
    weight_viewed_category=0.015,
    weight_viewed_world=0.01,
    max_boost_multiplier=2.0
)

# 4. Rank banners
banner_pool = [
    {'id': 'B001', 'model_score': 0.25},
    {'id': 'B002', 'model_score': 0.45},
    {'id': 'B003', 'model_score': 0.50}
]

ranked = matcher.rank_banners(banner_pool, enriched_features)

# 5. Get top N
top_5 = matcher.get_top_banners(banner_pool, enriched_features, top_n=5)
```

## Configuration

Default weights (can be overridden in constructor):

| Parameter | Loved/Cart | Viewed | Description |
|-----------|------------|--------|-------------|
| Product Match | 0.5 | 0.05 | Exact product ID match |
| Brand Match | 0.3 | 0.03 | Brand name match |
| Category Match | 0.15 | 0.015 | 3rd level category match |
| World Match | 0.1 | 0.01 | 1st level category match |

**Max Boost Multiplier**: 2.0 (prevents extreme boosts)

## Scoring Formula

```
Boost Score = Loved Boost + Cart Boost + Viewed Boost

Where:
  Loved Boost = Σ(Product Matches × 0.5) + Σ(Brand Matches × 0.3 × count) + ...
  Cart Boost  = Σ(Product Matches × 0.5) + Σ(Brand Matches × 0.3 × count) + ...
  Viewed Boost = Σ(Product Matches × 0.05) + Σ(Brand Matches × 0.03 × count) + ...

Boost Multiplier = min(1 + Boost Score, 2.0)

Final Score = Model Score × Boost Multiplier
```

## Testing

Run the example:

```bash
python example_usage.py
```

This will demonstrate:
- Session feature extraction
- Hierarchy enrichment with counting
- Boost score calculation
- Final ranking with model scores

## Integration with Databricks

For use in Databricks notebooks:

```python
# Load data
product_hierarchy = spark.sql("SELECT * FROM product_hierarchy_table").toPandas()
banner_metadata = spark.sql("SELECT * FROM banner_metadata_table").toPandas()

# Convert to dictionaries
product_hierarchy_map = dict(zip(product_hierarchy['product_id'], 
                                  product_hierarchy.to_dict('records')))
banner_metadata_map = dict(zip(banner_metadata['entry_id'], 
                                banner_metadata.to_dict('records')))

# Initialize
processor = SessionProcessor(spark)
enricher = HierarchyEnricher(product_hierarchy_map)
matcher = BannerMatcher(banner_metadata_map)

# Process user session
session_features = processor.get_session_features(user_id)
enriched = enricher.enrich_session_features(session_features)
ranked_banners = matcher.rank_banners(banner_pool, enriched)
```

## References

- **Demo Implementation**: `/NBC_Interactive_Demo.py`
- **Example Usage**: `/example_usage.py`
- **Confluence Documentation**: `/NBC_RERANKING_CONFLUENCE.md`
