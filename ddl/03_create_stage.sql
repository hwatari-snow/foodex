-- ============================================================
-- Foodex Buyer Agent Demo - Stage Setup
-- ============================================================

USE DATABASE FOODEX_DEMO;
USE SCHEMA BUYER_AGENT;

CREATE OR REPLACE STAGE FOODEX_DATA_STAGE
    FILE_FORMAT = (
        TYPE = 'CSV'
        FIELD_OPTIONALLY_ENCLOSED_BY = '"'
        SKIP_HEADER = 1
        NULL_IF = ('', 'NULL')
        ENCODING = 'UTF8'
    );

-- CSVファイルをアップロード（SnowSQL or Snowsight UIから実行）
-- PUT file:///path/to/data/product_master.csv @FOODEX_DATA_STAGE/product_master;
-- PUT file:///path/to/data/customer_master.csv @FOODEX_DATA_STAGE/customer_master;
-- PUT file:///path/to/data/store_master.csv @FOODEX_DATA_STAGE/store_master;
-- PUT file:///path/to/data/id_pos_transactions.csv @FOODEX_DATA_STAGE/id_pos_transactions;
-- PUT file:///path/to/data/inventory.csv @FOODEX_DATA_STAGE/inventory;
