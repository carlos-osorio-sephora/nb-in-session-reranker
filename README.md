# Sephora Clickstream Analysis

Session feature extraction from the clickstream online feature store in Unity Catalog for Next Best Content (NBC) and Next Best Offer (NBO) re-ranking.

## Overview

The clickstream data is available in Unity Catalog at:
```
ml_online_clickstream_prod.public.online_fs
```

Access it simply with:
```python
df = spark.read.table("ml_online_clickstream_prod.public.online_fs")
```

### Event Types

The following 8 event types are captured:

1. **add_to_basket** - Fields: `sku_ids`, `product_ids`
2. **add_to_loves** - Fields: `sku_ids`, `product_ids`
3. **cms_component_item_click** - Fields: `path`, `sid`
4. **cms_viewable_impression** - Fields: `path`, `sid`
5. **page_view** - Fields: `path`, `sku_ids`, `product_ids`
6. **purchase** - Fields: `price`, `quantity`, `sku_ids`, `product_ids`
7. **remove_from_basket** - Fields: `sku_ids`, `product_ids`
8. **un_love** - Fields: `sku_ids`, `product_ids`

## Usage

### Session Features (Primary Use Case)

Extract in-session user behavior for re-ranking:

```python
from src import SessionProcessor

# Initialize processor
processor = SessionProcessor()

# Get session features for last 30 minutes
features = processor.get_session_features(
    user_id="user_123",
    minutes_back=30
)

# Access the features
print(features.loved_ids)           # Products added to loves
print(features.unloved_ids)         # Products that were unloved
print(features.basket_ids)          # Products added to basket
print(features.removed_basket_ids)  # Products removed from basket
print(features.viewed_ids)          # Products viewed (from page view events)
print(features.purchased_ids)       # Products purchased
print(features.banner_ids)          # Banners shown (from cms viewable impression events)
```

### Hierarchy Enrichment

Enrich session features with product hierarchy information (brand, world, category, subcategory):

```python
from src import SessionProcessor, HierarchyEnricher

# Product hierarchy map
product_hierarchy = {
    'P0250': {
        'product_name': 'Duo Eyeshadow',
        'brand_name': 'NARS',
        'fragrances': None,
        'first_level_category': 'Makeup',
        'second_level_category': 'Eye',
        'third_level_category': 'Eyeshadow'
    },
    # ... more products
}

# Get session features
processor = SessionProcessor()
features = processor.get_session_features(user_id="user_123", minutes_back=30)

# Enrich with hierarchies
enricher = HierarchyEnricher(product_hierarchy)
enriched = enricher.enrich_session_features(features)

# Access hierarchy information
print(enriched['basket_brands'])                      # Brands in basket
print(enriched['basket_first_level_categories'])      # First level categories in basket
print(enriched['basket_third_level_categories'])      # Third level categories in basket
print(enriched['viewed_second_level_categories'])     # Second level categories viewed

# Get overall session summary
summary = enricher.get_hierarchy_summary(features)
print(summary['all_brands'])                 # All unique brands across session
print(summary['all_first_level_categories']) # All first level categories
```

### Banner Matching

Compute exact matches between banner metadata and session features for re-ranking:

```python
from src import SessionProcessor, HierarchyEnricher, BannerMatcher
import numpy as np

# Banner metadata
banner_metadata = {
    '1cfPsmkhSzOyHAP0kIF0Lp': {
        'banner_type': 'promotion',
        'promo_type': 'rewards',
        'mentioned_brands': np.array(['tarte', 'ILIA', 'MAC Cosmetics']),
        'mentioned_categories': np.array(['Foundation', 'Concealer']),
        'product_ids': np.array(['P516655', 'P522132']),
        'mentioned_worlds': np.array(['Makeup', 'Skincare'])
    }
}

# Get and enrich session features
processor = SessionProcessor()
enricher = HierarchyEnricher(product_hierarchy)
features = processor.get_session_features(user_id="user_123", minutes_back=30)
enriched = enricher.enrich_session_features(features)

# Compute banner matches
matcher = BannerMatcher(banner_metadata)
match_result = matcher.compute_banner_match('1cfPsmkhSzOyHAP0kIF0Lp', enriched)

print(match_result['total_match_score'])      # Overall match score
print(match_result['product_matches'])        # Product match details
print(match_result['brand_matches'])          # Brand match details

# Get top matching banners
top_banners = matcher.get_top_banners(enriched, top_n=5, min_score=1.0)
```

### Using Session Features for Re-ranking

```python
# Get session features and compute banner matches
features = processor.get_session_features(user_id="user_123", minutes_back=30)
enriched = enricher.enrich_session_features(features)

# Get WDL model candidates
nbc_candidates = wdl_model.predict(user_id)  # Your existing WDL model

# Compute match scores for each candidate
matcher = BannerMatcher(banner_metadata)
for candidate in nbc_candidates:
    match_result = matcher.compute_banner_match(candidate.banner_id, enriched)
    
    # Combine WDL score with session match score
    candidate.final_score = (
        0.6 * candidate.wdl_score +  # 60% from WDL model
        0.4 * min(match_result['total_match_score'] / 10, 1.0)  # 40% from session
    )

# Re-rank by combined score
nbc_candidates.sort(key=lambda x: x.final_score, reverse=True)

# Return top N
return nbc_candidates[:10]
```

### Direct Spark SQL

```python
# Read the table directly
df = spark.read.table("ml_online_clickstream_prod.public.online_fs")

# Or use SQL
spark.sql("""
    SELECT * 
    FROM ml_online_clickstream_prod.public.online_fs
    WHERE user_id = 'user_123'
    LIMIT 100
""").show()
```

## Available Functions

### Get Recent User Events
```python
events = features.get_user_events(
    user_id="user_123",
    event_types=['add_to_basket', 'purchase'],
    hours_back=24,
    limit=50
)
```

### Get Basket Additions
```python
basket = features.get_recent_basket_additions(
    user_id="user_123",
    hours=24
)
```

### Get User's Loved Items
```python
loves = features.get_user_loves(
    user_id="user_123",
    active_only=True  # Excludes unloved items
)
```

### Get Purchase History
```python
purchases = features.get_user_purchases(
    user_id="user_123",
    days_back=30
)
```

### Get Page Views
```python
page_views = features.get_page_views(
    user_id="user_123",
    path_pattern='/product%',
    hours=48
)
```

### Get Product Interactions
```python
interactions = features.get_product_interactions(
    user_id="user_123",
    product_id="P12345",
    hours=168  # Last 7 days
)
```

### Get Event Summary
```python
summary = features.get_event_summary(
    user_id="user_123",
    days=7
)
```

### Bulk User Features (for model training)
```python
bulk_features = features.get_bulk_user_features(
    user_ids=["user_1", "user_2", "user_3"],
    days=7
)
# Returns pivoted DataFrame with event counts per user
```

## Converting to Pandas

```python
# Convert any Spark DataFrame to Pandas
pandas_df = events.toPandas()
```

## Project Structure

```
.
├── src/
│   ├── __init__.py
│   ├── models.py                      # SessionFeatures dataclass
│   ├── session_processor.py           # Main session feature extraction
│   ├── hierarchy_enricher.py          # Product hierarchy enrichment
│   └── banner_matcher.py              # Banner matching and scoring
├── demo/
│   ├── NBC_Interactive_Demo.py        # Interactive Databricks demo
│   ├── sample_data.py                 # Sample data generation
│   ├── interactive_demo.py            # Demo helper functions
│   └── README.md                      # Demo documentation
├── tests/
│   └── __init__.py
├── clickstream_features.py            # Legacy: general feature extraction
├── example_usage.py                   # Legacy examples
├── example_session_features.py        # Session feature examples
├── example_hierarchy_enrichment.py    # Hierarchy enrichment examples
├── example_banner_matching.py         # Banner matching examples
└── README.md                          # This file
```

## Features

- **Session Feature Extraction**: Extract user behavior within configurable time windows
- **Hierarchy Enrichment**: Enrich product IDs with brand, world, category, and subcategory
- **Banner Matching**: Compute exact matches between banner metadata and session features
- **Match Scoring**: Weighted scoring across products, brands, categories, and worlds
- **Re-ranking Ready**: Output format designed for NBC/NBO re-ranking
- **Product Views**: Extracted from page view events with product_ids
- **Banner Tracking**: Track which banners were shown (cms viewable impression events)
- **Negative Signals**: Track unloved and removed items for better personalization
- **Simple Integration**: Works with existing Spark sessions in Databricks
- **Flexible Time Windows**: Support for relative (last N minutes) and absolute time ranges

## Interactive Demo

Try the live demo in Databricks to see real-time banner re-ranking:

```bash
# Navigate to demo folder
cd demo/

# See demo/README.md for detailed instructions
```

The demo includes:
- 100 sample products to browse
- 20 sample banners with images
- Love and Add to Cart interactions
- Real-time banner re-ranking
- Visual match score feedback

## Next Steps

Integrate these features into your Next Best Content and Next Best Offer models by:

1. Try the **interactive demo** in `demo/` folder to see it in action
2. Extract relevant features for your user base
3. Aggregate events into meaningful features (counts, recency, etc.)
4. Join with your existing model features
5. Combine WDL scores with session match scores for final ranking
