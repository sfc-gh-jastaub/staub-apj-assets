-- =====================================================================
-- GSI TAX WORKSHOP — CURATED + TAX LAYERS
-- Lab 1 Step 3 (Dynamic Table) and Step 4 (rules layer) / Step 5 (recon)
-- =====================================================================
USE WAREHOUSE GSI_TAX_WH;
USE DATABASE GSI_TAX_WORKSHOP;

-- ---------------------------------------------------------------------
-- CURATED.GL_HARMONISED — Dynamic Table. 2,400,000 rows.
-- Conformance and enrichment only. CONTAINS NO TAX LOGIC.
-- ---------------------------------------------------------------------
CREATE OR REPLACE DYNAMIC TABLE CURATED.GL_HARMONISED
    TARGET_LAG = '1 hour'
    WAREHOUSE  = GSI_TAX_WH
    REFRESH_MODE = AUTO
AS
WITH ent_xwalk AS (
    -- Unpivot the crosswalk once: three ERP identifiers, one group entity.
    SELECT ENTITY_ID, 'SAP'    AS SOURCE_SYSTEM, SAP_BUKRS        AS SRC_ENTITY
      FROM RAW_DATA.DIM_LEGAL_ENTITY WHERE SAP_BUKRS        IS NOT NULL
    UNION ALL
    SELECT ENTITY_ID, 'ORACLE', ORACLE_LEDGER_ID FROM RAW_DATA.DIM_LEGAL_ENTITY
     WHERE ORACLE_LEDGER_ID IS NOT NULL
    UNION ALL
    SELECT ENTITY_ID, 'LEGACY', LEGACY_ENTITY_CD FROM RAW_DATA.DIM_LEGAL_ENTITY
     WHERE LEGACY_ENTITY_CD IS NOT NULL
),
u AS (
    -- SAP: signed amounts, YYYYMMDD text dates
    SELECT 'SAP' AS SOURCE_SYSTEM, BELNR AS SOURCE_DOC_REF, BUZEI AS SOURCE_LINE_NUM,
           BUKRS AS SRC_ENTITY, HKONT AS NATIVE_ACCOUNT_CODE,
           TRY_TO_DATE(BUDAT, 'YYYYMMDD') AS DOC_DATE, DOC_TYPE,
           DMBTR AS NET_AMOUNT, MWSTS AS BOOKED_TAX_AMOUNT,
           WAERS AS CURRENCY, MWSKZ AS BOOKED_TAX_CODE,
           LIFNR AS SUPPLIER_ID, SGTXT AS LINE_NARRATIVE
    FROM RAW_DATA.ERP_SAP_GL
    UNION ALL
    -- Oracle: native DATE, separate DR/CR columns
    SELECT 'ORACLE', JE_HEADER_ID::VARCHAR, JE_LINE_NUM,
           LEDGER_ID, CODE_COMBINATION,
           GL_DATE, DOC_TYPE,
           COALESCE(ENTERED_DR, 0) - COALESCE(ENTERED_CR, 0), TAX_AMOUNT,
           CURRENCY_CODE, TAX_CLASSIFICATION,
           VENDOR_ID, DESCRIPTION
    FROM RAW_DATA.ERP_ORACLE_GL
    UNION ALL
    -- Legacy: DD/MM/YYYY text dates, GST-INCLUSIVE amounts (gross up removed)
    SELECT 'LEGACY', doc_ref, 1,
           entity_cd, acct,
           TRY_TO_DATE(txn_dt, 'DD/MM/YYYY'), doc_type,
           amt_incl_tax - tax_amt, tax_amt,
           curr_cd, tax_flag,
           vendor_ref, narrative
    FROM RAW_DATA.ERP_LEGACY_AP
)
SELECT
    u.SOURCE_SYSTEM || '-' || u.SOURCE_DOC_REF || '-' || u.SOURCE_LINE_NUM::VARCHAR AS GL_LINE_ID,
    u.SOURCE_SYSTEM, u.SOURCE_DOC_REF, u.SOURCE_LINE_NUM,
    x.ENTITY_ID, e.ENTITY_NAME, e.JURISDICTION, e.ABN AS ENTITY_ABN,
    u.DOC_DATE,
    DATE_TRUNC('month', u.DOC_DATE)                              AS TAX_PERIOD,
    u.DOC_TYPE,
    u.NATIVE_ACCOUNT_CODE,
    m.GROUP_ACCOUNT_CODE, m.GROUP_ACCOUNT_NAME, m.SUPPLY_CATEGORY,
    u.SUPPLIER_ID, s.SUPPLIER_NAME, s.SUPPLIER_ABN,
    s.GST_REGISTERED                                             AS SUPPLIER_GST_REGISTERED,
    s.SUPPLIER_COUNTRY,
    (s.SUPPLIER_COUNTRY <> e.JURISDICTION)                       AS IS_CROSS_BORDER,
    u.CURRENCY,
    u.NET_AMOUNT,
    u.BOOKED_TAX_AMOUNT,
    u.NET_AMOUNT + u.BOOKED_TAX_AMOUNT                           AS GROSS_AMOUNT,
    u.BOOKED_TAX_CODE,
    u.LINE_NARRATIVE,
    -- conformance flags: is the DATA complete? (not: is the TAX right?)
    (u.DOC_DATE          IS NOT NULL)                            AS IS_DATE_PARSED,
    (x.ENTITY_ID         IS NOT NULL)                            AS IS_ENTITY_RESOLVED,
    (m.SUPPLY_CATEGORY   IS NOT NULL)                            AS IS_ACCOUNT_MAPPED,
    (s.SUPPLIER_ID       IS NOT NULL)                            AS IS_SUPPLIER_RESOLVED
FROM u
LEFT JOIN ent_xwalk x
       ON x.SOURCE_SYSTEM = u.SOURCE_SYSTEM AND x.SRC_ENTITY = u.SRC_ENTITY
LEFT JOIN RAW_DATA.DIM_LEGAL_ENTITY e   ON e.ENTITY_ID = x.ENTITY_ID
LEFT JOIN RAW_DATA.DIM_ACCOUNT_MAPPING m
       ON m.SOURCE_SYSTEM = u.SOURCE_SYSTEM AND m.NATIVE_ACCOUNT_CODE = u.NATIVE_ACCOUNT_CODE
LEFT JOIN RAW_DATA.DIM_SUPPLIER s       ON s.SUPPLIER_ID = u.SUPPLIER_ID;

-- ---------------------------------------------------------------------
-- TAX.V_GST_DETERMINED — VIEW. Decision-table match + effective-dated
-- rate join, both on DOC_DATE. LEFT JOIN on purpose: a line whose date
-- cannot be parsed has no determinable treatment, and must survive so the
-- exception register can flag it. Must stay a view: edit a rule and the
-- answer changes on the next query, with no rebuild.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW TAX.V_GST_DETERMINED AS
WITH matched AS (
    SELECT
        g.*,
        r.RULE_ID          AS APPLIED_RULE_ID,
        r.RULE_DESCRIPTION AS APPLIED_RULE_DESCRIPTION,
        r.TAX_TREATMENT,
        r.RECOVERABLE
    FROM CURATED.GL_HARMONISED g
    LEFT JOIN TAX.TAX_RULE_DETERMINATION r
      ON (r.JURISDICTION            IS NULL OR r.JURISDICTION            = g.JURISDICTION)
     AND (r.SUPPLY_CATEGORY         IS NULL OR r.SUPPLY_CATEGORY         = g.SUPPLY_CATEGORY)
     AND (r.SUPPLIER_GST_REGISTERED IS NULL OR r.SUPPLIER_GST_REGISTERED = g.SUPPLIER_GST_REGISTERED)
     AND (r.IS_CROSS_BORDER         IS NULL OR r.IS_CROSS_BORDER         = g.IS_CROSS_BORDER)
     AND  g.DOC_DATE BETWEEN r.VALID_FROM AND r.VALID_TO
    QUALIFY ROW_NUMBER() OVER (PARTITION BY g.GL_LINE_ID
                               ORDER BY r.PRIORITY, r.RULE_ID) = 1
)
SELECT
    m.*,
    rt.RATE_PCT                                          AS APPLIED_RATE_PCT,
    ROUND(m.NET_AMOUNT * rt.RATE_PCT / 100, 2)           AS EXPECTED_TAX_AMOUNT,
    ROUND(m.BOOKED_TAX_AMOUNT
          - ROUND(m.NET_AMOUNT * rt.RATE_PCT / 100, 2), 2) AS TAX_VARIANCE
FROM matched m
LEFT JOIN TAX.TAX_RULE_RATE rt
       ON rt.JURISDICTION   = m.JURISDICTION
      AND rt.TAX_TREATMENT  = m.TAX_TREATMENT
      AND m.DOC_DATE BETWEEN rt.VALID_FROM AND rt.VALID_TO;

-- ---------------------------------------------------------------------
-- TAX.V_GST_VS_BAS — VIEW. Computed vs lodged, AU entities only.
-- ---------------------------------------------------------------------
CREATE OR REPLACE VIEW TAX.V_GST_VS_BAS AS
WITH computed AS (
    SELECT ENTITY_ID, ENTITY_NAME, TAX_PERIOD,
           ABS(COALESCE(SUM(CASE WHEN DOC_TYPE='AR_INVOICE'
                                 THEN EXPECTED_TAX_AMOUNT END), 0)) AS COMPUTED_1A,
           ABS(COALESCE(SUM(CASE WHEN DOC_TYPE='AP_INVOICE' AND RECOVERABLE
                                 THEN EXPECTED_TAX_AMOUNT END), 0)) AS COMPUTED_1B
    FROM TAX.V_GST_DETERMINED
    WHERE JURISDICTION = 'AU' AND TAX_PERIOD IS NOT NULL
      -- exclude the current, incomplete month: it has no lodged BAS yet and
      -- would otherwise show as a false variance
      AND TAX_PERIOD < '2026-08-01'::DATE
    GROUP BY ENTITY_ID, ENTITY_NAME, TAX_PERIOD
)
SELECT
    COALESCE(c.ENTITY_ID, b.ENTITY_ID)                              AS ENTITY_ID,
    COALESCE(c.ENTITY_NAME, e.ENTITY_NAME)                          AS ENTITY_NAME,
    COALESCE(c.TAX_PERIOD, b.TAX_PERIOD)                            AS TAX_PERIOD,
    ROUND(COALESCE(c.COMPUTED_1A, 0), 2)                            AS COMPUTED_1A,
    ROUND(COALESCE(c.COMPUTED_1B, 0), 2)                            AS COMPUTED_1B,
    ROUND(COALESCE(c.COMPUTED_1A, 0) - COALESCE(c.COMPUTED_1B, 0), 2) AS COMPUTED_NET_GST,
    COALESCE(b.LABEL_1A_GST_ON_SALES, 0)                            AS LODGED_1A,
    COALESCE(b.LABEL_1B_GST_CREDITS, 0)                             AS LODGED_1B,
    COALESCE(b.NET_GST, 0)                                          AS LODGED_NET_GST,
    ROUND(COALESCE(c.COMPUTED_1A,0) - COALESCE(b.LABEL_1A_GST_ON_SALES,0), 2) AS VARIANCE_1A,
    ROUND(COALESCE(c.COMPUTED_1B,0) - COALESCE(b.LABEL_1B_GST_CREDITS,0), 2)  AS VARIANCE_1B,
    ROUND((COALESCE(c.COMPUTED_1A,0) - COALESCE(c.COMPUTED_1B,0))
          - COALESCE(b.NET_GST,0), 2)                               AS VARIANCE_NET,
    ROUND(((COALESCE(c.COMPUTED_1A,0) - COALESCE(c.COMPUTED_1B,0)) - COALESCE(b.NET_GST,0))
          / NULLIF(ABS(COALESCE(b.NET_GST,0)), 0) * 100, 2)         AS VARIANCE_PCT,
    CASE
      WHEN ABS((COALESCE(c.COMPUTED_1A,0)-COALESCE(c.COMPUTED_1B,0))
               - COALESCE(b.NET_GST,0)) <= 100  THEN 'MATCHED'
      WHEN ABS((COALESCE(c.COMPUTED_1A,0)-COALESCE(c.COMPUTED_1B,0))
               - COALESCE(b.NET_GST,0)) <= 1000 THEN 'REVIEW'
      ELSE 'INVESTIGATE'
    END                                                             AS RECON_STATUS
FROM computed c
FULL OUTER JOIN RAW_DATA.FCT_BAS_LODGED b
     ON b.ENTITY_ID = c.ENTITY_ID AND b.TAX_PERIOD = c.TAX_PERIOD
LEFT JOIN RAW_DATA.DIM_LEGAL_ENTITY e
     ON e.ENTITY_ID = COALESCE(c.ENTITY_ID, b.ENTITY_ID);

-- Exception register moved to 05_exceptions.sql (must be a VIEW - see that file).
