-- =====================================================================================
-- Synthetic data for agentic evaluations: SETUP 2 of 2 (optional, only for notebook section 7 "At scale")
--
-- A 20M-row applications table is over the 14M-rows-per-table limit of one GENERATE_SYNTHETIC_DATA call,
-- so it is generated the way you would in production:
--   1. Seed MORTGAGE_PROD.SCALE.APPLICATION_20M (same patterns as setup 1; ~12M applicants, many with several applications)
--   2. Split into two halves by a hash of application_id (deterministic, every row in exactly one half)
--   3. One GENERATE_SYNTHETIC_DATA call per half with the SAME consistency secret,
--      so a real applicant gets the same synthetic ID in both calls
--   4. Stitch into MORTGAGE_DEV.SCALE_SYNTH.APPLICATION_20M (generation_call = 1 or 2); record SCALE_SPLIT_RUN
--   5. Precompute MORTGAGE_DEV.CORE_EVAL.SPLIT_SCORECARD (prod vs call 1 vs call 2 vs combined) + SPLIT_LOAN_DIST (chart)
--
-- Run AFTER setup_1_core.sql. Takes about 30-40 minutes and about 2-3 credits (two ~13-minute calls on a
-- Medium Snowpark-optimised warehouse, SCALE_GEN_WH, created here), plus the seed and scorecard on AI_WH.
-- How to run: Run All in a Workspace / worksheet, or: snow sql -c <connection> -f setup_2_at_scale.sql
-- Rerunnable. Skip it and the notebook still runs; only the section 7 cells will fail.
-- =====================================================================================
USE ROLE ACCOUNTADMIN;
CREATE WAREHOUSE IF NOT EXISTS SCALE_GEN_WH
  WAREHOUSE_SIZE = MEDIUM WAREHOUSE_TYPE = 'SNOWPARK-OPTIMIZED'
  AUTO_SUSPEND = 60 AUTO_RESUME = TRUE INITIALLY_SUSPENDED = TRUE;
CREATE SCHEMA IF NOT EXISTS MORTGAGE_PROD.SCALE;
CREATE SCHEMA IF NOT EXISTS MORTGAGE_DEV.SCALE_SYNTH;
USE WAREHOUSE AI_WH;

-- 1. Seed
CREATE OR REPLACE TABLE MORTGAGE_PROD.SCALE.APPLICATION_20M AS
WITH g AS (
  SELECT SEQ8() + 1 AS n,
         UNIFORM(1, 12000000, RANDOM(31)) AS apl,
         UNIFORM(0::FLOAT, 1::FLOAT, RANDOM(11)) AS r_emp, UNIFORM(0::FLOAT, 1::FLOAT, RANDOM(12)) AS r_brk,
         UNIFORM(0::FLOAT, 1::FLOAT, RANDOM(13)) AS r_dec, UNIFORM(0::FLOAT, 1::FLOAT, RANDOM(14)) AS r_pur,
         UNIFORM(0::FLOAT, 1::FLOAT, RANDOM(16)) AS r_sub,
         NORMAL(0, 1, RANDOM(17)) AS z_inc, NORMAL(0, 1, RANDOM(18)) AS z_lvr, NORMAL(0, 1, RANDOM(19)) AS z_mult,
         UNIFORM(0, 272, RANDOM(23)) AS d_app
  FROM TABLE(GENERATOR(ROWCOUNT => 20000000))
), s AS (
  SELECT g.*,
    CASE WHEN r_emp < 0.12 THEN 'SELF_EMPLOYED' WHEN r_emp < 0.22 THEN 'CONTRACT' ELSE 'PAYG' END AS employment_type,
    CASE WHEN r_brk < 0.40 THEN 'AGGREGATOR' WHEN r_brk < 0.60 THEN 'BROKER_TIER1' ELSE 'DIRECT' END AS broker_type,
    CASE WHEN r_sub < 0.70 THEN 'METRO' WHEN r_sub < 0.93 THEN 'REGIONAL' ELSE 'REMOTE' END AS suburb_type,
    ROUND(LEAST(97, GREATEST(30, 72 + 9 * z_lvr)), 1) AS lvr
  FROM g
), t AS (
  SELECT s.*,
    ROUND(GREATEST(40000, CASE employment_type WHEN 'SELF_EMPLOYED' THEN 140000 + 60000 * z_inc
                                               WHEN 'CONTRACT' THEN 120000 + 40000 * z_inc
                                               ELSE 105000 + 35000 * z_inc END), -2) AS declared_income
  FROM s
)
SELECT 'APP-' || LPAD(n, 9, '0') AS application_id,
       'APL-' || LPAD(apl, 9, '0') AS applicant_id,
       broker_type,
       CASE WHEN r_pur < 0.55 THEN 'OWNER_OCCUPIED_PURCHASE' WHEN r_pur < 0.80 THEN 'INVESTMENT_PURCHASE' ELSE 'REFINANCE' END AS purpose,
       ROUND(LEAST(3000000, GREATEST(150000, declared_income * (5.2 + 0.9 * z_mult))), -3) AS loan_amount,
       lvr,
       DATEADD(day, d_app, '2026-01-01'::DATE) AS application_date,
       CASE WHEN r_dec < (CASE WHEN lvr > 90 THEN 0.30 ELSE 0.10 END) THEN 'DECLINED'
            WHEN r_dec > 0.87 THEN 'WITHDRAWN' ELSE 'APPROVED' END AS decision,
       employment_type, declared_income, suburb_type
FROM t;

-- 2. Split: two halves by a hash of application_id (each ~10M rows, under the 14M limit)
CREATE OR REPLACE VIEW MORTGAGE_PROD.SCALE.APPLICATION_20M_PART1 AS
  SELECT * FROM MORTGAGE_PROD.SCALE.APPLICATION_20M WHERE MOD(ABS(HASH(application_id)), 2) = 0;
CREATE OR REPLACE VIEW MORTGAGE_PROD.SCALE.APPLICATION_20M_PART2 AS
  SELECT * FROM MORTGAGE_PROD.SCALE.APPLICATION_20M WHERE MOD(ABS(HASH(application_id)), 2) = 1;
SELECT (SELECT COUNT(*) FROM MORTGAGE_PROD.SCALE.APPLICATION_20M) AS total_rows,
       (SELECT COUNT(*) FROM MORTGAGE_PROD.SCALE.APPLICATION_20M_PART1) AS part1_rows,
       (SELECT COUNT(*) FROM MORTGAGE_PROD.SCALE.APPLICATION_20M_PART2) AS part2_rows;

-- 3. Two calls, same secret (join keys: application_id unique, applicant_id repeats across halves)
USE WAREHOUSE SCALE_GEN_WH;
USE SCHEMA MORTGAGE_PROD.ADMIN;   -- secret reference resolves in the session schema
CALL SNOWFLAKE.DATA_PRIVACY.GENERATE_SYNTHETIC_DATA({
  'datasets': [
    { 'input_table':  'MORTGAGE_PROD.SCALE.APPLICATION_20M_PART1',
      'output_table': 'MORTGAGE_DEV.SCALE_SYNTH.APPLICATION_20M_PART1',
      'columns': { 'application_id': {'join_key': TRUE, 'replace': 'uuid'},
                   'applicant_id':   {'join_key': TRUE, 'replace': 'uuid'} } }
  ],
  'consistency_secret': SYSTEM$REFERENCE('SECRET', 'SYNTH_SECRET', 'SESSION', 'READ')::STRING,
  'replace_output_tables': TRUE
});
SET call1_qid = LAST_QUERY_ID();
CALL SNOWFLAKE.DATA_PRIVACY.GENERATE_SYNTHETIC_DATA({
  'datasets': [
    { 'input_table':  'MORTGAGE_PROD.SCALE.APPLICATION_20M_PART2',
      'output_table': 'MORTGAGE_DEV.SCALE_SYNTH.APPLICATION_20M_PART2',
      'columns': { 'application_id': {'join_key': TRUE, 'replace': 'uuid'},
                   'applicant_id':   {'join_key': TRUE, 'replace': 'uuid'} } }
  ],
  'consistency_secret': SYSTEM$REFERENCE('SECRET', 'SYNTH_SECRET', 'SESSION', 'READ')::STRING,
  'replace_output_tables': TRUE
});
SET call2_qid = LAST_QUERY_ID();
USE WAREHOUSE AI_WH;

-- 4. Stitch, record the run
CREATE OR REPLACE TABLE MORTGAGE_DEV.SCALE_SYNTH.APPLICATION_20M AS
SELECT 1 AS generation_call, * FROM MORTGAGE_DEV.SCALE_SYNTH.APPLICATION_20M_PART1
UNION ALL
SELECT 2 AS generation_call, * FROM MORTGAGE_DEV.SCALE_SYNTH.APPLICATION_20M_PART2;
DROP TABLE MORTGAGE_DEV.SCALE_SYNTH.APPLICATION_20M_PART1;
DROP TABLE MORTGAGE_DEV.SCALE_SYNTH.APPLICATION_20M_PART2;

CREATE OR REPLACE TABLE MORTGAGE_DEV.CORE_EVAL.SCALE_SPLIT_RUN AS
SELECT IFF(q.query_id = $call1_qid, 1, 2) AS generation_call,
       (SELECT COUNT(*) FROM MORTGAGE_PROD.SCALE.APPLICATION_20M WHERE MOD(ABS(HASH(application_id)), 2) = IFF(q.query_id = $call1_qid, 0, 1)) AS input_rows,
       (SELECT COUNT(*) FROM MORTGAGE_DEV.SCALE_SYNTH.APPLICATION_20M s WHERE s.generation_call = IFF(q.query_id = $call1_qid, 1, 2)) AS synthetic_rows,
       q.warehouse_size, ROUND(q.total_elapsed_time / 60000, 1) AS minutes, q.start_time, q.end_time
FROM TABLE(MORTGAGE_PROD.INFORMATION_SCHEMA.QUERY_HISTORY_BY_WAREHOUSE(WAREHOUSE_NAME => 'SCALE_GEN_WH', RESULT_LIMIT => 1000)) q
WHERE q.query_id IN ($call1_qid, $call2_qid);
-- Credits for the generation warehouse over both calls (metering is hourly; nothing else runs on SCALE_GEN_WH)
SET (run_start, run_end) = (SELECT MIN(start_time), MAX(end_time) FROM MORTGAGE_DEV.CORE_EVAL.SCALE_SPLIT_RUN);
SET run_credits = (SELECT ROUND(SUM(credits_used), 2) FROM TABLE(MORTGAGE_PROD.INFORMATION_SCHEMA.WAREHOUSE_METERING_HISTORY(
                     DATEADD('hour', -1, $run_start::TIMESTAMP_LTZ), DATEADD('hour', 1, $run_end::TIMESTAMP_LTZ), 'SCALE_GEN_WH')));
CREATE OR REPLACE TABLE MORTGAGE_DEV.CORE_EVAL.SCALE_SPLIT_RUN AS
SELECT r.*, $run_credits AS credits_both_calls FROM MORTGAGE_DEV.CORE_EVAL.SCALE_SPLIT_RUN r ORDER BY generation_call;
GRANT SELECT ON ALL TABLES IN SCHEMA MORTGAGE_DEV.SCALE_SYNTH TO ROLE DEMO_DEV_ROLE;

-- 5. Scorecard: prod (20M) vs call 1 vs call 2 vs combined, saved to MORTGAGE_DEV.CORE_EVAL.SPLIT_SCORECARD.
--    Few passes over the 40M rows: one narrow copy, one grouped aggregate (percentile states combine across halves),
--    one bucket pass for the K-S distances, one pass for applicant IDs. Same tolerances as the main scorecard.
USE WAREHOUSE AI_WH;
USE SCHEMA MORTGAGE_DEV.CORE_EVAL;
CREATE OR REPLACE TEMPORARY TABLE SPLIT_ROWS AS   -- g: P1 / P2 = prod halves, S1 / S2 = generation calls
SELECT IFF(MOD(ABS(HASH(application_id)), 2) = 0, 'P1', 'P2') AS g, application_id, applicant_id,
       broker_type, purpose, decision, employment_type, lvr, loan_amount, declared_income
FROM MORTGAGE_PROD.SCALE.APPLICATION_20M
UNION ALL
SELECT 'S' || generation_call, application_id, applicant_id,
       broker_type, purpose, decision, employment_type, lvr, loan_amount, declared_income
FROM MORTGAGE_DEV.SCALE_SYNTH.APPLICATION_20M;

CREATE OR REPLACE TEMPORARY TABLE SPLIT_AGG AS
SELECT g, COUNT(*) AS n,
       COUNT_IF(broker_type <> 'DIRECT') AS broker, COUNT_IF(employment_type = 'SELF_EMPLOYED') AS self_emp,
       COUNT_IF(decision = 'APPROVED') AS approved, COUNT_IF(purpose = 'OWNER_OCCUPIED_PURCHASE') AS owner_occ,
       COUNT_IF(lvr > 90) AS lvr_90,
       APPROX_PERCENTILE_ACCUMULATE(loan_amount) AS loan_acc, APPROX_PERCENTILE_ACCUMULATE(declared_income) AS inc_acc,
       COUNT(*) - COUNT(DISTINCT application_id) AS dup_ids
FROM SPLIT_ROWS GROUP BY g;

-- K-S distance vs prod on 200 fixed buckets per measure (values outside the range fall in the end buckets)
CREATE OR REPLACE TEMPORARY TABLE SPLIT_KS AS
WITH bk AS (
  SELECT 'ks_loan' AS metric, WIDTH_BUCKET(loan_amount, 150000, 2000000, 200) AS b,
         COUNT_IF(g LIKE 'P%') AS np, COUNT_IF(g = 'S1') AS n1, COUNT_IF(g = 'S2') AS n2 FROM SPLIT_ROWS GROUP BY 1, 2
  UNION ALL
  SELECT 'ks_lvr', WIDTH_BUCKET(lvr, 30, 97, 200), COUNT_IF(g LIKE 'P%'), COUNT_IF(g = 'S1'), COUNT_IF(g = 'S2') FROM SPLIT_ROWS GROUP BY 1, 2
  UNION ALL
  SELECT 'ks_income', WIDTH_BUCKET(declared_income, 40000, 400000, 200), COUNT_IF(g LIKE 'P%'), COUNT_IF(g = 'S1'), COUNT_IF(g = 'S2') FROM SPLIT_ROWS GROUP BY 1, 2),
cum AS (
  SELECT metric,
         SUM(np) OVER (PARTITION BY metric ORDER BY b) / SUM(np) OVER (PARTITION BY metric) AS cp,
         SUM(n1) OVER (PARTITION BY metric ORDER BY b) / SUM(n1) OVER (PARTITION BY metric) AS c1,
         SUM(n2) OVER (PARTITION BY metric ORDER BY b) / SUM(n2) OVER (PARTITION BY metric) AS c2,
         SUM(n1 + n2) OVER (PARTITION BY metric ORDER BY b) / SUM(n1 + n2) OVER (PARTITION BY metric) AS cs
  FROM bk)
SELECT metric, NULL::FLOAT AS p, MAX(ABS(c1 - cp))::FLOAT AS s1, MAX(ABS(c2 - cp))::FLOAT AS s2, MAX(ABS(cs - cp))::FLOAT AS s
FROM cum GROUP BY 1;

-- Applicants whose applications sit in both halves (prod) / both calls (synthetic): equal counts = one fake ID per real applicant
CREATE OR REPLACE TEMPORARY TABLE SPLIT_SPAN AS
SELECT 'span' AS metric,
       COUNT_IF(LEFT(g_min, 1) = 'P' AND g_min <> g_max)::FLOAT AS p, NULL::FLOAT AS s1, NULL::FLOAT AS s2,
       COUNT_IF(LEFT(g_min, 1) = 'S' AND g_min <> g_max)::FLOAT AS s
FROM (SELECT LEFT(g, 1) AS side, applicant_id, MIN(g) AS g_min, MAX(g) AS g_max FROM SPLIT_ROWS GROUP BY 1, 2);

-- Duplicate synthetic application IDs across both calls combined
SET dup_combined = (SELECT COUNT(*) - COUNT(DISTINCT application_id) FROM MORTGAGE_DEV.SCALE_SYNTH.APPLICATION_20M);

CREATE OR REPLACE TABLE SPLIT_SCORECARD AS
WITH
grp AS (   -- P = prod, S1 / S2 = each call, S = both calls combined
  SELECT IFF(g LIKE 'P%', 'P', g) AS k, a.* FROM SPLIT_AGG a
  UNION ALL SELECT 'S', a.* FROM SPLIT_AGG a WHERE g LIKE 'S%'),
m AS (
  SELECT k,
         (SUM(broker) / SUM(n) * 100)::FLOAT AS broker, (SUM(self_emp) / SUM(n) * 100)::FLOAT AS self_emp,
         (SUM(approved) / SUM(n) * 100)::FLOAT AS approved, (SUM(owner_occ) / SUM(n) * 100)::FLOAT AS owner_occ,
         (SUM(lvr_90) / SUM(n) * 100)::FLOAT AS lvr_90,
         APPROX_PERCENTILE_ESTIMATE(APPROX_PERCENTILE_COMBINE(loan_acc), 0.1)::FLOAT AS loan_p10,
         APPROX_PERCENTILE_ESTIMATE(APPROX_PERCENTILE_COMBINE(loan_acc), 0.5)::FLOAT AS loan_p50,
         APPROX_PERCENTILE_ESTIMATE(APPROX_PERCENTILE_COMBINE(loan_acc), 0.9)::FLOAT AS loan_p90,
         APPROX_PERCENTILE_ESTIMATE(APPROX_PERCENTILE_COMBINE(inc_acc), 0.5)::FLOAT AS inc_p50,
         APPROX_PERCENTILE_ESTIMATE(APPROX_PERCENTILE_COMBINE(inc_acc), 0.9)::FLOAT AS inc_p90,
         IFF(k = 'S', $dup_combined, SUM(dup_ids))::FLOAT AS dup_ids
  FROM grp GROUP BY k),
ml AS (
  SELECT k, metric, val FROM m
  UNPIVOT (val FOR metric IN (broker, self_emp, approved, owner_occ, lvr_90, loan_p10, loan_p50, loan_p90, inc_p50, inc_p90, dup_ids))),
wide AS (
  SELECT LOWER(metric) AS metric, MAX(IFF(k = 'P', val, NULL)) AS p, MAX(IFF(k = 'S1', val, NULL)) AS s1,
         MAX(IFF(k = 'S2', val, NULL)) AS s2, MAX(IFF(k = 'S', val, NULL)) AS s
  FROM ml GROUP BY 1
  UNION ALL SELECT metric, p, s1, s2, s FROM SPLIT_KS
  UNION ALL SELECT metric, p, s1, s2, s FROM SPLIT_SPAN),
meta (o, metric, area, chk, unit) AS (
  SELECT * FROM VALUES
    (1, 'broker', 'Same mix', 'Broker share', 'pct'),
    (2, 'self_emp', 'Same mix', 'Self-employed share', 'pct'),
    (3, 'approved', 'Same mix', 'Approval rate', 'pct'),
    (4, 'owner_occ', 'Same mix', 'Owner-occupier purchases', 'pct'),
    (5, 'lvr_90', 'Same mix', 'LVR above 90%', 'pct'),
    (10, 'loan_p10', 'Same spread', 'Loan amount, 10th percentile', 'usd'),
    (11, 'loan_p50', 'Same spread', 'Loan amount, median', 'usd'),
    (12, 'loan_p90', 'Same spread', 'Loan amount, 90th percentile', 'usd'),
    (13, 'inc_p50', 'Same spread', 'Declared income, median', 'usd'),
    (14, 'inc_p90', 'Same spread', 'Declared income, 90th percentile', 'usd'),
    (20, 'ks_loan', 'Same shape', 'Loan amount distribution (K-S vs prod)', 'ks'),
    (21, 'ks_lvr', 'Same shape', 'LVR distribution (K-S vs prod)', 'ks'),
    (22, 'ks_income', 'Same shape', 'Income distribution (K-S vs prod)', 'ks'),
    (30, 'dup_ids', 'Keys across calls', 'Duplicate application IDs', 'zero'),
    (31, 'span', 'Keys across calls', 'Applicants split across both calls, one ID each', 'match')),
scored AS (
  SELECT meta.*, w.p, w.s1, w.s2, w.s,
         CASE unit WHEN 'pct' THEN GREATEST(ABS(w.s1 - w.p), ABS(w.s2 - w.p), ABS(w.s - w.p))
                   WHEN 'usd' THEN GREATEST(ABS(w.s1 - w.p), ABS(w.s2 - w.p), ABS(w.s - w.p)) / NULLIF(w.p, 0) * 100
                   WHEN 'ks'  THEN GREATEST(w.s1, w.s2, w.s)
                   WHEN 'zero' THEN GREATEST(w.s1, w.s2, w.s)
                   ELSE ABS(w.s - w.p) END AS gap
  FROM meta JOIN wide w USING (metric))
SELECT area AS "Check area", chk AS "Check",
       CASE unit WHEN 'pct' THEN TO_VARCHAR(ROUND(p, 1)) || '%' WHEN 'usd' THEN '$' || TRIM(TO_VARCHAR(ROUND(p, -3), '999,999,999'))
                 WHEN 'ks' THEN '–' ELSE TRIM(TO_VARCHAR(p, '999,999,999')) END AS "Prod (20M)",
       CASE unit WHEN 'pct' THEN TO_VARCHAR(ROUND(s1, 1)) || '%' WHEN 'usd' THEN '$' || TRIM(TO_VARCHAR(ROUND(s1, -3), '999,999,999'))
                 WHEN 'ks' THEN TO_VARCHAR(ROUND(s1, 3)) WHEN 'zero' THEN TO_VARCHAR(s1::INT) ELSE '–' END AS "Call 1",
       CASE unit WHEN 'pct' THEN TO_VARCHAR(ROUND(s2, 1)) || '%' WHEN 'usd' THEN '$' || TRIM(TO_VARCHAR(ROUND(s2, -3), '999,999,999'))
                 WHEN 'ks' THEN TO_VARCHAR(ROUND(s2, 3)) WHEN 'zero' THEN TO_VARCHAR(s2::INT) ELSE '–' END AS "Call 2",
       CASE unit WHEN 'pct' THEN TO_VARCHAR(ROUND(s, 1)) || '%' WHEN 'usd' THEN '$' || TRIM(TO_VARCHAR(ROUND(s, -3), '999,999,999'))
                 WHEN 'ks' THEN TO_VARCHAR(ROUND(s, 3)) WHEN 'zero' THEN TO_VARCHAR(s::INT) ELSE TRIM(TO_VARCHAR(s, '999,999,999')) END AS "Combined",
       CASE unit WHEN 'pct' THEN 'within 5 pts' WHEN 'usd' THEN 'within 5%' WHEN 'ks' THEN 'K-S <= 0.05' WHEN 'zero' THEN 'must be 0' ELSE 'must equal prod' END AS "Tolerance",
       CASE unit WHEN 'pct' THEN IFF(gap <= 5, 'GREEN', IFF(gap <= 8, 'AMBER', 'RED'))
                 WHEN 'usd' THEN IFF(gap <= 5, 'GREEN', IFF(gap <= 10, 'AMBER', 'RED'))
                 WHEN 'ks'  THEN IFF(gap <= 0.05, 'GREEN', IFF(gap <= 0.10, 'AMBER', 'RED'))
                 ELSE IFF(gap = 0, 'GREEN', 'RED') END AS "Status",
       o AS sort_order
FROM scored;

-- Loan amount distribution for the notebook chart (60 buckets per source)
CREATE OR REPLACE TABLE SPLIT_LOAN_DIST AS
SELECT IFF(g LIKE 'P%', 'Prod (20M)', 'Call ' || RIGHT(g, 1)) AS source, WIDTH_BUCKET(loan_amount, 150000, 2000000, 60) AS bucket, COUNT(*) AS n
FROM SPLIT_ROWS GROUP BY 1, 2;

SELECT * EXCLUDE sort_order FROM SPLIT_SCORECARD ORDER BY sort_order;
SELECT * FROM SCALE_SPLIT_RUN;
