import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import BannerMatcher, BannerPoolItem, HierarchyEnricher
from src.models import SessionFeatures

st.set_page_config(page_title="NBC Demo · Sephora", layout="wide", page_icon="🖤")

WORLD_GRADIENTS = {
    "Makeup":    "linear-gradient(135deg,#f8a5c2,#c84b81)",
    "Skincare":  "linear-gradient(135deg,#a8e6cf,#3d9970)",
    "Fragrance": "linear-gradient(135deg,#d7aefb,#7b2ff7)",
    "Hair":      "linear-gradient(135deg,#ffd89b,#d4960a)",
    "Tools":     "linear-gradient(135deg,#c9d6df,#636e72)",
}

BANNER_GRADIENTS = [
    "linear-gradient(135deg,#667eea,#764ba2)",
    "linear-gradient(135deg,#f093fb,#f5576c)",
    "linear-gradient(135deg,#4facfe,#00f2fe)",
    "linear-gradient(135deg,#43e97b,#38f9d7)",
    "linear-gradient(135deg,#fa709a,#fee140)",
    "linear-gradient(135deg,#a18cd1,#fbc2eb)",
    "linear-gradient(135deg,#fccb90,#d57eeb)",
    "linear-gradient(135deg,#e0c3fc,#8ec5fc)",
    "linear-gradient(135deg,#f6d365,#fda085)",
    "linear-gradient(135deg,#96fbc4,#f9f586)",
]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

#MainMenu, footer, .stDeployButton,
header[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] { display: none !important; }

.stApp { background: #f0f0f0; }

.block-container {
    padding-top: 0 !important;
    padding-bottom: 3rem !important;
    max-width: 1300px !important;
}

.hero {
    background: #1a1a1a;
    color: white;
    padding: 22px 32px 20px;
    margin: 0 -4rem 2rem -4rem;
    display: flex;
    align-items: center;
    gap: 20px;
}
.hero-logo {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 3px;
    text-transform: uppercase;
    border: 2px solid white;
    padding: 5px 9px;
    line-height: 1;
    flex-shrink: 0;
}
.hero-title { font-size: 18px; font-weight: 700; letter-spacing: -0.3px; }
.hero-sub   { font-size: 12px; color: #888; margin-top: 2px; }

.card {
    background: white;
    border-radius: 14px;
    box-shadow: 0 2px 16px rgba(0,0,0,0.07);
    overflow: hidden;
    margin-bottom: 16px;
    transition: box-shadow 0.22s ease, transform 0.22s ease;
}
.card:hover {
    box-shadow: 0 10px 36px rgba(0,0,0,0.13);
    transform: translateY(-3px);
}

.product-swatch {
    height: 220px;
    display: flex;
    align-items: flex-end;
    padding: 14px 18px;
    position: relative;
    overflow: hidden;
}
.product-img {
    position: absolute;
    inset: 0;
    width: 100%; height: 100%;
    object-fit: contain;
    transition: transform 0.35s ease;
}
.card:hover .product-img { transform: scale(1.06); }
.product-price-badge {
    background: rgba(255,255,255,0.93);
    color: #1a1a1a;
    font-size: 22px;
    font-weight: 800;
    padding: 6px 14px;
    border-radius: 8px;
    position: relative;
    z-index: 1;
}
.state-badges {
    position: absolute;
    top: 12px;
    right: 14px;
    display: flex;
    gap: 6px;
    z-index: 1;
}
.badge {
    background: rgba(255,255,255,0.93);
    border-radius: 20px;
    padding: 4px 10px;
    font-size: 12px;
    font-weight: 600;
}
.product-body { padding: 18px 20px 20px; }
.product-name {
    font-size: 19px;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 4px;
    line-height: 1.3;
}
.product-brand { font-size: 13px; font-weight: 500; color: #555; margin-bottom: 4px; }
.product-crumb { font-size: 11px; color: #aaa; letter-spacing: 0.2px; }

.nav-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 20px;
    border-top: 1px solid #f0f0f0;
    background: #fafafa;
    font-size: 12px;
    color: #888;
    font-weight: 500;
}

.stat-row { display: flex; gap: 10px; margin-bottom: 14px; }
.stat-tile {
    flex: 1;
    background: #1a1a1a;
    color: white;
    border-radius: 12px;
    padding: 18px 10px 14px;
    text-align: center;
}
.stat-value { font-size: 38px; font-weight: 800; line-height: 1; }
.stat-label { font-size: 10px; color: #888; margin-top: 6px; text-transform: uppercase; letter-spacing: 0.8px; }

.signals-card {
    background: white;
    border-radius: 12px;
    padding: 16px 18px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}
.signals-heading {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #aaa;
    font-weight: 700;
    margin-bottom: 10px;
}
.pill { display: inline-block; border-radius: 20px; padding: 4px 10px; font-size: 11px; font-weight: 600; margin: 3px 3px 3px 0; }
.pill-brand { background: #fce4ec; color: #c2185b; }
.pill-cat   { background: #e8f5e9; color: #2e7d32; }
.pill-world { background: #e8eaf6; color: #3949ab; }
.pill-empty { background: #f5f5f5; color: #aaa; }

.section-label {
    font-size: 13px;
    font-weight: 700;
    color: #1a1a1a;
    letter-spacing: -0.2px;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 2px solid #1a1a1a;
    display: inline-block;
}

.bcard {
    background: white;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,0.07);
    margin-bottom: 14px;
    border: 2px solid transparent;
    transition: transform 0.22s ease, box-shadow 0.22s ease;
    cursor: pointer;
}
.bcard:hover { transform: translateY(-6px); box-shadow: 0 14px 38px rgba(0,0,0,0.14); }
.bcard.boosted { border-color: #f07428; box-shadow: 0 4px 20px rgba(240,116,40,0.18); }
.bcard.boosted:hover { box-shadow: 0 14px 38px rgba(240,116,40,0.30); }

.bcard-swatch {
    height: 120px;
    display: flex; align-items: center; justify-content: center;
    position: relative; overflow: hidden;
}
.bcard-swatch img {
    width: 100%; height: 100%; object-fit: cover;
    position: absolute; top: 0; left: 0;
    transition: transform 0.35s ease;
}
.bcard:hover .bcard-swatch img { transform: scale(1.07); }
.bcard-swatch-overlay {
    position: absolute; inset: 0;
    background: linear-gradient(to top, rgba(0,0,0,0.55) 0%, transparent 55%);
    z-index: 1;
}
.bcard-rank {
    position: absolute;
    top: 9px; left: 9px;
    color: white;
    font-size: 22px; font-weight: 800;
    letter-spacing: -1px;
    z-index: 2;
    text-shadow: 0 2px 8px rgba(0,0,0,0.5);
    line-height: 1;
}
.bcard-type-overlay {
    position: absolute;
    bottom: 9px; left: 11px; right: 11px;
    color: white;
    font-size: 9px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 1.2px;
    z-index: 2;
    text-shadow: 0 1px 4px rgba(0,0,0,0.6);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.bcard-body { padding: 11px 13px 13px; }
.bcard-score         { font-size: 17px; font-weight: 800; color: #1a1a1a; margin-bottom: 5px; }
.bcard-score.boosted { color: #f07428; }
.bcard-detail { font-size: 10px; color: #aaa; font-weight: 400; }
.score-bar  { height: 3px; background: #f0f0f0; border-radius: 2px; margin-bottom: 9px; }
.score-fill { height: 3px; border-radius: 2px; }
.match-tags { display: flex; flex-wrap: wrap; gap: 4px; }
.mtag {
    background: #fff3e0; color: #bf360c;
    border-radius: 20px; padding: 2px 8px;
    font-size: 10px; font-weight: 700;
    border: 1px solid #ffe0b2;
}

.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    border: 1.5px solid #1a1a1a !important;
    background: white !important;
    color: #1a1a1a !important;
    transition: all 0.12s ease !important;
    padding: 0.45rem 1rem !important;
}
.stButton > button:hover  { background: #1a1a1a !important; color: white !important; }
.stButton > button:focus  { box-shadow: none !important; outline: none !important; }
</style>
"""


@st.cache_resource
def get_spark():
    from databricks.connect.session import DatabricksSession
    return DatabricksSession.builder.serverless().getOrCreate()


def _to_np_array(val):
    if val is None:
        return None
    items = [str(x) for x in val if x is not None and str(x).strip()]
    return np.array(items, dtype=object) if items else None


@st.cache_data(show_spinner="Loading data from Databricks...")
def load_tables():
    spark = get_spark()

    rows = spark.read.table("ml_prod_dev.ds_team.nbc_in_session_product_hierarchy").collect()
    product_hierarchy = {}
    for row in rows:
        r = row.asDict()
        pid = r.get("product_id")
        if pid:
            product_hierarchy[str(pid)] = {k: v for k, v in r.items() if k != "product_id"}

    rows = spark.read.table("ml_prod_dev.ds_team.nbc_in_session_banners_metadata").collect()
    banner_metadata = {}
    for row in rows:
        r = row.asDict()
        bid = r.get("entry_id") or r.get("banner_id")
        if not bid:
            continue
        meta = {k: v for k, v in r.items() if k != "entry_id"}
        for field in ("mentioned_brands", "mentioned_categories", "product_ids", "mentioned_worlds"):
            meta[field] = _to_np_array(meta.get(field))
        banner_metadata[str(bid)] = meta

    rows = spark.read.table("ml_prod_dev.ds_team.nbc_in_session_banners_images").collect()
    banner_images = {}
    for row in rows:
        r = row.asDict()
        bid = r.get("entry_id") or r.get("banner_id")
        url = r.get("image_url") or r.get("url")
        if bid and url:
            banner_images[str(bid)] = str(url)

    return product_hierarchy, banner_metadata, banner_images


def init_state():
    if "initialized" in st.session_state:
        return

    product_hierarchy, banner_metadata, banner_images = load_tables()

    product_ids = list(product_hierarchy.keys())
    random.shuffle(product_ids)

    banner_pool = [
        BannerPoolItem(id=bid, model_score=round(random.betavariate(2, 5), 4))
        for bid in banner_metadata
    ]
    random.shuffle(banner_pool)

    st.session_state.products = product_hierarchy
    st.session_state.product_ids = product_ids
    st.session_state.banners = banner_metadata
    st.session_state.banner_images = banner_images
    st.session_state.banner_pool = banner_pool
    st.session_state.enricher = HierarchyEnricher(product_hierarchy)
    st.session_state.matcher = BannerMatcher(banner_metadata)
    st.session_state.current_index = 0
    st.session_state.loved = set()
    st.session_state.cart = set()
    st.session_state.viewed = set()
    st.session_state.unloved = set()
    st.session_state.removed = set()
    st.session_state.initialized = True


def reset_session():
    for key in ("loved", "cart", "viewed", "unloved", "removed"):
        st.session_state[key] = set()
    st.session_state.current_index = 0


def go_prev():
    st.session_state.current_index = max(0, st.session_state.current_index - 1)


def go_next():
    st.session_state.current_index = min(
        len(st.session_state.product_ids) - 1,
        st.session_state.current_index + 1,
    )


def toggle_love():
    pid = st.session_state.product_ids[st.session_state.current_index]
    if pid in st.session_state.loved:
        st.session_state.loved.discard(pid)
        st.session_state.unloved.add(pid)
    else:
        st.session_state.loved.add(pid)
        st.session_state.unloved.discard(pid)


def toggle_cart():
    pid = st.session_state.product_ids[st.session_state.current_index]
    if pid in st.session_state.cart:
        st.session_state.cart.discard(pid)
        st.session_state.removed.add(pid)
    else:
        st.session_state.cart.add(pid)
        st.session_state.removed.discard(pid)


def get_session_features():
    return SessionFeatures(
        loved_ids=list(st.session_state.loved),
        basket_ids=list(st.session_state.cart),
        viewed_ids=list(st.session_state.viewed),
        unloved_ids=list(st.session_state.unloved),
        removed_basket_ids=list(st.session_state.removed),
    )


def get_ranked_banners():
    enriched = st.session_state.enricher.enrich_session_features(get_session_features())
    return st.session_state.matcher.rank_banners(st.session_state.banner_pool, enriched)


def get_session_signals():
    features = get_session_features()
    brands, categories, worlds = [], [], []
    for pid in features.loved_ids + features.basket_ids:
        p = st.session_state.products.get(pid, {})
        if p.get("brand_name"):
            brands.append(p["brand_name"])
        if p.get("third_level_category"):
            categories.append(p["third_level_category"])
        if p.get("first_level_category"):
            worlds.append(p["first_level_category"])
    top = lambda lst, n: [x for x, _ in Counter(lst).most_common(n)]
    return top(brands, 4), top(categories, 4), top(worlds, 3)


def pills_html(items, css_class, empty_label):
    if not items:
        return f'<span class="pill pill-empty">{empty_label}</span>'
    return "".join(f'<span class="pill {css_class}">{item}</span>' for item in items)


# ── Bootstrap ─────────────────────────────────────────────────────────────────

st.markdown(CSS, unsafe_allow_html=True)
st.markdown("""
<div class="hero">
    <div class="hero-logo">Sephora</div>
    <div>
        <div class="hero-title">Next Best Content — Interactive Demo</div>
        <div class="hero-sub">Real-time banner re-ranking from clickstream session signals</div>
    </div>
</div>
""", unsafe_allow_html=True)

init_state()

# ── Banner rankings ────────────────────────────────────────────────────────────

ranked = get_ranked_banners()
max_score = ranked[0].final_score if ranked else 1.0

st.markdown('<div class="section-label">Live Banner Rankings</div>', unsafe_allow_html=True)

banner_cols = st.columns(5)
for i, score in enumerate(ranked[:5]):
    with banner_cols[i]:
        banner = st.session_state.banners[score.banner_id]
        boosted = score.boost_score > 0
        bar_pct = round((score.final_score / max_score) * 100)
        bar_color = "#f07428" if boosted else "#1a1a1a"

        tags = []
        if score.loved_boost > 0:
            tags.append("❤️ love")
        if score.cart_boost > 0:
            tags.append("🛒 cart")
        if score.viewed_boost > 0:
            tags.append("👁 viewed")
        tags_html = "".join(f'<span class="mtag">{t}</span>' for t in tags)
        detail = (
            f'<div class="bcard-detail">{score.model_score:.3f} base × {score.boost_multiplier:.2f}x boost</div>'
            if boosted else
            f'<div class="bcard-detail">base score: {score.model_score:.3f}</div>'
        )

        image_url = st.session_state.banner_images.get(score.banner_id)
        if image_url:
            swatch_bg = f'<img src="{image_url}" alt="">'
        else:
            idx = abs(hash(score.banner_id)) % len(BANNER_GRADIENTS)
            swatch_bg = f'<div style="position:absolute;inset:0;background:{BANNER_GRADIENTS[idx]}"></div>'

        banner_type = banner.get('banner_type', '')
        promo_type = banner.get('promo_type', '')
        rank_label = f"0{i + 1}" if i < 9 else str(i + 1)
        type_label = f"{banner_type} · {promo_type}".strip(" ·")

        st.markdown(f"""
        <div class="bcard {'boosted' if boosted else ''}">
            <div class="bcard-swatch">
                {swatch_bg}
                <div class="bcard-swatch-overlay"></div>
                <div class="bcard-rank">{rank_label}</div>
                <div class="bcard-type-overlay">{type_label}</div>
            </div>
            <div class="bcard-body">
                <div class="bcard-score {'boosted' if boosted else ''}">{score.final_score:.3f}</div>
                {detail}
                <div class="score-bar"><div class="score-fill" style="width:{bar_pct}%;background:{bar_color}"></div></div>
                <div class="match-tags">{tags_html}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ── Product browser + session stats ───────────────────────────────────────────

st.write("")
col_left, col_stats = st.columns([5, 4], gap="large")

with col_left:
    current_pid = st.session_state.product_ids[st.session_state.current_index]
    st.session_state.viewed.add(current_pid)
    current_product = st.session_state.products[current_pid]
    n_products = len(st.session_state.product_ids)
    is_loved = current_pid in st.session_state.loved
    in_cart = current_pid in st.session_state.cart

    gradient = WORLD_GRADIENTS.get(
        current_product.get("first_level_category", ""),
        "linear-gradient(135deg,#e0e0e0,#9e9e9e)",
    )
    love_badge = '<span class="badge">❤️ Loved</span>' if is_loved else ""
    cart_badge = '<span class="badge">🛒 In Cart</span>' if in_cart else ""
    price = current_product.get("price")
    price_html = f'${price:.2f}' if price is not None else "—"

    product_image_url = current_product.get("image_url")
    product_img_tag = (
        f'<img class="product-img" src="{product_image_url}" alt="">'
        if product_image_url else ""
    )

    st.markdown(f"""
    <div class="card">
        <div class="product-swatch" style="background:{gradient}">
            {product_img_tag}
            <div class="state-badges">{love_badge}{cart_badge}</div>
            <div class="product-price-badge">{price_html}</div>
        </div>
        <div class="product-body">
            <div class="product-name">{current_product.get('product_name', current_pid)}</div>
            <div class="product-brand">{current_product.get('brand_name', '')}</div>
            <div class="product-crumb">
                {current_product.get('first_level_category', '')} &rsaquo;
                {current_product.get('second_level_category', '')} &rsaquo;
                {current_product.get('third_level_category', '')}
            </div>
        </div>
        <div class="nav-bar">
            <span>Product {st.session_state.current_index + 1} of {n_products}</span>
            <span>{current_pid}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    b1, b2 = st.columns(2)
    b1.button("❤️ Loved" if is_loved else "🤍 Love It", on_click=toggle_love, use_container_width=True)
    b2.button("✓ In Cart" if in_cart else "🛒 Add to Cart", on_click=toggle_cart, use_container_width=True)

    st.write("")
    n1, n2, n3 = st.columns([1, 5, 1])
    n1.button("← Prev", disabled=st.session_state.current_index == 0,
              on_click=go_prev, use_container_width=True)
    n2.markdown(
        f"<p style='text-align:center;margin:0;padding:6px 0;font-size:13px;"
        f"font-weight:600;color:#1a1a1a;letter-spacing:-0.2px'>"
        f"{st.session_state.current_index + 1} / {n_products}</p>",
        unsafe_allow_html=True,
    )
    n3.button("Next →", disabled=st.session_state.current_index == n_products - 1,
              on_click=go_next, use_container_width=True)

with col_stats:
    features = get_session_features()
    top_brands, top_cats, top_worlds = get_session_signals()

    st.markdown(f"""
    <div class="stat-row">
        <div class="stat-tile">
            <div class="stat-value">{len(features.loved_ids)}</div>
            <div class="stat-label">❤️ Loved</div>
        </div>
        <div class="stat-tile">
            <div class="stat-value">{len(features.basket_ids)}</div>
            <div class="stat-label">🛒 Cart</div>
        </div>
        <div class="stat-tile">
            <div class="stat-value">{len(features.viewed_ids)}</div>
            <div class="stat-label">👁 Viewed</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.button("↺ Reset Session", on_click=reset_session, use_container_width=True)
    st.write("")

    st.markdown(f"""
    <div class="signals-card">
        <div class="signals-heading">Session Signals</div>
        <div style="margin-bottom:10px">
            <div style="font-size:11px;color:#aaa;margin-bottom:5px;font-weight:600">BRANDS</div>
            {pills_html(top_brands, "pill-brand", "No interactions yet")}
        </div>
        <div style="margin-bottom:10px">
            <div style="font-size:11px;color:#aaa;margin-bottom:5px;font-weight:600">CATEGORIES</div>
            {pills_html(top_cats, "pill-cat", "No interactions yet")}
        </div>
        <div>
            <div style="font-size:11px;color:#aaa;margin-bottom:5px;font-weight:600">WORLDS</div>
            {pills_html(top_worlds, "pill-world", "No interactions yet")}
        </div>
    </div>
    """, unsafe_allow_html=True)
