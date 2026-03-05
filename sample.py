import streamlit as st
import pandas as pd
import numpy as np
from snowflake.snowpark.context import get_active_session
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
import io
import base64

# ページ設定
st.set_page_config(
    page_title="売上データ分析ダッシュボード", 
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Snowflakeセッション取得
@st.cache_resource
def get_session():
    return get_active_session()

session = get_session()

# データキャッシュ用関数
@st.cache_data(ttl=300)
def get_unique_values(column):
    """指定されたカラムのユニークな値を取得"""
    query = f"SELECT DISTINCT {column} FROM DEMO.PALTAC.POS_DATA WHERE {column} IS NOT NULL ORDER BY {column}"
    return session.sql(query).to_pandas()[column].tolist()

@st.cache_data(ttl=300)
def get_date_range():
    """データの日付範囲を取得"""
    query = """
    SELECT 
        MIN(SALES_DATE) as min_date, 
        MAX(SALES_DATE) as max_date 
    FROM DEMO.PALTAC.POS_DATA
    """
    result = session.sql(query).to_pandas()
    min_date = pd.to_datetime(str(result['MIN_DATE'].iloc[0]), format='%Y%m%d')
    max_date = pd.to_datetime(str(result['MAX_DATE'].iloc[0]), format='%Y%m%d')
    return min_date.date(), max_date.date()

@st.cache_data(ttl=60)
def execute_aggregation_query(
    select_columns, group_by_columns, aggregate_columns, 
    where_conditions, order_by, limit_rows
):
    """集計クエリを実行"""
    # SELECT句構築
    select_parts = []
    if group_by_columns:
        select_parts.extend(group_by_columns)
    if aggregate_columns:
        select_parts.extend(aggregate_columns)
    
    select_clause = ", ".join(select_parts) if select_parts else "*"
    
    # FROM句
    from_clause = "DEMO.PALTAC.POS_DATA"
    
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
    
    # 最終クエリ組み立て
    query = f"""
    SELECT {select_clause}
    FROM {from_clause}
    {where_clause}
    {group_by_clause}
    {order_by_clause}
    {limit_clause}
    """
    
    return session.sql(query).to_pandas()

def convert_df_to_csv(df):
    """DataFrameをCSV形式のバイト列に変換"""
    return df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')

# アプリケーションタイトル
st.title("📊 売上データ分析ダッシュボード")
st.markdown("**DEMO.PALTAC.POS_DATA**を使用した柔軟な売上分析ツール")

# サイドバー：フィルター設定
st.sidebar.header("🔍 データフィルター")

# 日付範囲フィルター
min_date, max_date = get_date_range()
st.sidebar.subheader("📅 期間設定")
date_range = st.sidebar.date_input(
    "分析期間を選択",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# 基本フィルター
st.sidebar.subheader("🏢 基本フィルター")

# 会社名フィルター
company_names = get_unique_values("COMPANY_NAME")
selected_companies = st.sidebar.multiselect(
    "会社名", 
    company_names, 
    default=company_names[:3] if len(company_names) > 3 else company_names
)

# ゾーンフィルター
zones = get_unique_values("ZONE")
selected_zones = st.sidebar.multiselect("ゾーン", zones, default=zones)

# 部門フィルター
departments = get_unique_values("DEPARTMENT")
selected_departments = st.sidebar.multiselect("部門", departments, default=departments)

# カテゴリーフィルター
categories = get_unique_values("CATEGORY")
selected_categories = st.sidebar.multiselect("カテゴリー", categories)

# メイン画面：集計設定
col1, col2 = st.columns([2, 1])

with col1:
    st.header("⚙️ 集計設定")
    
    # 集計軸選択
    st.subheader("📊 集計軸（グループ化項目）")
    
    available_group_columns = [
        "YEAR", "MONTH", "DAY_OF_WEEK", "WEEK",
        "COMPANY_NAME", "STORE_NAME", "ZONE", 
        "DEPARTMENT", "CATEGORY", "SUBCATEGORY", "SEGMENT",
        "MANUFACTURER_NAME", "PRODUCT_NAME"
    ]
    
    selected_group_columns = st.multiselect(
        "グループ化に使用する項目を選択してください",
        available_group_columns,
        default=["COMPANY_NAME", "DEPARTMENT"]
    )
    
    # 集計項目選択
    st.subheader("🔢 集計項目")
    
    aggregate_options = {
        "売上数量合計": "SUM(SALES_QUANTITY) as SALES_QUANTITY_TOTAL",
        "売上金額合計": "SUM(SALES_AMOUNT) as SALES_AMOUNT_TOTAL", 
        "平均単価": "AVG(UNIT_PRICE) as AVG_UNIT_PRICE",
        "売上件数": "COUNT(*) as SALES_COUNT",
        "商品数": "COUNT(DISTINCT JAN_CODE) as PRODUCT_COUNT",
        "店舗数": "COUNT(DISTINCT STORE_CODE) as STORE_COUNT"
    }
    
    # 日本語表示用のマッピング
    column_display_names = {
        "SALES_QUANTITY_TOTAL": "売上数量合計",
        "SALES_AMOUNT_TOTAL": "売上金額合計",
        "AVG_UNIT_PRICE": "平均単価",
        "SALES_COUNT": "売上件数", 
        "PRODUCT_COUNT": "商品数",
        "STORE_COUNT": "店舗数"
    }
    
    selected_aggregates = st.multiselect(
        "集計する項目を選択してください",
        list(aggregate_options.keys()),
        default=["売上数量合計", "売上金額合計", "売上件数"]
    )

with col2:
    st.header("🎯 詳細設定")
    
    # ソート設定
    st.subheader("📈 ソート設定")
    sort_options = selected_group_columns.copy()
    
    # 集計項目のソートオプションを追加（英語カラム名を使用）
    for jp_name in selected_aggregates:
        if jp_name in aggregate_options:
            eng_col = aggregate_options[jp_name].split(" as ")[-1]
            sort_options.append(eng_col)
    
    if sort_options:
        sort_column = st.selectbox("ソート項目", sort_options)
        sort_direction = st.selectbox("ソート順", ["降順", "昇順"])
        sort_order = f"{sort_column} {'DESC' if sort_direction == '降順' else 'ASC'}"
    else:
        sort_order = ""
    
    # 表示件数制限
    st.subheader("📊 表示設定")
    limit_results = st.checkbox("表示件数を制限", value=True)
    limit_rows = st.number_input("最大表示件数", min_value=1, max_value=10000, value=100) if limit_results else None
    
    # 実行ボタン
    if st.button("🚀 分析実行", type="primary"):
        st.session_state['execute_analysis'] = True

# 分析実行
if 'execute_analysis' in st.session_state and st.session_state['execute_analysis']:
    
    # WHERE条件構築
    where_conditions = []
    
    # 日付条件
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_date = date_range[0].strftime('%Y%m%d')
        end_date = date_range[1].strftime('%Y%m%d')
        where_conditions.append(f"SALES_DATE BETWEEN {start_date} AND {end_date}")
    
    # その他のフィルター条件
    if selected_companies:
        company_list = "', '".join(selected_companies)
        where_conditions.append(f"COMPANY_NAME IN ('{company_list}')")
    
    if selected_zones:
        zone_list = "', '".join(selected_zones)
        where_conditions.append(f"ZONE IN ('{zone_list}')")
    
    if selected_departments:
        dept_list = "', '".join(selected_departments)
        where_conditions.append(f"DEPARTMENT IN ('{dept_list}')")
    
    if selected_categories:
        cat_list = "', '".join(selected_categories)
        where_conditions.append(f"CATEGORY IN ('{cat_list}')")
    
    try:
        # 集計実行
        with st.spinner("データを集計中..."):
            aggregate_columns_sql = [aggregate_options[agg] for agg in selected_aggregates]
            
            result_df = execute_aggregation_query(
                select_columns=[],
                group_by_columns=selected_group_columns,
                aggregate_columns=aggregate_columns_sql,
                where_conditions=where_conditions,
                order_by=sort_order,
                limit_rows=limit_rows
            )
        
        if not result_df.empty:
            st.success(f"✅ {len(result_df):,}件のデータを取得しました")
            
            # カラム名を日本語に変換して表示
            display_df = result_df.copy()
            for eng_col, jp_col in column_display_names.items():
                if eng_col in display_df.columns:
                    display_df = display_df.rename(columns={eng_col: jp_col})
            
            # セッション状態にデータフレームを保存
            st.session_state['result_df'] = result_df
            st.session_state['display_df'] = display_df
            
            # 結果表示
            st.header("📋 集計結果")
            
            # メトリクス表示
            if len(selected_aggregates) > 0:
                metrics_cols = st.columns(min(len(selected_aggregates), 4))
                for i, agg in enumerate(selected_aggregates):
                    with metrics_cols[i % 4]:
                        # 英語カラム名を取得
                        eng_col = aggregate_options[agg].split(" as ")[-1]
                        if eng_col in result_df.columns:
                            total_value = result_df[eng_col].sum() if result_df[eng_col].dtype in ['int64', 'float64'] else len(result_df)
                            if isinstance(total_value, (int, float)):
                                if total_value > 1000000:
                                    display_value = f"{total_value/1000000:.1f}M"
                                elif total_value > 1000:
                                    display_value = f"{total_value/1000:.1f}K"
                                else:
                                    display_value = f"{total_value:,.0f}"
                            else:
                                display_value = str(total_value)
                            st.metric(label=agg, value=display_value)
            
            # データテーブル表示（日本語カラム名で表示）
            st.subheader("📊 詳細データ")
            st.dataframe(display_df, use_container_width=True)
            
            # グラフ表示
            if len(result_df) > 1 and len(selected_group_columns) > 0:
                st.subheader("📈 グラフ表示")
                
                # グラフタイプ選択
                chart_col1, chart_col2 = st.columns([1, 3])
                
                with chart_col1:
                    chart_type = st.selectbox(
                        "グラフタイプ", 
                        ["棒グラフ", "折れ線グラフ", "円グラフ", "散布図"]
                    )
                    
                    if len(selected_aggregates) > 0:
                        y_column_jp = st.selectbox("Y軸（数値）", selected_aggregates)
                        # 日本語から英語カラム名に変換
                        y_column = aggregate_options[y_column_jp].split(" as ")[-1]
                
                with chart_col2:
                    if len(selected_group_columns) > 0 and len(selected_aggregates) > 0:
                        x_column = selected_group_columns[0]
                        
                        if chart_type == "棒グラフ":
                            fig = px.bar(result_df, x=x_column, y=y_column, title=f"{y_column_jp} by {x_column}")
                        elif chart_type == "折れ線グラフ":
                            fig = px.line(result_df, x=x_column, y=y_column, title=f"{y_column_jp} by {x_column}")
                        elif chart_type == "円グラフ":
                            fig = px.pie(result_df.head(10), names=x_column, values=y_column, title=f"{y_column_jp} 構成比")
                        elif chart_type == "散布図" and len(selected_aggregates) >= 2:
                            y2_column_jp = selected_aggregates[1] if len(selected_aggregates) > 1 else selected_aggregates[0]
                            y2_column = aggregate_options[y2_column_jp].split(" as ")[-1]
                            fig = px.scatter(result_df, x=y_column, y=y2_column, size=y_column, 
                                           hover_name=x_column, title=f"{y_column_jp} vs {y2_column_jp}")
                        
                        st.plotly_chart(fig, use_container_width=True)
            
            # 実行されたSQLクエリ表示（デバッグ用）
            with st.expander("🔍 実行されたSQLクエリ（デバッグ用）"):
                aggregate_columns_sql = [aggregate_options[agg] for agg in selected_aggregates]
                select_parts = selected_group_columns + aggregate_columns_sql
                select_clause = ", ".join(select_parts)
                where_clause = f"WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
                group_by_clause = f"GROUP BY {', '.join(selected_group_columns)}" if selected_group_columns else ""
                order_by_clause = f"ORDER BY {sort_order}" if sort_order else ""
                limit_clause = f"LIMIT {limit_rows}" if limit_rows else ""
                
                debug_query = f"""SELECT {select_clause}
FROM DEMO.PALTAC.POS_DATA
{where_clause}
{group_by_clause}
{order_by_clause}
{limit_clause}"""
                st.code(debug_query, language="sql")
            
        else:
            st.warning("⚠️ 指定された条件に該当するデータが見つかりませんでした。フィルター条件を確認してください。")
            
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
        st.info("クエリ条件を確認して、再度実行してください。")
        
        # エラー詳細表示（デバッグ用）
        with st.expander("🔍 エラー詳細（デバッグ用）"):
            if selected_aggregates:
                aggregate_columns_sql = [aggregate_options[agg] for agg in selected_aggregates]
                select_parts = selected_group_columns + aggregate_columns_sql
                select_clause = ", ".join(select_parts)
                st.code(f"SELECT {select_clause}", language="sql")

# ダウンロード用のヘルパー関数
def get_download_link_csv(df, filename):
    """CSVダウンロードリンクを生成"""
    csv = df.to_csv(index=False, encoding='utf-8-sig')
    b64 = base64.b64encode(csv.encode('utf-8-sig')).decode()
    href = f'<a href="data:text/csv;base64,{b64}" download="{filename}" style="display: inline-block; padding: 0.5rem 1rem; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">📥 CSVダウンロード</a>'
    return href

def get_download_link_excel(df, filename):
    """Excelダウンロードリンクを生成"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='集計結果')
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}" style="display: inline-block; padding: 0.5rem 1rem; background-color: #217346; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">📊 Excelダウンロード</a>'
    return href

# ダウンロード機能（Base64エンコード方式）
if 'display_df' in st.session_state and not st.session_state['display_df'].empty:
    st.header("💾 データダウンロード")
    
    # 現在の日時を取得
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # データ件数表示
        st.metric("データ件数", f"{len(st.session_state['display_df']):,}件")
    
    with col2:
        # CSVダウンロードリンク
        csv_filename = f"sales_analysis_{current_time}.csv"
        csv_link = get_download_link_csv(st.session_state['display_df'], csv_filename)
        st.markdown(csv_link, unsafe_allow_html=True)
        st.caption("CSV形式（Excel/テキストエディタで開けます）")
    
    with col3:
        # Excelダウンロードリンク
        try:
            excel_filename = f"sales_analysis_{current_time}.xlsx"
            excel_link = get_download_link_excel(st.session_state['display_df'], excel_filename)
            st.markdown(excel_link, unsafe_allow_html=True)
            st.caption("Excel形式（.xlsx）")
        except Exception as e:
            st.warning("Excel出力にはopenpyxlが必要です")
            st.caption(f"エラー: {str(e)}")

# フッター情報
st.markdown("---")
st.markdown("💡 **使い方のヒント:**")
st.markdown("""
- **集計軸**: データをグループ化する項目を選択（例：会社名、部門、月など）
- **集計項目**: 計算したい数値項目を選択（例：売上合計、件数など）
- **フィルター**: 分析対象を絞り込むための条件設定
- **ソート**: 結果の並び順を指定
- **CSV出力**: 集計結果をExcelで開ける形式でダウンロード
""")

st.markdown("🏢 **データソース**: DEMO.PALTAC.POS_DATA | 🔄 **データ更新**: リアルタイム")

# セッション状態のリセット
if st.sidebar.button("🔄 設定リセット"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()