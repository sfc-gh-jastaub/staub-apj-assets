-- ============================================================================
-- Lab 2 Step 5 - the scripted path for the semantic view's agent.
-- The lab teaches the Snowsight UI path first; this is the same agent as DDL
-- so a facilitator can rebuild it in one statement.
-- ============================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE GSI_TAX_WH;
USE DATABASE GSI_TAX_WORKSHOP;

CREATE OR REPLACE AGENT GSI_TAX_WORKSHOP.AGENTS.GST_COMPLIANCE_AGENT
  COMMENT = 'Answers Australian GST compliance questions over the governed tax ledger built in Lab 1.'
  PROFILE = '{"display_name": "GST Compliance Agent", "color": "blue"}'
  FROM SPECIFICATION
  $$
{
  "models": { "orchestration": "auto" },
  "orchestration": { "budget": { "seconds": 300, "tokens": 200000 } },
  "instructions": {
    "orchestration": "You answer Australian indirect tax (GST) questions for a corporate tax team, using the GST compliance semantic view. The data covers a group of Australian legal entities whose three source ERP systems have been conformed into one governed ledger. Domain rules you must respect: GST in Australia is 10 percent and has never changed. BOOKED_TAX_AMOUNT is what the ERP actually recorded. EXPECTED_TAX_AMOUNT is what the tax rules determine should apply. The difference between them is the variance that matters, so when a user asks about discrepancies, compare those two. Tax treatments are STANDARD, GST_FREE, INPUT_TAXED, EXPORT, REVERSE_CHARGE and NON_DEDUCTIBLE. Imported professional fees from non-registered offshore suppliers changed treatment on 1 July 2024, moving from out of scope to reverse charge, so whenever a question spans that date, split the result either side of it rather than aggregating across the boundary. If the user says last quarter or this month without naming a period, use the most recent complete tax period in the data and say which period you used. Always use the analyst tool for numeric questions; never estimate a figure yourself.",
    "response": "Lead with the direct answer and the figure. Then show the SQL you ran. Then state any assumptions you made about the tax period, the entity scope, or the treatment of NULL values. Format currency in Australian dollars with thousands separators. Never present a computed GST position as a lodgeable figure: it is an analytical result that a tax professional must review before it goes anywhere near a return.",
    "sample_questions": [
      { "question": "What was our total GST payable last quarter?" },
      { "question": "Which entities have exceptions this month?" },
      { "question": "Show me net GST by entity for the last six months." },
      { "question": "Which suppliers are missing an ABN on claimed credits?" },
      { "question": "What is our total exposure from unmapped accounts?" },
      { "question": "Compare computed GST to lodged GST by period." },
      { "question": "Which supply categories generate the most exceptions?" },
      { "question": "Show imported professional fees before and after 1 July 2024." }
    ]
  },
  "tools": [
    {
      "tool_spec": {
        "type": "cortex_analyst_text_to_sql",
        "name": "query_gst_compliance",
        "description": "Query the group GST position, the BAS reconciliation and the exception register. Use this for any question about GST payable or collected, net GST by entity or tax period, computed versus lodged BAS comparisons, exception and error counts, supply categories, tax treatments, source systems, or supplier ABN issues."
      }
    },
    {
      "tool_spec": {
        "type": "data_to_chart",
        "name": "data_to_chart",
        "description": "Generates a chart from data returned by the analyst tool. Use when the user asks to see a trend, a comparison across entities or periods, or explicitly asks for a chart."
      }
    }
  ],
  "tool_resources": {
    "query_gst_compliance": {
      "semantic_view": "GSI_TAX_WORKSHOP.AGENTS.SV_GST_COMPLIANCE",
      "execution_environment": { "type": "warehouse", "warehouse": "GSI_TAX_WH", "query_timeout": 299 }
    }
  }
}
  $$;

SHOW AGENTS IN SCHEMA GSI_TAX_WORKSHOP.AGENTS;
