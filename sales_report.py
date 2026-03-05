"""
顧客分析ダッシュボード
FOODEX_DEMO.BUYER_AGENTデータを使用した柔軟な顧客・売上分析ツール
(Streamlit in Snowflake対応版)
"""

import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session
from datetime import datetime
import io
import base64

# ページ設定
st.set_page_config(
    page_title="顧客分析ダッシュボード",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Snowflakeセッション取得
@st.cache_resource
def get_session():
    return get_active_session()

session = get_session()

# カスタムCSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+JP:wght@400;500;600;700&display=swap');
html, body, [class*="st-"] {
    font-family: 'Inter', 'Noto Sans JP', sans-serif;
}

/* サイドバー - 明るいベージュ系に変更（視認性向上） */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #fef2f2 0%, #fee2e2 100%);
}
section[data-testid="stSidebar"] * {
    color: #7f1d1d !important;
}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
    background-color: #dc2626 !important;
    color: white !important;
}
section[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] * {
    color: white !important;
}
section[data-testid="stSidebar"] hr {
    border-color: #fecaca !important;
}
section[data-testid="stSidebar"] h3, 
section[data-testid="stSidebar"] .stMarkdown h3 {
    color: #991b1b !important;
    font-weight: 700 !important;
}
section[data-testid="stSidebar"] label {
    color: #7f1d1d !important;
    font-weight: 600 !important;
}

/* メトリクスカード */
div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #ffffff 0%, #fef2f2 100%);
    border: 1px solid #fecaca;
    border-radius: 16px;
    padding: 20px 24px;
    box-shadow: 0 1px 3px rgba(185,28,28,0.04), 0 4px 12px rgba(185,28,28,0.03);
}
div[data-testid="stMetric"] label {
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #991b1b !important;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 700 !important;
    color: #7f1d1d !important;
}

/* タブ */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #fef2f2;
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 10px 20px;
    font-weight: 600;
    font-size: 0.88rem;
    color: #991b1b;
    background: transparent;
    border: none;
}
.stTabs [aria-selected="true"] {
    background: #ffffff !important;
    color: #7f1d1d !important;
    box-shadow: 0 2px 4px rgba(185,28,28,0.15);
    border-left: 3px solid #dc2626 !important;
}

/* アイコンフォント文字化け完全非表示 */
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

/* ボタン */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px;
    font-weight: 600;
}
.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #b91c1c 0%, #991b1b 100%) !important;
}
.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    border: 1px solid #fecaca;
}
.stButton > button:hover {
    border-color: #dc2626;
    color: #dc2626;
}

/* チェックボックス */
.stCheckbox label span {
    color: #7f1d1d !important;
}

/* マルチセレクト */
.stMultiSelect [data-baseweb="tag"] {
    background-color: #dc2626 !important;
}

/* データフレーム */
.stDataFrame {
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #fecaca;
}

/* ヘッダー */
.dashboard-header {
    background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 50%, #dc2626 100%);
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
    background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
    border-radius: 50%;
}
.dashboard-header h1 {
    font-size: 2rem;
    font-weight: 700;
    margin: 0 0 8px 0;
    color: white;
    position: relative;
}
.dashboard-header p {
    font-size: 0.95rem;
    color: #fecaca;
    margin: 0;
    position: relative;
}
.dashboard-header .logo-text {
    font-size: 0.75rem;
    color: #fca5a5;
    margin-top: 12px;
    position: relative;
}

/* セクションヘッダー */
.section-icon {
    display: inline-block;
    width: 28px;
    height: 28px;
    background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
    border-radius: 8px;
    text-align: center;
    line-height: 28px;
    margin-right: 8px;
    color: white;
    font-size: 14px;
}

/* 成功メッセージ */
.stSuccess {
    background-color: #f0fdf4 !important;
    border-color: #86efac !important;
}

/* divider */
hr {
    border: none;
    border-top: 1px solid #fecaca;
    margin: 1.5rem 0;
}

/* Keyboard文字化け強制非表示 */
body *:not(script):not(style) {
    font-variant-ligatures: none;
}
</style>
""", unsafe_allow_html=True)


# データ取得関数
@st.cache_data(ttl=300)
def get_date_range():
    """取引日の範囲を取得"""
    df = session.sql("""
        SELECT 
            MIN(TRANSACTION_DATE) as MIN_DATE,
            MAX(TRANSACTION_DATE) as MAX_DATE
        FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS
    """).to_pandas()
    return df.iloc[0]["MIN_DATE"], df.iloc[0]["MAX_DATE"]


@st.cache_data(ttl=300)
def get_filter_options():
    """フィルターオプションを取得"""
    # 顧客属性
    customer_df = session.sql("""
        SELECT DISTINCT GENDER, AGE_GROUP, PREFECTURE, MEMBERSHIP_TIER, OCCUPATION
        FROM FOODEX_DEMO.BUYER_AGENT.CUSTOMER_MASTER
    """).to_pandas()
    
    # 商品カテゴリ
    product_df = session.sql("""
        SELECT DISTINCT CATEGORY_LARGE, CATEGORY_MEDIUM, MANUFACTURER_NAME
        FROM FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER
        ORDER BY CATEGORY_LARGE, CATEGORY_MEDIUM
    """).to_pandas()
    
    # 店舗
    store_df = session.sql("""
        SELECT STORE_ID, STORE_NAME, PREFECTURE, STORE_FORMAT
        FROM FOODEX_DEMO.BUYER_AGENT.STORE_MASTER
        ORDER BY STORE_ID
    """).to_pandas()
    
    return {
        "genders": sorted(customer_df["GENDER"].dropna().unique().tolist()),
        "age_groups": sorted(customer_df["AGE_GROUP"].dropna().unique().tolist()),
        "prefectures": sorted(customer_df["PREFECTURE"].dropna().unique().tolist()),
        "membership_tiers": sorted(customer_df["MEMBERSHIP_TIER"].dropna().unique().tolist()),
        "occupations": sorted(customer_df["OCCUPATION"].dropna().unique().tolist()),
        "categories_large": sorted(product_df["CATEGORY_LARGE"].dropna().unique().tolist()),
        "categories_medium": sorted(product_df["CATEGORY_MEDIUM"].dropna().unique().tolist()),
        "manufacturers": sorted(product_df["MANUFACTURER_NAME"].dropna().unique().tolist()),
        "stores": store_df
    }


@st.cache_data(ttl=60)
def execute_customer_analysis(
    group_by_columns,
    aggregate_columns,
    where_conditions,
    order_by,
    limit_rows
):
    """顧客分析クエリを実行"""
    
    # SELECT句構築（group_byとaggregateは別々に渡される）
    select_parts = aggregate_columns if aggregate_columns else ["*"]
    select_clause = ", ".join(select_parts)
    
    # WHERE句構築
    where_clause = ""
    if where_conditions:
        where_clause = f"WHERE {' AND '.join(where_conditions)}"
    
    # GROUP BY句構築
    group_by_clause = ""
    if group_by_columns:
        group_by_clause = f"GROUP BY {', '.join(group_by_columns)}"
    
    # ORDER BY句構築
    order_by_clause = ""
    if order_by:
        order_by_clause = f"ORDER BY {order_by}"
    
    # LIMIT句構築
    limit_clause = ""
    if limit_rows and limit_rows > 0:
        limit_clause = f"LIMIT {limit_rows}"
    
    # クエリ組み立て
    query = f"""
    SELECT {select_clause}
    FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
    JOIN FOODEX_DEMO.BUYER_AGENT.CUSTOMER_MASTER c ON t.CUSTOMER_ID = c.CUSTOMER_ID
    JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
    JOIN FOODEX_DEMO.BUYER_AGENT.STORE_MASTER s ON t.STORE_ID = s.STORE_ID
    {where_clause}
    {group_by_clause}
    {order_by_clause}
    {limit_clause}
    """
    
    return session.sql(query).to_pandas(), query


def get_download_link_csv(df, filename):
    """CSVダウンロードリンクを生成"""
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    b64 = base64.b64encode(csv.encode('utf-8-sig')).decode()
    href = f'<a href="data:text/csv;base64,{b64}" download="{filename}" style="display: inline-block; padding: 0.5rem 1rem; background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">CSV Download</a>'
    return href


def get_download_link_excel(df, filename):
    """Excelダウンロードリンクを生成"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='顧客分析結果')
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" style="display: inline-block; padding: 0.5rem 1rem; background: linear-gradient(135deg, #991b1b 0%, #7f1d1d 100%); color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">Excel Download</a>'
    return href


# メイン処理
# ヘッダー
st.markdown("""
<div class="dashboard-header">
    <h1>Customer Analytics Dashboard</h1>
    <p>ID-POSデータを活用した顧客セグメント分析・集計ツール</p>
    <div class="logo-text">Powered by Snowflake</div>
</div>
""", unsafe_allow_html=True)

# データ取得
min_date, max_date = get_date_range()
min_date = pd.to_datetime(min_date).date()
max_date = pd.to_datetime(max_date).date()
filter_options = get_filter_options()

# サイドバー：フィルター設定
with st.sidebar:
    st.markdown("### フィルター設定")
    st.markdown("---")
    
    # 期間フィルター
    st.subheader("期間")
    date_range = st.date_input(
        "分析期間",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    st.markdown("---")
    
    # 顧客属性フィルター
    st.subheader("顧客属性")
    
    selected_genders = st.multiselect(
        "性別",
        options=filter_options["genders"],
        default=[]
    )
    
    selected_age_groups = st.multiselect(
        "年代",
        options=filter_options["age_groups"],
        default=[]
    )
    
    selected_prefectures = st.multiselect(
        "都道府県",
        options=filter_options["prefectures"],
        default=[]
    )
    
    selected_tiers = st.multiselect(
        "会員ランク",
        options=filter_options["membership_tiers"],
        default=[]
    )
    
    selected_occupations = st.multiselect(
        "職業",
        options=filter_options["occupations"],
        default=[]
    )
    
    st.markdown("---")
    
    # 商品フィルター
    st.subheader("商品")
    
    selected_categories = st.multiselect(
        "カテゴリ（大分類）",
        options=filter_options["categories_large"],
        default=[]
    )
    
    selected_manufacturers = st.multiselect(
        "メーカー",
        options=filter_options["manufacturers"],
        default=[]
    )
    
    st.markdown("---")
    
    # 店舗フィルター
    st.subheader("店舗")
    store_options = {
        f"{row['STORE_NAME']} ({row['STORE_ID']})": row["STORE_ID"]
        for _, row in filter_options["stores"].iterrows()
    }
    selected_store_names = st.multiselect(
        "店舗",
        options=list(store_options.keys()),
        default=[]
    )
    selected_stores = [store_options[name] for name in selected_store_names]
    
    st.markdown("---")
    st.caption(f"データ範囲: {min_date} 〜 {max_date}")


# タブ構成
tab1, tab2, tab3 = st.tabs([
    "カスタム集計",
    "顧客セグメント分析",
    "購買行動分析"
])

# 共通のWHERE条件を構築（全タブで使用）
common_where_conditions = []

# 日付条件
if isinstance(date_range, tuple) and len(date_range) == 2:
    common_where_conditions.append(f"t.TRANSACTION_DATE BETWEEN '{date_range[0]}' AND '{date_range[1]}'")

# 顧客属性フィルター
if selected_genders:
    common_where_conditions.append(f"c.GENDER IN ({','.join([repr(g) for g in selected_genders])})")
if selected_age_groups:
    common_where_conditions.append(f"c.AGE_GROUP IN ({','.join([repr(a) for a in selected_age_groups])})")
if selected_prefectures:
    common_where_conditions.append(f"c.PREFECTURE IN ({','.join([repr(p) for p in selected_prefectures])})")
if selected_tiers:
    common_where_conditions.append(f"c.MEMBERSHIP_TIER IN ({','.join([repr(t) for t in selected_tiers])})")
if selected_occupations:
    common_where_conditions.append(f"c.OCCUPATION IN ({','.join([repr(o) for o in selected_occupations])})")

# 商品フィルター
if selected_categories:
    common_where_conditions.append(f"p.CATEGORY_LARGE IN ({','.join([repr(c) for c in selected_categories])})")
if selected_manufacturers:
    common_where_conditions.append(f"p.MANUFACTURER_NAME IN ({','.join([repr(m) for m in selected_manufacturers])})")

# 店舗フィルター
if selected_stores:
    common_where_conditions.append(f"t.STORE_ID IN ({','.join([repr(s) for s in selected_stores])})")

# WHERE句（日付のみ - 顧客テーブルをJOINしないクエリ用）
date_where = common_where_conditions[0] if common_where_conditions else "1=1"

# WHERE句（全条件）
common_where = " AND ".join(common_where_conditions) if common_where_conditions else "1=1"

# タブ1: カスタム集計
with tab1:
    st.header("カスタム集計")
    st.markdown("集計軸と集計項目を自由に選択して分析できます。")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("集計軸（グループ化項目）")
        
        # 利用可能な集計軸: 表示名 -> (SQL列, 英語エイリアス)
        all_group_columns = {
            # 顧客属性
            "[顧客] 性別": ("c.GENDER", "GENDER"),
            "[顧客] 年代": ("c.AGE_GROUP", "AGE_GROUP"),
            "[顧客] 都道府県": ("c.PREFECTURE", "CUST_PREFECTURE"),
            "[顧客] 会員ランク": ("c.MEMBERSHIP_TIER", "MEMBERSHIP_TIER"),
            "[顧客] 職業": ("c.OCCUPATION", "OCCUPATION"),
            "[顧客] 子供有無": ("c.HAS_CHILDREN", "HAS_CHILDREN"),
            "[顧客] 家族人数": ("c.FAMILY_SIZE", "FAMILY_SIZE"),
            # 商品属性
            "[商品] カテゴリ（大）": ("p.CATEGORY_LARGE", "CATEGORY_LARGE"),
            "[商品] カテゴリ（中）": ("p.CATEGORY_MEDIUM", "CATEGORY_MEDIUM"),
            "[商品] カテゴリ（小）": ("p.CATEGORY_SMALL", "CATEGORY_SMALL"),
            "[商品] メーカー": ("p.MANUFACTURER_NAME", "MANUFACTURER_NAME"),
            "[商品] ブランド": ("p.BRAND_NAME", "BRAND_NAME"),
            "[商品] 新商品フラグ": ("p.IS_NEW_PRODUCT", "IS_NEW_PRODUCT"),
            # 店舗属性
            "[店舗] 店舗名": ("s.STORE_NAME", "STORE_NAME"),
            "[店舗] 都道府県": ("s.PREFECTURE", "STORE_PREFECTURE"),
            "[店舗] 店舗フォーマット": ("s.STORE_FORMAT", "STORE_FORMAT"),
            # 時間軸
            "[時間] 曜日": ("t.DAY_OF_WEEK", "DAY_OF_WEEK"),
            "[時間] 年月": ("TO_CHAR(t.TRANSACTION_DATE, 'YYYY-MM')", "YEAR_MONTH"),
            "[時間] 月": ("MONTH(t.TRANSACTION_DATE)", "MONTH"),
            "[時間] 年": ("YEAR(t.TRANSACTION_DATE)", "YEAR")
        }
        
        # multiselect で複数選択
        selected_group_keys = st.multiselect(
            "グループ化する項目を選択（複数選択可）",
            options=list(all_group_columns.keys()),
            default=["[顧客] 年代", "[顧客] 性別"]
        )
        
        # (表示名, SQL列, 英語エイリアス)
        selected_groups = [(key, all_group_columns[key][0], all_group_columns[key][1]) for key in selected_group_keys]
        
        st.subheader("集計項目")
        
        # 集計項目: 表示名 -> (SQL式, 英語エイリアス)
        aggregate_options = {
            "売上金額合計": ("SUM(t.SALES_AMOUNT)", "TOTAL_SALES"),
            "販売数量合計": ("SUM(t.QUANTITY)", "TOTAL_QUANTITY"),
            "取引件数": ("COUNT(*)", "TX_COUNT"),
            "顧客数": ("COUNT(DISTINCT t.CUSTOMER_ID)", "CUSTOMER_COUNT"),
            "バスケット数": ("COUNT(DISTINCT t.BASKET_ID)", "BASKET_COUNT"),
            "平均客単価": ("ROUND(SUM(t.SALES_AMOUNT) / NULLIF(COUNT(DISTINCT t.BASKET_ID), 0), 0)", "AVG_BASKET_VALUE"),
            "平均購入点数": ("ROUND(SUM(t.QUANTITY) / NULLIF(COUNT(DISTINCT t.BASKET_ID), 0), 1)", "AVG_ITEMS_PER_BASKET"),
            "購入商品種類数": ("COUNT(DISTINCT t.PRODUCT_ID)", "PRODUCT_VARIETY"),
            "割引適用率": ("ROUND(SUM(CASE WHEN t.DISCOUNT_AMOUNT > 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)", "DISCOUNT_RATE")
        }
        
        selected_aggregates = st.multiselect(
            "集計する項目を選択",
            list(aggregate_options.keys()),
            default=["売上金額合計", "顧客数", "取引件数"]
        )
    
    with col2:
        st.subheader("詳細設定")
        
        # ソート設定（日本語表示名で選択）
        sort_options = [jp for jp, _, _ in selected_groups] + selected_aggregates
        if sort_options:
            sort_column = st.selectbox("ソート項目", sort_options)
            sort_direction = st.selectbox("ソート順", ["降順", "昇順"])
        else:
            sort_column = None
            sort_direction = "降順"
        
        # 表示件数
        limit_results = st.checkbox("表示件数を制限", value=True)
        limit_rows = st.number_input("最大表示件数", min_value=1, max_value=10000, value=100) if limit_results else None
        
        st.markdown("---")
        
        # 実行ボタン
        execute_btn = st.button("分析実行", type="primary", use_container_width=True)
    
    # 分析実行
    if execute_btn:
        if not selected_groups and not selected_aggregates:
            st.warning("集計軸または集計項目を1つ以上選択してください。")
        else:
            # WHERE条件構築
            where_conditions = []
            
            # 日付条件
            if isinstance(date_range, tuple) and len(date_range) == 2:
                where_conditions.append(f"t.TRANSACTION_DATE BETWEEN '{date_range[0]}' AND '{date_range[1]}'")
            
            # 顧客属性フィルター
            if selected_genders:
                where_conditions.append(f"c.GENDER IN ({','.join([repr(g) for g in selected_genders])})")
            if selected_age_groups:
                where_conditions.append(f"c.AGE_GROUP IN ({','.join([repr(a) for a in selected_age_groups])})")
            if selected_prefectures:
                where_conditions.append(f"c.PREFECTURE IN ({','.join([repr(p) for p in selected_prefectures])})")
            if selected_tiers:
                where_conditions.append(f"c.MEMBERSHIP_TIER IN ({','.join([repr(t) for t in selected_tiers])})")
            if selected_occupations:
                where_conditions.append(f"c.OCCUPATION IN ({','.join([repr(o) for o in selected_occupations])})")
            
            # 商品フィルター
            if selected_categories:
                where_conditions.append(f"p.CATEGORY_LARGE IN ({','.join([repr(c) for c in selected_categories])})")
            if selected_manufacturers:
                where_conditions.append(f"p.MANUFACTURER_NAME IN ({','.join([repr(m) for m in selected_manufacturers])})")
            
            # 店舗フィルター
            if selected_stores:
                where_conditions.append(f"t.STORE_ID IN ({','.join([repr(s) for s in selected_stores])})")
            
            # 日本語→英語エイリアスのマッピング作成
            jp_to_eng = {}
            for jp_name, _, eng_alias in selected_groups:
                jp_to_eng[jp_name] = eng_alias
            for jp_name, (_, eng_alias) in aggregate_options.items():
                jp_to_eng[jp_name] = eng_alias
            
            # 英語→日本語のマッピング（結果表示用）
            eng_to_jp = {v: k for k, v in jp_to_eng.items()}
            
            # GROUP BY列（SQL式のみ）
            group_by_cols = [sql_col for _, sql_col, _ in selected_groups]
            
            # SELECT列（英語エイリアス付き）
            select_cols = [f"{sql_col} as {eng_alias}" for _, sql_col, eng_alias in selected_groups]
            agg_cols = [f"{aggregate_options[agg][0]} as {aggregate_options[agg][1]}" for agg in selected_aggregates]
            
            # ソート（英語エイリアスで指定）
            order_by = ""
            if sort_column and sort_column in jp_to_eng:
                eng_sort_col = jp_to_eng[sort_column]
                order_by = f"{eng_sort_col} {'DESC' if sort_direction == '降順' else 'ASC'}"
            
            try:
                with st.spinner("データを集計中..."):
                    result_df, executed_query = execute_customer_analysis(
                        group_by_columns=group_by_cols,
                        aggregate_columns=select_cols + agg_cols,
                        where_conditions=where_conditions,
                        order_by=order_by,
                        limit_rows=limit_rows
                    )
                
                if not result_df.empty:
                    # 列名を日本語に変換
                    result_df = result_df.rename(columns=eng_to_jp)
                    
                    st.success(f"{len(result_df):,}件のデータを取得しました")
                    
                    # セッションに保存
                    st.session_state['result_df'] = result_df
                    st.session_state['executed_query'] = executed_query
                    
                    # メトリクス表示
                    if selected_aggregates:
                        metric_cols = st.columns(min(len(selected_aggregates), 4))
                        for i, agg in enumerate(selected_aggregates):
                            with metric_cols[i % 4]:
                                if agg in result_df.columns:
                                    total = result_df[agg].sum() if result_df[agg].dtype in ['int64', 'float64'] else 0
                                    if total > 1000000:
                                        display_val = f"{total/1000000:.1f}M"
                                    elif total > 1000:
                                        display_val = f"{total/1000:.1f}K"
                                    else:
                                        display_val = f"{total:,.0f}"
                                    st.metric(label=agg, value=display_val)
                    
                    # データテーブル
                    st.subheader("集計結果")
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                    
                    # ダウンロード
                    st.subheader("データダウンロード")
                    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    dl_col1, dl_col2, dl_col3 = st.columns(3)
                    with dl_col1:
                        st.metric("データ件数", f"{len(result_df):,}件")
                    with dl_col2:
                        csv_link = get_download_link_csv(result_df, f"customer_analysis_{current_time}.csv")
                        st.markdown(csv_link, unsafe_allow_html=True)
                    with dl_col3:
                        try:
                            excel_link = get_download_link_excel(result_df, f"customer_analysis_{current_time}.xlsx")
                            st.markdown(excel_link, unsafe_allow_html=True)
                        except Exception:
                            st.info("Excel出力にはopenpyxlが必要です")
                else:
                    st.warning("条件に該当するデータがありませんでした。")
            
            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
    
    # 実行クエリ表示（セッション状態から）
    if 'executed_query' in st.session_state:
        show_sql = st.checkbox("実行されたSQLクエリを表示", key="show_sql_custom")
        if show_sql:
            st.code(st.session_state['executed_query'], language="sql")


# タブ2: 顧客セグメント分析
with tab2:
    st.header("顧客セグメント分析")
    st.markdown("事前定義された顧客セグメント別の分析を実行できます。")
    
    segment_type = st.selectbox(
        "セグメント軸を選択",
        ["会員ランク別", "年代別", "性別×年代", "都道府県別", "職業別", "RFM分析"]
    )
    
    if st.button("セグメント分析実行", key="segment_btn"):
        with st.spinner("分析中..."):
            try:
                # 列名マッピング（英語→日本語）
                column_mapping = {}
                
                if segment_type == "会員ランク別":
                    query = f"""
                    SELECT 
                        c.MEMBERSHIP_TIER,
                        COUNT(DISTINCT c.CUSTOMER_ID) as CUSTOMER_COUNT,
                        COUNT(DISTINCT t.BASKET_ID) as PURCHASE_COUNT,
                        SUM(t.SALES_AMOUNT) as TOTAL_SALES,
                        ROUND(SUM(t.SALES_AMOUNT) / NULLIF(COUNT(DISTINCT t.BASKET_ID), 0), 0) as AVG_BASKET_VALUE,
                        ROUND(COUNT(DISTINCT t.BASKET_ID) * 1.0 / NULLIF(COUNT(DISTINCT c.CUSTOMER_ID), 0), 2) as AVG_FREQUENCY
                    FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
                    JOIN FOODEX_DEMO.BUYER_AGENT.CUSTOMER_MASTER c ON t.CUSTOMER_ID = c.CUSTOMER_ID
                    JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
                    WHERE {common_where}
                    GROUP BY c.MEMBERSHIP_TIER
                    ORDER BY TOTAL_SALES DESC
                    """
                    column_mapping = {
                        "MEMBERSHIP_TIER": "会員ランク",
                        "CUSTOMER_COUNT": "顧客数",
                        "PURCHASE_COUNT": "購買回数",
                        "TOTAL_SALES": "売上金額合計",
                        "AVG_BASKET_VALUE": "平均客単価",
                        "AVG_FREQUENCY": "平均購買頻度"
                    }
                elif segment_type == "年代別":
                    query = f"""
                    SELECT 
                        c.AGE_GROUP,
                        COUNT(DISTINCT c.CUSTOMER_ID) as CUSTOMER_COUNT,
                        COUNT(DISTINCT t.BASKET_ID) as PURCHASE_COUNT,
                        SUM(t.SALES_AMOUNT) as TOTAL_SALES,
                        ROUND(SUM(t.SALES_AMOUNT) / NULLIF(COUNT(DISTINCT t.BASKET_ID), 0), 0) as AVG_BASKET_VALUE,
                        ROUND(SUM(t.QUANTITY) / NULLIF(COUNT(DISTINCT t.BASKET_ID), 0), 1) as AVG_ITEMS
                    FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
                    JOIN FOODEX_DEMO.BUYER_AGENT.CUSTOMER_MASTER c ON t.CUSTOMER_ID = c.CUSTOMER_ID
                    JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
                    WHERE {common_where}
                    GROUP BY c.AGE_GROUP
                    ORDER BY TOTAL_SALES DESC
                    """
                    column_mapping = {
                        "AGE_GROUP": "年代",
                        "CUSTOMER_COUNT": "顧客数",
                        "PURCHASE_COUNT": "購買回数",
                        "TOTAL_SALES": "売上金額合計",
                        "AVG_BASKET_VALUE": "平均客単価",
                        "AVG_ITEMS": "平均購入点数"
                    }
                elif segment_type == "性別×年代":
                    query = f"""
                    SELECT 
                        c.GENDER,
                        c.AGE_GROUP,
                        COUNT(DISTINCT c.CUSTOMER_ID) as CUSTOMER_COUNT,
                        SUM(t.SALES_AMOUNT) as TOTAL_SALES,
                        ROUND(SUM(t.SALES_AMOUNT) / NULLIF(COUNT(DISTINCT t.BASKET_ID), 0), 0) as AVG_BASKET_VALUE
                    FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
                    JOIN FOODEX_DEMO.BUYER_AGENT.CUSTOMER_MASTER c ON t.CUSTOMER_ID = c.CUSTOMER_ID
                    JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
                    WHERE {common_where}
                    GROUP BY c.GENDER, c.AGE_GROUP
                    ORDER BY TOTAL_SALES DESC
                    """
                    column_mapping = {
                        "GENDER": "性別",
                        "AGE_GROUP": "年代",
                        "CUSTOMER_COUNT": "顧客数",
                        "TOTAL_SALES": "売上金額合計",
                        "AVG_BASKET_VALUE": "平均客単価"
                    }
                elif segment_type == "都道府県別":
                    query = f"""
                    SELECT 
                        c.PREFECTURE,
                        COUNT(DISTINCT c.CUSTOMER_ID) as CUSTOMER_COUNT,
                        SUM(t.SALES_AMOUNT) as TOTAL_SALES,
                        ROUND(SUM(t.SALES_AMOUNT) / NULLIF(COUNT(DISTINCT c.CUSTOMER_ID), 0), 0) as SALES_PER_CUSTOMER
                    FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
                    JOIN FOODEX_DEMO.BUYER_AGENT.CUSTOMER_MASTER c ON t.CUSTOMER_ID = c.CUSTOMER_ID
                    JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
                    WHERE {common_where}
                    GROUP BY c.PREFECTURE
                    ORDER BY TOTAL_SALES DESC
                    """
                    column_mapping = {
                        "PREFECTURE": "都道府県",
                        "CUSTOMER_COUNT": "顧客数",
                        "TOTAL_SALES": "売上金額合計",
                        "SALES_PER_CUSTOMER": "顧客あたり売上"
                    }
                elif segment_type == "職業別":
                    query = f"""
                    SELECT 
                        c.OCCUPATION,
                        COUNT(DISTINCT c.CUSTOMER_ID) as CUSTOMER_COUNT,
                        SUM(t.SALES_AMOUNT) as TOTAL_SALES,
                        ROUND(SUM(t.SALES_AMOUNT) / NULLIF(COUNT(DISTINCT t.BASKET_ID), 0), 0) as AVG_BASKET_VALUE,
                        ROUND(SUM(t.QUANTITY) / NULLIF(COUNT(DISTINCT t.BASKET_ID), 0), 1) as AVG_ITEMS
                    FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
                    JOIN FOODEX_DEMO.BUYER_AGENT.CUSTOMER_MASTER c ON t.CUSTOMER_ID = c.CUSTOMER_ID
                    JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
                    WHERE {common_where}
                    GROUP BY c.OCCUPATION
                    ORDER BY TOTAL_SALES DESC
                    """
                    column_mapping = {
                        "OCCUPATION": "職業",
                        "CUSTOMER_COUNT": "顧客数",
                        "TOTAL_SALES": "売上金額合計",
                        "AVG_BASKET_VALUE": "平均客単価",
                        "AVG_ITEMS": "平均購入点数"
                    }
                else:  # RFM分析
                    query = f"""
                    WITH customer_rfm AS (
                        SELECT 
                            t.CUSTOMER_ID,
                            DATEDIFF('day', MAX(t.TRANSACTION_DATE), CURRENT_DATE()) as RECENCY,
                            COUNT(DISTINCT t.BASKET_ID) as FREQUENCY,
                            SUM(t.SALES_AMOUNT) as MONETARY
                        FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
                        JOIN FOODEX_DEMO.BUYER_AGENT.CUSTOMER_MASTER c ON t.CUSTOMER_ID = c.CUSTOMER_ID
                        JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
                        WHERE {common_where}
                        GROUP BY t.CUSTOMER_ID
                    ),
                    rfm_scores AS (
                        SELECT 
                            CUSTOMER_ID,
                            RECENCY,
                            FREQUENCY,
                            MONETARY,
                            NTILE(5) OVER (ORDER BY RECENCY DESC) as R_SCORE,
                            NTILE(5) OVER (ORDER BY FREQUENCY) as F_SCORE,
                            NTILE(5) OVER (ORDER BY MONETARY) as M_SCORE
                        FROM customer_rfm
                    )
                    SELECT 
                        CASE 
                            WHEN R_SCORE >= 4 AND F_SCORE >= 4 AND M_SCORE >= 4 THEN 'VIP'
                            WHEN R_SCORE >= 4 AND (F_SCORE >= 3 OR M_SCORE >= 3) THEN 'Loyal'
                            WHEN R_SCORE >= 3 THEN 'Active'
                            WHEN R_SCORE >= 2 THEN 'At_Risk'
                            ELSE 'Churned'
                        END as RFM_SEGMENT,
                        COUNT(*) as CUSTOMER_COUNT,
                        ROUND(AVG(RECENCY), 1) as AVG_RECENCY,
                        ROUND(AVG(FREQUENCY), 1) as AVG_FREQUENCY,
                        ROUND(AVG(MONETARY), 0) as AVG_MONETARY
                    FROM rfm_scores
                    GROUP BY RFM_SEGMENT
                    ORDER BY CUSTOMER_COUNT DESC
                    """
                    column_mapping = {
                        "RFM_SEGMENT": "RFMセグメント",
                        "CUSTOMER_COUNT": "顧客数",
                        "AVG_RECENCY": "平均経過日数",
                        "AVG_FREQUENCY": "平均購買回数",
                        "AVG_MONETARY": "平均購買金額"
                    }
                
                result_df = session.sql(query).to_pandas()
                
                if not result_df.empty:
                    # 列名を日本語に変換
                    result_df = result_df.rename(columns=column_mapping)
                    st.session_state['segment_result_df'] = result_df
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                    
                    # ダウンロード
                    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                    csv_link = get_download_link_csv(result_df, f"segment_analysis_{current_time}.csv")
                    st.markdown(csv_link, unsafe_allow_html=True)
                else:
                    st.warning("データが見つかりませんでした。")
                    
            except Exception as e:
                st.error(f"エラー: {str(e)}")


# タブ3: 購買行動分析
with tab3:
    st.header("購買行動分析")
    st.markdown("顧客の購買パターンを分析します。")
    
    analysis_type = st.selectbox(
        "分析タイプを選択",
        ["曜日別購買傾向", "時間帯別購買傾向", "カテゴリ別顧客構成", "リピート購買分析", "併売分析（よく一緒に買われる商品）"]
    )
    
    if st.button("購買行動分析実行", key="behavior_btn"):
        with st.spinner("分析中..."):
            try:
                column_mapping = {}
                
                if analysis_type == "曜日別購買傾向":
                    query = f"""
                    SELECT 
                        t.DAY_OF_WEEK,
                        COUNT(DISTINCT t.CUSTOMER_ID) as CUSTOMER_COUNT,
                        COUNT(DISTINCT t.BASKET_ID) as BASKET_COUNT,
                        SUM(t.SALES_AMOUNT) as TOTAL_SALES,
                        ROUND(SUM(t.SALES_AMOUNT) / NULLIF(COUNT(DISTINCT t.BASKET_ID), 0), 0) as AVG_BASKET_VALUE
                    FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
                    JOIN FOODEX_DEMO.BUYER_AGENT.CUSTOMER_MASTER c ON t.CUSTOMER_ID = c.CUSTOMER_ID
                    JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
                    WHERE {common_where}
                    GROUP BY t.DAY_OF_WEEK
                    ORDER BY CASE t.DAY_OF_WEEK 
                        WHEN '月' THEN 1 WHEN '火' THEN 2 WHEN '水' THEN 3 
                        WHEN '木' THEN 4 WHEN '金' THEN 5 WHEN '土' THEN 6 WHEN '日' THEN 7 
                    END
                    """
                    column_mapping = {
                        "DAY_OF_WEEK": "曜日",
                        "CUSTOMER_COUNT": "来店顧客数",
                        "BASKET_COUNT": "購買件数",
                        "TOTAL_SALES": "売上金額合計",
                        "AVG_BASKET_VALUE": "平均客単価"
                    }
                elif analysis_type == "時間帯別購買傾向":
                    query = f"""
                    SELECT 
                        CASE 
                            WHEN HOUR(t.TRANSACTION_TIME) < 10 THEN 'Morning'
                            WHEN HOUR(t.TRANSACTION_TIME) < 14 THEN 'Noon'
                            WHEN HOUR(t.TRANSACTION_TIME) < 18 THEN 'Afternoon'
                            ELSE 'Evening'
                        END as TIME_SLOT,
                        COUNT(DISTINCT t.CUSTOMER_ID) as CUSTOMER_COUNT,
                        COUNT(DISTINCT t.BASKET_ID) as BASKET_COUNT,
                        SUM(t.SALES_AMOUNT) as TOTAL_SALES
                    FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
                    JOIN FOODEX_DEMO.BUYER_AGENT.CUSTOMER_MASTER c ON t.CUSTOMER_ID = c.CUSTOMER_ID
                    JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
                    WHERE {common_where}
                    GROUP BY TIME_SLOT
                    ORDER BY TOTAL_SALES DESC
                    """
                    column_mapping = {
                        "TIME_SLOT": "時間帯",
                        "CUSTOMER_COUNT": "顧客数",
                        "BASKET_COUNT": "購買件数",
                        "TOTAL_SALES": "売上金額合計"
                    }
                elif analysis_type == "カテゴリ別顧客構成":
                    query = f"""
                    SELECT 
                        p.CATEGORY_LARGE,
                        COUNT(DISTINCT t.CUSTOMER_ID) as BUYER_COUNT,
                        SUM(t.SALES_AMOUNT) as TOTAL_SALES,
                        ROUND(SUM(t.SALES_AMOUNT) / NULLIF(COUNT(DISTINCT t.CUSTOMER_ID), 0), 0) as SALES_PER_CUSTOMER
                    FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
                    JOIN FOODEX_DEMO.BUYER_AGENT.CUSTOMER_MASTER c ON t.CUSTOMER_ID = c.CUSTOMER_ID
                    JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
                    WHERE {common_where}
                    GROUP BY p.CATEGORY_LARGE
                    ORDER BY BUYER_COUNT DESC
                    """
                    column_mapping = {
                        "CATEGORY_LARGE": "カテゴリ",
                        "BUYER_COUNT": "購入顧客数",
                        "TOTAL_SALES": "売上金額合計",
                        "SALES_PER_CUSTOMER": "顧客あたり売上"
                    }
                elif analysis_type == "リピート購買分析":
                    query = f"""
                    WITH customer_purchases AS (
                        SELECT 
                            t.CUSTOMER_ID,
                            COUNT(DISTINCT t.BASKET_ID) as purchase_count
                        FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
                        JOIN FOODEX_DEMO.BUYER_AGENT.CUSTOMER_MASTER c ON t.CUSTOMER_ID = c.CUSTOMER_ID
                        JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
                        WHERE {common_where}
                        GROUP BY t.CUSTOMER_ID
                    )
                    SELECT 
                        CASE 
                            WHEN purchase_count = 1 THEN '1_Once'
                            WHEN purchase_count <= 3 THEN '2_2to3'
                            WHEN purchase_count <= 5 THEN '3_4to5'
                            WHEN purchase_count <= 10 THEN '4_6to10'
                            ELSE '5_11plus'
                        END as PURCHASE_SEGMENT,
                        COUNT(*) as CUSTOMER_COUNT,
                        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as PERCENTAGE
                    FROM customer_purchases
                    GROUP BY PURCHASE_SEGMENT
                    ORDER BY PURCHASE_SEGMENT
                    """
                    column_mapping = {
                        "PURCHASE_SEGMENT": "購買回数区分",
                        "CUSTOMER_COUNT": "顧客数",
                        "PERCENTAGE": "構成比(%)"
                    }
                else:  # 併売分析
                    query = f"""
                    WITH basket_items AS (
                        SELECT 
                            t.BASKET_ID,
                            p.CATEGORY_LARGE
                        FROM FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS t
                        JOIN FOODEX_DEMO.BUYER_AGENT.CUSTOMER_MASTER c ON t.CUSTOMER_ID = c.CUSTOMER_ID
                        JOIN FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER p ON t.PRODUCT_ID = p.PRODUCT_ID
                        WHERE {common_where}
                    )
                    SELECT 
                        a.CATEGORY_LARGE as CATEGORY_A,
                        b.CATEGORY_LARGE as CATEGORY_B,
                        COUNT(DISTINCT a.BASKET_ID) as CO_PURCHASE_COUNT
                    FROM basket_items a
                    JOIN basket_items b ON a.BASKET_ID = b.BASKET_ID AND a.CATEGORY_LARGE < b.CATEGORY_LARGE
                    GROUP BY a.CATEGORY_LARGE, b.CATEGORY_LARGE
                    HAVING COUNT(DISTINCT a.BASKET_ID) >= 10
                    ORDER BY CO_PURCHASE_COUNT DESC
                    LIMIT 20
                    """
                    column_mapping = {
                        "CATEGORY_A": "カテゴリA",
                        "CATEGORY_B": "カテゴリB",
                        "CO_PURCHASE_COUNT": "同時購入バスケット数"
                    }
                
                result_df = session.sql(query).to_pandas()
                
                if not result_df.empty:
                    result_df = result_df.rename(columns=column_mapping)
                    st.session_state['behavior_result_df'] = result_df
                    st.dataframe(result_df, use_container_width=True, hide_index=True)
                    
                    # ダウンロード
                    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                    csv_link = get_download_link_csv(result_df, f"behavior_analysis_{current_time}.csv")
                    st.markdown(csv_link, unsafe_allow_html=True)
                else:
                    st.warning("データが見つかりませんでした。")
                    
            except Exception as e:
                st.error(f"エラー: {str(e)}")


# フッター
st.markdown("---")
st.markdown("""
<div style="background: #fef2f2; border-radius: 12px; padding: 20px; border: 1px solid #fecaca;">
<p style="font-weight: 600; color: #7f1d1d; margin-bottom: 12px;">How to Use</p>
<ul style="color: #991b1b; margin: 0; padding-left: 20px;">
<li><b>カスタム集計</b>: 集計軸と集計項目を自由に選択して柔軟な分析が可能</li>
<li><b>顧客セグメント分析</b>: 事前定義されたセグメント別の分析を即座に実行</li>
<li><b>購買行動分析</b>: 顧客の購買パターンを様々な切り口で分析</li>
<li>各タブの分析結果はCSV/Excelでダウンロード可能</li>
</ul>
</div>
""", unsafe_allow_html=True)
st.caption("Data Source: FOODEX_DEMO.BUYER_AGENT | Powered by Snowflake")

# リセットボタン
if st.sidebar.button("設定リセット"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()
