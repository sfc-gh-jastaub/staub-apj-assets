-- NOTE: every RANDOM() call is seeded so the generated data is byte-identical
-- on every run, in every account, at any warehouse size. The figures quoted in
-- the lab HTML depend on this. Do not remove the seeds.
-- =====================================================================
-- GSI TAX WORKSHOP — RAW ERP EXTRACTS
-- 1,200,000 SAP + 800,000 Oracle + 400,000 Legacy = 2,400,000 GL lines
--
-- IMPORTANT: booked tax is derived from the account's supply category,
-- not chosen at random. If the booked tax code were random relative to
-- the account, almost every line would disagree with the rule-determined
-- treatment and the exception register would flag ~70% of the ledger,
-- which is useless as a work queue. Defects are injected deliberately
-- and at controlled rates instead. See sql/DEFECT_RATES.md.
-- =====================================================================
-- ---------------------------------------------------------------------
-- DATA AS-OF DATE (pinned deliberately)
-- The ledger spans 2023-06-01 .. 2026-07-31. This is pinned rather than
-- relative to CURRENT_DATE() so that every figure quoted in the lab guide
-- and the notebook reproduces exactly, on any day, in any account.
-- A real tax dataset also never contains today's postings, so ending on a
-- completed month is the more realistic shape.
-- To roll the window forward, change both dates here and in 03/04, then
-- re-measure the figures and re-run _build/build.py.
-- ---------------------------------------------------------------------
USE WAREHOUSE GSI_TAX_WH;
USE DATABASE GSI_TAX_WORKSHOP;

-- ---------------------------------------------------------------------
-- ERP_SAP_GL — 1,200,000 rows. Signed amounts, YYYYMMDD text dates.
-- NOTE: 1,200,000 > 1,048,576 (the Excel row limit) — deliberate.
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE RAW_DATA.ERP_SAP_GL AS
WITH p AS (
  SELECT ARRAY_CONSTRUCT('1010','1020','1030','1040','1050','1060','1070','1090','1100','1110','1130','1140') AS BK,
         ARRAY_CONSTRUCT('Freight and cartage','External consulting fee','Client hospitality',
           'Raw material purchase','Bank facility fee','Premises lease','Staff training course',
           'Software subscription','Equipment purchase','Audit and assurance fee',
           'Canteen provisions','Medical screening') AS TXT
),
b AS (
  SELECT
    'SAP' || LPAD((SEQ4() + 1)::VARCHAR, 7, '0')                                AS BELNR,
    UNIFORM(1, 8, RANDOM(1010))                                                     AS BUZEI,
    p.BK[UNIFORM(0,11,RANDOM(1011))]::VARCHAR                                       AS BUKRS,
    '4' || LPAD(UNIFORM(1, 62, RANDOM(1012))::VARCHAR, 5, '0')                      AS HKONT,
    DATEADD('day', (DATEDIFF('day','2023-06-01'::DATE, '2026-07-31'::DATE)
            * UNIFORM(0::FLOAT, 1::FLOAT, RANDOM(1013)))::INT, '2023-06-01'::DATE)  AS D,
    UNIFORM(50, 250000, RANDOM(1014))                                               AS AMT,
    'SUP' || LPAD(UNIFORM(1, 2000, RANDOM(1015))::VARCHAR, 6, '0')                  AS LIFNR,
    CASE WHEN UNIFORM(1,100,RANDOM(1016)) <= 65 THEN 'AP_INVOICE'
         WHEN UNIFORM(1,100,RANDOM(1017)) <= 88 THEN 'AR_INVOICE'
         ELSE 'CREDIT_NOTE' END                                                 AS DOC_TYPE,
    p.TXT[UNIFORM(0,11,RANDOM(1018))]::VARCHAR                                      AS SGTXT,
    UNIFORM(1,1000,RANDOM(1019))                                                    AS R_DISTORT,
    UNIFORM(1,100,RANDOM(1020))                                                     AS R_UNREG_TAX,
    UNIFORM(1,100,RANDOM(1021))                                                     AS R_IT_WRONG
  FROM TABLE(GENERATOR(ROWCOUNT => 1200000)), p
),
j AS (
  SELECT b.*, m.SUPPLY_CATEGORY, s.GST_REGISTERED,
         -- booked tax code and rate follow the account's supply category
         CASE
           WHEN s.GST_REGISTERED = FALSE THEN IFF(b.R_UNREG_TAX <= 15, 'S1', 'S0')
           WHEN m.SUPPLY_CATEGORY IN ('RESIDENTIAL_RENT','FINANCIAL_SUPPLY')
                THEN IFF(b.R_IT_WRONG <= 10, 'S1', 'IT')
           WHEN m.SUPPLY_CATEGORY = 'EXPORT_SALES'                     THEN 'EX'
           WHEN m.SUPPLY_CATEGORY IN ('FOOD_BASIC','MEDICAL','EDUCATION') THEN 'ZF'
           ELSE 'S1'
         END                                                                    AS MWSKZ
  FROM b
  LEFT JOIN RAW_DATA.DIM_ACCOUNT_MAPPING m
         ON m.SOURCE_SYSTEM = 'SAP' AND m.NATIVE_ACCOUNT_CODE = b.HKONT
  LEFT JOIN RAW_DATA.DIM_SUPPLIER s ON s.SUPPLIER_ID = b.LIFNR
)
SELECT
    BELNR, BUZEI, BUKRS, HKONT,
    TO_VARCHAR(D, 'YYYYMMDD')                                                   AS BUDAT,
    ROUND(AMT * IFF(DOC_TYPE = 'AP_INVOICE', 1, -1), 2)                         AS DMBTR,
    ROUND(
      IFF(MWSKZ = 'S1', AMT * 0.10, 0)
      * IFF(DOC_TYPE = 'AP_INVOICE', 1, -1)
      * IFF(R_DISTORT <=  5, UNIFORM(40, 160, RANDOM(1022)) / 100.0, 1.0)
    , 2)                                                                        AS MWSTS,
    'AUD'                                                                       AS WAERS,
    MWSKZ, LIFNR, DOC_TYPE, SGTXT
FROM j;

-- ---------------------------------------------------------------------
-- ERP_ORACLE_GL — 800,000 rows. Native DATE, separate DR/CR columns.
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE RAW_DATA.ERP_ORACLE_GL AS
WITH p AS (
  SELECT ARRAY_CONSTRUCT('LED_2001','LED_2002','LED_2003','LED_2004','LED_2005','LED_2007',
           'LED_2008','LED_2009','LED_2010','LED_2011','LED_2012','LED_2013') AS LG,
         ARRAY_CONSTRUCT('Professional services rendered','Goods received','Entertainment expense',
           'Property rental','Interest and bank charges','Export freight','Training and development',
           'Capital asset acquisition','Consumables','Health services') AS TXT
),
b AS (
  SELECT
    SEQ4() + 1                                                                  AS JE_HEADER_ID,
    UNIFORM(1, 8, RANDOM(1023))                                                     AS JE_LINE_NUM,
    p.LG[UNIFORM(0,11,RANDOM(1024))]::VARCHAR                                       AS LEDGER_ID,
    '5100-' || LPAD(UNIFORM(1, 62, RANDOM(1025))::VARCHAR, 4, '0')                  AS CODE_COMBINATION,
    DATEADD('day', (DATEDIFF('day','2023-06-01'::DATE, '2026-07-31'::DATE)
            * UNIFORM(0::FLOAT, 1::FLOAT, RANDOM(1026)))::INT, '2023-06-01'::DATE)  AS GL_DATE,
    UNIFORM(50, 250000, RANDOM(1027))                                               AS AMT,
    'SUP' || LPAD(UNIFORM(1, 2000, RANDOM(1028))::VARCHAR, 6, '0')                  AS VENDOR_ID,
    CASE WHEN UNIFORM(1,100,RANDOM(1029)) <= 65 THEN 'AP_INVOICE'
         WHEN UNIFORM(1,100,RANDOM(1030)) <= 88 THEN 'AR_INVOICE'
         ELSE 'CREDIT_NOTE' END                                                 AS DOC_TYPE,
    p.TXT[UNIFORM(0,9,RANDOM(1031))]::VARCHAR                                       AS DESCRIPTION,
    UNIFORM(1,1000,RANDOM(1032))                                                    AS R_DISTORT,
    UNIFORM(1,100,RANDOM(1033))                                                     AS R_UNREG_TAX,
    UNIFORM(1,100,RANDOM(1034))                                                     AS R_IT_WRONG
  FROM TABLE(GENERATOR(ROWCOUNT => 800000)), p
),
j AS (
  SELECT b.*, m.SUPPLY_CATEGORY, s.GST_REGISTERED,
         CASE
           WHEN s.GST_REGISTERED = FALSE THEN IFF(b.R_UNREG_TAX <= 15, 'STANDARD', 'OUT_OF_SCOPE')
           WHEN m.SUPPLY_CATEGORY IN ('RESIDENTIAL_RENT','FINANCIAL_SUPPLY')
                THEN IFF(b.R_IT_WRONG <= 10, 'STANDARD', 'EXEMPT')
           WHEN m.SUPPLY_CATEGORY = 'EXPORT_SALES'                     THEN 'ZERO_RATED'
           WHEN m.SUPPLY_CATEGORY IN ('FOOD_BASIC','MEDICAL','EDUCATION') THEN 'ZERO_RATED'
           ELSE 'STANDARD'
         END                                                                    AS TAX_CLASSIFICATION
  FROM b
  LEFT JOIN RAW_DATA.DIM_ACCOUNT_MAPPING m
         ON m.SOURCE_SYSTEM = 'ORACLE' AND m.NATIVE_ACCOUNT_CODE = b.CODE_COMBINATION
  LEFT JOIN RAW_DATA.DIM_SUPPLIER s ON s.SUPPLIER_ID = b.VENDOR_ID
)
SELECT
    JE_HEADER_ID, JE_LINE_NUM, LEDGER_ID, CODE_COMBINATION, GL_DATE,
    IFF(DOC_TYPE = 'AP_INVOICE', ROUND(AMT, 2), NULL)                           AS ENTERED_DR,
    IFF(DOC_TYPE = 'AP_INVOICE', NULL, ROUND(AMT, 2))                           AS ENTERED_CR,
    ROUND(
      IFF(TAX_CLASSIFICATION = 'STANDARD', AMT * 0.10, 0)
      * IFF(DOC_TYPE = 'AP_INVOICE', 1, -1)   -- sign must match ENTERED_DR/CR
      * IFF(R_DISTORT <= 5, UNIFORM(40, 160, RANDOM(1035)) / 100.0, 1.0)
    , 2)                                                                        AS TAX_AMOUNT,
    'AUD'                                                                       AS CURRENCY_CODE,
    TAX_CLASSIFICATION, VENDOR_ID, DOC_TYPE, DESCRIPTION
FROM j;

-- ---------------------------------------------------------------------
-- ERP_LEGACY_AP — 400,000 rows. Lower case, DD/MM/YYYY text dates,
-- GST-INCLUSIVE amounts, ~2% unparseable dates.
-- ---------------------------------------------------------------------
CREATE OR REPLACE TABLE RAW_DATA.ERP_LEGACY_AP AS
WITH p AS (
  SELECT ARRAY_CONSTRUCT('AU01','AU02','AU03','AU04','AU05','AU06','AU08','AU09','AU10',
           'AU11','AU12','AU14') AS EC,
         ARRAY_CONSTRUCT('sundry purchase','contractor invoice','staff amenities',
           'office rent','finance charge','freight out','course fees','plant purchase',
           'stationery','clinic fees') AS TXT
),
b AS (
  SELECT
    'LEG' || LPAD((SEQ4() + 1)::VARCHAR, 7, '0')                                AS doc_ref,
    p.EC[UNIFORM(0,11,RANDOM(1036))]::VARCHAR                                       AS entity_cd,
    'AP' || LPAD(UNIFORM(1, 62, RANDOM(1037))::VARCHAR, 3, '0')                     AS acct,
    DATEADD('day', (DATEDIFF('day','2023-06-01'::DATE, '2026-07-31'::DATE)
            * UNIFORM(0::FLOAT, 1::FLOAT, RANDOM(1038)))::INT, '2023-06-01'::DATE)  AS D,
    UNIFORM(55, 275000, RANDOM(1039))                                               AS GROSS,
    'SUP' || LPAD(UNIFORM(1, 2000, RANDOM(1040))::VARCHAR, 6, '0')                  AS vendor_ref,
    IFF(UNIFORM(1,100,RANDOM(1041)) <= 95, 'AP_INVOICE', 'CREDIT_NOTE')             AS doc_type,
    p.TXT[UNIFORM(0,9,RANDOM(1042))]::VARCHAR                                       AS narrative,
    UNIFORM(1,1000,RANDOM(1043))                                                    AS R_DISTORT,
    UNIFORM(1,100,RANDOM(1044))                                                     AS R_UNREG_TAX,
    UNIFORM(1,100,RANDOM(1045))                                                     AS R_IT_WRONG,
    UNIFORM(1,1000,RANDOM(1046))                                                    AS R_BADDATE
  FROM TABLE(GENERATOR(ROWCOUNT => 400000)), p
),
j AS (
  SELECT b.*, m.SUPPLY_CATEGORY, s.GST_REGISTERED,
         CASE
           WHEN s.GST_REGISTERED = FALSE THEN IFF(b.R_UNREG_TAX <= 15, 'Y', 'N')
           WHEN m.SUPPLY_CATEGORY IN ('RESIDENTIAL_RENT','FINANCIAL_SUPPLY')
                THEN IFF(b.R_IT_WRONG <= 10, 'Y', 'N')
           WHEN m.SUPPLY_CATEGORY = 'EXPORT_SALES'                     THEN 'N'
           WHEN m.SUPPLY_CATEGORY IN ('FOOD_BASIC','MEDICAL','EDUCATION') THEN 'N'
           WHEN m.SUPPLY_CATEGORY IS NULL                              THEN 'X'
           ELSE 'Y'
         END                                                                    AS tax_flag
  FROM b
  LEFT JOIN RAW_DATA.DIM_ACCOUNT_MAPPING m
         ON m.SOURCE_SYSTEM = 'LEGACY' AND m.NATIVE_ACCOUNT_CODE = b.acct
  LEFT JOIN RAW_DATA.DIM_SUPPLIER s ON s.SUPPLIER_ID = b.vendor_ref
)
SELECT
    doc_ref, entity_cd, acct,
    CASE WHEN R_BADDATE <=  7 THEN '31/02/2024'
         WHEN R_BADDATE <= 14 THEN 'N/A'
         WHEN R_BADDATE <= 20 THEN ''
         ELSE TO_VARCHAR(D, 'DD/MM/YYYY') END                                   AS txn_dt,
    ROUND(GROSS, 2)                                                             AS amt_incl_tax,
    ROUND(
      IFF(tax_flag IN ('Y','X'), GROSS / 11.0, 0)
      * IFF(R_DISTORT <=  5, UNIFORM(40, 160, RANDOM(1047)) / 100.0, 1.0)
    , 2)                                                                        AS tax_amt,
    'AUD'                                                                       AS curr_cd,
    tax_flag, vendor_ref, doc_type, narrative
FROM j;
