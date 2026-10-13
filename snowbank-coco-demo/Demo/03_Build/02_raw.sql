-- =====================================================================
-- 02_raw.sql
-- SnowBank Demo — Raw layer (set-based generation, ~2 sec runtime)
-- Builds: MERCHANTS, CUSTOMERS, ACCOUNTS, TRANSACTIONS
-- Embedded anomalies: structuring band, international skew, decline rates
-- =====================================================================

USE ROLE      ACCOUNTADMIN;
USE DATABASE  SNOWBANK_DEMO;
USE SCHEMA    RAW;
USE WAREHOUSE SNOWBANK_DEMO_WH;

-- ---------------------------------------------------------------------
-- MERCHANTS (~200) — 80% AU domestic, 20% offshore (so int'l is a signal)
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE MERCHANTS AS
SELECT
    'M' || LPAD(SEQ4(), 4, '0')                                AS merchant_id,
    'Merchant_' || LPAD(SEQ4(), 4, '0')                        AS merchant_name,
    CASE UNIFORM(1, 8, RANDOM())
        WHEN 1 THEN 'Groceries'      WHEN 2 THEN 'Retail'
        WHEN 3 THEN 'Travel'         WHEN 4 THEN 'Crypto'
        WHEN 5 THEN 'Gambling'       WHEN 6 THEN 'Utilities'
        WHEN 7 THEN 'Entertainment'  ELSE        'Cash/ATM'
    END                                                         AS category,
    CASE UNIFORM(1, 10, RANDOM())
        WHEN 1 THEN 'critical' WHEN 2 THEN 'high'
        WHEN 3 THEN 'high'     WHEN 4 THEN 'medium'
        ELSE 'low'
    END                                                         AS risk_classification,
    CASE
        WHEN UNIFORM(1, 100, RANDOM()) <= 80 THEN 'AU'
        ELSE
            CASE UNIFORM(1, 5, RANDOM())
                WHEN 1 THEN 'SG' WHEN 2 THEN 'HK'
                WHEN 3 THEN 'US' WHEN 4 THEN 'GB' ELSE 'AE'
            END
    END                                                         AS country
FROM TABLE(GENERATOR(ROWCOUNT => 200));

-- ---------------------------------------------------------------------
-- CUSTOMERS (~500)
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE CUSTOMERS AS
SELECT
    'C' || LPAD(SEQ4(), 5, '0')                                 AS customer_id,
    'Customer ' || LPAD(SEQ4(), 5, '0')                         AS customer_name,
    CASE UNIFORM(1, 10, RANDOM())
        WHEN 1 THEN 'private_wealth' WHEN 2 THEN 'premium'
        WHEN 3 THEN 'premium'        WHEN 4 THEN 'small_business'
        ELSE 'retail'
    END                                                         AS segment,
    CASE UNIFORM(1, 8, RANDOM())
        WHEN 1 THEN 'NSW' WHEN 2 THEN 'VIC' WHEN 3 THEN 'QLD'
        WHEN 4 THEN 'WA'  WHEN 5 THEN 'SA'  WHEN 6 THEN 'TAS'
        WHEN 7 THEN 'ACT' ELSE 'NT'
    END                                                         AS state,
    CASE UNIFORM(1, 10, RANDOM())
        WHEN 1 THEN 'high' WHEN 2 THEN 'medium' ELSE 'low'
    END                                                         AS risk_rating,
    CASE UNIFORM(1, 6, RANDOM())
        WHEN 1 THEN 'Engineer'   WHEN 2 THEN 'Doctor'
        WHEN 3 THEN 'Teacher'    WHEN 4 THEN 'Retiree'
        WHEN 5 THEN 'Self-employed' ELSE 'Other'
    END                                                         AS occupation,
    UNIFORM(40000, 350000, RANDOM())::NUMBER(12,2)              AS annual_income,
    DATEADD(DAY, -UNIFORM(180, 3650, RANDOM()), CURRENT_DATE())  AS account_open_date
FROM TABLE(GENERATOR(ROWCOUNT => 500));

-- ---------------------------------------------------------------------
-- ACCOUNTS (~700) — every customer gets at least one
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE ACCOUNTS AS
WITH base AS (
    SELECT customer_id FROM CUSTOMERS                                        -- 500
    UNION ALL
    SELECT customer_id FROM CUSTOMERS SAMPLE (40)                            -- ~200 extras
)
SELECT
    'A' || LPAD(ROW_NUMBER() OVER (ORDER BY RANDOM()), 5, '0')  AS account_id,
    customer_id,
    CASE UNIFORM(1, 4, RANDOM())
        WHEN 1 THEN 'savings' WHEN 2 THEN 'checking'
        WHEN 3 THEN 'credit'  ELSE 'investment'
    END                                                         AS account_type,
    UNIFORM(0, 250000, RANDOM())::NUMBER(12,2)                  AS opening_balance,
    'AUD'                                                       AS currency
FROM base;

-- ---------------------------------------------------------------------
-- TRANSACTIONS (~15k) — 12 months
-- Embedded anomalies (last 90 days, concentrated on a small cohort):
--   - ~30 customers in private_wealth + premium are flagged "suspicious"
--   - For these in the last 90 days only:
--       * 60% of amounts fall in the $9,000–$9,999 structuring band
--       * 70% are international
--       * ~18% decline rate (vs ~2% baseline)
--   - Everyone else / earlier history: normal patterns
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE TRANSACTIONS AS
WITH gen AS (
    SELECT
        SEQ4()                                                AS rn,
        UNIFORM(1, 700,  RANDOM())                            AS account_idx,
        UNIFORM(1, 200,  RANDOM())                            AS merchant_idx,
        UNIFORM(0, 364,  RANDOM())                            AS days_back,
        UNIFORM(0, 86400, RANDOM())                           AS sec_offset,
        UNIFORM(1, 100,  RANDOM())                            AS amt_bucket,
        UNIFORM(1, 100,  RANDOM())                            AS intl_dice,
        UNIFORM(1, 100,  RANDOM())                            AS status_dice
    FROM TABLE(GENERATOR(ROWCOUNT => 15000))
),
acct AS (
    SELECT a.account_id, a.customer_id, c.segment,
           -- Flag a concentrated cohort as suspicious (~30 customers)
           CASE
               WHEN c.segment = 'private_wealth'
                    AND MOD(ABS(HASH(c.customer_id)), 4) = 0 THEN TRUE
               WHEN c.segment = 'premium'
                    AND MOD(ABS(HASH(c.customer_id)), 20) = 0 THEN TRUE
               ELSE FALSE
           END AS is_suspicious_customer,
           ROW_NUMBER() OVER (ORDER BY a.account_id) AS rn
    FROM ACCOUNTS a
    JOIN CUSTOMERS c USING (customer_id)
),
merch AS (
    SELECT merchant_id, category, country, risk_classification,
           ROW_NUMBER() OVER (ORDER BY merchant_id) AS rn
    FROM MERCHANTS
),
base AS (
    SELECT
        g.rn,
        a.account_id,
        a.customer_id,
        a.segment,
        a.is_suspicious_customer,
        m.merchant_id,
        m.category                                                AS merchant_category,
        m.country                                                  AS counterparty_country,
        DATEADD(SECOND, g.sec_offset,
            DATEADD(DAY, -g.days_back, CURRENT_DATE()))             AS transaction_ts,
        g.days_back,
        g.amt_bucket,
        g.intl_dice,
        g.status_dice,
        -- recent = last 90 days; the anomaly window
        (g.days_back <= 90)                                        AS is_recent
    FROM gen g
    JOIN acct  a ON a.rn  = MOD(g.account_idx,  (SELECT COUNT(*) FROM acct))  + 1
    JOIN merch m ON m.rn  = MOD(g.merchant_idx, (SELECT COUNT(*) FROM merch)) + 1
)
SELECT
    'T' || LPAD(rn, 8, '0')                                     AS transaction_id,
    account_id,
    customer_id,
    merchant_id,
    merchant_category,
    transaction_ts,
    -- Amount: anomalous cohort in last 90d clusters in structuring band;
    -- everyone else: normal mix, no $9k cluster.
    CASE
        WHEN is_suspicious_customer AND is_recent THEN
            CASE
                WHEN amt_bucket <= 60 THEN UNIFORM(9000, 9999, RANDOM())::NUMBER(12,2)   -- structuring
                WHEN amt_bucket <= 80 THEN UNIFORM(15000, 75000, RANDOM())::NUMBER(12,2) -- big movers
                ELSE UNIFORM(50, 4000, RANDOM())::NUMBER(12,2)
            END
        ELSE
            CASE
                WHEN amt_bucket <= 70 THEN UNIFORM(5, 500, RANDOM())::NUMBER(12,2)
                WHEN amt_bucket <= 95 THEN UNIFORM(500, 5000, RANDOM())::NUMBER(12,2)
                ELSE UNIFORM(5000, 25000, RANDOM())::NUMBER(12,2)
            END
    END                                                        AS amount,
    'AUD'                                                       AS currency,
    CASE UNIFORM(1, 4, RANDOM())
        WHEN 1 THEN 'card' WHEN 2 THEN 'transfer'
        WHEN 3 THEN 'atm'  ELSE 'online'
    END                                                         AS channel,
    -- International: anomalous cohort in last 90d ~70%; baseline driven by merchant country (~20%).
    CASE
        WHEN is_suspicious_customer AND is_recent AND intl_dice <= 70 THEN TRUE
        WHEN counterparty_country <> 'AU' THEN TRUE
        ELSE FALSE
    END                                                         AS is_international,
    counterparty_country,
    -- Decline rate: anomalous cohort in last 90d ~18%; baseline ~2%.
    CASE
        WHEN is_suspicious_customer AND is_recent THEN
            CASE
                WHEN status_dice <= 18 THEN 'declined'
                WHEN status_dice <= 21 THEN 'pending'
                ELSE 'completed'
            END
        ELSE
            CASE
                WHEN status_dice <= 2  THEN 'declined'
                WHEN status_dice <= 4  THEN 'pending'
                ELSE 'completed'
            END
    END                                                         AS status
FROM base;

-- ---------------------------------------------------------------------
-- Confirmation
-- ---------------------------------------------------------------------
SELECT 'CUSTOMERS'    AS table_name, COUNT(*) AS row_count FROM CUSTOMERS
UNION ALL SELECT 'ACCOUNTS',     COUNT(*) FROM ACCOUNTS
UNION ALL SELECT 'MERCHANTS',    COUNT(*) FROM MERCHANTS
UNION ALL SELECT 'TRANSACTIONS', COUNT(*) FROM TRANSACTIONS;
