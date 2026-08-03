-- ============================================================================
-- GENERATED FILE - DO NOT EDIT.
-- Produced by _build/build.py from the Lab 2 step fragments.
-- These are the AI_INSIGHTS / AGENTS objects a participant creates by working
-- through Lab 2. This file exists so a facilitator can stand the whole stack up
-- non-interactively, and so sql/07_agent.sql has its semantic view to point at.
--
-- Full rebuild order:
--   01_setup_raw  02_setup_erp  03_setup_rules_bas_docs
--   04_curated_tax  05_exceptions  06_lab2_ai_objects  07_agent
-- ============================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE GSI_TAX_WH;
USE DATABASE GSI_TAX_WORKSHOP;


-- Lab 2 Step 2
CREATE OR REPLACE VIEW AI_INSIGHTS.V_AI_SUPPLY_CLASSIFIED AS
WITH classified AS (
    SELECT
        d.DOC_ID,
        d.SOURCE_SYSTEM,
        d.SOURCE_DOC_REF,
        d.SUPPLIER_ID,
        d.INVOICE_NARRATIVE,
        d.BOOKED_SUPPLY_CATEGORY,
        AI_CLASSIFY(
            d.INVOICE_NARRATIVE,
            ['taxable supply','GST-free supply','input taxed supply',
             'export','entertainment','capital acquisition']
        ):labels[0]::VARCHAR AS AI_SUPPLY_CATEGORY
    FROM RAW_DATA.DOC_TAX_INVOICE d
)
SELECT
    c.*,
    -- Map the ledger's account-level category onto the classifier's
    -- tax-relevant vocabulary so the two can be compared at all.
    CASE c.BOOKED_SUPPLY_CATEGORY
        WHEN 'ENTERTAINMENT'     THEN 'entertainment'
        WHEN 'CAPITAL_EQUIPMENT' THEN 'capital acquisition'
        WHEN 'EXPORT_SALES'      THEN 'export'
        WHEN 'RESIDENTIAL_RENT'  THEN 'input taxed supply'
        WHEN 'FINANCIAL_SUPPLY'  THEN 'input taxed supply'
        WHEN 'FOOD_BASIC'        THEN 'GST-free supply'
        WHEN 'MEDICAL'           THEN 'GST-free supply'
        WHEN 'EDUCATION'         THEN 'GST-free supply'
        ELSE 'taxable supply'
    END                                                    AS BOOKED_EQUIVALENT,
    (AI_SUPPLY_CATEGORY IS NOT NULL
     AND AI_SUPPLY_CATEGORY <> CASE c.BOOKED_SUPPLY_CATEGORY
        WHEN 'ENTERTAINMENT'     THEN 'entertainment'
        WHEN 'CAPITAL_EQUIPMENT' THEN 'capital acquisition'
        WHEN 'EXPORT_SALES'      THEN 'export'
        WHEN 'RESIDENTIAL_RENT'  THEN 'input taxed supply'
        WHEN 'FINANCIAL_SUPPLY'  THEN 'input taxed supply'
        WHEN 'FOOD_BASIC'        THEN 'GST-free supply'
        WHEN 'MEDICAL'           THEN 'GST-free supply'
        WHEN 'EDUCATION'         THEN 'GST-free supply'
        ELSE 'taxable supply'
     END)                                                  AS MISCODING_FLAG
FROM classified c;

-- Lab 2 Step 3
CREATE OR REPLACE VIEW AI_INSIGHTS.V_AI_DOC_EXTRACTED AS
WITH extracted AS (
    SELECT
        d.DOC_ID,
        d.SOURCE_SYSTEM,
        d.SOURCE_DOC_REF,
        d.SUPPLIER_ID,
        d.SUPPLIER_REMARKS,
        SNOWFLAKE.CORTEX.EXTRACT_ANSWER(
            d.SUPPLIER_REMARKS, 'What is the supplier ABN?'
        )[0]:answer::VARCHAR AS EXTRACTED_ABN_RAW,
        SNOWFLAKE.CORTEX.EXTRACT_ANSWER(
            d.SUPPLIER_REMARKS, 'What GST amount is stated on this invoice?'
        )[0]:answer::VARCHAR AS EXTRACTED_GST_RAW
    FROM RAW_DATA.DOC_TAX_INVOICE d
),
doc_tax AS (
    -- Aggregate to one row per document BEFORE joining, so a multi-line
    -- document cannot fan out and double-count the tax.
    SELECT SOURCE_SYSTEM, SOURCE_DOC_REF,
           SUM(NET_AMOUNT)        AS DOC_NET_AMOUNT,
           SUM(BOOKED_TAX_AMOUNT) AS BOOKED_TAX_AMOUNT,
           SUM(GROSS_AMOUNT)      AS DOC_GROSS_AMOUNT,
           MAX(DOC_TYPE)          AS DOC_TYPE,
           MAX(ENTITY_NAME)       AS ENTITY_NAME,
           MAX(TAX_PERIOD)        AS TAX_PERIOD,
           BOOLOR_AGG(RECOVERABLE) AS RECOVERABLE
    FROM TAX.V_GST_DETERMINED
    GROUP BY SOURCE_SYSTEM, SOURCE_DOC_REF
)
SELECT
    x.DOC_ID,
    x.SOURCE_SYSTEM,
    x.SOURCE_DOC_REF,
    x.SUPPLIER_ID,
    s.SUPPLIER_NAME,
    t.ENTITY_NAME,
    t.TAX_PERIOD,
    t.DOC_TYPE,
    t.RECOVERABLE,
    x.SUPPLIER_REMARKS,
    x.EXTRACTED_ABN_RAW,
    x.EXTRACTED_GST_RAW,
    -- Strip everything that is not a digit from BOTH sides so the
    -- comparison is not defeated by spacing conventions.
    REGEXP_REPLACE(COALESCE(x.EXTRACTED_ABN_RAW, ''), '[^0-9]', '') AS EXTRACTED_ABN_DIGITS,
    REGEXP_REPLACE(COALESCE(s.SUPPLIER_ABN,      ''), '[^0-9]', '') AS MASTER_ABN_DIGITS,
    TRY_TO_NUMBER(REGEXP_REPLACE(COALESCE(x.EXTRACTED_GST_RAW, ''), '[^0-9.]', '')) AS EXTRACTED_GST_AMOUNT,
    t.DOC_NET_AMOUNT,
    t.DOC_GROSS_AMOUNT,
    t.BOOKED_TAX_AMOUNT,
    -- The fallback every reviewer uses when the invoice states GST as
    -- included rather than stated: one eleventh of the GST-inclusive total.
    ROUND(COALESCE(t.DOC_GROSS_AMOUNT, 0) / 11, 2)                  AS GST_FRACTION_AMOUNT,
    (LENGTH(REGEXP_REPLACE(COALESCE(x.EXTRACTED_ABN_RAW, ''), '[^0-9]', '')) = 11) AS HAS_ABN_ON_INVOICE,
    (s.SUPPLIER_ABN IS NULL)                                        AS MASTER_ABN_MISSING
FROM extracted x
LEFT JOIN RAW_DATA.DIM_SUPPLIER s ON s.SUPPLIER_ID = x.SUPPLIER_ID
LEFT JOIN doc_tax t
       ON t.SOURCE_SYSTEM  = x.SOURCE_SYSTEM
      AND t.SOURCE_DOC_REF = x.SOURCE_DOC_REF;

-- Lab 2 Step 4
CREATE OR REPLACE VIEW AI_INSIGHTS.V_AI_EXCEPTION_RATIONALE AS
WITH ranked AS (
    -- The bound lives HERE. 25 rows reach the model, no matter how the
    -- view is queried downstream.
    SELECT e.GL_LINE_ID, e.ENTITY_ID, e.ENTITY_NAME, e.TAX_PERIOD,
           e.SUPPLIER_ID, e.SUPPLIER_NAME, e.SOURCE_SYSTEM, e.SOURCE_DOC_REF,
           e.DOC_TYPE, e.SUPPLY_CATEGORY, e.TAX_TREATMENT, e.APPLIED_RULE_ID,
           e.EXCEPTION_CODES, e.EXCEPTION_REASONS, e.EXCEPTION_COUNT,
           e.MAX_SEVERITY, e.NET_AMOUNT, e.BOOKED_TAX_AMOUNT,
           e.EXPECTED_TAX_AMOUNT, e.TAX_VARIANCE, e.RISK_SCORE,
           r.RULE_DESCRIPTION AS APPLIED_RULE_DESCRIPTION
    FROM TAX.V_GST_EXCEPTIONS e
    LEFT JOIN TAX.TAX_RULE_DETERMINATION r ON r.RULE_ID = e.APPLIED_RULE_ID
    ORDER BY e.RISK_SCORE DESC
    LIMIT 25
)
SELECT
    k.*,
    AI_COMPLETE('claude-sonnet-4-6',
        'You are an Australian indirect tax specialist preparing a working '  ||
        'paper for a review partner. Write exactly three sentences in '       ||
        'British English, no headings and no bullet points. Sentence one: '   ||
        'state what the exception is. Sentence two: state why it matters '    ||
        'for GST, referring to the determination rule provided. Sentence '    ||
        'three: state the specific next step for the reviewer. Do not '       ||
        'speculate beyond the facts given.'                                   ||
        ' FACTS -- Entity: '            || COALESCE(k.ENTITY_NAME, 'unknown')  ||
        '; Supplier: '                  || COALESCE(k.SUPPLIER_NAME, 'unknown')||
        '; Tax period: '                || COALESCE(k.TAX_PERIOD::VARCHAR, 'unknown') ||
        '; Source: '                    || COALESCE(k.SOURCE_SYSTEM, 'unknown')       ||
        ' document '                    || COALESCE(k.SOURCE_DOC_REF, 'unknown')      ||
        '; Document type: '             || COALESCE(k.DOC_TYPE, 'unknown')            ||
        '; Supply category: '           || COALESCE(k.SUPPLY_CATEGORY, 'unmapped')     ||
        '; Determined treatment: '      || COALESCE(k.TAX_TREATMENT, 'undetermined')   ||
        '; Determination rule applied: '|| COALESCE(k.APPLIED_RULE_DESCRIPTION, 'none')||
        '; Exception codes: '           || COALESCE(k.EXCEPTION_CODES, 'none')         ||
        '; Exception reasons: '         || COALESCE(k.EXCEPTION_REASONS, 'none')       ||
        '; Net amount AUD: '            || COALESCE(k.NET_AMOUNT::VARCHAR, '0')        ||
        '; Booked tax AUD: '            || COALESCE(k.BOOKED_TAX_AMOUNT::VARCHAR, '0') ||
        '; Expected tax AUD: '          || COALESCE(k.EXPECTED_TAX_AMOUNT::VARCHAR, '0')||
        '; Tax variance AUD: '          || COALESCE(k.TAX_VARIANCE::VARCHAR, '0')       ||
        '; Severity: '                  || COALESCE(k.MAX_SEVERITY, 'unknown')
    )                                                     AS WORKING_PAPER_NARRATIVE
FROM ranked k;

-- Lab 2 Step 5
CREATE OR REPLACE VIEW AGENTS.V_GST_INTELLIGENCE AS
SELECT
    -- keys and dimensions
    d.GL_LINE_ID,
    d.SOURCE_SYSTEM,
    d.SOURCE_DOC_REF,
    d.ENTITY_ID,
    d.ENTITY_NAME,
    d.JURISDICTION,
    d.DOC_DATE,
    d.TAX_PERIOD,
    d.DOC_TYPE,
    d.GROUP_ACCOUNT_CODE,
    d.GROUP_ACCOUNT_NAME,
    d.SUPPLY_CATEGORY,
    d.SUPPLIER_ID,
    d.SUPPLIER_NAME,
    d.SUPPLIER_ABN,
    d.SUPPLIER_COUNTRY,
    d.SUPPLIER_GST_REGISTERED,
    d.IS_CROSS_BORDER,
    d.TAX_TREATMENT,
    d.RECOVERABLE,
    d.APPLIED_RULE_ID,
    d.APPLIED_RULE_DESCRIPTION,
    d.APPLIED_RATE_PCT,
    d.IS_ACCOUNT_MAPPED,
    d.IS_DATE_PARSED,

    -- measures from the determination layer
    d.NET_AMOUNT,
    d.BOOKED_TAX_AMOUNT,
    d.EXPECTED_TAX_AMOUNT,
    d.TAX_VARIANCE,

    -- exception context, one row per line, so no fan-out is possible
    COALESCE(e.EXCEPTION_COUNT, 0)                       AS EXCEPTION_COUNT,
    (e.GL_LINE_ID IS NOT NULL)                           AS HAS_EXCEPTION,
    e.EXCEPTION_CODES,
    e.EXCEPTION_REASONS,
    COALESCE(e.MAX_SEVERITY, 'NONE')                     AS MAX_SEVERITY,
    COALESCE(e.RISK_SCORE, 0)                            AS RISK_SCORE,

    -- BAS reconciliation context, repeated per line within its entity/period
    b.COMPUTED_NET_GST,
    b.LODGED_NET_GST,
    b.VARIANCE_NET                                       AS BAS_VARIANCE_NET,
    b.VARIANCE_PCT                                       AS BAS_VARIANCE_PCT,
    COALESCE(b.RECON_STATUS, 'NOT_RECONCILED')           AS RECON_STATUS
FROM TAX.V_GST_DETERMINED d
LEFT JOIN TAX.V_GST_EXCEPTIONS e
       ON e.GL_LINE_ID = d.GL_LINE_ID
LEFT JOIN TAX.V_GST_VS_BAS b
       ON b.ENTITY_ID  = d.ENTITY_ID
      AND b.TAX_PERIOD = d.TAX_PERIOD;

-- Lab 2 Step 5
CREATE OR REPLACE SEMANTIC VIEW AGENTS.SV_GST_COMPLIANCE
    TABLES (
        gst AS AGENTS.V_GST_INTELLIGENCE
            PRIMARY KEY (GL_LINE_ID)
            WITH SYNONYMS = ('GST ledger','tax ledger','transactions','GST lines')
            COMMENT = 'One row per general ledger line with its determined Australian GST treatment, exception status and BAS reconciliation context.'
    )
    DIMENSIONS (
        gst.ENTITY_NAME AS ENTITY_NAME
            WITH SYNONYMS = ('entity','company','legal entity','business','subsidiary')
            COMMENT = 'Australian group entity that recorded the transaction.',
        gst.TAX_PERIOD AS TAX_PERIOD
            WITH SYNONYMS = ('period','month','tax period','BAS period','reporting period')
            COMMENT = 'Monthly GST period, stored as the first day of the month.',
        gst.DOC_DATE AS DOC_DATE
            WITH SYNONYMS = ('document date','transaction date','invoice date')
            COMMENT = 'Date of the underlying document. Determination rules are applied as at this date.',
        gst.SUPPLY_CATEGORY AS SUPPLY_CATEGORY
            WITH SYNONYMS = ('supply category','expense type','category','account category','spend type')
            COMMENT = 'Category of supply from the account mapping. NULL means the account is unmapped.',
        gst.TAX_TREATMENT AS TAX_TREATMENT
            WITH SYNONYMS = ('treatment','tax treatment','GST treatment','reverse charge','GST free','input taxed')
            COMMENT = 'GST treatment determined by the rules: TAXABLE, GST_FREE, INPUT_TAXED, REVERSE_CHARGE, EXPORT, NON_DEDUCTIBLE or OUT_OF_SCOPE.',
        gst.SOURCE_SYSTEM AS SOURCE_SYSTEM
            WITH SYNONYMS = ('source system','ERP','system','source')
            COMMENT = 'Originating ERP: SAP, ORACLE or LEGACY.',
        gst.RECON_STATUS AS RECON_STATUS
            WITH SYNONYMS = ('reconciliation status','recon status','BAS status','match status')
            COMMENT = 'Reconciliation outcome against the lodged BAS: MATCHED, REVIEW or INVESTIGATE.',
        gst.SUPPLIER_NAME AS SUPPLIER_NAME
            WITH SYNONYMS = ('supplier','vendor','creditor','payee')
            COMMENT = 'Supplier of the acquisition or customer of the supply.',
        gst.SUPPLIER_ABN AS SUPPLIER_ABN
            WITH SYNONYMS = ('ABN','supplier ABN','Australian business number')
            COMMENT = 'Supplier ABN from the supplier master. NULL means no ABN is held, which denies the input tax credit above $82.50.',
        gst.EXCEPTION_CODES AS EXCEPTION_CODES
            WITH SYNONYMS = ('exception codes','issue codes','error codes','findings')
            COMMENT = 'Comma separated exception codes raised against the line, E1 to E7.',
        gst.MAX_SEVERITY AS MAX_SEVERITY
            WITH SYNONYMS = ('severity','risk level','priority')
            COMMENT = 'Highest severity among the exceptions on the line: HIGH, MEDIUM, LOW or NONE.',
        gst.IS_ACCOUNT_MAPPED AS IS_ACCOUNT_MAPPED
            WITH SYNONYMS = ('account mapped','mapped account','unmapped account','mapping complete')
            COMMENT = 'FALSE where the native account code has no entry in the account mapping table.',
        gst.IS_CROSS_BORDER AS IS_CROSS_BORDER
            WITH SYNONYMS = ('cross border','imported','offshore','overseas supplier')
            COMMENT = 'TRUE where the supplier country differs from the entity jurisdiction.'
    )
    METRICS (
        gst.LINE_COUNT AS COUNT(gst.GL_LINE_ID)
            WITH SYNONYMS = ('line count','number of lines','transactions','volume','how many')
            COMMENT = 'Number of ledger lines.',
        gst.TOTAL_NET_AMOUNT AS SUM(gst.NET_AMOUNT)
            WITH SYNONYMS = ('net amount','net','value excluding GST','ex GST amount','turnover')
            COMMENT = 'Total amount net of GST, in AUD.',
        gst.TOTAL_BOOKED_TAX AS SUM(gst.BOOKED_TAX_AMOUNT)
            WITH SYNONYMS = ('booked GST','posted GST','GST as booked','recorded GST')
            COMMENT = 'GST actually posted by the source ERP, in AUD.',
        gst.TOTAL_EXPECTED_TAX AS SUM(gst.EXPECTED_TAX_AMOUNT)
            WITH SYNONYMS = ('expected GST','computed GST','GST per the rules','correct GST','GST payable')
            COMMENT = 'GST expected under the determination rules, in AUD. This is the computed position.',
        gst.TOTAL_TAX_VARIANCE AS SUM(gst.TAX_VARIANCE)
            WITH SYNONYMS = ('variance','GST variance','difference','exposure','under or over')
            COMMENT = 'Booked GST minus expected GST, in AUD. Positive means over-booked.',
        gst.TOTAL_EXCEPTION_COUNT AS SUM(gst.EXCEPTION_COUNT)
            WITH SYNONYMS = ('exceptions','number of exceptions','issues','findings count','errors')
            COMMENT = 'Total exceptions raised across the selected lines.',
        gst.LODGED_NET_GST_AMOUNT AS MAX(gst.LODGED_NET_GST)
            WITH SYNONYMS = ('lodged GST','lodged net GST','BAS lodged','as lodged','net GST on the BAS')
            COMMENT = 'Net GST per the lodged BAS for the entity and period. Uses MAX because this figure repeats across every line in the period and must never be summed.',
        gst.COMPUTED_NET_GST_AMOUNT AS MAX(gst.COMPUTED_NET_GST)
            WITH SYNONYMS = ('computed net GST','calculated net GST','our GST position')
            COMMENT = 'Net GST computed from the ledger for the entity and period. Uses MAX because this figure repeats across every line in the period and must never be summed.'
    )
    COMMENT = 'Australian GST compliance semantic model over the governed ledger. Monthly periods, AUD, 14 Australian entities.';

-- Lab 2 Step 6
CREATE OR REPLACE DYNAMIC TABLE AI_INSIGHTS.DT_AI_EXCEPTION_REVIEW
    TARGET_LAG = '24 hours'
    WAREHOUSE  = GSI_TAX_WH
AS
WITH doc_sample AS (
    -- Bound the population BEFORE the model sees it. 25 documents, joined to
    -- the supplier master so the prompt has something to reason about.
    SELECT d.DOC_ID,
           d.SOURCE_SYSTEM,
           d.SOURCE_DOC_REF,
           d.SUPPLIER_ID,
           d.BOOKED_SUPPLY_CATEGORY,
           d.INVOICE_NARRATIVE,
           s.SUPPLIER_NAME,
           s.SUPPLIER_ABN,
           s.GST_REGISTERED       AS SUPPLIER_GST_REGISTERED,
           s.SUPPLIER_COUNTRY
    FROM RAW_DATA.DOC_TAX_INVOICE d
    LEFT JOIN RAW_DATA.DIM_SUPPLIER s
           ON s.SUPPLIER_ID = d.SUPPLIER_ID
    LIMIT 25
),
classified AS (
    -- Same AI_CLASSIFY call and same six categories as Step 2.
    SELECT c.*,
           AI_CLASSIFY(
               c.INVOICE_NARRATIVE,
               ['taxable supply','GST-free supply','input taxed supply',
                'export','entertainment','capital acquisition']
           ):labels[0]::VARCHAR AS AI_SUPPLY_CLASSIFICATION
    FROM doc_sample c
),
flagged AS (
    SELECT c.*,
           -- Booked category translated into the vocabulary the model returns,
           -- so the two are comparable.
           CASE c.BOOKED_SUPPLY_CATEGORY
                WHEN 'ENTERTAINMENT'      THEN 'entertainment'
                WHEN 'CAPITAL_EQUIPMENT'  THEN 'capital acquisition'
                WHEN 'EXPORT_SALES'       THEN 'export'
                WHEN 'RESIDENTIAL_RENT'   THEN 'input taxed supply'
                WHEN 'FINANCIAL_SUPPLY'   THEN 'input taxed supply'
                WHEN 'FOOD_BASIC'         THEN 'GST-free supply'
                WHEN 'MEDICAL'            THEN 'GST-free supply'
                WHEN 'EDUCATION'          THEN 'GST-free supply'
                ELSE 'taxable supply'
           END AS BOOKED_AS_CLASSIFICATION,
           (c.AI_SUPPLY_CLASSIFICATION <>
            CASE c.BOOKED_SUPPLY_CATEGORY
                 WHEN 'ENTERTAINMENT'      THEN 'entertainment'
                 WHEN 'CAPITAL_EQUIPMENT'  THEN 'capital acquisition'
                 WHEN 'EXPORT_SALES'       THEN 'export'
                 WHEN 'RESIDENTIAL_RENT'   THEN 'input taxed supply'
                 WHEN 'FINANCIAL_SUPPLY'   THEN 'input taxed supply'
                 WHEN 'FOOD_BASIC'         THEN 'GST-free supply'
                 WHEN 'MEDICAL'            THEN 'GST-free supply'
                 WHEN 'EDUCATION'          THEN 'GST-free supply'
                 ELSE 'taxable supply'
            END) AS MISCODING_FLAG
    FROM classified c
)
SELECT
    f.DOC_ID,
    f.SOURCE_SYSTEM,
    f.SOURCE_DOC_REF,
    f.SUPPLIER_ID,
    f.SUPPLIER_NAME,
    f.SUPPLIER_COUNTRY,
    f.SUPPLIER_GST_REGISTERED,
    f.BOOKED_SUPPLY_CATEGORY,
    f.AI_SUPPLY_CLASSIFICATION,
    f.MISCODING_FLAG,
    -- Every concatenated column wrapped in COALESCE. One NULL nulls the whole
    -- prompt and the call returns NULL without complaining.
    AI_COMPLETE(
        'claude-sonnet-4-6',
        'You are an Australian indirect tax analyst preparing a review note. '  ||
        'In no more than three sentences, state whether the booked supply '     ||
        'category looks correct and what the GST consequence is if it is not. ' ||
        'Invoice narrative: '   || COALESCE(f.INVOICE_NARRATIVE, 'not supplied')      ||
        '. Booked category: '   || COALESCE(f.BOOKED_SUPPLY_CATEGORY, 'unmapped')     ||
        '. Category suggested by classification: '
                                || COALESCE(f.AI_SUPPLY_CLASSIFICATION, 'undetermined') ||
        '. Supplier: '          || COALESCE(f.SUPPLIER_NAME, 'unknown')              ||
        ' in '                  || COALESCE(f.SUPPLIER_COUNTRY, 'an unknown country') ||
        '. Supplier ABN: '      || COALESCE(f.SUPPLIER_ABN, 'not held')              ||
        '.'
    ) AS AI_REVIEW_NOTE
FROM flagged f;

-- Lab 2 Step 7
CREATE OR REPLACE VIEW AI_INSIGHTS.V_AI_CORRESPONDENCE_TRIAGE AS
WITH correspondence AS (
    SELECT DOC_ID,
           SOURCE_SYSTEM,
           SOURCE_DOC_REF,
           SUPPLIER_ID,
           BOOKED_SUPPLY_CATEGORY,
           CORRESPONDENCE_TEXT
    FROM RAW_DATA.DOC_TAX_INVOICE
    WHERE CORRESPONDENCE_TEXT IS NOT NULL
    LIMIT 25
),
scored AS (
    SELECT c.*,
           AI_SENTIMENT(c.CORRESPONDENCE_TEXT):categories[0]:sentiment::VARCHAR AS SENTIMENT_LABEL
    FROM correspondence c
)
SELECT
    s.DOC_ID,
    s.SOURCE_SYSTEM,
    s.SOURCE_DOC_REF,
    s.SUPPLIER_ID,
    s.BOOKED_SUPPLY_CATEGORY,
    s.CORRESPONDENCE_TEXT,
    s.SENTIMENT_LABEL,
    CASE s.SENTIMENT_LABEL
         WHEN 'negative' THEN '1 - URGENT'
         WHEN 'mixed'    THEN '2 - REVIEW'
         WHEN 'neutral'  THEN '3 - ROUTINE'
         WHEN 'positive' THEN '4 - MONITOR'
         ELSE                 '9 - UNCLASSIFIED'
    END AS TRIAGE_PRIORITY,
    (s.SENTIMENT_LABEL IN ('negative', 'mixed')) AS NEEDS_RESPONSE
FROM scored s;

-- Lab 2 Step 9
CREATE OR REPLACE VIEW AGENTS.V_SUPPLIER_RISK AS
WITH ledger AS (
    -- One row per supplier: what we buy from them and what it is worth.
    SELECT SUPPLIER_ID,
           SUPPLIER_NAME,
           SUPPLIER_COUNTRY,
           SUPPLIER_GST_REGISTERED,
           SUPPLIER_ABN,
           COUNT(*)                                              AS LINE_COUNT,
           COUNT(DISTINCT ENTITY_ID)                             AS ENTITIES_TRANSACTING,
           MIN(TAX_PERIOD)                                       AS FIRST_PERIOD,
           MAX(TAX_PERIOD)                                       AS LAST_PERIOD,
           SUM(NET_AMOUNT)                                       AS NET_AMOUNT,
           SUM(BOOKED_TAX_AMOUNT)                                AS BOOKED_TAX_AMOUNT,
           SUM(EXPECTED_TAX_AMOUNT)                              AS EXPECTED_TAX_AMOUNT,
           SUM(IFF(RECOVERABLE AND DOC_TYPE = 'AP_INVOICE',
                   EXPECTED_TAX_AMOUNT, 0))                      AS CREDITS_CLAIMED,
           SUM(IFF(IS_CROSS_BORDER, 1, 0))                       AS CROSS_BORDER_LINES
    FROM TAX.V_GST_DETERMINED
    GROUP BY ALL
),
exceptions AS (
    SELECT SUPPLIER_ID,
           COUNT(*)                                              AS EXCEPTION_LINES,
           SUM(IFF(MAX_SEVERITY = 'HIGH', 1, 0))                 AS HIGH_SEVERITY_LINES,
           SUM(ABS(COALESCE(TAX_VARIANCE, 0)))                   AS ABS_TAX_VARIANCE,
           LISTAGG(DISTINCT EXCEPTION_CODES, ', ')               AS EXCEPTION_CODE_MIX
    FROM TAX.V_GST_EXCEPTIONS
    GROUP BY SUPPLIER_ID
)
SELECT
    l.SUPPLIER_ID,
    l.SUPPLIER_NAME,
    l.SUPPLIER_COUNTRY,
    l.SUPPLIER_GST_REGISTERED,
    (l.SUPPLIER_ABN IS NULL)                                     AS ABN_MISSING,
    l.ENTITIES_TRANSACTING,
    l.FIRST_PERIOD,
    l.LAST_PERIOD,
    l.LINE_COUNT,
    l.CROSS_BORDER_LINES,
    l.NET_AMOUNT,
    l.BOOKED_TAX_AMOUNT,
    l.EXPECTED_TAX_AMOUNT,
    l.CREDITS_CLAIMED,
    COALESCE(e.EXCEPTION_LINES, 0)                               AS EXCEPTION_LINES,
    COALESCE(e.HIGH_SEVERITY_LINES, 0)                           AS HIGH_SEVERITY_LINES,
    COALESCE(e.ABS_TAX_VARIANCE, 0)                              AS ABS_TAX_VARIANCE,
    e.EXCEPTION_CODE_MIX,
    ROUND(100.0 * COALESCE(e.EXCEPTION_LINES, 0) / l.LINE_COUNT, 2)
                                                                 AS PCT_LINES_EXCEPTED,
    -- Credit exposure: what we have claimed from a supplier we cannot
    -- substantiate a claim against, because there is no ABN on file.
    IFF(l.SUPPLIER_ABN IS NULL, l.CREDITS_CLAIMED, 0)            AS UNSUBSTANTIATED_CREDITS,
    CASE WHEN l.SUPPLIER_ABN IS NULL AND l.CREDITS_CLAIMED > 0        THEN 'HIGH'
         WHEN NOT l.SUPPLIER_GST_REGISTERED AND l.BOOKED_TAX_AMOUNT <> 0 THEN 'HIGH'
         WHEN COALESCE(e.HIGH_SEVERITY_LINES, 0) > 0                  THEN 'MEDIUM'
         WHEN COALESCE(e.EXCEPTION_LINES, 0) > 0                      THEN 'LOW'
         ELSE 'NONE'
    END                                                          AS SUPPLIER_RISK_BAND
FROM ledger l
LEFT JOIN exceptions e ON e.SUPPLIER_ID = l.SUPPLIER_ID;
