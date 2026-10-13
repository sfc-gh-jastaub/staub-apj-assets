-- =====================================================================
-- send_email_tool.sql
-- Custom Cortex Agent tool for SnowBank demo.
-- Sends an HTML email to a specified recipient using a Snowflake
-- notification integration. Activated against the SnowBank Risk Agent
-- live in Scene 3.
--
-- Pre-reqs:
--   - 01_database_setup.sql has been executed (DB / schemas / WH exist)
--   - A notification integration with email enabled is available
--     (see CREATE NOTIFICATION INTEGRATION block below)
--   - Demo presenter's email is on the allow-list
-- =====================================================================

USE ROLE      ACCOUNTADMIN;
USE DATABASE  SNOWBANK_DEMO;
USE SCHEMA    ASSETS;
USE WAREHOUSE SNOWBANK_DEMO_WH;

-- ---------------------------------------------------------------------
-- 1. Notification integration (one-time, account level)
--    Edit ALLOWED_RECIPIENTS to include the presenter's email.
-- ---------------------------------------------------------------------
CREATE NOTIFICATION INTEGRATION IF NOT EXISTS SNOWBANK_EMAIL_INT
    TYPE = EMAIL
    ENABLED = TRUE
    ALLOWED_RECIPIENTS = ('your.email@example.com')
    COMMENT = 'Email channel for SnowBank Risk Agent reports';

-- ---------------------------------------------------------------------
-- 2. Stored procedure that the Cortex Agent will invoke as a tool.
--    Inputs:
--      RECIPIENT     - email address (must be on the allow-list)
--      SUBJECT       - email subject line
--      HTML_BODY     - HTML produced by the html_report skill
-- ---------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SNOWBANK_DEMO.ASSETS.SEND_REPORT_EMAIL(
    RECIPIENT VARCHAR,
    SUBJECT   VARCHAR,
    HTML_BODY VARCHAR
)
RETURNS VARCHAR
LANGUAGE SQL
EXECUTE AS CALLER
AS
$$
BEGIN
    CALL SYSTEM$SEND_EMAIL(
        'SNOWBANK_EMAIL_INT',
        :RECIPIENT,
        :SUBJECT,
        :HTML_BODY,
        'text/html'
    );
    RETURN 'Email sent to ' || :RECIPIENT;
EXCEPTION
    WHEN OTHER THEN
        RETURN 'Email failed: ' || SQLERRM;
END;
$$;

-- ---------------------------------------------------------------------
-- 3. Tool spec (YAML) — register this against the Cortex Agent in Scene 3.
--    The agent activation step in the demo will reference this spec.
-- ---------------------------------------------------------------------
/*
tool_spec:
  type: generic
  name: send_report_email
  description: |
    Email an HTML report to a recipient. Use after the html_report skill
    has produced an HTML document and the user has asked to send it.
  input_schema:
    type: object
    required: [recipient, subject, html_body]
    properties:
      recipient:
        type: string
        description: Email address. Must be on the allow-list.
      subject:
        type: string
        description: Subject line for the email.
      html_body:
        type: string
        description: HTML produced by the html_report skill.
  identifier: SNOWBANK_DEMO.ASSETS.SEND_REPORT_EMAIL
*/

-- ---------------------------------------------------------------------
-- 4. Smoke test (run manually before the demo to confirm delivery)
-- ---------------------------------------------------------------------
-- CALL SNOWBANK_DEMO.ASSETS.SEND_REPORT_EMAIL(
--     'your.email@example.com',
--     'SnowBank email tool — smoke test',
--     '<html><body><h2>Hello from SnowBank</h2><p>If you can read this, the tool works.</p></body></html>'
-- );
