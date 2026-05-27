import random
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src import BannerMatcher, BannerPoolItem, HierarchyEnricher, SessionProcessor
from src.models import SessionFeatures
from mock_data import generate_sample_banners, generate_sample_products

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

#MainMenu, footer, .stDeployButton { visibility: hidden; }

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
    margin: -1rem -1rem 2rem -1rem;
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
.hero-mode  {
    margin-left: auto;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    padding: 5px 12px;
    border-radius: 20px;
    border: 1.5px solid rgba(255,255,255,0.3);
    color: rgba(255,255,255,0.7);
}
.hero-mode.real { border-color: #43e97b; color: #43e97b; }

.card {
    background: white;
    border-radius: 14px;
    box-shadow: 0 2px 16px rgba(0,0,0,0.07);
    overflow: hidden;
    margin-bottom: 16px;
}

.product-swatch {
    height: 148px;
    display: flex;
    align-items: flex-end;
    padding: 14px 18px;
    position: relative;
}
.product-price-badge {
    background: rgba(255,255,255,0.93);
    color: #1a1a1a;
    font-size: 22px;
    font-weight: 800;
    padding: 6px 14px;
    border-radius: 8px;
}
.state-badges {
    position: absolute;
    top: 12px;
    right: 14px;
    display: flex;
    gap: 6px;
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

.nav-track { background: #e4e4e4; border-radius: 4px; height: 4px; margin-bottom: 4px; }
.nav-fill  { background: #1a1a1a; height: 4px; border-radius: 4px; transition: width 0.15s ease; }
.nav-label {
    font-size: 11px;
    color: #aaa;
    font-weight: 500;
    text-align: center;
    margin-bottom: 6px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.stSlider { padding: 0 !important; }
.stSlider > label { display: none !important; }
.stSlider [data-baseweb="slider"] > div:first-child {
    background: #e4e4e4 !important;
    height: 4px !important;
}
.stSlider [data-baseweb="slider"] [role="slider"] {
    background: #1a1a1a !important;
    border-color: #1a1a1a !important;
    width: 14px !important;
    height: 14px !important;
    top: -5px !important;
}
.stSlider [data-testid="stTickBar"] { display: none !important; }

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
    transition: transform 0.15s;
}
.bcard.boosted { border-color: #f07428; box-shadow: 0 4px 20px rgba(240,116,40,0.18); }
.bcard-swatch  { height: 96px; display: flex; align-items: center; justify-content: center; position: relative; }
.bcard-rank {
    position: absolute;
    top: 8px; left: 8px;
    background: rgba(0,0,0,0.45);
    color: white;
    font-size: 10px; font-weight: 700;
    border-radius: 20px; padding: 3px 8px;
    letter-spacing: 0.3px;
}
.bcard-id   { color: white; font-weight: 700; font-size: 13px; letter-spacing: 1.5px; text-shadow: 0 1px 6px rgba(0,0,0,0.25); }
.bcard-body { padding: 11px 13px 13px; }
.bcard-meta { font-size: 10px; color: #bbb; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 7px; }
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

.session-summary-body { padding: 20px 22px; }
.ss-section { margin-bottom: 16px; }
.ss-label {
    font-size: 10px; text-transform: uppercase;
    letter-spacing: 1px; color: #aaa;
    font-weight: 700; margin-bottom: 8px;
}
.pid-pill {
    display: inline-block;
    background: #f5f5f5; color: #444;
    border-radius: 6px; padding: 3px 8px;
    font-size: 11px; font-weight: 600;
    margin: 2px;
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


def init_state():
    if "initialized" in st.session_state:
        return
    random.seed(42)
    np.random.seed(42)
    products = generate_sample_products(100)
    banners = generate_sample_banners(20)
    st.session_state.products = products
    st.session_state.product_ids = list(products.keys())
    st.session_state.banners = banners
    st.session_state.banner_pool = [
        BannerPoolItem(id=bid, model_score=round(random.uniform(0.5, 1.0), 4))
        for bid in banners
    ]
    st.session_state.enricher = HierarchyEnricher(products)
    st.session_state.matcher = BannerMatcher(banners)
    st.session_state.current_index = 0
    st.session_state.nav_slider = 0
    st.session_state.loved = set()
    st.session_state.cart = set()
    st.session_state.viewed = set()
    st.session_state.unloved = set()
    st.session_state.removed = set()
    st.session_state.real_features = None
    st.session_state.real_load_error = None
    st.session_state.initialized = True


def reset_session():
    for key in ("loved", "cart", "viewed", "unloved", "removed"):
        st.session_state[key] = set()
    st.session_state.current_index = 0
    st.session_state.nav_slider = 0


def go_prev():
    new = max(0, st.session_state.current_index - 1)
    st.session_state.current_index = new
    st.session_state.nav_slider = new


def go_next():
    new = min(len(st.session_state.product_ids) - 1, st.session_state.current_index + 1)
    st.session_state.current_index = new
    st.session_state.nav_slider = new


def on_slider_change():
    st.session_state.current_index = st.session_state.nav_slider


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


def load_real_session(spark_master, user_id, session_id, minutes_back, hierarchy_table, banner_table):
    try:
        from pyspark.sql import SparkSession
        builder = SparkSession.builder.appName("nbc-demo")
        if spark_master:
            builder = builder.master(spark_master)
        spark = builder.getOrCreate()
        processor = SessionProcessor(spark)
        features = processor.get_session_features(
            user_id=user_id or None,
            session_id=session_id or None,
            minutes_back=minutes_back,
        )
        st.session_state.real_features = features

        if hierarchy_table:
            rows = spark.read.table(hierarchy_table).collect()
            hierarchy = {}
            for row in rows:
                r = row.asDict()
                pid = r.get("product_id") or r.get("atg_id") or r.get("id")
                if pid:
                    hierarchy[str(pid)] = r
            st.session_state.enricher = HierarchyEnricher(hierarchy)

        if banner_table:
            rows = spark.read.table(banner_table).collect()
            banners = {str(row["banner_id"]): row.asDict() for row in rows}
            st.session_state.banners = banners
            st.session_state.banner_pool = [
                BannerPoolItem(id=bid, model_score=round(random.uniform(0.5, 1.0), 4))
                for bid in banners
            ]
            st.session_state.matcher = BannerMatcher(banners)

        st.session_state.real_load_error = None
    except Exception as e:
        st.session_state.real_features = None
        st.session_state.real_load_error = str(e)


def is_real_mode():
    return st.session_state.get("data_source") == "Real Data"


def get_session_features():
    if is_real_mode() and st.session_state.real_features:
        return st.session_state.real_features
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


def pid_pills(ids, limit=12):
    if not ids:
        return '<span style="color:#ccc;font-size:12px">—</span>'
    visible = "".join(f'<span class="pid-pill">{pid}</span>' for pid in ids[:limit])
    more = f'<span style="font-size:11px;color:#aaa"> +{len(ids) - limit} more</span>' if len(ids) > limit else ""
    return visible + more


init_state()

with st.sidebar:
    st.markdown("### Configuration")
    st.radio("Data Source", ["Mock Data", "Real Data"], key="data_source")

    st.markdown("---")

    if is_real_mode():
        st.markdown("**Spark**")
        spark_master = st.text_input("Master URL", placeholder="Leave empty on Databricks (e.g. local[*])", key="spark_master")

        st.markdown("**Session Query**")
        st.radio("Query by", ["User ID", "Session ID"], key="query_by")

        if st.session_state.query_by == "User ID":
            st.text_input("User ID (atg_id)", key="user_id_input")
            st.slider("Minutes back", 5, 120, 30, key="minutes_back")
        else:
            st.text_input("Session ID (stag_id)", key="session_id_input")

        with st.expander("Advanced (optional)"):
            st.text_input("Hierarchy Table", placeholder="catalog.schema.products", key="hierarchy_table")
            st.text_input("Banner Table", placeholder="catalog.schema.banners", key="banner_table")

        if st.button("Load Session", use_container_width=True):
            uid = st.session_state.get("user_id_input") or None
            sid = st.session_state.get("session_id_input") or None
            load_real_session(
                spark_master=st.session_state.spark_master,
                user_id=uid,
                session_id=sid,
                minutes_back=st.session_state.get("minutes_back", 30),
                hierarchy_table=st.session_state.get("hierarchy_table") or None,
                banner_table=st.session_state.get("banner_table") or None,
            )

        if st.session_state.real_load_error:
            st.error(st.session_state.real_load_error)
        elif st.session_state.real_features:
            f = st.session_state.real_features
            n = len(f.viewed_ids) + len(f.loved_ids) + len(f.basket_ids) + len(f.purchased_ids)
            st.success(f"{n} events loaded")
    else:
        st.markdown("Interactively browse products and love or add to cart — banners re-rank in real time.")

mode_label = "Real Data" if is_real_mode() else "Mock Data"
mode_class = "real" if is_real_mode() else ""

st.markdown(CSS, unsafe_allow_html=True)
st.markdown(f"""
<div class="hero">
    <div class="hero-logo">Sephora</div>
    <div>
        <div class="hero-title">Next Best Content — Interactive Demo</div>
        <div class="hero-sub">Real-time banner re-ranking from clickstream session signals</div>
    </div>
    <div class="hero-mode {mode_class}">{mode_label}</div>
</div>
""", unsafe_allow_html=True)

ranked = get_ranked_banners()
max_score = ranked[0].final_score if ranked else 1.0

st.markdown('<div class="section-label">Live Banner Rankings</div>', unsafe_allow_html=True)

banner_cols = st.columns(5)
for i, score in enumerate(ranked[:5]):
    with banner_cols[i]:
        banner = st.session_state.banners[score.banner_id]
        boosted = score.boost_score > 0
        gradient = BANNER_GRADIENTS[int(score.banner_id.replace("BNR", "")) % len(BANNER_GRADIENTS)]
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

        st.markdown(f"""
        <div class="bcard {'boosted' if boosted else ''}">
            <div class="bcard-swatch" style="background:{gradient}">
                <div class="bcard-rank">#{i + 1}</div>
                <div class="bcard-id">{score.banner_id}</div>
            </div>
            <div class="bcard-body">
                <div class="bcard-meta">{banner['banner_type']} &middot; {banner['promo_type']}</div>
                <div class="bcard-score {'boosted' if boosted else ''}">{score.final_score:.3f}</div>
                {detail}
                <div class="score-bar"><div class="score-fill" style="width:{bar_pct}%;background:{bar_color}"></div></div>
                <div class="match-tags">{tags_html}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.write("")
col_left, col_stats = st.columns([5, 4], gap="large")

with col_left:
    if is_real_mode():
        features = st.session_state.real_features
        if features is None:
            st.markdown("""
            <div class="card">
                <div class="session-summary-body" style="text-align:center;padding:48px 24px;color:#aaa">
                    <div style="font-size:32px;margin-bottom:12px">⚙️</div>
                    <div style="font-size:14px;font-weight:600;color:#888">Configure a session in the sidebar and click <strong>Load Session</strong></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="card">
                <div class="session-summary-body">
                    <div style="font-size:15px;font-weight:700;margin-bottom:18px">Real Session Summary</div>
                    <div class="ss-section">
                        <div class="ss-label">Viewed ({len(features.viewed_ids)})</div>
                        {pid_pills(features.viewed_ids)}
                    </div>
                    <div class="ss-section">
                        <div class="ss-label">Loved ({len(features.loved_ids)})</div>
                        {pid_pills(features.loved_ids)}
                    </div>
                    <div class="ss-section">
                        <div class="ss-label">In Basket ({len(features.basket_ids)})</div>
                        {pid_pills(features.basket_ids)}
                    </div>
                    <div class="ss-section">
                        <div class="ss-label">Purchased ({len(features.purchased_ids)})</div>
                        {pid_pills(features.purchased_ids)}
                    </div>
                    <div class="ss-section">
                        <div class="ss-label">Unloved ({len(features.unloved_ids)})</div>
                        {pid_pills(features.unloved_ids)}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        current_pid = st.session_state.product_ids[st.session_state.current_index]
        st.session_state.viewed.add(current_pid)
        current_product = st.session_state.products[current_pid]
        n_products = len(st.session_state.product_ids)
        is_loved = current_pid in st.session_state.loved
        in_cart = current_pid in st.session_state.cart

        gradient = WORLD_GRADIENTS.get(current_product["first_level_category"], "linear-gradient(135deg,#e0e0e0,#9e9e9e)")
        love_badge = '<span class="badge">❤️ Loved</span>' if is_loved else ""
        cart_badge = '<span class="badge">🛒 In Cart</span>' if in_cart else ""

        st.markdown(f"""
        <div class="card">
            <div class="product-swatch" style="background:{gradient}">
                <div class="state-badges">{love_badge}{cart_badge}</div>
                <div class="product-price-badge">${current_product['price']:.2f}</div>
            </div>
            <div class="product-body">
                <div class="product-name">{current_product['product_name']}</div>
                <div class="product-brand">{current_product['brand_name']}</div>
                <div class="product-crumb">
                    {current_product['first_level_category']} &rsaquo;
                    {current_product['second_level_category']} &rsaquo;
                    {current_product['third_level_category']}
                </div>
            </div>
            <div class="nav-bar">
                <span>Product {st.session_state.current_index + 1} of {n_products}</span>
                <span>ID: {current_pid}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        b1, b2 = st.columns(2)
        b1.button("❤️ Loved" if is_loved else "🤍 Love It", on_click=toggle_love, use_container_width=True)
        b2.button("✓ In Cart" if in_cart else "🛒 Add to Cart", on_click=toggle_cart, use_container_width=True)

        st.write("")
        progress_pct = (st.session_state.current_index / max(1, n_products - 1)) * 100
        st.markdown(f"""
        <div class="nav-track"><div class="nav-fill" style="width:{progress_pct:.1f}%"></div></div>
        <div class="nav-label">
            {st.session_state.current_index + 1} / {n_products}
            &nbsp;·&nbsp; {current_product['product_name']}
        </div>
        """, unsafe_allow_html=True)

        n1, n2, n3 = st.columns([1, 10, 1])
        n1.button("←", disabled=st.session_state.current_index == 0, on_click=go_prev, use_container_width=True)
        with n2:
            st.slider("", min_value=0, max_value=n_products - 1, key="nav_slider",
                      on_change=on_slider_change, label_visibility="collapsed")
        n3.button("→", disabled=st.session_state.current_index == n_products - 1, on_click=go_next, use_container_width=True)

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

    if not is_real_mode():
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
