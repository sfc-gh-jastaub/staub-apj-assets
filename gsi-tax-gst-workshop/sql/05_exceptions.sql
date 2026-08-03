-- =====================================================================
-- GSI TAX WORKSHOP — EXCEPTION REGISTER
--
-- VERIFIED PLATFORM CONSTRAINT (executed 2026-08-03):
--   "Dynamic Tables do not support reading from views containing
--    objects of type DYNAMIC_TABLE"
-- DT_GST_EXCEPTIONS -> V_GST_DETERMINED (view) -> GL_HARMONISED (DT)
-- is therefore ILLEGAL. The exception register is a VIEW.
--
-- This is the right resolution rather than a workaround:
--   * V_GST_DETERMINED must stay a view so editing a rule changes the
--     answer on the next query (Lab 1 Step 4 Block 4).
--   * Inlining the rule join here would duplicate the determination
--     logic in two places, which is exactly what we tell them not to do.
--   * The register is always queried ORDER BY RISK_SCORE LIMIT n.
-- Net effect: the workshop has exactly ONE Dynamic Table, GL_HARMONISED.
-- =====================================================================
USE WAREHOUSE GSI_TAX_WH;
USE DATABASE GSI_TAX_WORKSHOP;

CREATE OR REPLACE VIEW TAX.V_GST_EXCEPTIONS AS
WITH d AS (SELECT * FROM TAX.V_GST_DETERMINED),
ex AS (
    SELECT GL_LINE_ID, 'E1' AS EXCEPTION_CODE, 'MEDIUM' AS SEVERITY,
           'Account code ' || COALESCE(NATIVE_ACCOUNT_CODE,'?') || ' has no group mapping' AS EXCEPTION_REASON
    FROM d WHERE NOT IS_ACCOUNT_MAPPED
    UNION ALL
    SELECT GL_LINE_ID, 'E2', 'HIGH', 'Document date could not be parsed from the source system'
    FROM d WHERE NOT IS_DATE_PARSED   -- reachable only because of the LEFT JOIN in V_GST_DETERMINED
    UNION ALL
    SELECT GL_LINE_ID, 'E3', 'HIGH', 'Supplier ABN missing on a claimed credit over $82.50'
    FROM d WHERE SUPPLIER_ABN IS NULL AND DOC_TYPE = 'AP_INVOICE'
             AND RECOVERABLE AND ABS(GROSS_AMOUNT) > 82.50
    UNION ALL
    SELECT GL_LINE_ID, 'E4', 'HIGH', 'GST charged by a supplier that is not GST registered'
    FROM d WHERE SUPPLIER_GST_REGISTERED = FALSE AND BOOKED_TAX_AMOUNT <> 0
    UNION ALL
    SELECT GL_LINE_ID, 'E5', 'MEDIUM',
           'Booked GST differs from expected by ' || TO_VARCHAR(ROUND(TAX_VARIANCE,2))
    FROM d WHERE ABS(COALESCE(TAX_VARIANCE, 0)) > 1.00
    UNION ALL
    SELECT GL_LINE_ID, 'E6', 'HIGH',
           'Credit claimed on a non-recoverable treatment (' || TAX_TREATMENT || ')'
    FROM d WHERE RECOVERABLE = FALSE AND TAX_TREATMENT <> 'NON_DEDUCTIBLE'
             AND DOC_TYPE = 'AP_INVOICE' AND BOOKED_TAX_AMOUNT <> 0
    UNION ALL
    SELECT GL_LINE_ID, 'E7', 'MEDIUM', 'Reverse charge required but not applied in the source system'
    FROM d WHERE TAX_TREATMENT = 'REVERSE_CHARGE'
             AND COALESCE(BOOKED_TAX_CODE,'') NOT IN ('RC','REVERSE_CHARGE')
)
SELECT
    d.GL_LINE_ID, d.ENTITY_ID, d.ENTITY_NAME, d.TAX_PERIOD,
    d.SUPPLIER_ID, d.SUPPLIER_NAME,
    d.SOURCE_SYSTEM, d.SOURCE_DOC_REF, d.DOC_TYPE, d.SUPPLY_CATEGORY,
    d.NET_AMOUNT, d.BOOKED_TAX_AMOUNT, d.EXPECTED_TAX_AMOUNT, d.TAX_VARIANCE,
    d.TAX_TREATMENT, d.APPLIED_RULE_ID,
    COUNT(*)                                                        AS EXCEPTION_COUNT,
    LISTAGG(DISTINCT ex.EXCEPTION_CODE, ', ')
        WITHIN GROUP (ORDER BY ex.EXCEPTION_CODE)                   AS EXCEPTION_CODES,
    LISTAGG(ex.EXCEPTION_REASON, ' | ')
        WITHIN GROUP (ORDER BY ex.EXCEPTION_CODE)                   AS EXCEPTION_REASONS,
    CASE MAX(CASE ex.SEVERITY WHEN 'HIGH' THEN 3 WHEN 'MEDIUM' THEN 2 ELSE 1 END)
         WHEN 3 THEN 'HIGH' WHEN 2 THEN 'MEDIUM' ELSE 'LOW' END     AS MAX_SEVERITY,
    ROUND(COUNT(*) * 10
          + LEAST(ABS(COALESCE(d.TAX_VARIANCE, 0)) / 100, 50), 2)   AS RISK_SCORE
FROM ex
JOIN d ON d.GL_LINE_ID = ex.GL_LINE_ID
GROUP BY ALL;
