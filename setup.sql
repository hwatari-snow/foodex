-- ============================================================
-- Foodex Buyer Agent Demo - 一括セットアップスクリプト
-- ============================================================
-- GitHub リポジトリから Git Integration 経由で CSV を取得し、
-- DB・スキーマ・テーブル作成・データロード・ビュー作成まで一括実行
-- ============================================================

-- ============================================================
-- Step 1: 初期設定
-- ============================================================

USE ROLE ACCOUNTADMIN;

ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';

CREATE WAREHOUSE IF NOT EXISTS FOODEX_WH
    WAREHOUSE_SIZE = 'XSMALL'
    WAREHOUSE_TYPE = 'STANDARD'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Warehouse for Foodex Buyer Agent Demo';

USE WAREHOUSE FOODEX_WH;

-- ============================================================
-- Step 2: データベース・スキーマ作成
-- ============================================================

CREATE DATABASE IF NOT EXISTS FOODEX_DEMO;
CREATE SCHEMA IF NOT EXISTS FOODEX_DEMO.BUYER_AGENT;

USE DATABASE FOODEX_DEMO;
USE SCHEMA BUYER_AGENT;

SHOW SCHEMAS IN DATABASE FOODEX_DEMO;

-- ============================================================
-- Step 3: Git Integration によるデータ取得
-- ============================================================

CREATE OR REPLACE STAGE FOODEX_DATA_STAGE
    DIRECTORY = (ENABLE = TRUE)
    ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
    COMMENT = 'Stage for Foodex Buyer Agent Demo data';

CREATE OR REPLACE API INTEGRATION foodex_git_api_integration
    API_PROVIDER = git_https_api
    API_ALLOWED_PREFIXES = ('https://github.com/')
    ENABLED = TRUE;

CREATE OR REPLACE GIT REPOSITORY FOODEX_GIT_REPO
    API_INTEGRATION = foodex_git_api_integration
    ORIGIN = 'https://github.com/hwatari-snow/foodex.git';

LIST @FOODEX_GIT_REPO/branches/main;

COPY FILES INTO @FOODEX_DATA_STAGE/csv/
    FROM @FOODEX_GIT_REPO/branches/main/data/
    PATTERN = '.*\.csv$';

LIST @FOODEX_DATA_STAGE/csv/;

-- ============================================================
-- Step 4: ファイルフォーマット作成
-- ============================================================

CREATE OR REPLACE FILE FORMAT CSV_FORMAT
    TYPE = 'CSV'
    FIELD_DELIMITER = ','
    SKIP_HEADER = 1
    FIELD_OPTIONALLY_ENCLOSED_BY = '"'
    NULL_IF = ('', 'NULL')
    ENCODING = 'UTF8';

-- ============================================================
-- Step 5: テーブル作成
-- ============================================================

-- 商品マスタ
CREATE OR REPLACE TABLE PRODUCT_MASTER (
    PRODUCT_ID        VARCHAR(10)   NOT NULL PRIMARY KEY,
    JAN_CODE          VARCHAR(13),
    PRODUCT_NAME      VARCHAR(200)  NOT NULL,
    BRAND_NAME        VARCHAR(100),
    MANUFACTURER_NAME VARCHAR(100)  NOT NULL,
    CATEGORY_LARGE    VARCHAR(50)   NOT NULL,
    CATEGORY_MEDIUM   VARCHAR(50),
    CATEGORY_SMALL    VARCHAR(50),
    UNIT_PRICE        NUMBER(10,0),
    COST_PRICE        NUMBER(10,0),
    UNIT_VOLUME       VARCHAR(20),
    UNIT_MEASURE      VARCHAR(10),
    LAUNCH_DATE       DATE,
    PRODUCT_DESCRIPTION VARCHAR(2000),
    IS_NEW_PRODUCT    BOOLEAN DEFAULT FALSE
);

-- 顧客マスタ
CREATE OR REPLACE TABLE CUSTOMER_MASTER (
    CUSTOMER_ID       VARCHAR(10)   NOT NULL PRIMARY KEY,
    GENDER            VARCHAR(4),
    BIRTH_DATE        DATE,
    AGE_GROUP         VARCHAR(10),
    PREFECTURE        VARCHAR(10),
    CITY              VARCHAR(50),
    MEMBERSHIP_TIER   VARCHAR(20),
    REGISTRATION_DATE DATE,
    FAMILY_SIZE       NUMBER(2,0),
    HAS_CHILDREN      BOOLEAN,
    OCCUPATION        VARCHAR(30)
);

-- 店舗マスタ
CREATE OR REPLACE TABLE STORE_MASTER (
    STORE_ID          VARCHAR(5)    NOT NULL PRIMARY KEY,
    STORE_NAME        VARCHAR(100)  NOT NULL,
    PREFECTURE        VARCHAR(10),
    CITY              VARCHAR(50),
    STORE_FORMAT      VARCHAR(20),
    SALES_FLOOR_AREA  NUMBER(8,0),
    OPENING_DATE      DATE
);

-- ID-POSトランザクション
CREATE OR REPLACE TABLE ID_POS_TRANSACTIONS (
    TRANSACTION_ID     VARCHAR(20)  NOT NULL PRIMARY KEY,
    BASKET_ID          VARCHAR(20)  NOT NULL,
    TRANSACTION_DATE   DATE         NOT NULL,
    TRANSACTION_TIME   TIME,
    CUSTOMER_ID        VARCHAR(10)  NOT NULL,
    STORE_ID           VARCHAR(5)   NOT NULL,
    PRODUCT_ID         VARCHAR(10)  NOT NULL,
    QUANTITY           NUMBER(5,0)  DEFAULT 1,
    UNIT_SELLING_PRICE NUMBER(10,0),
    DISCOUNT_AMOUNT    NUMBER(10,0) DEFAULT 0,
    SALES_AMOUNT       NUMBER(10,0),
    DAY_OF_WEEK        VARCHAR(3),
    FOREIGN KEY (CUSTOMER_ID) REFERENCES CUSTOMER_MASTER(CUSTOMER_ID),
    FOREIGN KEY (STORE_ID)    REFERENCES STORE_MASTER(STORE_ID),
    FOREIGN KEY (PRODUCT_ID)  REFERENCES PRODUCT_MASTER(PRODUCT_ID)
);

-- 在庫データ
CREATE OR REPLACE TABLE INVENTORY (
    INVENTORY_DATE          DATE        NOT NULL,
    STORE_ID                VARCHAR(5)  NOT NULL,
    PRODUCT_ID              VARCHAR(10) NOT NULL,
    STOCK_QUANTITY          NUMBER(8,0),
    REORDER_POINT           NUMBER(8,0),
    SAFETY_STOCK            NUMBER(8,0),
    DAYS_OF_SUPPLY          NUMBER(5,1),
    LAST_REPLENISHMENT_DATE DATE,
    PRIMARY KEY (INVENTORY_DATE, STORE_ID, PRODUCT_ID),
    FOREIGN KEY (STORE_ID)    REFERENCES STORE_MASTER(STORE_ID),
    FOREIGN KEY (PRODUCT_ID)  REFERENCES PRODUCT_MASTER(PRODUCT_ID)
);

-- ============================================================
-- Step 6: データロード
-- ============================================================

-- 店舗マスタ（FK参照元のため先にロード）
COPY INTO STORE_MASTER
FROM @FOODEX_DATA_STAGE/csv/
FILE_FORMAT = (FORMAT_NAME = 'CSV_FORMAT')
PATTERN = '.*store_master.*\.csv.*'
ON_ERROR = 'CONTINUE';

-- 商品マスタ
COPY INTO PRODUCT_MASTER
FROM @FOODEX_DATA_STAGE/csv/
FILE_FORMAT = (FORMAT_NAME = 'CSV_FORMAT')
PATTERN = '.*product_master.*\.csv.*'
ON_ERROR = 'CONTINUE';

-- 商品説明をAI_COMPLETEで生成し、PRODUCT_MASTER.PRODUCT_DESCRIPTIONを上書き
UPDATE PRODUCT_MASTER
SET PRODUCT_DESCRIPTION = TRIM(SNOWFLAKE.CORTEX.AI_COMPLETE(
    'llama3.1-8b',
    '以下の商品について、小売バイヤー向けの商品説明を日本語で1段落（150文字以内）で書いてください。'
    || 'マークダウン記法や箇条書きは使わず、プレーンテキストのみで出力してください。'
    || '消費者ターゲット、売場での訴求ポイント、競合との差別化要素を簡潔に含めてください。'
    || '\n\n'
    || '商品名: ' || PRODUCT_NAME
    || ' / ブランド: ' || COALESCE(BRAND_NAME, '不明')
    || ' / メーカー: ' || MANUFACTURER_NAME
    || ' / カテゴリ: ' || CATEGORY_LARGE || '>' || COALESCE(CATEGORY_MEDIUM, '') || '>' || COALESCE(CATEGORY_SMALL, '')
    || ' / 定価: ' || CAST(UNIT_PRICE AS VARCHAR) || '円',
    OBJECT_CONSTRUCT('max_tokens', 200, 'temperature', 0.3)
));


-- 顧客マスタ
COPY INTO CUSTOMER_MASTER
FROM @FOODEX_DATA_STAGE/csv/
FILE_FORMAT = (FORMAT_NAME = 'CSV_FORMAT')
PATTERN = '.*customer_master.*\.csv.*'
ON_ERROR = 'CONTINUE';

-- ID-POSトランザクション
COPY INTO ID_POS_TRANSACTIONS
FROM @FOODEX_DATA_STAGE/csv/
FILE_FORMAT = (FORMAT_NAME = 'CSV_FORMAT')
PATTERN = '.*id_pos_transactions.*\.csv.*'
ON_ERROR = 'CONTINUE';

-- 在庫データ
COPY INTO INVENTORY
FROM @FOODEX_DATA_STAGE/csv/
FILE_FORMAT = (FORMAT_NAME = 'CSV_FORMAT')
PATTERN = '.*inventory.*\.csv.*'
ON_ERROR = 'CONTINUE';

-- ============================================================
-- Step 7: Cortex Search Service 作成（商品の自然言語検索用）
-- ============================================================

CREATE OR REPLACE CORTEX SEARCH SERVICE PRODUCT_SEARCH
    ON PRODUCT_DESCRIPTION
    ATTRIBUTES PRODUCT_NAME, BRAND_NAME, MANUFACTURER_NAME, CATEGORY_LARGE, CATEGORY_MEDIUM, CATEGORY_SMALL, UNIT_PRICE, COST_PRICE, IS_NEW_PRODUCT
    WAREHOUSE = FOODEX_WH
    TARGET_LAG = '1 hour'
    AS (
        SELECT
            PRODUCT_ID,
            PRODUCT_NAME,
            BRAND_NAME,
            MANUFACTURER_NAME,
            CATEGORY_LARGE,
            CATEGORY_MEDIUM,
            CATEGORY_SMALL,
            UNIT_PRICE,
            COST_PRICE,
            UNIT_VOLUME || UNIT_MEASURE AS UNIT_SIZE,
            LAUNCH_DATE,
            IS_NEW_PRODUCT,
            PRODUCT_DESCRIPTION
        FROM PRODUCT_MASTER
    );

-- ============================================================
-- Step 8: セマンティックビュー作成（Snowflake Intelligence 用）
-- ============================================================

CREATE OR REPLACE SEMANTIC VIEW FOODEX_BUYER_ANALYSIS

  TABLES (
    product   AS FOODEX_DEMO.BUYER_AGENT.PRODUCT_MASTER
      PRIMARY KEY (PRODUCT_ID)
      COMMENT = 'NB加工食品の商品マスタ（192商品）',

    customer  AS FOODEX_DEMO.BUYER_AGENT.CUSTOMER_MASTER
      PRIMARY KEY (CUSTOMER_ID)
      COMMENT = '顧客マスタ（2,000顧客、年代・性別・世帯構成等）',

    store     AS FOODEX_DEMO.BUYER_AGENT.STORE_MASTER
      PRIMARY KEY (STORE_ID)
      COMMENT = '店舗マスタ（20店舗）',

    txn       AS FOODEX_DEMO.BUYER_AGENT.ID_POS_TRANSACTIONS
      PRIMARY KEY (TRANSACTION_ID)
      COMMENT = 'ID-POSトランザクション（10万件、2年分、basket_id付き）',

    inventory AS FOODEX_DEMO.BUYER_AGENT.INVENTORY
      PRIMARY KEY (INVENTORY_DATE, STORE_ID, PRODUCT_ID)
      COMMENT = '在庫データ（直近日の商品×店舗、約3,840件）'
  )

  RELATIONSHIPS (
    txn       (CUSTOMER_ID) REFERENCES customer,
    txn       (STORE_ID)    REFERENCES store,
    txn       (PRODUCT_ID)  REFERENCES product,
    inventory (STORE_ID)    REFERENCES store,
    inventory (PRODUCT_ID)  REFERENCES product
  )

  FACTS (
    -- 取引系計算カラム
    txn.gross_profit AS (txn.SALES_AMOUNT - txn.QUANTITY * product.COST_PRICE)
      COMMENT = '粗利額（売上金額 − 数量 × 原価）',

    txn.total_discount AS (txn.DISCOUNT_AMOUNT * txn.QUANTITY)
      COMMENT = '値引合計額',

    txn.transaction_hour AS HOUR(txn.TRANSACTION_TIME)
      COMMENT = '取引時間帯（0〜23）',

    -- 在庫系計算カラム
    inventory.stock_surplus AS (inventory.STOCK_QUANTITY - inventory.REORDER_POINT)
      COMMENT = '発注点との差分（負なら要発注）'
  )

  DIMENSIONS (
    -- === 商品属性 ===
    product.product_name AS product.PRODUCT_NAME
      COMMENT = '商品名',
    product.jan_code AS product.JAN_CODE
      COMMENT = 'JANコード',
    product.brand_name AS product.BRAND_NAME
      COMMENT = 'ブランド名',
    product.manufacturer_name AS product.MANUFACTURER_NAME
      COMMENT = 'メーカー名',
    product.category_large AS product.CATEGORY_LARGE
      COMMENT = '大カテゴリ（飲料・菓子・調味料・即席食品・缶詰レトルト・乳製品・冷凍食品・パンシリアル）',
    product.category_medium AS product.CATEGORY_MEDIUM
      COMMENT = '中カテゴリ',
    product.category_small AS product.CATEGORY_SMALL
      COMMENT = '小カテゴリ',
    product.is_new_product AS product.IS_NEW_PRODUCT
      COMMENT = '新商品フラグ（TRUE=直近発売の新商品）',
    product.unit_volume AS product.UNIT_VOLUME
      COMMENT = '内容量',
    product.unit_measure AS product.UNIT_MEASURE
      COMMENT = '単位（ml, g 等）',
    product.unit_price AS product.UNIT_PRICE
      COMMENT = '定価（税抜）',
    product.cost_price AS product.COST_PRICE
      COMMENT = '原価',
    product.launch_date AS product.LAUNCH_DATE
      COMMENT = '発売日',

    -- === 顧客属性 ===
    customer.gender AS customer.GENDER
      COMMENT = '性別（男性・女性）',
    customer.age_group AS customer.AGE_GROUP
      COMMENT = '年代（20代・30代・40代・50代・60代・70代以上）',
    customer.customer_prefecture AS customer.PREFECTURE
      COMMENT = '顧客の都道府県',
    customer.customer_city AS customer.CITY
      COMMENT = '顧客の市区町村',
    customer.membership_tier AS customer.MEMBERSHIP_TIER
      COMMENT = '会員ランク',
    customer.family_size AS customer.FAMILY_SIZE
      COMMENT = '世帯人数',
    customer.has_children AS customer.HAS_CHILDREN
      COMMENT = '子どもの有無',
    customer.occupation AS customer.OCCUPATION
      COMMENT = '職業',
    customer.birth_date AS customer.BIRTH_DATE
      COMMENT = '生年月日',
    customer.registration_date AS customer.REGISTRATION_DATE
      COMMENT = '会員登録日',

    -- === 店舗属性 ===
    store.store_name AS store.STORE_NAME
      COMMENT = '店舗名',
    store.store_prefecture AS store.PREFECTURE
      COMMENT = '店舗の都道府県',
    store.store_city AS store.CITY
      COMMENT = '店舗の市区町村',
    store.store_format AS store.STORE_FORMAT
      COMMENT = '店舗フォーマット（SM等）',
    store.sales_floor_area AS store.SALES_FLOOR_AREA
      COMMENT = '売場面積（平米）',
    store.opening_date AS store.OPENING_DATE
      COMMENT = '開店日',

    -- === 取引属性 ===
    txn.transaction_date AS txn.TRANSACTION_DATE
      COMMENT = '取引日',
    txn.day_of_week AS txn.DAY_OF_WEEK
      COMMENT = '曜日（月・火・水・木・金・土・日）',
    txn.basket_id AS txn.BASKET_ID
      COMMENT = 'バスケットID（同一会計の商品をグルーピング。併売分析に使用）',
    txn.hour_of_day AS txn.transaction_hour
      COMMENT = '取引時間帯（0〜23、FACT参照）',

    -- === 在庫属性 ===
    inventory.inventory_date AS inventory.INVENTORY_DATE
      COMMENT = '在庫日',
    inventory.last_replenishment_date AS inventory.LAST_REPLENISHMENT_DATE
      COMMENT = '最終補充日',
    inventory.stock_status AS
      CASE
        WHEN inventory.STOCK_QUANTITY = 0 THEN '欠品'
        WHEN inventory.STOCK_QUANTITY <= inventory.SAFETY_STOCK THEN '要緊急発注'
        WHEN inventory.STOCK_QUANTITY <= inventory.REORDER_POINT THEN '要発注'
        WHEN inventory.DAYS_OF_SUPPLY > 30 THEN '過剰在庫'
        ELSE '適正'
      END
      COMMENT = '在庫ステータス（欠品・要緊急発注・要発注・過剰在庫・適正）'
  )

  METRICS (
    -- === 売上系 ===
    txn.total_sales AS SUM(txn.SALES_AMOUNT)
      COMMENT = '売上合計（円）',
    txn.total_quantity AS SUM(txn.QUANTITY)
      COMMENT = '販売数量合計',
    txn.total_gross_profit AS SUM(txn.gross_profit)
      COMMENT = '粗利合計（円）',
    txn.gross_margin_pct AS SUM(txn.gross_profit) / NULLIF(SUM(txn.SALES_AMOUNT), 0) * 100
      COMMENT = '粗利率（%）',
    txn.avg_selling_price AS AVG(txn.UNIT_SELLING_PRICE)
      COMMENT = '平均売価（円）',
    txn.total_discount_amount AS SUM(txn.total_discount)
      COMMENT = '値引合計額（円）',

    -- === 件数・ユニーク数 ===
    txn.transaction_count AS COUNT(txn.TRANSACTION_ID)
      COMMENT = '取引件数',
    txn.basket_count AS COUNT(DISTINCT txn.BASKET_ID)
      COMMENT = 'バスケット数（来店回数の近似）',
    txn.unique_customer_count AS COUNT(DISTINCT txn.CUSTOMER_ID)
      COMMENT = 'ユニーク顧客数',
    txn.unique_product_count AS COUNT(DISTINCT txn.PRODUCT_ID)
      COMMENT = '購入商品種類数',
    txn.unique_store_count AS COUNT(DISTINCT txn.STORE_ID)
      COMMENT = '販売店舗数',

    -- === 在庫系 ===
    inventory.total_stock AS SUM(inventory.STOCK_QUANTITY)
      COMMENT = '在庫数合計',
    inventory.avg_days_of_supply AS AVG(inventory.DAYS_OF_SUPPLY)
      COMMENT = '平均在庫日数',
    inventory.inventory_item_count AS COUNT(*)
      COMMENT = '在庫レコード数（商品×店舗の組み合わせ数）',

    -- === マスタ系 ===
    product.product_count AS COUNT(product.PRODUCT_ID)
      COMMENT = '商品数',
    customer.customer_count AS COUNT(customer.CUSTOMER_ID)
      COMMENT = '顧客数',
    store.store_count AS COUNT(store.STORE_ID)
      COMMENT = '店舗数'
  )

  COMMENT = 'Foodex Buyer Agent デモ用セマンティックビュー。小売バイヤーの売上分析・在庫最適化・新商品評価・併売分析を支援。'

  AI_SQL_GENERATION '
このセマンティックビューは日本の小売チェーン「フーデックスマート」のバイヤー（仕入担当者）向け分析データセットです。

## データの特性
- 金額はすべて日本円（JPY）、税抜表示
- 商品はNB（ナショナルブランド）加工食品が中心（飲料・菓子・調味料・即席食品・缶詰レトルト・乳製品・冷凍食品・パンシリアル）
- 商品名・カテゴリ名・店舗名は日本語
- DAY_OF_WEEK は月・火・水・木・金・土・日の漢字1文字
- 2年分のID-POSデータと直近日の在庫データを保持

## 主要ユースケース
1. **カテゴリ・商品別売上分析**: カテゴリ別、メーカー別、ブランド別の売上・数量・粗利を分析
2. **新商品仕入れ判断**: IS_NEW_PRODUCT = TRUE の商品について、発売後の売上推移や顧客浸透率を評価
3. **併売（バスケット）分析**: BASKET_ID を使い、同一バスケット内で一緒に購入される商品ペアを特定。セルフジョインで txn テーブルを BASKET_ID で結合する
4. **在庫最適化・欠品リスク分析**: stock_status ディメンションで欠品・要発注の商品×店舗を特定
5. **メーカー別シェア分析**: カテゴリ内でのメーカー別売上シェアを算出
6. **顧客セグメント分析**: 年代・性別・世帯構成別の購買傾向を分析
7. **時間帯・曜日分析**: 曜日や時間帯ごとの売上パターンを把握

## 重要な注意事項
- 併売分析では、txn テーブルを a, b として BASKET_ID で自己結合し、a.PRODUCT_ID < b.PRODUCT_ID の条件で重複排除すること
- 粗利率は (売上 - 原価×数量) / 売上 × 100 で計算
- 在庫データ（inventory）とPOSデータ（txn）は直接結合しない。それぞれ独立して分析するか、商品・店舗をキーに比較する
'
;

-- ============================================================
-- Step 9: Cortex Agent 作成
-- ============================================================

CREATE OR REPLACE AGENT FOODEX_BUYER_AGENT
    COMMENT = 'Foodex Buyer Agent - 小売バイヤー向けAIアシスタント'
    PROFILE = '{"display_name": "Foodex バイヤーアシスタント", "color": "green"}'
    FROM SPECIFICATION
    $$
    orchestration:
        budget:
            seconds: 60
            tokens: 32000

    instructions:
        system: >
            あなたは日本の小売チェーン「フーデックスマート」のバイヤー（仕入担当者）を支援するAIアシスタントです。
            商品の売上分析、新商品の仕入れ判断、在庫最適化、併売分析などの業務をサポートします。
            回答は常に日本語で行い、具体的な数値やデータに基づいた提案を行ってください。
        response: >
            回答は日本語で、簡潔かつ具体的に行ってください。
            数値データを含む場合は表形式で見やすく整理してください。
            分析結果に基づくアクション提案（仕入れ増減、棚割り変更、プロモーション提案など）を必ず含めてください。
        orchestration: >
            売上・在庫・顧客に関する定量的な質問にはAnalystツールを使用してください。
            商品の特徴や説明に関する質問、商品検索にはSearchツールを使用してください。
            新商品の仕入れ判断では、まずSearchで商品情報を取得し、次にAnalystで売上データを分析する2段階で回答してください。
        sample_questions:
            - question: "新商品で一番売れているのは何ですか？"
            - question: "アサヒスーパードライ 生ジョッキ缶と一緒に買われている商品は？"
            - question: "アサヒスーパードライ 生ジョッキ缶の在庫は足りていますか？追加発注が必要な店舗はありますか？"
            - question: "伊右衛門 京の抹茶入りが発売されてから、既存の伊右衛門525mlの売上は落ちていませんか？カニバリが発生しているか分析してください"
            - question: "明治チョコレート効果カカオ86%を買っている顧客は、カカオ72%も買っていますか？それとも新規の顧客層を取り込めていますか？"
            - question: "ポッキー贅沢仕立て（250円）と通常のポッキー（180円）の購買層を比較してください。プレミアム路線は機能していますか？"
            - question: "新商品12品の中で、定番棚に残すべき商品と終売候補を、初動売上・リピーター率・販売店舗数をもとに判断してください"
            - question: "緑茶カテゴリでサントリー（伊右衛門）とコカ・コーラ（綾鷹）と伊藤園（お～いお茶）のシェア推移を月別で見せてください。どのメーカーに棚を増やすべきですか？"
            - question: "飲料カテゴリで売上トップ10の商品を教えてください"
            - question: "アサヒスーパードライ生ジョッキ缶の現在の在庫状況と販売ペースを確認してください。このまま行くと何日で欠品しますか？"
            - question: "ビールと一緒に買われている商品は何ですか？おつまみ売り場の棚割りの参考にしたいです"
            - question: "30代女性・子供あり世帯がよく買っている商品トップ20を教えてください。この層に向けた売場提案をしてください"
            - question: "プラチナ会員の購買単価と購入カテゴリの特徴を教えてください。この層が買っていてレギュラー会員が買っていない商品は何ですか？"
            - question: "現在、欠品リスクのある商品を店舗別に教えてください"
            - question: "健康志向の商品を探しています"

    tools:
        - tool_spec:
              type: "cortex_analyst_text_to_sql"
              name: "Analyst"
              description: >
                  売上データ、在庫データ、顧客データを使った定量分析ツール。
                  商品別・カテゴリ別の売上集計、粗利分析、併売分析、在庫状況確認、
                  顧客セグメント分析、時系列トレンド分析などに使用する。
        - tool_spec:
              type: "cortex_search"
              name: "ProductSearch"
              description: >
                  商品マスタに対する自然言語検索ツール。
                  商品名、ブランド名、メーカー名、カテゴリ、商品説明をもとに
                  関連する商品を検索する。新商品の情報取得や、
                  特定の条件に合う商品の検索に使用する。

    tool_resources:
        Analyst:
            semantic_view: "FOODEX_DEMO.BUYER_AGENT.FOODEX_BUYER_ANALYSIS"
        ProductSearch:
            name: "FOODEX_DEMO.BUYER_AGENT.PRODUCT_SEARCH"
            max_results: "10"
            id_column: "PRODUCT_ID"
    $$;

-- ============================================================
-- Step 10: データ確認・動作確認
-- ============================================================

-- テーブル件数確認
SELECT 'PRODUCT_MASTER'      AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM PRODUCT_MASTER
UNION ALL
SELECT 'CUSTOMER_MASTER',     COUNT(*) FROM CUSTOMER_MASTER
UNION ALL
SELECT 'STORE_MASTER',        COUNT(*) FROM STORE_MASTER
UNION ALL
SELECT 'ID_POS_TRANSACTIONS', COUNT(*) FROM ID_POS_TRANSACTIONS
UNION ALL
SELECT 'INVENTORY',           COUNT(*) FROM INVENTORY;

