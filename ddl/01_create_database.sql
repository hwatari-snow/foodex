-- ============================================================
-- Foodex Buyer Agent Demo - Database & Schema Setup
-- ============================================================

USE ROLE SYSADMIN;

CREATE DATABASE IF NOT EXISTS FOODEX_DEMO;
CREATE SCHEMA IF NOT EXISTS FOODEX_DEMO.BUYER_AGENT;

USE DATABASE FOODEX_DEMO;
USE SCHEMA BUYER_AGENT;

CREATE WAREHOUSE IF NOT EXISTS FOODEX_WH
    WITH WAREHOUSE_SIZE = 'XSMALL'
    AUTO_SUSPEND = 60
    AUTO_RESUME = TRUE;

USE WAREHOUSE FOODEX_WH;
