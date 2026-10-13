-- =====================================================================
-- 01_database_setup.sql
-- SnowBank Demo — initial Snowflake account scaffolding
-- Run once before Scene 2. Idempotent.
-- =====================================================================

USE ROLE ACCOUNTADMIN;

-- ---------- Warehouse ------------------------------------------------
CREATE WAREHOUSE IF NOT EXISTS SNOWBANK_DEMO_WH
    WAREHOUSE_SIZE = XSMALL
    AUTO_SUSPEND   = 60
    AUTO_RESUME    = TRUE
    INITIALLY_SUSPENDED = TRUE
    COMMENT = 'Compute for the SnowBank Cortex Code demo';

-- ---------- Database & Schemas --------------------------------------
CREATE DATABASE IF NOT EXISTS SNOWBANK_DEMO
    COMMENT = 'SnowBank Cortex Code demo — Raw / Curated / Analytics';

USE DATABASE SNOWBANK_DEMO;

CREATE SCHEMA IF NOT EXISTS RAW       COMMENT = 'Landing zone — raw ingested data';
CREATE SCHEMA IF NOT EXISTS CURATED   COMMENT = 'Conformed / cleansed business entities';
CREATE SCHEMA IF NOT EXISTS ANALYTICS COMMENT = 'Aggregations & behavioural views for Cortex Analyst';
CREATE SCHEMA IF NOT EXISTS ASSETS    COMMENT = 'Custom tools, skills, semantic views, agents';

-- ---------- Stage for assets (skills / tool definitions) ------------
CREATE STAGE IF NOT EXISTS SNOWBANK_DEMO.ASSETS.DEMO_ASSETS
    DIRECTORY = (ENABLE = TRUE)
    COMMENT = 'Holds prebuilt assets activated during the demo';

-- ---------- Confirmation -------------------------------------------
SELECT 'SnowBank demo scaffolding ready' AS status,
       CURRENT_DATABASE()  AS database,
       CURRENT_WAREHOUSE() AS warehouse,
       CURRENT_ROLE()      AS role;
