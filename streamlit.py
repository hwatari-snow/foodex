"""
Foodex Buyer Dashboard
小売バイヤー向け売上・在庫分析ダッシュボード
(Streamlit in Snowflake対応版)
"""

import streamlit as st
import pandas as pd
import altair as alt
import json
from datetime import timedelta

st.set_page_config(
    page_title="Foodex Buyer Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Snowflake接続 (SiS用)
from snowflake.snowpark.context import get_active_session
session = get_active_session()

# ---------------------------------------------------------------------------
# カスタムCSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
/* ---------- フォント & 全体 ---------- */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;600;700&display=swap');
html, body, [class*="st-"] {
    font-family: 'Inter', 'Noto Sans JP', sans-serif;
}

/* ---------- サイドバー ---------- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f1724 0%, #1a2744 100%);
}
section[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
    background-color: #3b82f6 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.1);
}

/* ---------- メトリクスカード ---------- */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.03);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
}
div[data-testid="stMetric"] label {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748b !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: #0f172a !important;
}

/* ---------- タブ ---------- */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #f1f5f9;
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 0.88rem;
    color: #475569;
    background: transparent;
    border: none;
    transition: all 0.2s ease;
}
.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: #0f172a !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

/* ---------- DataFrame テーブル ---------- */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #e2e8f0;
}

/* ---------- Expander ---------- */
.streamlit-expanderHeader {
    font-weight: 600;
    font-size: 0.95rem;
    border-radius: 10px;
}

/* ---------- アイコンフォント文字化け非表示 ---------- */
span[data-testid="stIconMaterial"],
[class*="keyboard"],
[class*="arrow"],
[data-baseweb="icon"],
.material-icons,
span:has(> svg[data-testid]),
div[data-testid="stExpanderToggleIcon"] {
    display: none !important;
    visibility: hidden !important;
    width: 0 !important;
    height: 0 !important;
    overflow: hidden !important;
}

/* Keyboard文字化け強制非表示 */
body *:not(script):not(style) {
    font-variant-ligatures: none;
}

/* ---------- チャットメッセージ ---------- */
.stChatMessage {
    border-radius: 16px;
    border: 1px solid #e2e8f0;
    padding: 16px;
}

/* ---------- ボタン ---------- */
.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    padding: 8px 20px;
    border: 1px solid #e2e8f0;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    border-color: #3b82f6;
    color: #3b82f6;
}

/* ---------- Intelligenceボタン ---------- */
.intelligence-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
    color: white !important;
    padding: 12px 24px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.95rem;
    text-decoration: none;
    box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
    transition: all 0.3s ease;
    border: none;
}
.intelligence-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45);
    color: white !important;
    text-decoration: none;
}
.intelligence-btn .sparkle {
    font-size: 1.1rem;
}

/* ---------- サンプル質問ボタン ---------- */
div[data-testid="stColumns"] .stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #eff6ff, #f0f9ff);
    border: 1px solid #bfdbfe;
    color: #1e40af;
    font-size: 0.85rem;
    border-radius: 12px;
}
div[data-testid="stColumns"] .stButton > button:hover {
    background: linear-gradient(135deg, #dbeafe, #e0f2fe);
    border-color: #3b82f6;
}

/* ---------- divider ---------- */
hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 1.5rem 0;
}

/* ---------- ヘッダーセクション ---------- */
.dashboard-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #1e40af 100%);
    border-radius: 20px;
    padding: 32px 40px;
    margin-bottom: 24px;
    color: white;
    position: relative;
    overflow: hidden;
}
.dashboard-header::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 400px;
    height: 400px;
    background: radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%);
    border-radius: 50%;
}
.dashboard-header h1 {
    font-size: 2rem;
    font-weight: 700;
    margin: 0 0 4px 0;
    color: white;
    position: relative;
}
.dashboard-header p {
    font-size: 0.95rem;
    color: #94a3b8;
    margin: 0;
    position: relative;
}

/* ---------- セクションヘッダー ---------- */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 8px 0 16px 0;
}
.section-header .icon {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
}
.section-header .icon.blue { background: #eff6ff; }
.section-header .icon.green { background: #f0fdf4; }
.section-header .icon.orange { background: #fff7ed; }
.section-header .icon.purple { background: #faf5ff; }
.section-header h3 {
    font-size: 1.1rem;
    font-weight: 700;
    color: #0f172a;
    margin: 0;
}

/* ---------- ステータスバッジ ---------- */
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 10px 16px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.9rem;
    margin: 4px 0;
    width: 100%;
    box-sizing: border-box;
}
.status-badge.critical { background: #fef2f2; color: #991b1b; border: 1px solid #fecaca; }
.status-badge.warning { background: #fffbeb; color: #92400e; border: 1px solid #fde68a; }
.status-badge.info { background: #eff6ff; color: #1e40af; border: 1px solid #bfdbfe; }
.status-badge.success { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; }

/* ---------- フッター ---------- */
.dashboard-footer {
    text-align: center;
    padding: 20px 0;
    color: #94a3b8;
    font-size: 0.82rem;
    letter-spacing: 0.05em;
}
.dashboard-footer span {
    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

def run_query(sql, params=None):
    """SQLを実行してDataFrameを返す"""
    if params:
        for key, value in params.items():
            if isinstance(value, str):
                sql = sql.replace(f":{key}", f"'{value}'")
            else:
                sql = sql.replace(f":{key}", str(value))
    return session.sql(sql).to_pandas()

# データ取得関数（キャッシュ付き）
@st.cache_data(ttl=600)
def get_categories():
    """カテゴリ一覧を取得"""
    return run_query("""
        SELECT DISTINCT 
            CATEGORY_LARGE, 
            CATEGORY_MEDIUM, 
            CATEGORY_SMALL
        FROM FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER
        ORDER BY CATEGORY_LARGE, CATEGORY_MEDIUM, CATEGORY_SMALL
    """)

@st.cache_data(ttl=600)
def get_stores():
    """店舗一覧を取得"""
    return run_query("""
        SELECT STORE_ID, STORE_NAME, PREFECTURE, STORE_FORMAT
        FROM FOODEX_DEMO.BUYER_AGENT.STORE_MASTER
        ORDER BY STORE_ID
    """)

@st.cache_data(ttl=600)
def get_manufacturers():
    """メーカー一覧を取得"""
    df = run_query("""
        SELECT DISTINCT MANUFACTURER_NAME
        FROM FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER
        ORDER BY MANUFACTURER_NAME
    """)
    return df["MANUFACTURER_NAME"].tolist()

@st.cache_data(ttl=600)
def get_date_range():
    """取引日の範囲を取得"""
    df = run_query("""
        SELECT 
            MIN(TRANSACTION_DATE) as MIN_DATE,
            MAX(TRANSACTION_DATE) as MAX_DATE
        FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS
    """)
    return df.iloc[0]["MIN_DATE"], df.iloc[0]["MAX_DATE"]

@st.cache_data(ttl=300)
def get_sales_summary(start_date, end_date, categories, stores, manufacturers):
    """売上サマリーを取得"""
    where_clauses = [f"t.TRANSACTION_DATE BETWEEN '{start_date}' AND '{end_date}'"]
    
    if categories:
        where_clauses.append("p.CATEGORY_LARGE IN ({})".format(
            ",".join([f"'{c}'" for c in categories])
        ))
    if stores:
        where_clauses.append("t.STORE_ID IN ({})".format(
            ",".join([f"'{s}'" for s in stores])
        ))
    if manufacturers:
        where_clauses.append("p.MANUFACTURER_NAME IN ({})".format(
            ",".join([f"'{m}'" for m in manufacturers])
        ))
    
    where_clause = " AND ".join(where_clauses)
    
    df = run_query(f"""
        SELECT 
            SUM(t.SALES_AMOUNT) as TOTAL_SALES,
            SUM(t.QUANTITY) as TOTAL_QUANTITY,
            COUNT(DISTINCT t.TRANSACTION_ID) as TRANSACTION_COUNT,
            COUNT(DISTINCT t.CUSTOMER_ID) as UNIQUE_CUSTOMERS,
            COUNT(DISTINCT t.BASKET_ID) as BASKET_COUNT,
            SUM(t.SALES_AMOUNT - t.QUANTITY * p.COST_PRICE) as GROSS_PROFIT
        FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
        JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
        WHERE {where_clause}
    """)
    return df.iloc[0]

@st.cache_data(ttl=300)
def get_daily_sales(start_date, end_date, categories, stores, manufacturers):
    """日別売上を取得"""
    where_clauses = [f"t.TRANSACTION_DATE BETWEEN '{start_date}' AND '{end_date}'"]
    
    if categories:
        where_clauses.append("p.CATEGORY_LARGE IN ({})".format(
            ",".join([f"'{c}'" for c in categories])
        ))
    if stores:
        where_clauses.append("t.STORE_ID IN ({})".format(
            ",".join([f"'{s}'" for s in stores])
        ))
    if manufacturers:
        where_clauses.append("p.MANUFACTURER_NAME IN ({})".format(
            ",".join([f"'{m}'" for m in manufacturers])
        ))
    
    where_clause = " AND ".join(where_clauses)
    
    return run_query(f"""
        SELECT 
            t.TRANSACTION_DATE,
            SUM(t.SALES_AMOUNT) as SALES_AMOUNT,
            SUM(t.QUANTITY) as QUANTITY
        FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
        JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
        WHERE {where_clause}
        GROUP BY t.TRANSACTION_DATE
        ORDER BY t.TRANSACTION_DATE
    """)

@st.cache_data(ttl=300)
def get_category_sales(start_date, end_date, categories, stores, manufacturers):
    """カテゴリ別売上を取得"""
    where_clauses = [f"t.TRANSACTION_DATE BETWEEN '{start_date}' AND '{end_date}'"]
    
    if categories:
        where_clauses.append("p.CATEGORY_LARGE IN ({})".format(
            ",".join([f"'{c}'" for c in categories])
        ))
    if stores:
        where_clauses.append("t.STORE_ID IN ({})".format(
            ",".join([f"'{s}'" for s in stores])
        ))
    if manufacturers:
        where_clauses.append("p.MANUFACTURER_NAME IN ({})".format(
            ",".join([f"'{m}'" for m in manufacturers])
        ))
    
    where_clause = " AND ".join(where_clauses)
    
    return run_query(f"""
        SELECT 
            p.CATEGORY_LARGE,
            SUM(t.SALES_AMOUNT) as SALES_AMOUNT,
            SUM(t.QUANTITY) as QUANTITY,
            SUM(t.SALES_AMOUNT - t.QUANTITY * p.COST_PRICE) as GROSS_PROFIT
        FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
        JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
        WHERE {where_clause}
        GROUP BY p.CATEGORY_LARGE
        ORDER BY SALES_AMOUNT DESC
    """)

@st.cache_data(ttl=300)
def get_top_products(start_date, end_date, categories, stores, manufacturers, limit=20):
    """売上TOP商品を取得"""
    where_clauses = [f"t.TRANSACTION_DATE BETWEEN '{start_date}' AND '{end_date}'"]
    
    if categories:
        where_clauses.append("p.CATEGORY_LARGE IN ({})".format(
            ",".join([f"'{c}'" for c in categories])
        ))
    if stores:
        where_clauses.append("t.STORE_ID IN ({})".format(
            ",".join([f"'{s}'" for s in stores])
        ))
    if manufacturers:
        where_clauses.append("p.MANUFACTURER_NAME IN ({})".format(
            ",".join([f"'{m}'" for m in manufacturers])
        ))
    
    where_clause = " AND ".join(where_clauses)
    
    return run_query(f"""
        SELECT 
            p.PRODUCT_ID,
            p.PRODUCT_NAME,
            p.BRAND_NAME,
            p.MANUFACTURER_NAME,
            p.CATEGORY_LARGE,
            p.IS_NEW_PRODUCT,
            SUM(t.SALES_AMOUNT) as SALES_AMOUNT,
            SUM(t.QUANTITY) as QUANTITY,
            SUM(t.SALES_AMOUNT - t.QUANTITY * p.COST_PRICE) as GROSS_PROFIT,
            ROUND(SUM(t.SALES_AMOUNT - t.QUANTITY * p.COST_PRICE) / NULLIF(SUM(t.SALES_AMOUNT), 0) * 100, 1) as GROSS_MARGIN_PCT,
            COUNT(DISTINCT t.CUSTOMER_ID) as UNIQUE_CUSTOMERS
        FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
        JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
        WHERE {where_clause}
        GROUP BY p.PRODUCT_ID, p.PRODUCT_NAME, p.BRAND_NAME, p.MANUFACTURER_NAME, 
                 p.CATEGORY_LARGE, p.IS_NEW_PRODUCT
        ORDER BY SALES_AMOUNT DESC
        LIMIT {limit}
    """)

@st.cache_data(ttl=300)
def get_new_products_performance(start_date, end_date):
    """新商品パフォーマンスを取得"""
    return run_query(f"""
        SELECT 
            p.PRODUCT_ID,
            p.PRODUCT_NAME,
            p.BRAND_NAME,
            p.MANUFACTURER_NAME,
            p.CATEGORY_LARGE,
            p.LAUNCH_DATE,
            SUM(t.SALES_AMOUNT) as SALES_AMOUNT,
            SUM(t.QUANTITY) as QUANTITY,
            COUNT(DISTINCT t.CUSTOMER_ID) as UNIQUE_CUSTOMERS,
            COUNT(DISTINCT t.STORE_ID) as SELLING_STORES
        FROM FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p
        JOIN FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t ON p.PRODUCT_ID = t.PRODUCT_ID
        WHERE p.IS_NEW_PRODUCT = TRUE
          AND t.TRANSACTION_DATE BETWEEN '{start_date}' AND '{end_date}'
        GROUP BY p.PRODUCT_ID, p.PRODUCT_NAME, p.BRAND_NAME, p.MANUFACTURER_NAME, 
                 p.CATEGORY_LARGE, p.LAUNCH_DATE
        ORDER BY SALES_AMOUNT DESC
    """)

@st.cache_data(ttl=300)
def get_inventory_status():
    """在庫状況を取得"""
    return run_query("""
        SELECT 
            i.STORE_ID,
            s.STORE_NAME,
            p.PRODUCT_ID,
            p.PRODUCT_NAME,
            p.CATEGORY_LARGE,
            p.MANUFACTURER_NAME,
            i.STOCK_QUANTITY,
            i.REORDER_POINT,
            i.SAFETY_STOCK,
            i.DAYS_OF_SUPPLY,
            CASE
                WHEN i.STOCK_QUANTITY = 0 THEN '欠品'
                WHEN i.STOCK_QUANTITY <= i.SAFETY_STOCK THEN '要緊急発注'
                WHEN i.STOCK_QUANTITY <= i.REORDER_POINT THEN '要発注'
                WHEN i.DAYS_OF_SUPPLY > 30 THEN '過剰在庫'
                ELSE '適正'
            END as STOCK_STATUS
        FROM FOODEX_DEMO.BUYER_AGENT.INVENTORY i
        JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON i.PRODUCT_ID = p.PRODUCT_ID
        JOIN FOODEX_DEMO.BUYER_AGENT.STORE_MASTER s ON i.STORE_ID = s.STORE_ID
        WHERE i.INVENTORY_DATE = (SELECT MAX(INVENTORY_DATE) FROM FOODEX_DEMO.BUYER_AGENT.INVENTORY)
        ORDER BY 
            CASE 
                WHEN i.STOCK_QUANTITY = 0 THEN 1
                WHEN i.STOCK_QUANTITY <= i.SAFETY_STOCK THEN 2
                WHEN i.STOCK_QUANTITY <= i.REORDER_POINT THEN 3
                ELSE 4
            END,
            p.PRODUCT_NAME
    """)

@st.cache_data(ttl=300)
def search_products(keyword, category, manufacturer):
    """商品検索"""
    where_clauses = ["1=1"]
    
    if keyword:
        escaped_keyword = keyword.replace("'", "''")
        where_clauses.append(f"(PRODUCT_NAME ILIKE '%{escaped_keyword}%' OR BRAND_NAME ILIKE '%{escaped_keyword}%' OR PRODUCT_DESCRIPTION ILIKE '%{escaped_keyword}%')")
    if category:
        where_clauses.append(f"CATEGORY_LARGE = '{category}'")
    if manufacturer:
        escaped_manufacturer = manufacturer.replace("'", "''")
        where_clauses.append(f"MANUFACTURER_NAME = '{escaped_manufacturer}'")
    
    where_clause = " AND ".join(where_clauses)
    
    return run_query(f"""
        SELECT 
            PRODUCT_ID,
            PRODUCT_NAME,
            BRAND_NAME,
            MANUFACTURER_NAME,
            CATEGORY_LARGE,
            CATEGORY_MEDIUM,
            UNIT_PRICE,
            COST_PRICE,
            UNIT_VOLUME || UNIT_MEASURE as UNIT_SIZE,
            IS_NEW_PRODUCT,
            PRODUCT_DESCRIPTION
        FROM FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER
        WHERE {where_clause}
        ORDER BY PRODUCT_NAME
    """)

# ---------------------------------------------------------------------------
# サイドバー：フィルター
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("#### FILTERS")
    st.caption("分析対象を絞り込み")
    st.markdown("---")

    min_date, max_date = get_date_range()
    min_date = pd.to_datetime(min_date).date()
    max_date = pd.to_datetime(max_date).date()

    date_range = st.date_input(
        "期間",
        value=(max_date - timedelta(days=30), max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range[0]

    st.markdown("---")

    categories_df = get_categories()
    all_categories = categories_df["CATEGORY_LARGE"].unique().tolist()
    selected_categories = st.multiselect(
        "カテゴリ（大分類）",
        options=all_categories,
        default=[],
    )

    stores_df = get_stores()
    store_options = {
        f"{row['STORE_NAME']} ({row['STORE_ID']})": row["STORE_ID"]
        for _, row in stores_df.iterrows()
    }
    selected_store_names = st.multiselect(
        "店舗",
        options=list(store_options.keys()),
        default=[],
    )
    selected_stores = [store_options[name] for name in selected_store_names]

    all_manufacturers = get_manufacturers()
    selected_manufacturers = st.multiselect(
        "メーカー",
        options=all_manufacturers,
        default=[],
    )

    st.markdown("---")
    st.caption(f"データ範囲: {min_date} 〜 {max_date}")

# ---------------------------------------------------------------------------
# ヘッダー
# ---------------------------------------------------------------------------
# Snowflake Intelligence URLを動的に生成
@st.cache_data(ttl=3600)
def get_intelligence_url():
    """現在のアカウント情報からIntelligence URLを生成"""
    result = session.sql("""
        SELECT 
            CURRENT_ORGANIZATION_NAME() as ORG_NAME,
            CURRENT_ACCOUNT_NAME() as ACCOUNT_NAME
    """).collect()
    org_name = result[0]["ORG_NAME"].lower()
    account_name = result[0]["ACCOUNT_NAME"].lower()
    return f"https://ai.snowflake.com/{org_name}/{account_name}"

INTELLIGENCE_URL = get_intelligence_url()

st.markdown(f"""
<div class="dashboard-header">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; position: relative;">
        <div>
            <h1>Foodex Buyer Dashboard</h1>
            <p>小売バイヤー向け  売上・在庫・商品 統合分析プラットフォーム</p>
        </div>
        <a href="{INTELLIGENCE_URL}" target="_blank" class="intelligence-btn">
            <span class="sparkle">✨</span>
            Intelligenceに聞いてみる
        </a>
    </div>
</div>
""", unsafe_allow_html=True)

# タブ
tab1, tab2, tab3, tab4 = st.tabs([
    "売上概要",
    "商品分析",
    "在庫状況",
    "商品検索",
])

# ---------------------------------------------------------------------------
# タブ1: 売上概要
# ---------------------------------------------------------------------------
with tab1:
    summary = get_sales_summary(
        start_date, end_date, selected_categories, selected_stores, selected_manufacturers
    )

    gross_margin = (
        (summary["GROSS_PROFIT"] / summary["TOTAL_SALES"] * 100)
        if summary["TOTAL_SALES"]
        else 0
    )
    avg_basket = (
        (summary["TOTAL_SALES"] / summary["BASKET_COUNT"])
        if summary["BASKET_COUNT"]
        else 0
    )

    row1 = st.columns(4)
    kpi_data_row1 = [
        ("売上合計", f"¥{summary['TOTAL_SALES']:,.0f}" if pd.notna(summary["TOTAL_SALES"]) else "¥0"),
        ("粗利合計", f"¥{summary['GROSS_PROFIT']:,.0f}" if pd.notna(summary["GROSS_PROFIT"]) else "¥0"),
        ("粗利率", f"{gross_margin:.1f}%" if pd.notna(gross_margin) else "0%"),
        ("取引件数", f"{summary['TRANSACTION_COUNT']:,.0f}" if pd.notna(summary["TRANSACTION_COUNT"]) else "0"),
    ]
    for col, (label, value) in zip(row1, kpi_data_row1):
        col.metric(label=label, value=value)

    row2 = st.columns(4)
    kpi_data_row2 = [
        ("販売数量", f"{summary['TOTAL_QUANTITY']:,.0f}" if pd.notna(summary["TOTAL_QUANTITY"]) else "0"),
        ("ユニーク顧客数", f"{summary['UNIQUE_CUSTOMERS']:,.0f}" if pd.notna(summary["UNIQUE_CUSTOMERS"]) else "0"),
        ("バスケット数", f"{summary['BASKET_COUNT']:,.0f}" if pd.notna(summary["BASKET_COUNT"]) else "0"),
        ("平均客単価", f"¥{avg_basket:,.0f}" if pd.notna(avg_basket) else "¥0"),
    ]
    for col, (label, value) in zip(row2, kpi_data_row2):
        col.metric(label=label, value=value)

    st.markdown("")

    # --- チャートエリア ---
    col_left, col_right = st.columns([3, 2], gap="large")

    with col_left:
        st.markdown("""
        <div class="section-header">
            <div class="icon blue">📈</div>
            <h3>日別売上推移</h3>
        </div>
        """, unsafe_allow_html=True)

        daily_sales = get_daily_sales(
            start_date, end_date, selected_categories, selected_stores, selected_manufacturers
        )
        if not daily_sales.empty:
            daily_sales["TRANSACTION_DATE"] = pd.to_datetime(daily_sales["TRANSACTION_DATE"])

            area_chart = (
                alt.Chart(daily_sales)
                .mark_area(
                    interpolate="monotone",
                    line={"color": "#3b82f6", "strokeWidth": 2.5},
                    color=alt.Gradient(
                        gradient="linear",
                        stops=[
                            alt.GradientStop(color="rgba(59,130,246,0.35)", offset=0),
                            alt.GradientStop(color="rgba(59,130,246,0.02)", offset=1),
                        ],
                        x1=1, x2=1, y1=1, y2=0,
                    ),
                )
                .encode(
                    x=alt.X("TRANSACTION_DATE:T", title="日付", axis=alt.Axis(format="%m/%d", labelAngle=-45)),
                    y=alt.Y("SALES_AMOUNT:Q", title="売上（円）", axis=alt.Axis(format="~s")),
                    tooltip=[
                        alt.Tooltip("TRANSACTION_DATE:T", title="日付", format="%Y/%m/%d"),
                        alt.Tooltip("SALES_AMOUNT:Q", title="売上", format=",.0f"),
                    ],
                )
                .properties(height=340)
                .configure_view(strokeWidth=0)
                .configure_axis(grid=True, gridColor="#f1f5f9", gridDash=[4, 4])
            )
            st.altair_chart(area_chart, use_container_width=True)
        else:
            st.info("データがありません")

    with col_right:
        st.markdown("""
        <div class="section-header">
            <div class="icon green">📊</div>
            <h3>カテゴリ別売上構成</h3>
        </div>
        """, unsafe_allow_html=True)

        category_sales = get_category_sales(
            start_date, end_date, selected_categories, selected_stores, selected_manufacturers
        )
        if not category_sales.empty:
            bar_chart = (
                alt.Chart(category_sales)
                .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                .encode(
                    x=alt.X("CATEGORY_LARGE:N", title="カテゴリ", sort="-y", axis=alt.Axis(labelAngle=-45)),
                    y=alt.Y("SALES_AMOUNT:Q", title="売上（円）", axis=alt.Axis(format="~s")),
                    color=alt.Color(
                        "CATEGORY_LARGE:N",
                        scale=alt.Scale(scheme="tableau20"),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("CATEGORY_LARGE:N", title="カテゴリ"),
                        alt.Tooltip("SALES_AMOUNT:Q", title="売上", format=",.0f"),
                        alt.Tooltip("GROSS_PROFIT:Q", title="粗利", format=",.0f"),
                    ],
                )
                .properties(height=340)
                .configure_view(strokeWidth=0)
                .configure_axis(grid=True, gridColor="#f1f5f9", gridDash=[4, 4])
            )
            st.altair_chart(bar_chart, use_container_width=True)
        else:
            st.info("データがありません")

# ---------------------------------------------------------------------------
# タブ2: 商品分析
# ---------------------------------------------------------------------------
with tab2:
    st.markdown("""
    <div class="section-header">
        <div class="icon blue">🏆</div>
        <h3>売上 TOP 20 商品</h3>
    </div>
    """, unsafe_allow_html=True)

    top_products = get_top_products(
        start_date, end_date, selected_categories, selected_stores, selected_manufacturers
    )

    if not top_products.empty:
        top_products["商品名"] = top_products.apply(
            lambda x: f"🆕 {x['PRODUCT_NAME']}" if x["IS_NEW_PRODUCT"] else x["PRODUCT_NAME"],
            axis=1,
        )

        display_df = top_products[[
            "商品名", "BRAND_NAME", "MANUFACTURER_NAME",
            "CATEGORY_LARGE", "SALES_AMOUNT", "QUANTITY",
            "GROSS_PROFIT", "GROSS_MARGIN_PCT", "UNIQUE_CUSTOMERS",
        ]].copy()
        display_df.columns = [
            "商品名", "ブランド", "メーカー", "カテゴリ",
            "売上（円）", "数量", "粗利（円）", "粗利率（%）", "購入顧客数",
        ]

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "売上（円）": st.column_config.NumberColumn(format="¥%d"),
                "粗利（円）": st.column_config.NumberColumn(format="¥%d"),
                "粗利率（%）": st.column_config.ProgressColumn(
                    format="%.1f%%", min_value=0, max_value=100
                ),
                "購入顧客数": st.column_config.NumberColumn(format="%d 人"),
            },
        )

        st.markdown("")

        st.markdown("""
        <div class="section-header">
            <div class="icon green">📊</div>
            <h3>売上 TOP 10（グラフ）</h3>
        </div>
        """, unsafe_allow_html=True)

        top10 = top_products.head(10)[["PRODUCT_NAME", "SALES_AMOUNT", "GROSS_PROFIT"]].copy()
        bar_h = (
            alt.Chart(top10)
            .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6)
            .encode(
                y=alt.Y("PRODUCT_NAME:N", sort="-x", title=None),
                x=alt.X("SALES_AMOUNT:Q", title="売上（円）", axis=alt.Axis(format="~s")),
                color=alt.value("#3b82f6"),
                tooltip=[
                    alt.Tooltip("PRODUCT_NAME:N", title="商品名"),
                    alt.Tooltip("SALES_AMOUNT:Q", title="売上", format=",.0f"),
                    alt.Tooltip("GROSS_PROFIT:Q", title="粗利", format=",.0f"),
                ],
            )
            .properties(height=360)
            .configure_view(strokeWidth=0)
            .configure_axis(grid=True, gridColor="#f1f5f9", gridDash=[4, 4])
        )
        st.altair_chart(bar_h, use_container_width=True)
    else:
        st.info("データがありません")

    st.divider()

    st.markdown("""
    <div class="section-header">
        <div class="icon orange">🆕</div>
        <h3>新商品パフォーマンス</h3>
    </div>
    """, unsafe_allow_html=True)

    new_products = get_new_products_performance(start_date, end_date)

    if not new_products.empty:
        display_new = new_products[[
            "PRODUCT_NAME", "BRAND_NAME", "MANUFACTURER_NAME",
            "CATEGORY_LARGE", "LAUNCH_DATE", "SALES_AMOUNT",
            "QUANTITY", "UNIQUE_CUSTOMERS", "SELLING_STORES",
        ]].copy()
        display_new.columns = [
            "商品名", "ブランド", "メーカー", "カテゴリ",
            "発売日", "売上（円）", "数量", "購入顧客数", "販売店舗数",
        ]

        st.dataframe(
            display_new,
            use_container_width=True,
            hide_index=True,
            column_config={
                "売上（円）": st.column_config.NumberColumn(format="¥%d"),
                "発売日": st.column_config.DateColumn(format="YYYY/MM/DD"),
                "購入顧客数": st.column_config.NumberColumn(format="%d 人"),
                "販売店舗数": st.column_config.NumberColumn(format="%d 店"),
            },
        )
    else:
        st.info("新商品データがありません")

# ---------------------------------------------------------------------------
# タブ3: 在庫状況
# ---------------------------------------------------------------------------
with tab3:
    st.markdown("""
    <div class="section-header">
        <div class="icon orange">📋</div>
        <h3>在庫ステータス概要</h3>
    </div>
    """, unsafe_allow_html=True)

    inventory = get_inventory_status()

    if not inventory.empty:
        status_summary = inventory.groupby("STOCK_STATUS").size().reset_index(name="件数")
        status_order = ["欠品", "要緊急発注", "要発注", "適正", "過剰在庫"]
        status_summary["STOCK_STATUS"] = pd.Categorical(
            status_summary["STOCK_STATUS"], categories=status_order, ordered=True
        )
        status_summary = status_summary.sort_values("STOCK_STATUS")

        col1, col2 = st.columns([2, 3], gap="large")

        with col1:
            badge_map = {
                "欠品":     ("critical", "🚨"),
                "要緊急発注": ("warning",  "⚠️"),
                "要発注":    ("warning",  "📦"),
                "適正":      ("success",  "✅"),
                "過剰在庫":  ("info",     "📈"),
            }
            for _, row in status_summary.iterrows():
                status = row["STOCK_STATUS"]
                count = row["件数"]
                cls, icon = badge_map.get(status, ("info", "📋"))
                st.markdown(
                    f'<div class="status-badge {cls}">{icon} {status}<span style="margin-left:auto;font-size:1.1rem">{count}件</span></div>',
                    unsafe_allow_html=True,
                )

        with col2:
            status_color_map = {
                "欠品": "#ef4444",
                "要緊急発注": "#f59e0b",
                "要発注": "#fb923c",
                "適正": "#22c55e",
                "過剰在庫": "#3b82f6",
            }
            status_summary["color"] = status_summary["STOCK_STATUS"].map(status_color_map)
            domain = [s for s in status_order if s in status_summary["STOCK_STATUS"].values]
            range_colors = [status_color_map[s] for s in domain]

            inv_bar = (
                alt.Chart(status_summary)
                .mark_bar(cornerRadiusTopLeft=6, cornerRadiusTopRight=6)
                .encode(
                    x=alt.X("STOCK_STATUS:N", sort=status_order, title=None),
                    y=alt.Y("件数:Q", title="件数"),
                    color=alt.Color(
                        "STOCK_STATUS:N",
                        scale=alt.Scale(domain=domain, range=range_colors),
                        legend=None,
                    ),
                    tooltip=[
                        alt.Tooltip("STOCK_STATUS:N", title="ステータス"),
                        alt.Tooltip("件数:Q", title="件数"),
                    ],
                )
                .properties(height=280)
                .configure_view(strokeWidth=0)
                .configure_axis(grid=True, gridColor="#f1f5f9", gridDash=[4, 4])
            )
            st.altair_chart(inv_bar, use_container_width=True)

        st.divider()

        st.markdown("""
        <div class="section-header">
            <div class="icon orange">⚠️</div>
            <h3>要対応商品リスト</h3>
        </div>
        """, unsafe_allow_html=True)

        attention_items = inventory[
            inventory["STOCK_STATUS"].isin(["欠品", "要緊急発注", "要発注"])
        ]

        if not attention_items.empty:
            display_inv = attention_items[[
                "STOCK_STATUS", "STORE_NAME", "PRODUCT_NAME",
                "CATEGORY_LARGE", "MANUFACTURER_NAME",
                "STOCK_QUANTITY", "REORDER_POINT", "DAYS_OF_SUPPLY",
            ]].copy()
            display_inv.columns = [
                "ステータス", "店舗", "商品名", "カテゴリ",
                "メーカー", "在庫数", "発注点", "在庫日数",
            ]

            st.dataframe(
                display_inv,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "在庫日数": st.column_config.NumberColumn(format="%.1f 日"),
                    "在庫数": st.column_config.NumberColumn(format="%d"),
                    "発注点": st.column_config.NumberColumn(format="%d"),
                },
            )
        else:
            st.success("要対応商品はありません")
    else:
        st.info("在庫データがありません")

# ---------------------------------------------------------------------------
# タブ4: 商品検索
# ---------------------------------------------------------------------------
with tab4:
    st.markdown("""
    <div class="section-header">
        <div class="icon purple">🔎</div>
        <h3>商品を検索</h3>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        search_keyword = st.text_input(
            "キーワード", placeholder="商品名・ブランド名で検索…"
        )
    with col2:
        search_category = st.selectbox(
            "カテゴリ",
            options=[""] + all_categories,
            format_func=lambda x: "すべて" if x == "" else x,
        )
    with col3:
        search_manufacturer = st.selectbox(
            "メーカー",
            options=[""] + all_manufacturers,
            format_func=lambda x: "すべて" if x == "" else x,
        )

    if search_keyword or search_category or search_manufacturer:
        search_results = search_products(
            search_keyword,
            search_category if search_category else None,
            search_manufacturer if search_manufacturer else None,
        )

        st.caption(f"検索結果: **{len(search_results)}** 件")

        if not search_results.empty:
            for _, product in search_results.iterrows():
                margin_pct = (
                    (product["UNIT_PRICE"] - product["COST_PRICE"])
                    / product["UNIT_PRICE"]
                    * 100
                    if product["UNIT_PRICE"]
                    else 0
                )
                label = (
                    f"{'🆕 ' if product['IS_NEW_PRODUCT'] else ''}"
                    f"{product['PRODUCT_NAME']}　—　{product['BRAND_NAME'] or ''}"
                )
                with st.expander(label, expanded=False):
                    col_a, col_b = st.columns([2, 3], gap="medium")

                    with col_a:
                        st.markdown(
                            f"| 項目 | 値 |\n"
                            f"|:--|:--|\n"
                            f"| 商品ID | `{product['PRODUCT_ID']}` |\n"
                            f"| メーカー | {product['MANUFACTURER_NAME']} |\n"
                            f"| カテゴリ | {product['CATEGORY_LARGE']} › {product['CATEGORY_MEDIUM'] or '-'} |\n"
                            f"| 容量 | {product['UNIT_SIZE'] or '-'} |\n"
                            f"| 定価 | ¥{product['UNIT_PRICE']:,.0f} |\n"
                            f"| 原価 | ¥{product['COST_PRICE']:,.0f} |\n"
                            f"| 粗利率 | **{margin_pct:.1f}%** |"
                        )

                    with col_b:
                        st.markdown("**商品説明**")
                        st.write(product["PRODUCT_DESCRIPTION"] or "説明なし")
        else:
            st.info("該当する商品が見つかりませんでした")
    else:
        st.info("検索条件を入力してください")

# ---------------------------------------------------------------------------
# フッター
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    '<div class="dashboard-footer">Powered by <span>Snowflake</span> & <span>Streamlit</span></div>',
    unsafe_allow_html=True,
)
