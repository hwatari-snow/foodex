-- =============================================================
-- SALES_ML スキーマ作成 & ML関連オブジェクト移行スクリプト
-- =============================================================
-- 目的: FOODEX_DEMO.BUYER_AGENT 内のML関連オブジェクトを
--       FOODEX_DEMO.SALES_ML スキーマに集約する
-- =============================================================

USE DATABASE FOODEX_DEMO;
USE WAREHOUSE COMPUTE_WH;

-- =============================================================
-- 1. SALES_ML スキーマの作成
-- =============================================================
CREATE SCHEMA IF NOT EXISTS FOODEX_DEMO.SALES_ML
    COMMENT = 'ML関連オブジェクト集約スキーマ（売上予測モデル、Feature Store、Model Monitor等）';

USE SCHEMA FOODEX_DEMO.SALES_ML;


