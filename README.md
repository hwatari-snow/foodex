# Foodex Buyer Agent デモデータセット

Foodex Japan デモ向け Snowflake Intelligence Buyer エージェント用データセット。

## 概要
です

小売バイヤーの業務を支援するAIエージェントのデモ用に、NB（ナショナルブランド）加工食品を中心としたリアルなデータセットを提供します！

## データセット構成

| テーブル | 件数 | 説明 |
|---|---|---|
| PRODUCT_MASTER | 192件 | NB商品マスタ（飲料・菓子・調味料・即席食品・缶詰/レトルト・乳製品・冷凍食品・パン/シリアル） |
| CUSTOMER_MASTER | 2,000件 | 顧客属性情報（年代・性別・世帯構成など） |
| ID_POS_TRANSACTIONS | 10万件 | 2年分のID-POSデータ（併売分析対応のbasket_id付き） |
| INVENTORY | 3,840件 | 直近日の在庫データ（商品×店舗） |
| STORE_MASTER | 20件 | 店舗マスタ |

## 想定ユースケース

- **新商品仕入れ判断**: 過去データ＋Web検索を組み合わせ、新商品の売上ポテンシャルを分析
- **自然言語商品検索**: 商品を自然言語で検索し、売れ行き分析と連携
- **併売分析**: バスケット分析による関連商品の特定
- **在庫最適化**: 在庫状況と販売傾向のギャップ分析

## セットアップ手順

### 1. データ生成

```bash
cd scripts
pip install -r requirements.txt
python generate_data.py
```

### 2. Snowflake へのデプロイ

```sql
-- 1. データベース・スキーマ作成
-- ddl/01_create_database.sql を実行

-- 2. テーブル作成
-- ddl/02_create_tables.sql を実行

-- 3. Stage 作成・データアップロード
-- ddl/03_create_stage.sql を実行
-- PUT コマンドでCSVファイルをアップロード

-- 4. データロード
-- ddl/04_load_data.sql を実行

-- 5. 分析用ビュー作成
-- ddl/05_create_views.sql を実行
```

## ディレクトリ構成

```
Foodex_BuyerAgent/
├── README.md
├── ddl/
│   ├── 01_create_database.sql
│   ├── 02_create_tables.sql
│   ├── 03_create_stage.sql
│   ├── 04_load_data.sql
│   └── 05_create_views.sql
├── data/
│   ├── product_master.csv
│   ├── customer_master.csv
│   ├── id_pos_transactions.csv
│   ├── inventory.csv
│   └── store_master.csv
└── scripts/
    ├── generate_data.py
    └── requirements.txt
```
