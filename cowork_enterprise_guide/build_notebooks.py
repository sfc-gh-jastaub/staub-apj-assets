#!/usr/bin/env python3
"""Builder for the CoWork Enterprise Demo notebook series.

Self-contained: assembles nine SQL-kernel Snowflake Workspace notebooks for the
CoWork enterprise deployment guide, in the isolated COWORK_ENTERPRISE_DEMO
namespace. All SQL is defined in this file (see the INLINE dict and the n00-n08
cell lists) — it reads no external notebooks or files. Run: python3 build_notebooks.py
"""
import json, os, uuid

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "notebooks")

def uid():
    return uuid.uuid4().hex[:8]

def md(text):
    return {"cell_type": "markdown", "id": uid(), "metadata": {"codeCollapsed": True},
            "source": text}

def sql(name, title, source):
    src = f"%%sql -r {name}\n" + source.rstrip() + "\n"
    return {"cell_type": "code", "id": uid(), "execution_count": None,
            "metadata": {"language": "sql", "name": name, "title": title,
                         "resultVariableName": name},
            "outputs": [], "source": src}

ICONS = "_Icons used throughout: 🛠️ Action  📌 Note  🔹 Info_"

def nb_header(topic, num, title, does, why_title, why, est, prereqs):
    """Rich HOL-style header cell: What This Does / Why It Matters / Time / Prereqs."""
    out = [f"# CoWork Enterprise Demo — {topic}",
           f"## Notebook {num} — {title}", "", ICONS, "", '> ⚠️ _Generated from `build_notebooks.py` — edit the builder and re-run. Direct edits to this notebook are overwritten._', "", "---", "",
           "### What This Notebook Does:", ""]
    out += [f"{i}. 🛠️ {d}" for i, d in enumerate(does, 1)]
    out += ["", "---", "", f"### Why {why_title}:", "", why, "", "---", "",
            f"### Estimated Time: **{est}**", "", "### Prerequisites:"]
    out += [f"- {p}" for p in prereqs]
    return "\n".join(out)

def nb_complete(num, built, points, nxt):
    """Rich HOL-style completion cell."""
    out = [f"## ✅ Notebook {num} Complete", "", "### What You Just Built:"]
    out += [f"- {b}" for b in built]
    out += ["", "---", "", "### Key Points:"]
    out += [f"- {p}" for p in points]
    out += ["", "---", "", "### Next:", "", nxt]
    return "\n".join(out)

def write_nb(fname, cells):
    nb = {"cells": cells,
          "metadata": {"kernelspec": {"display_name": "SQL", "language": "sql", "name": "sql"},
                       "language_info": {"name": "sql"}},
          "nbformat": 4, "nbformat_minor": 5}
    path = os.path.join(OUT, fname)
    with open(path, "w") as f:
        json.dump(nb, f, indent=1)
    print("wrote", path, "cells=", len(cells))

DB = "COWORK_ENTERPRISE_DEMO"
WH = "COWORK_ENTERPRISE_DEMO_WH"
ADMIN = "COWORK_ENTERPRISE_DEMO_ADMIN"
SIUSER = "COWORK_ENTERPRISE_DEMO_SI_USER"
BIZUSER = "COWORK_ENTERPRISE_DEMO_BIZ_USER"
AGENT = f"{DB}.AGENTS.DEMO_AGENT"
SV = f"{DB}.SEMANTIC.DEMO_SV"
SEARCH = f"{DB}.AGENTS.DEMO_SEARCH"
SEARCH_CLIENT = f"{DB}.AGENTS.DEMO_CLIENT_SEARCH"
COOBJ = "SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT"

# --- Inlined SQL (self-contained; no external notebook dependencies) ---
INLINE = {
    'CreateRole': "USE ROLE ACCOUNTADMIN;\n\n-- Create lab role\nCREATE ROLE IF NOT EXISTS COWORK_ENTERPRISE_DEMO_ADMIN\n  COMMENT = 'Summit 2026 HOL - Strive Capital lab role';\n\n-- Grant role to current user and ACCOUNTADMIN\nGRANT ROLE COWORK_ENTERPRISE_DEMO_ADMIN TO ROLE ACCOUNTADMIN;\n\nSELECT 'COWORK_ENTERPRISE_DEMO_ADMIN role created and granted' AS STATUS;",
    'CreateWH': "-- Create warehouse\nCREATE WAREHOUSE IF NOT EXISTS COWORK_ENTERPRISE_DEMO_WH\n  WAREHOUSE_SIZE = 'XSMALL'\n  AUTO_SUSPEND = 60\n  AUTO_RESUME = TRUE\n  INITIALLY_SUSPENDED = TRUE\n  COMMENT = 'Summit 2026 HOL - Strive Capital compute';\n\n-- Grant usage to COWORK_ENTERPRISE_DEMO_ADMIN\nGRANT USAGE ON WAREHOUSE COWORK_ENTERPRISE_DEMO_WH TO ROLE COWORK_ENTERPRISE_DEMO_ADMIN;\nGRANT OPERATE ON WAREHOUSE COWORK_ENTERPRISE_DEMO_WH TO ROLE COWORK_ENTERPRISE_DEMO_ADMIN;\n\nSELECT 'COWORK_ENTERPRISE_DEMO_WH warehouse created (XS, auto-suspend 60s)' AS STATUS;",
    'EnableCrossRegionInference': "-- Enable cross-region inference (Global for best cost and model access)\nALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';\n\nSHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;\n\nSELECT 'Cross-region inference enabled (ANY_REGION)' AS STATUS;",
    'UseNew': 'USE ROLE COWORK_ENTERPRISE_DEMO_ADMIN;\nUSE DATABASE COWORK_ENTERPRISE_DEMO;\nUSE SCHEMA ANALYTICS;\nUSE WAREHOUSE COWORK_ENTERPRISE_DEMO_WH;',
    'CreateTables': "-- CLIENTS table: Client master data\nCREATE OR REPLACE TABLE COWORK_ENTERPRISE_DEMO.ANALYTICS.CLIENTS (\n    CLIENT_ID           NUMBER AUTOINCREMENT PRIMARY KEY,\n    CLIENT_NAME         VARCHAR(100) NOT NULL,\n    ACCOUNT_TYPE        VARCHAR(20) NOT NULL,      -- INSTITUTIONAL, RETAIL, HNW\n    REGION              VARCHAR(30) NOT NULL,\n    AUM                 NUMBER(15,2),              -- Assets Under Management\n    RISK_PROFILE        VARCHAR(20),               -- CONSERVATIVE, MODERATE, AGGRESSIVE\n    ONBOARDED_DATE      DATE NOT NULL,\n    RELATIONSHIP_MANAGER VARCHAR(50),\n    EMAIL               VARCHAR(100),\n    STATUS              VARCHAR(20) DEFAULT 'ACTIVE'\n);\n\n-- POSITIONS table: Current portfolio positions\nCREATE OR REPLACE TABLE COWORK_ENTERPRISE_DEMO.ANALYTICS.POSITIONS (\n    POSITION_ID         NUMBER AUTOINCREMENT PRIMARY KEY,\n    CLIENT_ID           NUMBER NOT NULL,\n    SYMBOL              VARCHAR(10) NOT NULL,\n    QUANTITY            NUMBER NOT NULL,\n    AVG_COST            NUMBER(12,4) NOT NULL,\n    CURRENT_PRICE       NUMBER(12,4),\n    MARKET_VALUE        NUMBER(15,2),\n    UNREALIZED_PNL      NUMBER(15,2),\n    SECTOR              VARCHAR(30),\n    LAST_UPDATED        TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()\n);\n\n-- TRADES table: Recent trade executions\nCREATE OR REPLACE TABLE COWORK_ENTERPRISE_DEMO.ANALYTICS.TRADES (\n    TRADE_ID            NUMBER AUTOINCREMENT PRIMARY KEY,\n    CLIENT_ID           NUMBER NOT NULL,\n    SYMBOL              VARCHAR(10) NOT NULL,\n    TRADE_TYPE          VARCHAR(4) NOT NULL,       -- BUY or SELL\n    QUANTITY            NUMBER NOT NULL,\n    PRICE               NUMBER(12,4) NOT NULL,\n    TRADE_DATE          TIMESTAMP_NTZ NOT NULL DEFAULT CURRENT_TIMESTAMP(),\n    SETTLEMENT_DATE     DATE,\n    STATUS              VARCHAR(20) DEFAULT 'EXECUTED',\n    EXCHANGE            VARCHAR(10) DEFAULT 'NYSE',\n    NOTES               VARCHAR(500)\n);\n\n-- DAILY_METRICS table: Aggregated daily business metrics\nCREATE OR REPLACE TABLE COWORK_ENTERPRISE_DEMO.ANALYTICS.DAILY_METRICS (\n    METRIC_DATE         DATE NOT NULL,\n    TOTAL_AUM           NUMBER(18,2),\n    TOTAL_CLIENTS       NUMBER,\n    ACTIVE_CLIENTS      NUMBER,\n    TOTAL_TRADES        NUMBER,\n    TRADE_VOLUME_USD    NUMBER(18,2),\n    NET_FLOWS           NUMBER(15,2),\n    TOTAL_REVENUE       NUMBER(15,2),\n    AVG_PORTFOLIO_RISK  NUMBER(5,3),\n    TOP_SECTOR          VARCHAR(30)\n);\n\nSELECT 'Analytics tables created' AS STATUS;",
    'LoadClientData': "-- Load client data\nINSERT INTO COWORK_ENTERPRISE_DEMO.ANALYTICS.CLIENTS (CLIENT_NAME, ACCOUNT_TYPE, REGION, AUM, RISK_PROFILE, ONBOARDED_DATE, RELATIONSHIP_MANAGER, EMAIL, STATUS)\nVALUES\n('Meridian Pension Fund', 'INSTITUTIONAL', 'North America', 2500000000.00, 'MODERATE', '2019-03-15', 'Sarah Chen', 'contact@meridianpf.com', 'ACTIVE'),\n('Atlas Sovereign Wealth', 'INSTITUTIONAL', 'EMEA', 8700000000.00, 'CONSERVATIVE', '2017-08-22', 'James Morrison', 'invest@atlasswf.com', 'ACTIVE'),\n('Velocity Capital Partners', 'INSTITUTIONAL', 'North America', 1200000000.00, 'AGGRESSIVE', '2020-01-10', 'Sarah Chen', 'ops@velocitycap.com', 'ACTIVE'),\n('Sakura Asset Management', 'INSTITUTIONAL', 'APJ', 3100000000.00, 'MODERATE', '2018-11-05', 'Kenji Tanaka', 'info@sakura-am.jp', 'ACTIVE'),\n('Nordic Growth Fund', 'INSTITUTIONAL', 'EMEA', 950000000.00, 'AGGRESSIVE', '2021-06-18', 'Erik Lindqvist', 'invest@nordicgf.se', 'ACTIVE'),\n('Wellington Family Office', 'HNW', 'North America', 450000000.00, 'MODERATE', '2016-02-28', 'Sarah Chen', 'pw@wellingtonfamily.com', 'ACTIVE'),\n('Horizon Endowment', 'INSTITUTIONAL', 'North America', 1800000000.00, 'CONSERVATIVE', '2015-09-12', 'Michael Brooks', 'endowment@horizonedu.org', 'ACTIVE'),\n('Pacific Rim Ventures', 'INSTITUTIONAL', 'APJ', 2200000000.00, 'AGGRESSIVE', '2019-07-30', 'Kenji Tanaka', 'invest@pacificrimv.sg', 'ACTIVE'),\n('Blackstone Ridge Capital', 'HNW', 'North America', 680000000.00, 'AGGRESSIVE', '2022-03-01', 'Michael Brooks', 'admin@blackstoneridge.com', 'ACTIVE'),\n('Emirates Diversified Holdings', 'INSTITUTIONAL', 'EMEA', 5400000000.00, 'MODERATE', '2018-01-20', 'James Morrison', 'invest@emiratesdh.ae', 'ACTIVE'),\n('Redwood Retirement Systems', 'INSTITUTIONAL', 'North America', 4100000000.00, 'CONSERVATIVE', '2014-05-15', 'Sarah Chen', 'ops@redwoodretire.com', 'ACTIVE'),\n('Chen Wei Holdings', 'HNW', 'APJ', 320000000.00, 'MODERATE', '2021-11-22', 'Kenji Tanaka', 'office@chenwei.hk', 'ACTIVE');\n\nSELECT 'Clients loaded: ' || COUNT(*) || ' rows' AS STATUS FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.CLIENTS;",
    'LoadPortfolioPositions': "-- Load portfolio positions\nINSERT INTO COWORK_ENTERPRISE_DEMO.ANALYTICS.POSITIONS (CLIENT_ID, SYMBOL, QUANTITY, AVG_COST, CURRENT_PRICE, MARKET_VALUE, UNREALIZED_PNL, SECTOR)\nVALUES\n(1, 'AAPL', 50000, 145.2300, 198.5000, 9925000.00, 2663500.00, 'Technology'),\n(1, 'MSFT', 35000, 280.5000, 425.3000, 14885500.00, 5068000.00, 'Technology'),\n(1, 'JNJ', 40000, 155.8000, 162.4000, 6496000.00, 264000.00, 'Healthcare'),\n(2, 'BRK.B', 25000, 310.0000, 465.2000, 11630000.00, 3880000.00, 'Financials'),\n(2, 'PG', 60000, 138.5000, 168.9000, 10134000.00, 1824000.00, 'Consumer Staples'),\n(2, 'XOM', 45000, 85.6000, 112.3000, 5053500.00, 1201500.00, 'Energy'),\n(3, 'NVDA', 80000, 42.5000, 135.8000, 10864000.00, 7464000.00, 'Technology'),\n(3, 'TSLA', 30000, 185.0000, 248.5000, 7455000.00, 1905000.00, 'Consumer Discretionary'),\n(3, 'AMD', 55000, 95.3000, 168.7000, 9278500.00, 4037000.00, 'Technology'),\n(4, 'SONY', 90000, 78.5000, 95.2000, 8568000.00, 1503000.00, 'Technology'),\n(4, 'TM', 40000, 155.0000, 182.4000, 7296000.00, 1096000.00, 'Consumer Discretionary'),\n(5, 'ASML', 12000, 580.0000, 890.5000, 10686000.00, 3726000.00, 'Technology'),\n(5, 'SPOT', 25000, 145.0000, 328.6000, 8215000.00, 4590000.00, 'Technology'),\n(6, 'AAPL', 20000, 130.0000, 198.5000, 3970000.00, 1370000.00, 'Technology'),\n(6, 'V', 15000, 220.0000, 295.8000, 4437000.00, 1137000.00, 'Financials'),\n(7, 'VTI', 100000, 195.0000, 268.4000, 26840000.00, 7340000.00, 'Broad Market'),\n(7, 'BND', 80000, 72.5000, 69.8000, 5584000.00, -216000.00, 'Fixed Income'),\n(8, 'BABA', 120000, 88.0000, 125.3000, 15036000.00, 4476000.00, 'Technology'),\n(8, 'SE', 65000, 52.0000, 98.5000, 6402500.00, 3022500.00, 'Technology'),\n(9, 'COIN', 35000, 65.0000, 225.4000, 7889000.00, 5614000.00, 'Financials'),\n(9, 'MSTR', 18000, 320.0000, 1650.0000, 29700000.00, 23940000.00, 'Technology'),\n(10, 'ADNOC', 200000, 3.2000, 4.1000, 820000.00, 180000.00, 'Energy'),\n(10, 'SAP', 30000, 145.0000, 235.6000, 7068000.00, 2718000.00, 'Technology'),\n(11, 'VTI', 150000, 180.0000, 268.4000, 40260000.00, 13260000.00, 'Broad Market'),\n(11, 'SCHD', 200000, 72.0000, 82.5000, 16500000.00, 2100000.00, 'Dividends'),\n(12, 'TCEHY', 50000, 42.0000, 58.3000, 2915000.00, 815000.00, 'Technology'),\n(12, '9988.HK', 80000, 72.5000, 108.2000, 8656000.00, 2856000.00, 'Technology');\n\nSELECT 'Positions loaded: ' || COUNT(*) || ' rows' AS STATUS FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.POSITIONS;",
    'LoadRecentTrades': "-- Load recent trades\nINSERT INTO COWORK_ENTERPRISE_DEMO.ANALYTICS.TRADES (CLIENT_ID, SYMBOL, TRADE_TYPE, QUANTITY, PRICE, TRADE_DATE, SETTLEMENT_DATE, STATUS, EXCHANGE, NOTES)\nVALUES\n(1, 'AAPL', 'BUY', 5000, 197.80, DATEADD('hour', -2, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NASDAQ', 'Adding to core tech position'),\n(1, 'MSFT', 'BUY', 2000, 424.50, DATEADD('hour', -3, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NASDAQ', 'Pre-earnings accumulation'),\n(3, 'NVDA', 'SELL', 10000, 136.20, DATEADD('hour', -1, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NASDAQ', 'Profit taking after run-up'),\n(3, 'TSLA', 'BUY', 8000, 247.90, DATEADD('hour', -4, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NASDAQ', 'Momentum entry'),\n(2, 'XOM', 'SELL', 5000, 111.80, DATEADD('hour', -5, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NYSE', 'Reducing energy exposure'),\n(5, 'ASML', 'BUY', 2000, 892.00, DATEADD('minute', -30, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NASDAQ', 'Semiconductor thesis'),\n(4, 'SONY', 'BUY', 15000, 94.80, DATEADD('hour', -6, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NYSE', 'Gaming sector exposure'),\n(9, 'COIN', 'BUY', 10000, 224.50, DATEADD('minute', -45, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NASDAQ', 'Crypto proxy play'),\n(6, 'V', 'BUY', 3000, 294.20, DATEADD('hour', -7, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NYSE', 'Payments thesis'),\n(8, 'SE', 'SELL', 20000, 99.10, DATEADD('hour', -2, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NYSE', 'Taking profits on SE Asia tech'),\n(7, 'BND', 'BUY', 25000, 69.90, DATEADD('hour', -8, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NYSE', 'Rebalancing fixed income allocation'),\n(10, 'SAP', 'BUY', 5000, 236.10, DATEADD('hour', -3, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NYSE', 'Enterprise software conviction'),\n(11, 'SCHD', 'BUY', 30000, 82.30, DATEADD('day', -1, CURRENT_TIMESTAMP()), DATEADD('day', 1, CURRENT_DATE()), 'SETTLED', 'NYSE', 'Dividend reinvestment'),\n(12, 'TCEHY', 'BUY', 10000, 57.80, DATEADD('day', -1, CURRENT_TIMESTAMP()), DATEADD('day', 1, CURRENT_DATE()), 'SETTLED', 'OTC', 'China tech rebound thesis'),\n(1, 'JNJ', 'SELL', 10000, 163.00, DATEADD('day', -1, CURRENT_TIMESTAMP()), DATEADD('day', 1, CURRENT_DATE()), 'SETTLED', 'NYSE', 'Trimming healthcare overweight'),\n(3, 'AMD', 'BUY', 12000, 167.50, DATEADD('minute', -90, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NASDAQ', 'AI infrastructure play'),\n(5, 'SPOT', 'SELL', 5000, 330.00, DATEADD('hour', -4, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NYSE', 'Locking in gains'),\n(2, 'PG', 'BUY', 10000, 169.20, DATEADD('hour', -5, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NYSE', 'Defensive positioning'),\n(4, 'TM', 'SELL', 8000, 183.00, DATEADD('hour', -6, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NYSE', 'Rotating out of auto'),\n(9, 'MSTR', 'BUY', 3000, 1645.00, DATEADD('minute', -20, CURRENT_TIMESTAMP()), DATEADD('day', 2, CURRENT_DATE()), 'EXECUTED', 'NASDAQ', 'Bitcoin proxy - high conviction');\n\nSELECT 'Trades loaded: ' || COUNT(*) || ' rows' AS STATUS FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.TRADES;",
    'LoadDailyMetrics': "-- Load daily metrics (last 30 days of aggregated business metrics)\nINSERT INTO COWORK_ENTERPRISE_DEMO.ANALYTICS.DAILY_METRICS (METRIC_DATE, TOTAL_AUM, TOTAL_CLIENTS, ACTIVE_CLIENTS, TOTAL_TRADES, TRADE_VOLUME_USD, NET_FLOWS, TOTAL_REVENUE, AVG_PORTFOLIO_RISK, TOP_SECTOR)\nSELECT\n    DATEADD('day', -seq4(), CURRENT_DATE()) AS METRIC_DATE,\n    31400000000.00 + (RANDOM() % 500000000) AS TOTAL_AUM,\n    12 AS TOTAL_CLIENTS,\n    CASE WHEN seq4() % 7 = 0 THEN 10 ELSE 12 END AS ACTIVE_CLIENTS,\n    15 + (ABS(RANDOM()) % 20) AS TOTAL_TRADES,\n    25000000.00 + (ABS(RANDOM()) % 50000000) AS TRADE_VOLUME_USD,\n    -5000000.00 + (ABS(RANDOM()) % 10000000) AS NET_FLOWS,\n    850000.00 + (ABS(RANDOM()) % 300000) AS TOTAL_REVENUE,\n    0.45 + (ABS(RANDOM()) % 20) / 100.0 AS AVG_PORTFOLIO_RISK,\n    CASE (ABS(RANDOM()) % 4)\n        WHEN 0 THEN 'Technology'\n        WHEN 1 THEN 'Financials'\n        WHEN 2 THEN 'Energy'\n        ELSE 'Healthcare'\n    END AS TOP_SECTOR\nFROM TABLE(GENERATOR(ROWCOUNT => 30));\n\nSELECT 'Daily metrics loaded: ' || COUNT(*) || ' rows' AS STATUS FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.DAILY_METRICS;",
    'CreateUnstructuredData': "-- Research notes and market commentary (for Cortex Search)\nCREATE OR REPLACE TABLE COWORK_ENTERPRISE_DEMO.ANALYTICS.RESEARCH_NOTES (\n    NOTE_ID         NUMBER AUTOINCREMENT PRIMARY KEY,\n    TITLE           VARCHAR(200) NOT NULL,\n    CONTENT         VARCHAR(5000) NOT NULL,\n    AUTHOR          VARCHAR(50),\n    CATEGORY        VARCHAR(30),\n    PUBLISHED_DATE  DATE,\n    REGION          VARCHAR(30),\n    SYMBOLS_MENTIONED VARCHAR(200)\n);\n\nINSERT INTO COWORK_ENTERPRISE_DEMO.ANALYTICS.RESEARCH_NOTES (TITLE, CONTENT, AUTHOR, CATEGORY, PUBLISHED_DATE, REGION, SYMBOLS_MENTIONED)\nVALUES\n('Q2 Technology Sector Outlook', 'The technology sector continues to benefit from AI infrastructure buildout. NVIDIA remains the primary beneficiary of data center GPU demand, with hyperscaler capex showing no signs of deceleration. We maintain overweight positions in semiconductor names (NVDA, AMD, ASML) and see further upside in AI-adjacent software companies. Risk: elevated valuations leave limited margin of safety if earnings disappoint.', 'Sarah Chen', 'Market Commentary', CURRENT_DATE() - 5, 'North America', 'NVDA,AMD,ASML'),\n('Emerging Markets Risk Assessment', 'Geopolitical tensions in the South China Sea and ongoing US-China trade restrictions create headwinds for APJ equity exposure. However, Japanese equities (SONY, TM) benefit from yen weakness and corporate governance reforms. We recommend selective positioning in Japan while maintaining caution on Greater China names. Sakura Asset Management has expressed interest in increasing Japan allocation.', 'Kenji Tanaka', 'Risk Assessment', CURRENT_DATE() - 3, 'APJ', 'SONY,TM,TCEHY,BABA'),\n('Fixed Income Rebalancing Strategy', 'With rate cuts expected in H2, we recommend gradually extending duration in fixed income portfolios. Horizon Endowment and Redwood Retirement Systems should consider shifting from short-duration BND positions to intermediate-term corporates. The yield curve normalization thesis supports this move. Current BND position shows unrealized loss of $216K — acceptable given the strategic rationale.', 'Michael Brooks', 'Strategy', CURRENT_DATE() - 7, 'North America', 'BND,SCHD'),\n('EMEA Energy Transition Update', 'European energy majors are accelerating renewable investments. Emirates Diversified Holdings should maintain XOM exposure for dividend yield but consider adding renewable energy ETFs for long-term positioning. SAP enterprise software adoption continues to accelerate across EMEA — strong conviction on the digital transformation thesis.', 'James Morrison', 'Sector Update', CURRENT_DATE() - 2, 'EMEA', 'XOM,SAP'),\n('Crypto and Digital Assets Thesis', 'Bitcoin proxy plays (COIN, MSTR) have outperformed direct crypto holdings on a risk-adjusted basis. Blackstone Ridge Capital has generated exceptional returns on MSTR position (+$23.9M unrealized). We recommend maintaining but not increasing allocation — concentration risk is elevated. Consider taking partial profits if MSTR exceeds $1,800.', 'Michael Brooks', 'Thematic Research', CURRENT_DATE() - 1, 'North America', 'COIN,MSTR'),\n('Client Portfolio Compliance Review - May 2026', 'Monthly compliance check complete. All portfolios within risk mandate boundaries. One flagged item: Velocity Capital Partners TSLA position approaching 15% single-name concentration limit after recent BUY order (8,000 shares at $247.90). Recommend monitoring and potential trim if position exceeds threshold. No other policy breaches detected across 12 active accounts.', 'Compliance Team', 'Compliance', CURRENT_DATE(), 'North America', 'TSLA'),\n('Nordic Growth Fund - Quarterly Review', 'Nordic Growth Fund continues to outperform benchmark with aggressive tech allocation (ASML, SPOT). ASML position has generated $3.7M unrealized gains on semiconductor thesis. Spotify gains reflect subscriber growth exceeding expectations. Fund manager Erik Lindqvist has requested exploration of AI infrastructure names — recommend presenting NVDA and AMD analysis at next quarterly meeting.', 'Erik Lindqvist', 'Client Review', CURRENT_DATE() - 10, 'EMEA', 'ASML,SPOT,NVDA,AMD'),\n('Pacific Rim Ventures - Rotation Strategy', 'Client has requested rotation out of SE Asia tech (SE position) into broader AI plays. The $3M+ unrealized gain on SE provides tax-loss harvesting opportunity if paired with appropriate offset. Recommend phased exit over 2 weeks to minimize market impact. Replacement candidates: BABA (already held), or new positions in Korean AI chip names.', 'Kenji Tanaka', 'Trading Strategy', CURRENT_DATE() - 4, 'APJ', 'SE,BABA');\n\nSELECT 'Research notes loaded: ' || COUNT(*) || ' rows' AS STATUS FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.RESEARCH_NOTES;",
    'ValidateSetup': "-- Validate all tables and row counts\nSELECT 'CLIENTS' AS TABLE_NAME, COUNT(*) AS ROW_COUNT FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.CLIENTS\nUNION ALL\nSELECT 'POSITIONS', COUNT(*) FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.POSITIONS\nUNION ALL\nSELECT 'TRADES', COUNT(*) FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.TRADES\nUNION ALL\nSELECT 'DAILY_METRICS', COUNT(*) FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.DAILY_METRICS\nUNION ALL\nSELECT 'RESEARCH_NOTES', COUNT(*) FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.RESEARCH_NOTES\nORDER BY TABLE_NAME;",
    'SanityCheck': '-- Quick sanity check: Top 5 clients by AUM\nSELECT CLIENT_NAME, ACCOUNT_TYPE, REGION, AUM, RISK_PROFILE\nFROM COWORK_ENTERPRISE_DEMO.ANALYTICS.CLIENTS\nORDER BY AUM DESC\nLIMIT 5;',
    'VerifyCrossRegion': "-- Verify cross-region inference is enabled\nSHOW PARAMETERS LIKE 'CORTEX_ENABLED_CROSS_REGION' IN ACCOUNT;",
    'CreateSemanticView': 'CREATE OR REPLACE SEMANTIC VIEW COWORK_ENTERPRISE_DEMO.SEMANTIC.DEMO_SV\n\n  TABLES (\n    clients AS COWORK_ENTERPRISE_DEMO.ANALYTICS.CLIENTS\n      PRIMARY KEY (CLIENT_ID)\n      COMMENT = \'Client master data including institutional and HNW accounts with AUM and risk profiles\',\n\n    positions AS COWORK_ENTERPRISE_DEMO.ANALYTICS.POSITIONS\n      PRIMARY KEY (POSITION_ID)\n      COMMENT = \'Current portfolio positions by client and symbol with market values and unrealized PnL\',\n\n    trades AS COWORK_ENTERPRISE_DEMO.ANALYTICS.TRADES\n      PRIMARY KEY (TRADE_ID)\n      COMMENT = \'Trade execution history including buy/sell orders with prices, quantities, and status\'\n  )\n\n  RELATIONSHIPS (\n    positions_to_clients AS\n      positions(CLIENT_ID) REFERENCES clients,\n    trades_to_clients AS\n      trades(CLIENT_ID) REFERENCES clients\n  )\n\n  FACTS (\n    clients.AUM AS AUM\n      COMMENT = \'Assets Under Management in USD. Total value of assets the client has with Strive Capital.\',\n    positions.POSITION_QUANTITY AS QUANTITY\n      COMMENT = \'Number of shares held in the position\',\n    positions.AVG_COST AS AVG_COST\n      COMMENT = \'Average cost basis per share for the position\',\n    positions.CURRENT_PRICE AS CURRENT_PRICE\n      COMMENT = \'Current market price per share\',\n    positions.MARKET_VALUE AS MARKET_VALUE\n      COMMENT = \'Current market value of the position (quantity * current_price)\',\n    positions.UNREALIZED_PNL AS UNREALIZED_PNL\n      COMMENT = \'Unrealized profit or loss on the position (market_value - cost_basis). Positive = gain, negative = loss.\',\n    trades.TRADE_QUANTITY AS QUANTITY\n      COMMENT = \'Number of shares in the trade order\',\n    trades.TRADE_PRICE AS PRICE\n      COMMENT = \'Execution price per share for the trade\'\n  )\n\n  DIMENSIONS (\n    clients.CLIENT_NAME AS CLIENT_NAME\n      COMMENT = \'Full name of the client account\'\n      WITH CORTEX SEARCH SERVICE COWORK_ENTERPRISE_DEMO.AGENTS.DEMO_CLIENT_SEARCH,\n    clients.ACCOUNT_TYPE AS ACCOUNT_TYPE\n      COMMENT = \'Account classification: INSTITUTIONAL, HNW (High Net Worth), or RETAIL\',\n    clients.REGION AS REGION\n      COMMENT = \'Geographic region: North America, EMEA, or APJ\',\n    clients.RISK_PROFILE AS RISK_PROFILE\n      COMMENT = \'Investment risk tolerance: CONSERVATIVE, MODERATE, or AGGRESSIVE\',\n    clients.RELATIONSHIP_MANAGER AS RELATIONSHIP_MANAGER\n      COMMENT = \'Name of the assigned relationship manager\',\n    clients.STATUS AS STATUS\n      COMMENT = \'Client account status: ACTIVE or INACTIVE\',\n    clients.ONBOARDED_DATE AS ONBOARDED_DATE\n      COMMENT = \'Date the client was onboarded\',\n\n    positions.SYMBOL AS SYMBOL\n      COMMENT = \'Stock ticker symbol (e.g., AAPL, NVDA, MSFT)\',\n    positions.SECTOR AS SECTOR\n      COMMENT = \'Market sector classification (Technology, Financials, Energy, Healthcare, etc.)\',\n\n    trades.TRADE_TYPE AS TRADE_TYPE\n      COMMENT = \'Direction of the trade: BUY or SELL\',\n    trades.TRADE_STATUS AS STATUS\n      COMMENT = \'Trade execution status: EXECUTED or SETTLED\',\n    trades.EXCHANGE AS EXCHANGE\n      COMMENT = \'Exchange where trade was executed (NYSE, NASDAQ, OTC)\',\n    trades.TRADE_DATE AS TRADE_DATE\n      COMMENT = \'Timestamp when the trade was executed\',\n    trades.TRADE_NOTES AS NOTES\n      COMMENT = \'Trader notes explaining the rationale for the trade\'\n  )\n\n  METRICS (\n    clients.TOTAL_AUM AS SUM(clients.AUM)\n      COMMENT = \'Total Assets Under Management across all clients in USD\',\n\n    clients.CLIENT_COUNT AS COUNT(DISTINCT CLIENT_ID)\n      COMMENT = \'Number of distinct client accounts\',\n\n    positions.TOTAL_PORTFOLIO_VALUE AS SUM(positions.MARKET_VALUE)\n      COMMENT = \'Total current market value across all positions in USD\',\n\n    positions.TOTAL_UNREALIZED_PNL AS SUM(positions.UNREALIZED_PNL)\n      COMMENT = \'Total unrealized profit/loss across all positions. Positive = overall portfolio gains.\',\n\n    positions.POSITION_COUNT AS COUNT(DISTINCT POSITION_ID)\n      COMMENT = \'Number of distinct portfolio positions\',\n\n    positions.AVG_POSITION_VALUE AS AVG(positions.MARKET_VALUE)\n      COMMENT = \'Average market value per position\',\n\n    trades.TRADE_COUNT AS COUNT(DISTINCT TRADE_ID)\n      COMMENT = \'Number of trade executions\',\n\n    trades.TOTAL_TRADE_VOLUME AS SUM(trades.TRADE_QUANTITY * trades.TRADE_PRICE)\n      COMMENT = \'Total dollar volume of trades (quantity * price summed across all trades)\'\n  )\n\n  COMMENT = \'Strive Capital - Financial analytics semantic view covering clients, positions, and trades\'\n\n  AI_SQL_GENERATION \'\n    -- Business rules for SQL generation:\n    -- 1. When asked about "top clients" or "biggest clients", rank by AUM unless otherwise specified.\n    -- 2. When asked about portfolio performance, use UNREALIZED_PNL. Positive = gains.\n    -- 3. Default time filter: if no date specified, include all available data.\n    -- 4. "Active clients" means STATUS = \'\'ACTIVE\'\'.\n    -- 5. When asked about "recent trades", order by TRADE_DATE DESC and limit to last 7 days unless specified.\n    -- 6. Trade volume = QUANTITY * PRICE. Always compute as dollar volume, not share count.\n    -- 7. For region breakdowns, use the CLIENTS.REGION column (North America, EMEA, APJ).\n    -- 8. When computing concentration, use MARKET_VALUE / total portfolio MARKET_VALUE.\n  \'\n\n  AI_VERIFIED_QUERIES (\n    top_clients_by_aum AS (\n      QUESTION \'What are our top 5 clients by AUM?\'\n      SQL \'SELECT CLIENT_NAME, ACCOUNT_TYPE, REGION, AUM, RISK_PROFILE\n      FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.CLIENTS\n      WHERE STATUS = \'\'ACTIVE\'\'\n      ORDER BY AUM DESC\n      LIMIT 5\'\n    ),\n\n    portfolio_value_by_sector AS (\n      QUESTION \'What is the total portfolio value by sector?\'\n      SQL \'SELECT p.SECTOR, SUM(p.MARKET_VALUE) AS TOTAL_VALUE, SUM(p.UNREALIZED_PNL) AS TOTAL_PNL\n      FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.POSITIONS p\n      GROUP BY p.SECTOR\n      ORDER BY TOTAL_VALUE DESC\'\n    ),\n\n    recent_large_buy_trades AS (\n      QUESTION \'Show me recent buy trades over $1M in value\'\n      SQL \'SELECT c.CLIENT_NAME, t.SYMBOL, t.QUANTITY, t.PRICE, (t.QUANTITY * t.PRICE) AS TRADE_VALUE, t.TRADE_DATE, t.NOTES\n      FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.TRADES t\n      JOIN COWORK_ENTERPRISE_DEMO.ANALYTICS.CLIENTS c ON t.CLIENT_ID = c.CLIENT_ID\n      WHERE t.TRADE_TYPE = \'\'BUY\'\' AND (t.QUANTITY * t.PRICE) > 1000000\n      ORDER BY t.TRADE_DATE DESC\'\n    ),\n\n    clients_highest_unrealized_gains AS (\n      QUESTION \'Which clients have the highest unrealized gains?\'\n      SQL \'SELECT c.CLIENT_NAME, c.ACCOUNT_TYPE, SUM(p.UNREALIZED_PNL) AS TOTAL_UNREALIZED_PNL, SUM(p.MARKET_VALUE) AS TOTAL_PORTFOLIO_VALUE\n      FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.CLIENTS c\n      JOIN COWORK_ENTERPRISE_DEMO.ANALYTICS.POSITIONS p ON c.CLIENT_ID = p.CLIENT_ID\n      GROUP BY c.CLIENT_NAME, c.ACCOUNT_TYPE\n      ORDER BY TOTAL_UNREALIZED_PNL DESC\'\n    ),\n\n    aum_breakdown_by_region AS (\n      QUESTION \'What is our AUM breakdown by region?\'\n      SQL \'SELECT REGION, COUNT(*) AS CLIENT_COUNT, SUM(AUM) AS TOTAL_AUM, AVG(AUM) AS AVG_AUM\n      FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.CLIENTS\n      WHERE STATUS = \'\'ACTIVE\'\'\n      GROUP BY REGION\n      ORDER BY TOTAL_AUM DESC\'\n    ),\n\n    tech_sector_exposure AS (\n      QUESTION \'Show me the technology sector exposure across all clients\'\n      SQL \'SELECT c.CLIENT_NAME, p.SYMBOL, p.QUANTITY, p.MARKET_VALUE, p.UNREALIZED_PNL\n      FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.POSITIONS p\n      JOIN COWORK_ENTERPRISE_DEMO.ANALYTICS.CLIENTS c ON p.CLIENT_ID = c.CLIENT_ID\n      WHERE p.SECTOR = \'\'Technology\'\'\n      ORDER BY p.MARKET_VALUE DESC\'\n    )\n  );\n\nSELECT \'Semantic view DEMO_SV created successfully\' AS STATUS;',
    'CreateCortexSearchService': "CREATE OR REPLACE CORTEX SEARCH SERVICE COWORK_ENTERPRISE_DEMO.AGENTS.DEMO_SEARCH\n  ON CONTENT\n  ATTRIBUTES TITLE, AUTHOR, CATEGORY, REGION, SYMBOLS_MENTIONED\n  WAREHOUSE = COWORK_ENTERPRISE_DEMO_WH\n  TARGET_LAG = '1 hour'\n  COMMENT = 'Search service over Strive Capital research notes, market commentary, and compliance reports'\nAS (\n  SELECT\n    NOTE_ID,\n    TITLE,\n    CONTENT,\n    AUTHOR,\n    CATEGORY,\n    REGION,\n    SYMBOLS_MENTIONED,\n    PUBLISHED_DATE\n  FROM COWORK_ENTERPRISE_DEMO.ANALYTICS.RESEARCH_NOTES\n);\n\nSELECT 'Cortex Search service DEMO_SEARCH created' AS STATUS;",
    'TestAgent': '-- Test 1: Client ranking (uses Cortex Analyst → semantic view → SQL)\nSELECT\n  TRY_PARSE_JSON(\n    SNOWFLAKE.CORTEX.DATA_AGENT_RUN(\n      \'COWORK_ENTERPRISE_DEMO.AGENTS.DEMO_AGENT\',\n      $${\n        "messages": [\n          {\n            "role": "user",\n            "content": [\n              { "type": "text", "text": "Who are our top 5 clients by AUM and what regions are they in?" }\n            ]\n          }\n        ],\n        "stream": false\n      }$$\n    )\n  ) AS resp;',
}


# Prod-promotion target (Notebook 06) - a separate, prod-scoped schema in the demo DB.
AGENT_PROD = f"{DB}.AGENTS_PROD.DEMO_AGENT"

# Single source of truth for the agent specification (agent-as-code). Both the dev
# agent (NB03) and the promoted prod agent (NB06) are built from this same body, so
# the promotion demonstrably ships an identical spec.
AGENT_SPEC_BODY = '''models:
  orchestration: auto

orchestration:
  budget:
    seconds: 45
    tokens: 16000

instructions:
  response: |
    You are the Enterprise Demo Analyst. You help portfolio managers, relationship managers,
    and compliance officers understand client portfolios, trading activity, and market research.

    Guidelines:
    - Be concise and data-driven. Lead with numbers when available.
    - When showing financial data, format large numbers (e.g., $2.5B not $2500000000).
    - If a question spans both structured data (portfolios, trades) and unstructured data
      (research notes), use BOTH tools to provide a complete answer.
    - Always cite which data source your answer came from.
    - For compliance questions, flag any potential issues clearly.
  orchestration: |
    - For questions about client AUM, portfolio values, positions, or trades: use the Analyst tool.
    - For questions about market outlook, research opinions, or compliance reports: use the Search tool.
    - For questions that need both, use both tools.
  sample_questions:
    - question: "Who are our top 5 clients by AUM?"
    - question: "What is our total technology sector exposure?"
    - question: "Are there any compliance concerns I should know about?"
    - question: "Show me recent trades over $1M and the rationale behind them."

tools:
  - tool_spec:
      type: "cortex_analyst_text_to_sql"
      name: "nexus_analytics"
      description: "Query structured financial data including client accounts, portfolio positions, trade history, and business metrics. Use this for any question about numbers, rankings, aggregations, or trends."
  - tool_spec:
      type: "cortex_search"
      name: "nexus_research"
      description: "Search analyst research notes, market commentary, risk assessments, and compliance reports. Use this for qualitative insights, opinions, recommendations, and compliance flags."
  - tool_spec:
      type: "data_to_chart"
      name: "data_to_chart"
      description: "Generate visualizations from query results when the user asks for charts or visual breakdowns."

tool_resources:
  nexus_analytics:
    semantic_view: "COWORK_ENTERPRISE_DEMO.SEMANTIC.DEMO_SV"
    execution_environment:
      type: warehouse
      warehouse: "COWORK_ENTERPRISE_DEMO_WH"
  nexus_research:
    name: "COWORK_ENTERPRISE_DEMO.AGENTS.DEMO_SEARCH"
    max_results: "5"
'''

def create_agent_sql(fqn, comment):
    return ("CREATE OR REPLACE AGENT " + fqn + "\n"
            "  COMMENT = '" + comment + "'\n"
            "  PROFILE = '{\"display_name\": \"Enterprise Demo Analyst\", \"color\": \"blue\"}'\n"
            "  FROM SPECIFICATION\n$$\n" + AGENT_SPEC_BODY + "$$;")

# Continuous-improvement objects (Notebooks 05 + 07).
EVAL_TABLE = f"{DB}.AGENTS.EVAL_QUESTIONS"
EVAL_DATASET = f"{DB}.AGENTS.DEMO_AGENT_EVALSET"
EVAL_STAGE = f"{DB}.AGENTS.EVAL_CONFIG"
QUOTA = f"{DB}.AGENTS.DEMO_AGENT_QUOTA"
SHARED_BUDGET = f"{DB}.AGENTS.DEMO_TEAM_BUDGET"

# Agent GPA evaluation config (points at the agent + the registered dataset).
EVAL_YAML = ('evaluation:\n'
             '  agent_params:\n'
             f'    agent_name: "{AGENT}"\n'
             '    agent_type: "CORTEX AGENT"\n'
             '  run_params:\n'
             '    label: "Go-live gate"\n'
             '  source_metadata:\n'
             '    type: "dataset"\n'
             f'    dataset_name: "{EVAL_DATASET}"\n'
             'metrics:\n'
             '  - "answer_correctness"\n'
             '  - "logical_consistency"\n'
             '  - "tool_selection_accuracy"\n')

# Curated evaluation question bank. Ground truth is a plain-language rubric
# (answer_correctness) plus expected tool names (tool_selection_accuracy). Values
# are described, not hard-coded, because the sample data is synthetic.
def _gt(output, tools):
    inv = ",".join('{"tool_name": "' + t + '"}' for t in tools)
    return ("PARSE_JSON('" + '{"ground_truth_output": "' + output.replace("'", "''")
            + '", "ground_truth_invocations": [' + inv + "]}')")

EVAL_ROWS = [
    ("Who are our top 5 clients by AUM?",
     "Returns exactly five clients ranked by assets under management, largest first, with a value per client. Should read from the structured portfolio/client data, not research notes.",
     ["nexus_analytics"]),
    ("What is our total technology sector exposure?",
     "Gives a single aggregate exposure figure for the technology sector across positions, presented as a formatted currency amount. Derived from structured position data.",
     ["nexus_analytics"]),
    ("Are there any compliance concerns I should know about?",
     "Surfaces qualitative compliance flags/issues from the research and compliance notes and clearly identifies them as compliance concerns. Should draw on the research/search corpus, not fabricate numbers.",
     ["nexus_research"]),
    ("Summarize recent trades over $1M and the rationale behind them.",
     "Lists recent trades above $1M with amounts (from structured trade data) AND explains the rationale (from research notes), citing both sources. A complete answer uses both structured and unstructured data.",
     ["nexus_analytics", "nexus_research"]),
    ("What's the weather in Sydney today?",
     "States that weather is outside the agent's scope (portfolios, trades, research) and does not fabricate a forecast. A graceful refusal, not a hallucinated answer.",
     []),
    ("Show AUM by region.",
     "Returns assets under management broken down by client region, one row per region with a value, sourced from structured data.",
     ["nexus_analytics"]),
]

def eval_insert_sql():
    lines = [f"CREATE OR REPLACE TABLE {EVAL_TABLE} (",
             "  INPUT_QUERY VARCHAR,",
             "  GROUND_TRUTH VARIANT",
             ");", "", f"INSERT INTO {EVAL_TABLE} (INPUT_QUERY, GROUND_TRUTH)"]
    selects = []
    for q, out, tools in EVAL_ROWS:
        selects.append("  SELECT '" + q.replace("'", "''") + "', " + _gt(out, tools))
    return "\n".join(lines) + "\n" + "\nUNION ALL\n".join(selects) + ";"

# Improved spec (instruction-only change) used to demonstrate the optimize step
# in Notebook 07: add an efficiency rule to orchestration; tools are unchanged.
AGENT_SPEC_BODY_V2 = AGENT_SPEC_BODY.replace(
    "    - For questions that need both, use both tools.\n",
    "    - For questions that need both, use both tools.\n"
    "    - Prefer a single Analyst call for a purely numeric question; only add the Search tool\n"
    "      when the question is qualitative, compliance-related, or explicitly asks \"why\".\n"
    "    - Do not call the same tool twice for one question unless the user asks a follow-up.\n")

# =====================================================================
# NOTEBOOK 00 - LAB SETUP  (guide Phase 0, as build-the-sandbox)
# =====================================================================
n00 = [
 md(nb_header("Lab Setup", "00", "Build the Foundation (Phase 0)",
    ["Creates an **isolated lab role, database, and schemas** (`COWORK_ENTERPRISE_DEMO`) so nothing "
     "collides with existing objects on a shared account",
     "Creates an **XS warehouse** and grants the demo admin role focused privileges",
     "Enables **cross-region inference** (a safe no-op if already on)",
     "Loads **self-contained sample data** for a fictional buy-side firm, *Strive Capital* (clients, "
     "positions, trades, daily metrics, and unstructured research notes)",
     "Validates every table loaded and the account is ready to build on"],
    "This Is Phase 0",
    "🔹 In a real engagement, Phase 0 is to **confirm** the estate you already run — RBAC, network "
    "policies, MFA, masking, cross-region inference. There is no estate "
    "to confirm in a demo, so this notebook instead **builds a clean sandbox** you can safely tear down "
    "later (Notebook 08).\n\n"
    "**Run order:** 00 → 01 → 02 → 03 → 04 → 05 → 06 (dev→prod) → 07 (continuous improvement), then 08 "
    "(cleanup) last.",
    "10–15 minutes",
    ["`ACCOUNTADMIN` (or a role that can create databases, warehouses, and roles)",
     "Enterprise Edition (for later notebooks: Cortex AI Guardrails, masking)"])),
 md("## Step 1: Create the Lab Role\n\n"
    "🛠️ A dedicated role (`COWORK_ENTERPRISE_DEMO_ADMIN`) owns everything we build, so the whole demo "
    "can be granted and dropped as a unit — and nothing runs as `ACCOUNTADMIN` that doesn't have to."),
 sql("create_role", "Create Lab Role", INLINE["CreateRole"]),
 md("## Step 2: Create the Database & Schemas\n\n"
    "🛠️ Three schemas separate concerns: **ANALYTICS** (raw/gold tables), **SEMANTIC** (the governed "
    "semantic view), and **AGENTS** (the agent, search service, budgets). Ownership is transferred to "
    "the lab role so it can manage its own objects."),
 sql("create_db_schema", "Create Database & Schemas", """-- Database + 3 schemas (isolated demo namespace)
CREATE DATABASE IF NOT EXISTS COWORK_ENTERPRISE_DEMO COMMENT = 'CoWork Enterprise Demo - AI enterprise application';
CREATE SCHEMA IF NOT EXISTS COWORK_ENTERPRISE_DEMO.ANALYTICS COMMENT = 'Gold-layer analytical tables';
CREATE SCHEMA IF NOT EXISTS COWORK_ENTERPRISE_DEMO.SEMANTIC COMMENT = 'Semantic views and governed metrics';
CREATE SCHEMA IF NOT EXISTS COWORK_ENTERPRISE_DEMO.AGENTS COMMENT = 'Cortex Agents, Search services, budgets';
GRANT OWNERSHIP ON DATABASE COWORK_ENTERPRISE_DEMO TO ROLE COWORK_ENTERPRISE_DEMO_ADMIN COPY CURRENT GRANTS;
GRANT OWNERSHIP ON ALL SCHEMAS IN DATABASE COWORK_ENTERPRISE_DEMO TO ROLE COWORK_ENTERPRISE_DEMO_ADMIN COPY CURRENT GRANTS;
SELECT 'Database and schemas created' AS STATUS;"""),
 md("## Step 3: Create the Warehouse & Grant Privileges\n\n"
    "🛠️ An XS warehouse runs the demo's SQL (agent LLM reasoning is serverless and billed separately). "
    "The grants give the lab role exactly what it needs to create semantic views, search services, "
    "agents, and tables — nothing more.\n\n"
    "🔹 `SNOWFLAKE.CORTEX_USER` is the database role that entitles a role to call Cortex AI features."),
 sql("create_wh", "Create Warehouse", INLINE["CreateWH"]),
 sql("grant_privileges", "Grant Privileges", """-- Focused privileges for the demo admin role
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE COWORK_ENTERPRISE_DEMO_ADMIN;
GRANT CREATE SEMANTIC VIEW ON SCHEMA COWORK_ENTERPRISE_DEMO.SEMANTIC TO ROLE COWORK_ENTERPRISE_DEMO_ADMIN;
GRANT CREATE CORTEX SEARCH SERVICE ON SCHEMA COWORK_ENTERPRISE_DEMO.AGENTS TO ROLE COWORK_ENTERPRISE_DEMO_ADMIN;
GRANT CREATE AGENT ON SCHEMA COWORK_ENTERPRISE_DEMO.AGENTS TO ROLE COWORK_ENTERPRISE_DEMO_ADMIN;
GRANT CREATE TABLE ON SCHEMA COWORK_ENTERPRISE_DEMO.ANALYTICS TO ROLE COWORK_ENTERPRISE_DEMO_ADMIN;
GRANT CREATE VIEW ON SCHEMA COWORK_ENTERPRISE_DEMO.ANALYTICS TO ROLE COWORK_ENTERPRISE_DEMO_ADMIN;
SELECT 'Privileges granted' AS STATUS;"""),
 md("## Step 4: Enable Cross-Region Inference\n\n"
    "🔹 Cortex may route a request to an LLM hosted in another region. This account-level setting "
    "permits that (required for some models and for evaluations). It is a **safe no-op** if already set."),
 sql("enable_cross_region", "Enable Cross-Region Inference (no-op if already set)",
     INLINE["EnableCrossRegionInference"]),
 md("## Step 5: Load the Sample Data\n\n"
    "🛠️ Sets working context, then creates and loads the *Strive Capital* dataset: **clients, portfolio "
    "positions, recent trades, daily metrics** (structured) plus **research notes** (unstructured, for "
    "Cortex Search). This is the data every later notebook builds on."),
 sql("use_context", "Set Working Context", INLINE["UseNew"]),
 sql("create_tables", "Create Analytics Tables", INLINE["CreateTables"]),
 sql("load_clients", "Load Client Data", INLINE["LoadClientData"]),
 sql("load_positions", "Load Portfolio Positions", INLINE["LoadPortfolioPositions"]),
 sql("load_trades", "Load Recent Trades", INLINE["LoadRecentTrades"]),
 sql("load_metrics", "Load Daily Metrics", INLINE["LoadDailyMetrics"]),
 sql("load_research", "Create & Load Research Notes (unstructured)",
     INLINE["CreateUnstructuredData"]),
 md("## Step 6: Validate\n\n📌 Confirm every table loaded and cross-region inference is set before "
    "moving on — later notebooks assume this data exists."),
 sql("validate_setup", "Validate: Row Counts", INLINE["ValidateSetup"]),
 sql("sanity_check", "Sanity Check: Top Clients", INLINE["SanityCheck"]),
 sql("verify_cross_region", "Verify Cross-Region Inference",
     INLINE["VerifyCrossRegion"]),
 md(nb_complete("00",
    ["Lab role `COWORK_ENTERPRISE_DEMO_ADMIN` + database `COWORK_ENTERPRISE_DEMO` with ANALYTICS / "
     "SEMANTIC / AGENTS schemas",
     "XS warehouse `COWORK_ENTERPRISE_DEMO_WH` and focused grants",
     "Cross-region inference enabled",
     "*Strive Capital* sample data: clients, positions, trades, daily metrics, and research notes"],
    ["Everything lives under one database + role, so the demo is isolated on a shared account and "
     "trivially removable (Notebook 08).",
     "The data layer is the foundation — semantic-view and agent quality depend on it."],
    "Continue to **Notebook 01 — Build the Context Layer**: define a governed semantic view over this "
    "data and a Cortex Search service over the research notes.")),
]


# =====================================================================
# NOTEBOOK 01 - CONTEXT LAYER  (Phase 1)
# =====================================================================
n01 = [
 md(nb_header("Context Layer", "01", "Build the Context Layer (Phase 1)",
    ["Creates a **governed semantic view** — logical tables, relationships, dimensions, metrics, and "
     "verified queries — as the single source of truth for structured questions",
     "Creates a **Cortex Search service** over the unstructured research notes (RAG)",
     "**Validates** the semantic view returns correct numbers *before* any agent is built on it"],
    "the Context Layer Matters",
    "🔹 The context layer is the **single biggest driver of answer quality**. Without it, an AI agent "
    "guesses at column meanings and joins. With it:\n\n"
    "- The agent **knows** `AUM` means Assets Under Management, not a column to guess at\n"
    "- The agent **knows** how to join CLIENTS → POSITIONS → TRADES\n"
    "- **Verified queries** teach the agent the *correct* SQL for common questions\n"
    "- Data-layer governance (grants, masking) flows through automatically\n\n"
    "> **Documentation:** [Semantic Views](https://docs.snowflake.com/en/user-guide/views-semantic/overview) "
    "| [Cortex Search](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-search/cortex-search-overview)",
    "15–20 minutes",
    ["Notebook 00 complete (`COWORK_ENTERPRISE_DEMO` with analytics tables loaded)"])),
 md("## Step 1: Set Context\n\n🛠️ Point the session at the demo role, database, `SEMANTIC` schema, and "
    "warehouse before creating objects."),
 sql("set_context", "Set Context",
     f"USE ROLE {ADMIN};\nUSE DATABASE {DB};\nUSE SCHEMA SEMANTIC;\nUSE WAREHOUSE {WH};"),
 md("### 🔹 Two Ways to Build: SQL vs. the UI\n\n"
    "We author the semantic view and search services in **SQL** here — full control over every attribute, "
    "relationship, and metric, and it's reproducible and version-controllable (this whole guide is "
    "generated from code). You can also build both in **Snowsight**:\n\n"
    "| Object | UI path | What it gives you |\n"
    "|---|---|---|\n"
    "| Semantic view | AI & ML → Cortex Analyst → **Create with Autopilot** | Auto-proposes dimensions, "
    "metrics, and relationships from your tables, which you then refine |\n"
    "| Cortex Search service | AI & ML → Cortex Search → **Create** | Guided wizard for source table, "
    "search column, and attributes |\n\n"
    "🔹 **Autopilot** is great for a fast first draft; we use SQL so every component is explicit and you "
    "understand exactly what you're shipping."),
 md("## Step 2: Enable Fuzzy Matching on `CLIENT_NAME`\n\n"
    "🛠️ `CLIENT_NAME` is a **high-cardinality identifier** column — users will type *\"Acme\"* when the "
    "stored value is *\"Acme Capital Partners LLC\"*. We create a **Cortex Search service over its "
    "distinct values** so Cortex Analyst can resolve those fuzzy references to the exact literal it "
    "needs in the `WHERE` clause. (Step 3 links this service to the `CLIENT_NAME` dimension.)\n\n"
    "🔹 **Why this column and not others:** use a search service for high-cardinality identifier text "
    "(names, SKUs). For low-cardinality categoricals like `REGION` or `SECTOR` (a handful of values), "
    "sample values are better; and never point a search service at numeric/date columns or paragraph "
    "free text.\n\n"
    "> **Documentation:** [Improve literal search for Cortex Analyst]"
    "(https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst/cortex-analyst-search-integration)"),
 sql("create_client_search", "Create Cortex Search Service on CLIENT_NAME (fuzzy matching)",
     f"CREATE OR REPLACE CORTEX SEARCH SERVICE {SEARCH_CLIENT}\n"
     "  ON CLIENT_NAME\n"
     f"  WAREHOUSE = {WH}\n"
     "  TARGET_LAG = '1 hour'\n"
     "  COMMENT = 'Fuzzy literal matching for client names, linked to the DEMO_SV CLIENT_NAME dimension'\n"
     f"AS (\n  SELECT DISTINCT CLIENT_NAME FROM {DB}.ANALYTICS.CLIENTS\n);"),
 md("## Step 3: Create the Semantic View\n\n"
    "🛠️ This defines the meaning on top of the raw tables:\n\n"
    "- **Logical tables**: CLIENTS, POSITIONS, TRADES\n"
    "- **Relationships**: how they join (on `CLIENT_ID`)\n"
    "- **Dimensions**: client attributes, region, sector, time\n"
    "- **Metrics**: AUM, portfolio value, unrealized PnL, trade volume\n"
    "- **Verified queries**: worked examples that teach the agent correct SQL patterns\n\n"
    "🔹 The `CLIENT_NAME` dimension is defined `WITH CORTEX SEARCH SERVICE ...`, wiring in the fuzzy "
    "matching from Step 2. A single Cortex Analyst call operates against **one** semantic view, so keep "
    "tightly-related tables together (as here) and split genuinely distinct domains into separate views."),
 sql("create_semantic_view", "Create Semantic View",
     INLINE["CreateSemanticView"]),
 md("### 🔹 Best Practices: What Makes a Semantic View Accurate\n\n"
    "Snowflake's [semantic-view best practices]"
    "(https://www.snowflake.com/en/developers/guides/best-practices-semantic-views-cortex-analyst/) "
    "distill to a few high-leverage rules — the demo view above follows them:\n\n"
    "- **Descriptions are the #1 element (required, not optional).** LLMs can't infer proprietary "
    "terms, so every table and column needs a clear, business-language description that spells out "
    "abbreviations (e.g. *\"CSAT: customer satisfaction, 1–5; also called KPI_1 in legacy systems\"*), "
    "not just `\"score\"`.\n"
    "- **Relationships must be explicit.** Cortex Analyst **will not join** tables unless the "
    "relationship is defined. (Many-to-many isn't directly supported — bridge it with a shared "
    "dimension table.)\n"
    "- **Define metrics and filters wherever possible.** They're commonly underused but are critical "
    "for accuracy — a metric like `total_revenue = SUM(unit_price*quantity)` stops the model from "
    "re-deriving business math each time.\n"
    "- **Verified queries are the biggest accuracy lever.** Start with **10–20** covering your most "
    "common questions and grow from real usage. They only load when a question is *semantically "
    "similar*, so they rarely add token cost — and they seed better metric/filter/description suggestions.\n"
    "- **Think like the end user.** Model by business domain and terminology, not table structure. "
    "Include only columns users will actually ask about.\n"
    "- **Synonyms are no longer recommended** with frontier models — reserve them for genuinely unique "
    "or industry-specific terms the model won't know."),
 md("### 🔹 Best Practices: Custom Instructions (two distinct types)\n\n"
    "The most common custom-instruction mistake is mixing up the two types:\n\n"
    "| Type | Applies to | Use for |\n"
    "|---|---|---|\n"
    "| **`sql_generation`** | Every generated query | Business SQL logic, default filters, fiscal-year "
    "definitions, data quirks (e.g. *\"fiscal year starts Feb 1\"*, *\"always use net_revenue\"*) |\n"
    "| **`question_categorization`** | Question understanding | When to **reject** questions (e.g. "
    "salaries, profanity) or **ask a clarifying question** (e.g. define *\"active users\"*) |\n\n"
    "📌 Be **specific** (*\"if no date filter is provided, default to the last year\"* — not *\"filter by "
    "last year\"*) and **always test after adding instructions** (the Analyst playground is ideal)."),
 md("### 📐 Design Note: One Semantic View vs. Many\n\n"
    "`DEMO_SV` covers one domain (clients, positions, trades — all related, all joined on `CLIENT_ID`). "
    "In real deployments, *\"how many semantic views?\"* comes up fast.\n\n"
    "**Key constraint:** a single Cortex Analyst call operates against **one** semantic view. The agent "
    "can't generate a SQL JOIN across two separate SVs — but it *can* call them sequentially and "
    "synthesize the results.\n\n"
    "| Situation | Recommendation |\n"
    "|---|---|\n"
    "| Tables naturally join within one domain | One SV — keep it together |\n"
    "| ~100+ columns | Split by domain; accuracy degrades above the soft limit |\n"
    "| Distinct domains (Sales, HR, Finance) | Separate SVs + one Cortex Analyst tool per SV on the agent |\n"
    "| Cross-domain JOIN needed at query time | Unified SV with RELATIONSHIPS (or Composable SVs) |\n\n"
    "🔹 **`DEMO_SV` is the right scope:** CLIENTS / POSITIONS / TRADES are tightly related and questions "
    "span all three. A separate HR or Compliance domain would warrant its own SV, with the agent given "
    "one Analyst tool per SV. **Field note:** the ~100-column soft limit is a useful forcing function — "
    "it pushes domain decomposition that also makes the agent more accurate."),
 md("### 🧠 Going Deeper: Ontology & Knowledge Graphs\n\n"
    "A semantic view defines meaning for **one domain**. When an enterprise has many interconnected "
    "domains and the AI must reason *across* them, **Ontology on Snowflake** extends the idea with a "
    "formal ontology (shared vocabulary + business logic across domains), a **knowledge graph** (entity "
    "relationships spanning systems), and agent-based reasoning for multi-hop questions.\n\n"
    "📌 Relevant when customers say *\"our AI gives inconsistent answers depending on which team asks\"* "
    "or *\"we need explainable AI that can trace its reasoning\"* (often evaluated against Palantir / "
    "Neo4j). **Not required for this guide** — but a pattern worth knowing.\n\n"
    "> **Reference:** [Ontology on Snowflake (GitHub)]"
    "(https://github.com/Snowflake-Labs/ontology-on-snowflake) · [Ontology Stack Builder CoCo skill]"
    "(https://github.com/Snowflake-Labs/cortex-code-skills/tree/main/skills/ontology-stack-builder)"),
 md("## Step 4: Create the Cortex Search Service (research notes)\n\n"
    "🛠️ This is a **second, different** search service — over the unstructured research notes for **RAG** "
    "(Retrieval-Augmented Generation). It lets the agent answer qualitative questions (analyst opinions, "
    "risk assessments, compliance reports) that no SQL query could.\n\n"
    "🔹 Note the contrast with Step 2: **Step 2** indexes a structured *identifier column* for fuzzy "
    "literal matching; **this** indexes *document bodies* for semantic retrieval. Both are Cortex Search, "
    "used for different jobs."),
 sql("create_search_service", "Create Cortex Search Service",
     INLINE["CreateCortexSearchService"]),
 md("## Step 5: Validate (the pre-agent gate)\n\n"
    "📌 **Test the semantic view directly with `SEMANTIC_VIEW()` before building the agent.** If the "
    "view returns wrong numbers, the agent will too — catch it here, not in front of a business user."),
 sql("test_sv_clients", "Verify: Top Portfolios via SEMANTIC_VIEW()",
     f"SELECT * FROM SEMANTIC_VIEW(\n  {SV}\n  DIMENSIONS CLIENTS.CLIENT_NAME\n"
     f"  METRICS POSITIONS.TOTAL_PORTFOLIO_VALUE\n)\nORDER BY TOTAL_PORTFOLIO_VALUE DESC\nLIMIT 5;"),
 sql("test_sv_region", "Verify: AUM by Region via SEMANTIC_VIEW()",
     f"SELECT * FROM SEMANTIC_VIEW(\n  {SV}\n  DIMENSIONS CLIENTS.REGION\n"
     f"  METRICS CLIENTS.TOTAL_AUM\n)\nORDER BY TOTAL_AUM DESC;"),
 sql("show_search", "Verify: Search Service Exists",
     f"SHOW CORTEX SEARCH SERVICES IN SCHEMA {DB}.AGENTS;"),
 md("## 🧠 Common Pitfalls & Production Checklist\n\n"
    "From the field, the semantic-view mistakes that most hurt accuracy:\n\n"
    "| Pitfall | Fix |\n"
    "|---|---|\n"
    "| **Undefined scope** (\"just one more table\") | Set crisp success criteria and boundaries upfront |\n"
    "| **Starting too big** (whole warehouse day one) | Start with **5–10 tables**, one domain, one use case |\n"
    "| **Skipping verified queries** | Add **10–20** covering frequent questions from the start |\n"
    "| **Wrong first use case** (Finance/Legal, ~100% bar) | Begin with lower-stakes domains (Sales/Marketing) |\n\n"
    "**Production-ready checklist for a semantic view:**\n\n"
    "- ✅ Every table and column has a clear business description; abbreviations explained\n"
    "- ✅ 10–20 verified queries covering common questions\n"
    "- ✅ Metrics for reusable calculations; filters for common conditions\n"
    "- ✅ `sql_generation` custom instructions for business-specific logic\n"
    "- ✅ Cortex Search on high-cardinality identifier columns\n"
    "- ✅ An evaluation set + measured SQL accuracy before deployment (see Notebook 05)\n"
    "- ✅ A weekly loop to add verified queries from real usage (see Notebook 07)\n\n"
    "> **Reference:** [Best Practices for Semantic Views]"
    "(https://www.snowflake.com/en/developers/guides/best-practices-semantic-views-cortex-analyst/)"
    " · [Evaluation tool](https://github.com/Snowflake-Labs/semantic-model-generator/)"),
 md(nb_complete("01",
    [f"Semantic view `{SV}` — logical tables, relationships, dimensions, metrics, verified queries",
     f"Cortex Search service `{SEARCH}` over the research notes",
     f"Cortex Search service `{SEARCH_CLIENT}` on `CLIENT_NAME` for fuzzy literal matching",
     "Validation that the view returns correct numbers"],
    ["The semantic layer gives the agent *understanding*, not just *access*.",
     "Verified queries are like unit tests for your AI — they prove the agent generates correct SQL "
     "for known questions.",
     "Always validate the view directly before layering an agent on top."],
    "Continue to **Notebook 02 — Govern AI Access**: create a CoWork-only consumer role, grant the "
    "four layers of access, and prove masking policies apply to agent output automatically.")),
]

# =====================================================================
# NOTEBOOK 02 - GOVERN AI ACCESS  (Phase 2)
# =====================================================================
n02 = [
 md(nb_header("Govern AI Access", "02", "Govern AI Access (Phase 2)",
    ["Creates a **CoWork-only consumer role** for business users",
     "Grants it the **four independent layers** of access an agent needs at runtime",
     "Attaches an **`AI_REDACT` masking policy** and proves it applies to agent output automatically"],
    "Governance Is Inherited, Not Configured Separately",
    "🔹 **CoWork has no separate security layer.** Every query runs as the authenticated user, "
    "inheriting their role, masking, and row-access policies. Getting RBAC right *is* your CoWork "
    "security posture.\n\n"
    "🔹 Cortex Agents run with **caller's rights** — each tool uses the *calling user's* privileges, "
    "not the owner's. So the consumer role needs access to every object the agent touches:\n\n"
    "| Layer | What it grants | Privilege |\n"
    "|---|---|---|\n"
    "| 1. Platform | Can call Cortex + use compute | `CORTEX_USER` + `USAGE` on DB/WH |\n"
    "| 2. Which agent | See/use the specific agent | `USAGE ON AGENT` (granted in NB03) |\n"
    "| 3. Tool/resource | The search service + semantic view | `USAGE` on each |\n"
    "| 4. Data | The underlying tables | `SELECT` (+ masking/row-access still applies) |\n\n"
    "> **Documentation:** [Agent access control]"
    "(https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents#access-control-requirements)",
    "15–20 minutes",
    ["Notebook 01 complete (semantic view + search service created)"])),
 md("## Step 1: Set Context"),
 sql("set_context", "Set Context",
     f"USE ROLE ACCOUNTADMIN;\nUSE DATABASE {DB};\nUSE WAREHOUSE {WH};"),
 md("## Step 2: Create the CoWork-Only Role + Four-Layer Grants\n\n"
    "🛠️ One role, `COWORK_ENTERPRISE_DEMO_SI_USER`, gets layers 1, 3, and 4 now. Layer 2 "
    "(`USAGE ON AGENT`) is deferred to Notebook 03 because the agent doesn't exist yet.\n\n"
    "🔹 Pairing this role with `ALLOWED_INTERFACES = ('SNOWFLAKE_INTELLIGENCE')` on the user object "
    "confines a business user to the CoWork chat — no worksheets, no SQL — we provision exactly such a user at go-live (NB05)."),
 sql("four_layer_grants", "Create SI-only Role + Four-Layer Grants (agent grant deferred to NB03)",
     """USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS COWORK_ENTERPRISE_DEMO_SI_USER COMMENT = 'Business users who access the demo agent via CoWork only';
-- Tier 1: platform entitlement (can use Cortex + compute)
GRANT USAGE ON DATABASE COWORK_ENTERPRISE_DEMO TO ROLE COWORK_ENTERPRISE_DEMO_SI_USER;
GRANT USAGE ON WAREHOUSE COWORK_ENTERPRISE_DEMO_WH TO ROLE COWORK_ENTERPRISE_DEMO_SI_USER;
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE COWORK_ENTERPRISE_DEMO_SI_USER;
-- Tier 3: tool / resource access (search service + semantic view)
GRANT USAGE ON SCHEMA COWORK_ENTERPRISE_DEMO.AGENTS TO ROLE COWORK_ENTERPRISE_DEMO_SI_USER;
GRANT USAGE ON CORTEX SEARCH SERVICE COWORK_ENTERPRISE_DEMO.AGENTS.DEMO_SEARCH TO ROLE COWORK_ENTERPRISE_DEMO_SI_USER;
GRANT USAGE ON CORTEX SEARCH SERVICE COWORK_ENTERPRISE_DEMO.AGENTS.DEMO_CLIENT_SEARCH TO ROLE COWORK_ENTERPRISE_DEMO_SI_USER;
GRANT USAGE ON SCHEMA COWORK_ENTERPRISE_DEMO.SEMANTIC TO ROLE COWORK_ENTERPRISE_DEMO_SI_USER;
GRANT USAGE ON SEMANTIC VIEW COWORK_ENTERPRISE_DEMO.SEMANTIC.DEMO_SV TO ROLE COWORK_ENTERPRISE_DEMO_SI_USER;
-- Tier 4: data access (masking / row-access still applies automatically)
GRANT USAGE ON SCHEMA COWORK_ENTERPRISE_DEMO.ANALYTICS TO ROLE COWORK_ENTERPRISE_DEMO_SI_USER;
GRANT SELECT ON ALL TABLES IN SCHEMA COWORK_ENTERPRISE_DEMO.ANALYTICS TO ROLE COWORK_ENTERPRISE_DEMO_SI_USER;
-- Tier 2 (USAGE ON AGENT) is granted in Notebook 03, after the agent exists.
SELECT 'SI role created with tiers 1, 3, 4' AS STATUS;"""),
 md("### 📌 Reference only — do NOT run on a shared account\n"
    "For a controlled enterprise rollout you would restrict Cortex to intended roles. We skip this here "
    "because `CORTEX_USER` is granted to PUBLIC and shared with other teams.\n\n"
    "```sql\n"
    "REVOKE DATABASE ROLE SNOWFLAKE.CORTEX_USER FROM ROLE PUBLIC;\n"
    f"GRANT DATABASE ROLE SNOWFLAKE.CORTEX_AGENT_USER TO ROLE {SIUSER};\n"
    "```\n"
    "🔹 `CORTEX_AGENT_USER` grants only the Cortex Agents API (enough for CoWork), not every Cortex feature."),
 md("### 🔹 What the Agent's SQL Can Reach (and How to Scope It)\n\n"
    "Since **April 2026**, Cortex Agents generate SQL **directly** rather than delegating to a separate "
    "Analyst service. Practically:\n\n"
    "- **Can access:** any table the **caller's role** can `SELECT` — not only the tables in the semantic view.\n"
    "- **Still constrained by:** RBAC (no `SELECT`, no data), the semantic view (dimensions / metrics / "
    "verified queries steer the generated SQL), and orchestration instructions.\n\n"
    "📌 **For strict scoping** (agent may touch *only* semantic-view tables), grant the consumer role "
    "`SELECT` on **just those tables** — not broad schema-level `SELECT` — and optionally add an "
    "orchestration instruction: *\"Only query tables defined in the semantic view.\"* The `SI_USER` role "
    "here is scoped to the demo schema; tighten it to specific tables for a locked-down rollout.\n\n"
    "> **Reference:** [Cortex Agents]"
    "(https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents) — see the April 2026 "
    "SQL-generation release note."),
 md("## Step 3: Enforce PII at the Data Layer (`AI_REDACT`)\n\n"
    "🛠️ Attach a masking policy that redacts email for non-privileged roles. Because governance is "
    "inherited, **any agent answer that surfaces this column is masked the same way**.\n\n"
    "📌 **Enforce PII at the data layer, never in prompt instructions** — a prompt rule can be talked "
    "around; a masking policy cannot. `AI_REDACT` detects and redacts sensitive entities (here, EMAIL)."),
 sql("create_masking_policy", "Create AI_REDACT Masking Policy",
     f"CREATE MASKING POLICY IF NOT EXISTS {DB}.ANALYTICS.EMAIL_REDACT AS (val STRING)\n"
     f"  RETURNS STRING ->\n  CASE\n"
     f"    WHEN CURRENT_ROLE() IN ('{ADMIN}','ACCOUNTADMIN') THEN val\n"
     f"    ELSE AI_REDACT(val, ['EMAIL'])\n  END;\n\n"
     f"ALTER TABLE {DB}.ANALYTICS.CLIENTS\n"
     f"  MODIFY COLUMN EMAIL SET MASKING POLICY {DB}.ANALYTICS.EMAIL_REDACT;\n\n"
     "SELECT 'Masking policy applied to CLIENTS.EMAIL' AS STATUS;"),
 md("### 📌 Why a Masking Policy — Not Prompt Instructions\n\n"
    "A common question: *\"Can't I just tell the agent not to show PII in its instructions?\"* **No — "
    "orchestration instructions are not a security boundary.** They steer the LLM but aren't guaranteed "
    "under every input; a creative prompt can talk around them. Enforce PII at the **data layer**, where "
    "the agent's SQL only ever sees masked values:\n\n"
    "| Layer | What it does | Bypassable by a prompt? |\n"
    "|---|---|---|\n"
    "| Orchestration instruction (\"don't show PII\") | LLM guidance only | **Yes** |\n"
    "| RBAC (role can't `SELECT` the column) | Engine-enforced | **No** |\n"
    "| Dynamic Data Masking (`AI_REDACT`) | Redacts at the data layer before results return | **No** |\n\n"
    "🔹 That's why the policy above lives on the column, not in the agent spec — the agent never receives "
    "the raw value, no matter what the user asks."),
 md("## Step 4: Verify\n\n📌 Confirm the role has the expected grants and the masking policy is active."),
 sql("verify_grants", "Verify: Grants on SI Role",
     f"SHOW GRANTS TO ROLE {SIUSER};"),
 sql("verify_masking", "Verify: Masking Policy Present",
     f"SELECT EMAIL FROM {DB}.ANALYTICS.CLIENTS LIMIT 5;"),
 md(nb_complete("02",
    [f"CoWork-only role `{SIUSER}` with the four-layer access model (agent grant follows in NB03)",
     f"`AI_REDACT` masking policy on `CLIENTS.EMAIL`, applied at the data layer"],
    ["CoWork security = your RBAC. There is no separate AI security layer to configure.",
     "Agents run with caller's rights, so grant the consumer role every object the agent touches.",
     "Masking and row-access policies flow through to agent output automatically — enforce PII in the "
     "data, not the prompt."],
    "Continue to **Notebook 03 — Build & Harden the Agent**: create the agent from a specification, "
    "grant the final access layer, and confirm account guardrails.")),
]

# =====================================================================
# NOTEBOOK 03 - BUILD & HARDEN THE AGENT  (Phase 3)
# =====================================================================
mcp_md = (
 "## MCP governance (illustrative - external OAuth required)\n"
 "If the agent needs to take actions in external systems (e.g. create a Jira ticket), connect via a "
 "governed MCP server. This needs an external OAuth app, so it is shown for reference and **not run** here.\n\n"
 "```sql\n"
 "CREATE API INTEGRATION demo_mcp_integration\n"
 "  API_PROVIDER = external_mcp\n"
 "  API_ALLOWED_PREFIXES = ('https://mcp.example.com')\n"
 "  API_USER_AUTHENTICATION = (TYPE = OAUTH_DYNAMIC_CLIENT,\n"
 "    OAUTH_RESOURCE_URL = 'https://mcp.example.com/v1/mcp')\n"
 "  ENABLED = TRUE;\n\n"
 f"CREATE EXTERNAL MCP SERVER {DB}.AGENTS.DEMO_MCP\n"
 "  WITH DISPLAY_NAME = 'Demo MCP'\n"
 "  URL = 'https://mcp.example.com/v1/mcp'\n"
 "  API_INTEGRATION = demo_mcp_integration;\n\n"
 f"GRANT USAGE ON EXTERNAL MCP SERVER {DB}.AGENTS.DEMO_MCP TO ROLE {SIUSER};\n\n"
 "-- Governance: USAGE controls who can connect; actions are per-user OAuth scoped;\n"
 "-- every tool call is logged in Account Usage. Kill switch:\n"
 "ALTER API INTEGRATION demo_mcp_integration SET ENABLED = FALSE;\n"
 "```\n\n"
 "**Available connectors** (Snowflake-hosted proxy endpoints — Snowflake handles the MCP protocol and "
 "OAuth token management):\n\n"
 "| Connector | Auth | Setup |\n"
 "|---|---|---|\n"
 "| Atlassian (Jira/Confluence), Glean, Linear | Dynamic client registration | Easiest — no manual OAuth app |\n"
 "| GitHub, Salesforce | Standard OAuth | Create an OAuth / connected app |\n"
 "| Gmail, Google Drive/Calendar, Slack | Standard OAuth | Create the provider OAuth app (or one-click Browse Connectors on Snowhouse) |\n"
 "| Custom | OAuth2 (manual) | Any MCP endpoint |\n\n"
 "**MCP security model:**\n\n"
 "| Concern | How Snowflake handles it |\n"
 "|---|---|\n"
 "| Who can connect? | `USAGE` on the MCP server object — RBAC controlled |\n"
 "| What data leaves Snowflake? | Only the tool-call request + response — not raw table data |\n"
 "| Credentials | OAuth tokens managed by Snowflake, per-user, auto-rotating |\n"
 "| Audit | Every MCP tool call logged in Account Usage |\n"
 "| Kill switch | `ALTER API INTEGRATION ... SET ENABLED = FALSE` revokes all tokens instantly |\n\n"
 "> **Documentation:** [MCP Connectors — key considerations]"
 "(https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-mcp-connectors)")
n03 = [
 md(nb_header("Build & Harden the Agent", "03", "Build & Harden the Agent (Phase 3)",
    ["Creates a **Cortex Agent** from a YAML **specification** (agent-as-code)",
     "Wires it to the semantic view (structured) + Cortex Search (unstructured) with precise **tool "
     "descriptions**",
     "Grants the final access layer (**`USAGE ON AGENT`**) to the consumer role",
     "Tests the agent with `DATA_AGENT_RUN` and confirms account **guardrails** + the **audit trail**"],
    "Tool Descriptions Are the #1 Lever",
    "🔹 A **Cortex Agent** orchestrates across tools to answer questions: it **plans** (interprets "
    "intent), **selects a tool** (Analyst for SQL, Search for RAG), **reflects**, and **responds** with "
    "a grounded answer.\n\n"
    "The agent chooses tools by reading their **descriptions** — so clear, specific descriptions "
    "(what the tool does, what data, *when to use / when not to use*) matter more than any other "
    "single setting. Keep agents **narrow** (one clear purpose); narrow agents outperform catch-all "
    "agents.\n\n"
    "**Agent anatomy** (defined in the `FROM SPECIFICATION` YAML):\n\n"
    "| Component | What it does |\n"
    "|---|---|\n"
    "| `models` | The LLM that reasons (`auto` = best available) |\n"
    "| `orchestration.budget` | Per-request time/token cap — a cost + latency guardrail |\n"
    "| `instructions.response` | Tone/format of answers |\n"
    "| `instructions.orchestration` | **When to use which tool** |\n"
    "| `tools` + `tool_resources` | The tools and the objects they point at |\n\n"
    "> **Documentation:** [Cortex Agents]"
    "(https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)",
    "20–25 minutes",
    ["Notebook 02 complete (consumer role + masking in place)"])),
 md("## Step 1: Set Context"),
 sql("set_context", "Set Context",
     f"USE ROLE {ADMIN};\nUSE DATABASE {DB};\nUSE SCHEMA AGENTS;\nUSE WAREHOUSE {WH};"),
 md("## Step 2: Create the Agent (from specification)\n\n"
    "🛠️ `CREATE OR REPLACE AGENT ... FROM SPECIFICATION` defines the agent as code. Note two things in "
    "the spec:\n\n"
    "🔹 **`tool_resources.execution_environment`** — agents are **serverless**; they do *not* inherit "
    "your session's `USE WAREHOUSE`. You must name the warehouse the generated SQL runs on, right in "
    "the spec, so the agent works when called from CoWork or the REST API.\n\n"
    "🔹 **Tool descriptions** — the Analyst and Search tools each carry a description telling the agent "
    "exactly when to use them. This is the primary driver of correct routing."),
 sql("create_agent", "Create Agent (from specification)",
     create_agent_sql(AGENT, "CoWork Enterprise Demo agent - clients, portfolios, trades, and research")
     + "\nSELECT 'Agent DEMO_AGENT created' AS STATUS;"),
 md("## Step 3: Grant the Final Access Layer (Tier 2)\n\n"
    "🛠️ The agent now exists, so we can grant **`USAGE ON AGENT`** to the consumer role — completing "
    "the four-layer model from Notebook 02."),
 sql("grant_agent_usage", "Tier 2: Grant Agent USAGE to SI Role",
     f"USE ROLE ACCOUNTADMIN;\n"
     f"GRANT USAGE ON AGENT {AGENT} TO ROLE {SIUSER};\n"
     f"USE ROLE {ADMIN};\nSELECT 'Tier 2 agent USAGE granted' AS STATUS;"),
 sql("describe_agent", "Verify: Describe Agent", f"DESCRIBE AGENT {AGENT};"),
 md("### 🔹 Agent Identity: How the Agent Is Identified When It Acts\n\n"
    "A Cortex Agent has **no service account of its own** — it acts with the identity of whoever calls "
    "it. That single fact defines its whole security posture:\n\n"
    "| Facet | How it works here |\n"
    "|---|---|\n"
    "| **Runtime identity** | **Caller's rights** — every tool call and generated SQL runs as the "
    "invoking user's role, inheriting their grants, masking, and row-access (Notebook 02). |\n"
    "| **Object identity** | The agent is a **securable object** with an owner; access is `USAGE ON "
    "AGENT` (the Tier-2 grant above). |\n"
    "| **Display identity** | The `PROFILE` (name, avatar, colour) users see in CoWork (branding is "
    "finalized in Notebook 05). |\n"
    "| **Outbound identity** | For external actions via **MCP**, calls use **per-user OAuth** — the "
    "agent acts as the user in the target system too (see the MCP note below; illustrative). |\n"
    "| **Attribution** | Every interaction is logged to a `USER_NAME` in Account Usage (Step 6) — fully "
    "traceable, since there's no shared service principal to hide behind. |\n\n"
    "📌 **Implication:** you govern the *agent* by governing *users and RBAC* — there is no separate "
    "agent credential to manage or rotate. This is the Snowflake Security Framework's *Agent Identity* "
    "pillar in practice."),
 md("### 🔮 Restricting the Agent *Below* the Caller (Preview)\n\n"
    "⚠️ **Preview / reference — do not run unless these capabilities are enabled in your account.**\n\n"
    "RBAC answers *\"what can the user do?\"* An emerging pattern adds *\"even if the user can, should the "
    "**agent** be allowed to do it automatically?\"* — a tighter boundary for AI-driven execution than for "
    "a human at a worksheet.\n\n"
    "- **Agent Policy** — an account-level control that can restrict an agent session **below** the "
    "caller's role (e.g. read-only on one database), independent of what the user's role otherwise allows.\n"
    "- **`SYS_CONTEXT`** — exposes the acting agent's identity inside a session, so masking / row-access "
    "policies can branch on *whether an agent is calling*, not just on which role.\n\n"
    "📌 Until these are GA in your account, achieve the same intent with the layered controls already in "
    "this guide: a **narrow consumer role**, **tool scoping** in the spec, **guardrails**, and "
    "**budgets / quota** (Notebook 04)."),
 md("## Step 4: Test the Agent\n\n"
    "🛠️ `DATA_AGENT_RUN` calls the agent programmatically (the same engine CoWork uses). It should "
    "**ground** its answer in the semantic view and cite its source.\n\n"
    "📌 Faster iteration: **AI & ML → Agents → DEMO_AGENT → Test** gives a chat UI with no JSON."),
 sql("test_agent", "Test: Ask the Agent",
     INLINE["TestAgent"]),
 md("### 🔹 A Note on `DATA_AGENT_RUN` Output\n\n"
    "`SNOWFLAKE.CORTEX.DATA_AGENT_RUN` returns the agent's response as a **string**. Three patterns show "
    "up in practice:\n\n"
    "| Pattern | Behaviour | Best for |\n"
    "|---|---|---|\n"
    "| `DATA_AGENT_RUN(...)` | Raw string | Quick testing — errors are visible as text |\n"
    "| `PARSE_JSON(DATA_AGENT_RUN(...))` | Parses to JSON; errors on invalid JSON | Debugging — forces failures to surface |\n"
    "| `TRY_PARSE_JSON(DATA_AGENT_RUN(...))` | Parses to JSON; NULL on bad JSON (never errors) | Structured output — extract fields |\n\n"
    "🔹 The parsed response is an **object** with a `content` array (text blocks + tool blocks). To read "
    "just the answer, flatten `content` and keep the `text` rows:\n\n"
    "```sql\n"
    "SELECT f.value:text::string AS answer\n"
    "FROM TABLE(FLATTEN(input => TRY_PARSE_JSON(DATA_AGENT_RUN('...', '{...}')):content)) f\n"
    "WHERE f.value:type::string = 'text';\n"
    "```"),
 md("## Step 5: Guardrails (account-global — read-only here)\n\n"
    "🔹 **Cortex AI Guardrails** (prompt-injection / jailbreak protection) are set at the **account** "
    "level and apply across Cortex Agents, CoWork, and CoCo. On this shared account they are **already "
    "enabled**, so we only read the setting — we never overwrite another team's config.\n\n"
    "```sql\n"
    "-- Reference: enable guardrails (ACCOUNTADMIN, Enterprise Edition)\n"
    "ALTER ACCOUNT SET AI_SETTINGS = '{\"guardrails\":{\"prompt_injection\":{\"enabled\":true},"
    "\"jailbreak\":{\"enabled\":true}}}';\n"
    "```\n\n"
    "**Do you actually need to enable them?** Modern foundation models (Claude 4, GPT-4.1) have strong "
    "built-in safety, so native behaviour is often enough for **internal, read-only, narrowly-scoped** "
    "agents. Turn guardrails **on** when any of these apply:\n\n"
    "- **External-facing** agents (customers / partners have access, not just employees)\n"
    "- **Adversarial users** are plausible, or the cost of a single bypass is high (financial / legal / reputational)\n"
    "- **Compliance** mandates defense-in-depth\n\n"
    "🔹 Guardrails are **additive** (charged per token scanned), not mandatory — they layer on top of the "
    "RBAC and tool-scoping you already have."),
 sql("show_guardrails", "Verify: Current Guardrails Setting",
     "SHOW PARAMETERS LIKE 'AI_SETTINGS' IN ACCOUNT;"),
 md(mcp_md),
 md("### 🔹 The Trust Boundary — What Stays in Snowflake vs. Goes External\n\n"
    "```\n"
    "  +------------- SNOWFLAKE TRUST BOUNDARY -------------+\n"
    "  |  question -> agent orchestration -> tool select   |\n"
    "  |    Cortex Analyst (SQL)    Cortex Search (RAG)     |\n"
    "  |    your data stays here    your data stays here    |\n"
    "  |    cross-region inference: payload is transient,   |\n"
    "  |    encrypted, and never persisted                  |\n"
    "  +----------------------------+-----------------------+\n"
    "                               | MCP tool call (external)\n"
    "                               v\n"
    "     External service (e.g. Jira): receives only the tool\n"
    "     request + response via per-user OAuth — never raw tables\n"
    "```\n\n"
    "- **Data at rest never leaves your region** — tables, stages, and stored data stay put.\n"
    "- **Inference payloads** (prompt + response) may route cross-region, but are transient, encrypted "
    "(TLS 1.2+, mTLS cross-region), and never stored. **No egress charge.**\n"
    "- **MCP calls** send only the tool invocation and its result — not your underlying data.\n"
    "- **Pricing:** cross-region is governed by `CORTEX_ENABLED_CROSS_REGION` — Global (`ANY_REGION`) "
    "bills at a lower per-AI-credit rate than Regional; we enabled it in Notebook 00.\n\n"
    "> **Documentation:** [Cross-region inference]"
    "(https://docs.snowflake.com/en/user-guide/snowflake-cortex/cross-region-inference)"),
 md("## Step 6: Audit Trail\n\n📌 Every agent interaction is logged to Account Usage and attributable "
    "to an individual user (CoWork uses no service account). Usage data can take a short while to appear."),
 sql("audit_agent", "Verify: Agent Usage / Audit",
     "SELECT START_TIME, USER_NAME, AGENT_NAME, TOKENS, TOKEN_CREDITS\n"
     "FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY\n"
     "WHERE AGENT_NAME = 'DEMO_AGENT'\nORDER BY START_TIME DESC\nLIMIT 10;"),
 md("### 📌 Quick Reference — How to Lock Down AI Access\n\n"
    "| Goal | Command |\n"
    "|---|---|\n"
    "| Disable all AI for a role | `REVOKE DATABASE ROLE SNOWFLAKE.CORTEX_USER FROM ROLE <role>` |\n"
    "| Restrict who can use the agent | grant `USAGE ON AGENT` only to approved roles |\n"
    "| Scope the agent's SQL to specific tables | grant the role `SELECT` on just those tables (not schema-wide) |\n"
    "| Disable a specific MCP connector | `ALTER API INTEGRATION <name> SET ENABLED = FALSE` |\n"
    "| Turn off cross-region inference | `ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'DISABLED'` |\n"
    "| Enable prompt-injection / jailbreak guardrails | `ALTER ACCOUNT SET AI_SETTINGS = '{...guardrails...}'` |\n"
    "| Cap per-user AI credits | `SNOWFLAKE.CORE.QUOTA` + `SET_PER_USER_LIMIT` + block enforcement (NB04) |\n"
    "| Cap team / agent credits | `SNOWFLAKE.CORE.BUDGET` + `SET_SPENDING_LIMIT` (NB04) |\n\n"
    "🔹 **Defense in depth:** RBAC + agent scoping + guardrails + PII masking + budgets / quota + audit "
    "trail — no single layer is the whole answer."),
 md(nb_complete("03",
    [f"Agent `{AGENT}` created from a versionable YAML spec, wired to the semantic view + search service",
     "`USAGE ON AGENT` granted to the consumer role (four-layer model complete)",
     "A verified `DATA_AGENT_RUN` test, guardrails posture, and audit trail"],
    ["Tool descriptions are the #1 lever for agent accuracy — be specific about when to use each tool.",
     "Agents are serverless: the warehouse must be named in the spec, not inherited from the session.",
     "Guardrails and audit are account-native — every interaction is traceable to a user."],
    "Continue to **Notebook 04 — Control the Cost**: make AI spend visible, attribute it with tags, "
    "and cap it with budgets and a per-user quota.")),
]

# =====================================================================
# NOTEBOOK 04 - CONTROL THE COST  (Phase 4)
# =====================================================================
n04 = [
 md(nb_header("Control the Cost", "04", "Control the Cost (Phase 4)",
    ["**Observes** AI spend with Account Usage views",
     "**Attributes** every credit to a cost centre with tags (agent + warehouse)",
     "**Controls** spend with a warehouse timeout, a per-agent budget + alert, and a per-user quota"],
    "AI Cost Needs Its Own Discipline",
    "🔹 AI credits can be harder to predict than warehouse compute, and they come from **two meters**: "
    "warehouse compute (the SQL Cortex Analyst generates) **and** serverless LLM reasoning (billed "
    "separately). Manage both from day one with a simple framework: **Observe → Attribute → Control**.\n\n"
    "📌 **Attribution rule:** a request that starts in CoWork and invokes an agent is billed to "
    "**CoWork**, not to the agent object. To see the full picture, run *both* a CoWork-scoped budget "
    "and per-agent budgets.\n\n"
    "> **Documentation:** [AI cost management]"
    "(https://docs.snowflake.com/en/user-guide/snowflake-cortex/governance-and-availability/ai-cost-management-and-governance)",
    "15–20 minutes",
    ["Notebook 03 complete (agent created and tested)"])),
 sql("set_context", "Set Context",
     f"USE ROLE {ADMIN};\nUSE DATABASE {DB};\nUSE SCHEMA AGENTS;\nUSE WAREHOUSE {WH};"),
 md("## Step 1: Observe — Know What You're Spending\n\n"
    "🛠️ Before you can control cost you need visibility. `CORTEX_AGENT_USAGE_HISTORY` shows per-agent "
    "token spend; `METERING_DAILY_HISTORY` shows the account-wide AI credit trend."),
 sql("observe_agent", "Observe: Per-Agent Usage",
     "SELECT START_TIME, USER_NAME, AGENT_NAME, TOKENS, TOKEN_CREDITS\n"
     "FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY\n"
     "WHERE AGENT_NAME = 'DEMO_AGENT'\nORDER BY START_TIME DESC\nLIMIT 20;"),
 sql("observe_account", "Observe: Account AI Credit Trend",
     "SELECT USAGE_DATE, SERVICE_TYPE, SUM(CREDITS_USED) AS TOTAL_CREDITS\n"
     "FROM SNOWFLAKE.ACCOUNT_USAGE.METERING_DAILY_HISTORY\n"
     "WHERE SERVICE_TYPE = 'AI_SERVICES'\n"
     "  AND USAGE_DATE >= DATEADD('day', -7, CURRENT_DATE())\n"
     "GROUP BY USAGE_DATE, SERVICE_TYPE\nORDER BY USAGE_DATE DESC;"),
 md("## Step 2: Attribute — Know Who Is Spending What\n\n"
    "🛠️ Tag the agent **and** its warehouse with a cost centre so one tag-based budget or quota "
    "captures everything for that team.\n\n"
    "📌 **Tag before you budget** — retroactive tagging only captures *future* spend."),
 sql("create_tag", "Attribute: Create Cost-Centre Tag",
     f"CREATE TAG IF NOT EXISTS {DB}.AGENTS.COST_CENTER\n"
     f"  ALLOWED_VALUES 'demo', 'finance', 'shared'\n"
     f"  COMMENT = 'Cost-centre attribution for CoWork / agent spend';"),
 sql("tag_agent", "Attribute: Tag the Agent",
     f"ALTER AGENT {AGENT} SET TAG {DB}.AGENTS.COST_CENTER = 'demo';"),
 sql("tag_warehouse", "Attribute: Tag the Warehouse",
     f"ALTER WAREHOUSE {WH} SET TAG {DB}.AGENTS.COST_CENTER = 'demo';"),
 md("> **Tag users too (reference).** Per-user chargeback needs the user object tagged; we don't tag a "
    "real user on a shared account:\n```sql\n"
    f"ALTER USER <business_user> SET TAG {DB}.AGENTS.COST_CENTER = 'demo';\n```"),
 md("## Step 3: Control — Warehouse Guardrail\n"
    "🛠️ "
    "Cap runaway SQL with a **statement timeout** on the agent's warehouse. In production, use a "
    "dedicated warehouse per agent category (e.g. `COWORK_FINANCE_WH`), sized XS and upsized only if "
    "query performance requires it. (Cortex LLM reasoning is serverless and billed separately from this "
    "warehouse compute - budget both.)"),
 sql("harden_warehouse", "Control: Warehouse Statement Timeout",
     f"ALTER WAREHOUSE {WH} SET STATEMENT_TIMEOUT_IN_SECONDS = 120;"),
 md("## Step 4: Control — Per-Agent Budget\n\n🛠️ A **budget** tracks credits against a monthly limit "
    "and alerts (or acts) at a threshold. Enforcement is periodic, so alert well below the hard stop."),
 sql("create_budget", "Control: Create Resource Budget",
     f"CREATE OR REPLACE SNOWFLAKE.CORE.BUDGET {DB}.AGENTS.DEMO_AGENT_BUDGET();\n"
     f"CALL {DB}.AGENTS.DEMO_AGENT_BUDGET!SET_SPENDING_LIMIT(50);"),
 sql("budget_threshold", "Control: Budget Notification Threshold (75%)",
     f"CALL {DB}.AGENTS.DEMO_AGENT_BUDGET!SET_NOTIFICATION_THRESHOLD(75);"),
 md("> **Email alerts (reference).** Email needs verified recipients (or a notification integration); we "
    "don't send mail from a shared account:\n```sql\n"
    f"CALL {DB}.AGENTS.DEMO_AGENT_BUDGET!SET_EMAIL_NOTIFICATIONS('costadmin@yourco.com');\n"
    "-- raise the threshold for a second, higher alert:\n"
    f"CALL {DB}.AGENTS.DEMO_AGENT_BUDGET!SET_NOTIFICATION_THRESHOLD(90);\n```"),
 md("## Step 5: Control — Per-User Quota\n"
    "🛠️ "
    "A **quota** is a first-class object that caps AI credits **per user** and can auto-block at the "
    "limit. We create it in **monitoring mode** (no enforcement, no notifications) so it is safe on a "
    "shared account. Scope it to CoWork **and** the agent - a CoWork-initiated request is billed to "
    "CoWork, not the agent (the attribution rule from the intro), so cover both."),
 sql("create_quota", "Control: Per-User Quota (monitoring only)",
     f"USE ROLE ACCOUNTADMIN;\n"
     f"CREATE SNOWFLAKE.CORE.QUOTA {QUOTA}();\n"
     f"CALL {QUOTA}!ADD_SHARED_RESOURCE('SNOWFLAKE INTELLIGENCE');\n"
     f"CALL {QUOTA}!ADD_SHARED_RESOURCE('CORTEX AGENT', (SELECT SYSTEM$REFERENCE('CORTEX AGENT', '{AGENT}')));\n"
     f"CALL {QUOTA}!SET_PER_USER_LIMIT(50);\n"
     f"CALL {QUOTA}!SET_PER_USER_LIMIT(5, 'DAILY');\n"
     f"USE ROLE {ADMIN};\nSELECT 'Quota created (monitoring only)' AS STATUS;"),
 md("> **Enforce (reference).** In production, turn on automatic blocking and a proactive alert:\n```sql\n"
    f"CALL {QUOTA}!SET_BLOCK_ENFORCEMENT_ENABLED(TRUE);\n"
    f"CALL {QUOTA}!ADD_NOTIFICATION_THRESHOLD(80, 'PROJECTED', TRUE);\n```\n"
    "> Note: the legacy `ALTER USER ... SET MONTHLY_CORTEX_AI_CREDITS_QUOTA` form is **not** current "
    "syntax - the quota object above is the supported mechanism."),
 md("## Step 6: Budget Models — Resource-Level vs Shared Resource\n\n"
    "🔹 Beyond the **per-agent** budget above, Snowflake CoWork supports two budget *scopes* — pick "
    "based on your governance need:\n\n"
    "| Model | Scope | Tag what | Impact |\n"
    "|---|---|---|---|\n"
    "| **Resource-Level** | The entire CoWork (SI) object | the **SI object** | **all** users of the object |\n"
    "| **Shared Resource** | A subset of users (a team) | **individual users** | just that team/group |\n\n"
    "🔹 A CoWork-initiated request bills to the **CoWork object**, so an SI-scoped budget is how you cap "
    "total CoWork spend; a shared-resource budget gives each team its own cap on the *same* object. When "
    "a user is covered by several budgets, the **first threshold reached** stops them."),
 md("### 🛠️ Shared Resource budget (team-scoped) — runnable\n"
    "This is the safe, executable model: it tags **users** (not the shared object). We cap a team at "
    "200 credits/month on CoWork, tracked only for users carrying our `cost_centre` tag. Tagging real "
    "users is left as reference (no demo users on a shared account)."),
 sql("create_team_budget", "Control: Shared Resource Budget (team via user tag)",
     f"CREATE OR REPLACE SNOWFLAKE.CORE.BUDGET {SHARED_BUDGET}();\n"
     f"CALL {SHARED_BUDGET}!SET_SPENDING_LIMIT(200);\n"
     f"CALL {SHARED_BUDGET}!ADD_SHARED_RESOURCE('SNOWFLAKE INTELLIGENCE');\n"
     f"CALL {SHARED_BUDGET}!SET_USER_TAGS(\n"
     f"  [ [(SELECT SYSTEM$REFERENCE('TAG', '{DB}.AGENTS.COST_CENTER', 'SESSION', 'APPLYBUDGET')), 'demo'] ],\n"
     "  'UNION');\n"
     "-- Reference: apply the tag to the team's users so the budget tracks them:\n"
     f"-- ALTER USER <business_user> SET TAG {DB}.AGENTS.COST_CENTER = 'demo';"),
 md("### 📌 Resource-Level budget (SI object, all users) — reference only\n"
    "This caps the **entire shared CoWork object across every team**, so we do **not** run it here — "
    "tagging the shared singleton would affect other teams on this account.\n\n"
    "```sql\n"
    "CREATE OR REPLACE SNOWFLAKE.CORE.BUDGET org_si_budget();\n"
    "CALL org_si_budget!SET_SPENDING_LIMIT(10000);\n"
    "-- Tag the SHARED object (org-level cap):\n"
    f"ALTER SNOWFLAKE INTELLIGENCE {COOBJ} SET TAG {DB}.AGENTS.COST_CENTER = 'shared';\n"
    "CALL org_si_budget!SET_RESOURCE_TAGS(\n"
    f"  [ [(SELECT SYSTEM$REFERENCE('TAG', '{DB}.AGENTS.COST_CENTER', 'SESSION', 'APPLYBUDGET')), 'shared'] ],\n"
    "  'UNION');\n"
    "```"),
 md("### 📌 Threshold actions with stored procedures — reference only\n"
    "Budgets can **run a stored procedure at a threshold** (alert at 80%, block at 100%). Blocking "
    "works by revoking a **dedicated per-team role**, and the proc must be granted to the `SNOWFLAKE` "
    "application. Enforcement is periodic (up to ~8h, or ~2h with a low-latency budget), so alert well "
    "below the hard stop. Shown for reference — it needs a dedicated role and an app grant.\n\n"
    "```sql\n"
    f"CREATE OR REPLACE PROCEDURE {DB}.AGENTS.SP_REVOKE_TEAM(dept STRING)\n"
    "  RETURNS STRING LANGUAGE SQL AS\n"
    "BEGIN\n"
    "  EXECUTE IMMEDIATE 'REVOKE ROLE si_' || :dept || '_role FROM ROLE ' || :dept || '_role';\n"
    "  RETURN 'Access revoked for ' || :dept;\n"
    "END;\n"
    f"GRANT USAGE ON PROCEDURE {DB}.AGENTS.SP_REVOKE_TEAM(STRING) TO APPLICATION SNOWFLAKE;\n\n"
    "-- Block the team at 100% of its shared budget:\n"
    f"CALL {SHARED_BUDGET}!ADD_CUSTOM_ACTION(\n"
    f"  SYSTEM$REFERENCE('PROCEDURE', '{DB}.AGENTS.SP_REVOKE_TEAM(string)'),\n"
    "  ARRAY_CONSTRUCT('demo'), 'ACTUAL', 100);\n"
    "```\n"
    "> The same `ADD_CUSTOM_ACTION` pattern with `'PROJECTED'` fires on *forecast* spend, and "
    "thresholds up to 1000% let you script reinstatement for peak periods."),
 md("## Step 7: Verify"),
 sql("verify_tag", "Verify: Cost-Centre Tag Exists",
     f"SHOW TAGS IN SCHEMA {DB}.AGENTS;"),
 sql("verify_budget", "Verify: Per-Agent Budget Spending Limit",
     f"CALL {DB}.AGENTS.DEMO_AGENT_BUDGET!GET_SPENDING_LIMIT();"),
 sql("verify_team_budget", "Verify: Team Budget Scope",
     f"CALL {SHARED_BUDGET}!GET_BUDGET_SCOPE();"),
 sql("verify_quota", "Verify: Quota Config",
     f"CALL {QUOTA}!GET_CONFIG();"),
 md(nb_complete("04",
    ["Cost-centre tag on the agent and warehouse",
     "Warehouse statement timeout (runaway-query guardrail)",
     "Per-agent resource budget with a 75% alert threshold",
     "A team-scoped shared resource budget on CoWork (Resource-Level + stored-proc threshold actions "
     "shown as reference)",
     "Per-user quota (monitoring mode) scoped to CoWork + the agent"],
    ["AI spend comes from two meters — warehouse compute and serverless LLM reasoning. Budget both.",
     "CoWork-initiated spend attributes to CoWork, not the agent — so run both budget scopes.",
     "Tag before you budget; quotas cap individual users where budgets cap a team/agent."],
    "Continue to **Notebook 05 — Evaluate, Go Live & Operate**: score the agent with Agent GPA, "
    "publish it to CoWork under governance, and brand the interface.")),
]

# =====================================================================
# NOTEBOOK 05 - EVALUATE, GO LIVE & OPERATE  (Phase 5)
# =====================================================================
n05 = [
 md(nb_header("Evaluate, Go Live & Operate", "05", "Evaluate, Go Live & Operate (Phase 5)",
    ["**Evaluates** the agent — golden smoke tests + a scored **Agent GPA** run against a curated dataset",
     "**Publishes** the agent to the shared **CoWork object** (the curation gate) and grants access",
     "**Brands** the agent and the CoWork interface",
     "Sets up **operations** (published check + health-check pattern)"],
    "Evaluation Is the Go-Live Gate",
    "🔹 Never publish an agent a business user can reach without a scored evaluation behind it. The flow "
    "is **Evaluate (gate) → Go live (publish) → Operate (monitor)**.\n\n"
    "🔹 **Agent GPA** scores the agent at each stage of its reasoning (Goal → Plan → Action), not just "
    "the final answer: `answer_correctness`, `logical_consistency`, and `tool_selection_accuracy`. "
    "Require a threshold (e.g. ≥ 0.85, 0 regressions) before publishing.\n\n"
    "🔹 **Publishing is a curation gate:** agents are invisible in CoWork until an admin with `MODIFY` "
    "explicitly adds them to the singleton CoWork object. Only publish agents that passed the gate.\n\n"
    "> **Documentation:** [Cortex Agent evaluations]"
    "(https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents-evaluations)",
    "25–30 minutes",
    ["Notebook 04 complete (agent built; cost controls in place)"])),
 sql("set_context", "Set Context",
     f"USE ROLE {ADMIN};\nUSE DATABASE {DB};\nUSE SCHEMA AGENTS;\nUSE WAREHOUSE {WH};"),
 md("## Step 1: Evaluate — Golden Smoke Tests\n\n"
    "🛠️ Quick, runnable checks for fast iteration. Cover a **mix** of question types — core analytics, "
    "tool routing, multi-tool, and out-of-scope refusal — so you catch different failure modes."),
 sql("golden_q1", "Golden Q1: Top clients by AUM (Analyst)",
     "SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(\n"
     f"  '{AGENT}',\n"
     "  '{\"messages\": [{\"role\": \"user\", \"content\": [{\"type\": \"text\", "
     "\"text\": \"Who are our top 5 clients by AUM?\"}]}], \"stream\": false}'\n) AS resp;"),
 sql("golden_q2", "Golden Q2: Compliance concerns (Search)",
     "SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(\n"
     f"  '{AGENT}',\n"
     "  '{\"messages\": [{\"role\": \"user\", \"content\": [{\"type\": \"text\", "
     "\"text\": \"Are there any compliance concerns I should know about?\"}]}], \"stream\": false}'\n) AS resp;"),
 sql("golden_q3", "Golden Q3: Multi-tool (trades + rationale)",
     "SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(\n"
     f"  '{AGENT}',\n"
     "  '{\"messages\": [{\"role\": \"user\", \"content\": [{\"type\": \"text\", "
     "\"text\": \"Summarize recent trades over $1M and the rationale behind them.\"}]}], \"stream\": false}'\n) AS resp;"),
 sql("golden_q4", "Golden Q4: Out-of-scope refusal (should not hallucinate)",
     "SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(\n"
     f"  '{AGENT}',\n"
     "  '{\"messages\": [{\"role\": \"user\", \"content\": [{\"type\": \"text\", "
     "\"text\": \"What is the weather in Sydney today?\"}]}], \"stream\": false}'\n) AS resp;"),
 md("## Step 2: Evaluate — Agent GPA (scored gate)\n\n"
    "🛠️ The golden smoke tests confirm the agent *answers*; Agent GPA **scores** it. Build a curated "
    "question bank with ground truth, register it as an evaluation dataset, then run "
    "`EXECUTE_AI_EVALUATION`.\n\n"
    "📌 **Gate:** require a threshold (e.g. `answer_correctness >= 0.85`, 0 regressions) before "
    "publishing. Notebook 07 reuses this exact dataset for the continuous-improvement loop."),
 sql("create_eval_dataset", "Evaluate: Curated Question Bank (ground truth)",
     eval_insert_sql()),
 sql("register_eval_dataset", "Evaluate: Register the Evaluation Dataset",
     f"CALL SYSTEM$CREATE_EVALUATION_DATASET(\n"
     f"  'Cortex Agent',\n  '{EVAL_TABLE}',\n  '{EVAL_DATASET}',\n"
     "  OBJECT_CONSTRUCT('query_text', 'INPUT_QUERY', 'expected_tools', 'GROUND_TRUTH')\n);"),
 sql("create_eval_stage", "Evaluate: Stage + File Format for the Eval Config",
     f"CREATE FILE FORMAT IF NOT EXISTS {DB}.AGENTS.YAML_FF\n"
     "  TYPE = 'CSV' FIELD_DELIMITER = NONE RECORD_DELIMITER = '\\n'\n"
     "  SKIP_HEADER = 0 FIELD_OPTIONALLY_ENCLOSED_BY = NONE ESCAPE_UNENCLOSED_FIELD = NONE;\n"
     f"CREATE STAGE IF NOT EXISTS {EVAL_STAGE} FILE_FORMAT = {DB}.AGENTS.YAML_FF;"),
 md("### Run the scored evaluation\n"
    "`EXECUTE_AI_EVALUATION` reads a config YAML **from a stage**. Save the YAML below as "
    "`agent_eval.yaml` in this workspace, upload it to the stage (Snowsight **Add Data -> Load files "
    "into a Stage**, or `PUT`/`COPY FILES`), then run the evaluation. **Easier path:** in the CoCo CLI, "
    "use the `cortex-agent` skill (`evaluate-cortex-agent`) to run the whole flow in one prompt.\n\n"
    "```yaml\n" + EVAL_YAML + "```\n"
    "```sql\n"
    "-- After the YAML is on the stage:\n"
    "CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', 'go_live_gate'),\n"
    f"  '@{EVAL_STAGE}/agent_eval.yaml');\n"
    "-- Poll until COMPLETED:\n"
    "CALL EXECUTE_AI_EVALUATION('STATUS', OBJECT_CONSTRUCT('run_name', 'go_live_gate'),\n"
    f"  '@{EVAL_STAGE}/agent_eval.yaml');\n"
    "-- Read scores (gate on answer_correctness >= 0.85):\n"
    "SELECT METRIC_NAME, AVG(EVAL_AGG_SCORE) AS AVG_SCORE\n"
    "FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(\n"
    f"  '{DB}', 'AGENTS', 'DEMO_AGENT', 'CORTEX AGENT', 'go_live_gate'))\n"
    "GROUP BY METRIC_NAME;\n"
    "```\n"
    "> Also review scores in Snowsight: **AI & ML -> Agents -> DEMO_AGENT -> Evaluations**."),
 md("## Step 3: Go Live — Publish to the CoWork Object\n\n"
    "🛠️ The account already has a CoWork object (`SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT`, a singleton). "
    "We **add our agent to it** (the curation gate) and grant the consumer role `USAGE` on the object. "
    "We never create or drop the shared object.\n\n"
    "📌 Requires `MODIFY` on the object, so this uses ACCOUNTADMIN.\n\n"
    "🔹 **Curation, and the Preview→GA change:** the CoWork object curates *which* agents appear in the "
    "dropdown. Since GA, **without** curation (or if an agent isn't added) users see **every** agent they "
    "have `USAGE` on — flexible but noisy. **With** curation, only agents you add show — your production-"
    "ready shortlist. (In Preview, an agent had to live in a specific schema to appear; that restriction is gone.)\n\n"
    "🔗 **Deep links** reach a *non-curated* agent directly — useful to test before you curate: "
    "`https://ai.snowflake.com/{org-account}/#/agents/{database}.{schema}.{agent_name}`\n\n"
    "💬 **For customers:** (1) there is **one** CoWork object per account — it's account-level, not "
    "per-database; (2) there's no per-role curated list — use **RBAC** (`USAGE ON AGENT`) to control who "
    "sees what, and the object to curate the shared shortlist."),
 sql("publish_agent", "Go Live: Add Agent to CoWork Object",
     f"USE ROLE ACCOUNTADMIN;\n"
     f"ALTER SNOWFLAKE INTELLIGENCE {COOBJ} ADD AGENT {AGENT};\n"
     f"GRANT USAGE ON SNOWFLAKE INTELLIGENCE {COOBJ} TO ROLE {SIUSER};"),
 sql("brand_agent", "Go Live: Brand the Agent (display name, avatar, colour)",
     f"ALTER AGENT {AGENT} SET\n"
     "  PROFILE = '{\"display_name\": \"Enterprise Demo Analyst\", \"avatar\": \"shield\", "
     "\"color\": \"blue\"}';"),
 md("## Step 4: Brand the CoWork Interface (account-level)\n\n"
    "🛠️ The agent `PROFILE` above sets its display name/avatar/colour. The CoWork **object** carries "
    "the enterprise branding every user sees — brand name, welcome message, accent colour.\n\n"
    "📌 This is account-level (the object is a singleton), so it **overwrites any prior branding**. "
    "Logos/icons use staged image paths; upload images to a stage or set them via AI & ML → Agents → "
    "Open settings."),
 sql("brand_cowork", "Go Live: Brand the CoWork Interface",
     f"USE ROLE ACCOUNTADMIN;\n"
     f"ALTER SNOWFLAKE INTELLIGENCE {COOBJ} SET\n"
     "  BRAND_NAME = 'Strive Capital'\n"
     "  WELCOME_MESSAGE = 'Welcome to Strive Capital Intelligence. Ask about client portfolios, positions, trades, and market research.'\n"
     "  ACCENT_COLOR_LIGHT = '#0B3D91'\n"
     "  ACCENT_COLOR_DARK = '#5B9BD5';"),
 md("## Restrict business users to CoWork (reference)\n"
    "Confine non-technical users to the CoWork UI and ensure each has a default role + warehouse. Shown "
    "for reference - we do not lock a real user on a shared account.\n\n"
    "```sql\n"
    "ALTER USER <business_user> SET\n"
    f"  DEFAULT_ROLE = {SIUSER},\n  DEFAULT_WAREHOUSE = {WH},\n"
    "  ALLOWED_INTERFACES = (SNOWFLAKE_INTELLIGENCE);\n"
    "-- IdP redirect so users never see a native login page:\n"
    "ALTER ACCOUNT SET LOGIN_IDP_REDIRECT = (SNOWFLAKE_INTELLIGENCE = <security_integration>);\n"
    "```"),
 md("### 🔹 The Business-User Experience in CoWork\n\n"
    "Once published, business users chat with the agent in CoWork — a different surface from the Agent "
    "Admin **Test** tab that you (the builder) use:\n\n"
    "| | Agent Admin → Test | CoWork chat |\n"
    "|---|---|---|\n"
    "| Full agent spec visible / editable | Yes | No |\n"
    "| Who uses it | Agent builders | Business users |\n"
    "| MCP connectors | Configure (add/remove) | Connect & use (per-user OAuth) |\n"
    "| Save / share / explore answers | No | **Yes** |\n"
    "| Upload files for ad-hoc analysis | No | Yes (via + menu) |\n\n"
    "**Both** surfaces show thinking steps, generated SQL, cited sources, inline charts, and suggested "
    "follow-ups.\n\n"
    "🔹 **Artifacts:** a user can **Save** a chart or table from a response as an Artifact — a persistent, "
    "shareable snapshot, ideal for recurring analyses. Sharing an artifact shares the *saved output*; if "
    "a colleague clicks **Explore** or re-runs the query, **their** role permissions still apply. An "
    "artifact is a snapshot, not a privilege escalation."),
 md("> **What to tell customers:** AI usage is fully visible in the same Account Usage views you already "
    "use for warehouse and storage cost — no hidden meters. Governance *is* your existing RBAC + masking; "
    "there's no separate AI security layer to bolt on. And every answer is traceable to a user and cites "
    "its source."),
 md("## Step 5: Provision SI-Only Business Users\n\n"
    "🛠️ The agent is live and branded — now let business users in. Provision a dedicated user, restrict it "
    "with **`ALLOWED_INTERFACES`**, and grant it the `SI_USER` role (which already carries the agent + "
    "CoWork-object `USAGE` from the publish step above). Business users reach the agent through **CoWork "
    "only** — no worksheets, no SQL, no drivers.\n\n"
    "🔹 `ALLOWED_INTERFACES` controls which entry points a user can authenticate through:\n\n"
    "| Value | Grants access to | Example |\n"
    "|---|---|---|\n"
    "| `SNOWFLAKE_INTELLIGENCE` | Natural-language CoWork UI only | `ai.snowflake.com` |\n"
    "| `SNOWSIGHT` | Web SQL interface | `app.snowflake.com` |\n"
    "| `STREAMLIT` | Streamlit-in-Snowflake apps | Streamlit in Snowsight |\n"
    "| `DRIVERS` | JDBC / ODBC / Python connector | SnowSQL, scripts |\n\n"
    "📌 Interface restriction is **additive to RBAC**, not a replacement — the user still sees only the data "
    "their role grants + masking allow. In production, provision these users via **SSO / SAML** instead of "
    "passwords."),
 sql("create_si_user", "Provision SI-Only Business User (ai.snowflake.com only)",
     f"USE ROLE ACCOUNTADMIN;\n"
     f"CREATE USER IF NOT EXISTS {BIZUSER}\n"
     "  PASSWORD = 'ChangeMe_CoWorkDemo_2026!'\n"
     "  MUST_CHANGE_PASSWORD = TRUE\n"
     f"  DEFAULT_ROLE = {SIUSER}\n"
     f"  DEFAULT_WAREHOUSE = {WH}\n"
     "  COMMENT = 'CoWork Enterprise Demo - SI-only business user (demo; dropped in cleanup)';\n"
     f"ALTER USER {BIZUSER} SET ALLOWED_INTERFACES = ('SNOWFLAKE_INTELLIGENCE');\n"
     f"GRANT ROLE {SIUSER} TO USER {BIZUSER};\n"
     f"USE ROLE {ADMIN};\nSELECT 'SI-only user {BIZUSER} created' AS STATUS;"),
 md("### 📌 Validate SI-Only Access (manual)\n\n"
    "A notebook can't authenticate as another user, so confirm in a browser (incognito):\n\n"
    "- ✅ **`ai.snowflake.com`** → sign in as the user → sees the curated agent and can chat\n"
    "- ❌ **`app.snowflake.com`** (Snowsight) → sign-in blocked (*access restricted to allowed interfaces*)\n"
    "- ❌ **SnowSQL / driver** connect → authentication blocked\n\n"
    "🔹 If the user logs in but sees an **empty screen**, the role is missing `USAGE` on the CoWork object "
    "(granted in the publish step above) — the most common go-live gap."),
 md("## Step 6: Verify & Operate\n\n📌 Confirm the agent is published, then reuse the golden questions "
    "as a scheduled **health check** (track success rate + p95 latency). Continuous, post-go-live "
    "improvement is Notebook 07."),
 sql("verify_published", "Verify: Agent Published to CoWork",
     f"SHOW AGENTS IN SNOWFLAKE INTELLIGENCE {COOBJ};"),
 md(nb_complete("05",
    ["Golden smoke tests across four question types",
     f"Curated Agent GPA evaluation dataset `{EVAL_DATASET}` + config stage, with the scored-gate pattern",
     "Agent published to the shared CoWork object; consumer role granted object `USAGE`",
     "Agent + CoWork interface branding applied",
     f"SI-only business user `{BIZUSER}` provisioned (`ALLOWED_INTERFACES = SNOWFLAKE_INTELLIGENCE`)"],
    ["Evaluation is the go-live gate — publish only what clears the threshold.",
     "Publishing to the CoWork object is the curation gate; agents are invisible until added.",
     "The shared CoWork object is never created or dropped — we only ADD our agent."],
    "Continue to **Notebook 06 — Dev → Prod Promotion**: treat the agent spec as code and promote it "
    "through an evaluation gate. Then **Notebook 07** closes the continuous-improvement loop.")),
]

# =====================================================================
# NOTEBOOK 06 - DEV -> PROD PROMOTION (Agent-as-Code)
# =====================================================================
n06 = [
 md(nb_header("Dev → Prod Promotion", "06", "Dev → Prod Promotion (Agent-as-Code)",
    ["**Captures** the agent spec (the source of truth) with `DESCRIBE AGENT`",
     "**Versions** it in place with `ALTER AGENT ... MODIFY LIVE VERSION`",
     "**Deploys** the identical spec to a prod-scoped target (`AGENTS_PROD`)",
     "**Gates** promotion on an evaluation pass, then **publishes** and cuts over"],
    "Promote the Spec, Not the Running Agent",
    "🔹 The CoWork object is a **per-account singleton**, so real enterprises run **dev and prod in "
    "separate accounts** (or at least separate databases/schemas). You don't promote a *running* agent — "
    "you promote its **specification**.\n\n"
    "🔹 The agent is created `FROM SPECIFICATION`; that YAML spec is your **source of truth** (keep it in "
    "git). **Promotion = deploy the same spec to the prod target, gated by an evaluation pass.** Never "
    "hand-edit a live prod agent — edit the spec in source control and redeploy.\n\n"
    "This notebook shows the mechanics on one account using a prod-scoped schema (`AGENTS_PROD`); the "
    "same steps apply across accounts by pointing the deploy at the prod account.\n\n"
    "**Promotion model:** capture spec → version in place → deploy to prod → evaluate (gate) → publish.",
    "20–25 minutes",
    ["Notebooks 00–05 complete (they build the dev agent `DEMO_AGENT`)"])),
 sql("set_context", "Set Context",
     f"USE ROLE {ADMIN};\nUSE DATABASE {DB};\nUSE SCHEMA AGENTS;\nUSE WAREHOUSE {WH};"),
 md("## Step 1: Agent-as-Code — Capture the Spec (source of truth)\n"
    "`DESCRIBE AGENT` returns the full spec in the `agent_spec` column - this is the code you version in "
    "git. `DESCRIBE AS RESOURCE AGENT <name>` returns the same as JSON. Never hand-edit prod: edit the "
    "spec in source control and redeploy."),
 sql("capture_spec", "Capture: Agent Spec (agent-as-code)",
     f"DESCRIBE AGENT {AGENT};"),
 md("## Step 2: Version in Place (iterate safely)\n"
    "Agents are versioned. `ALTER AGENT ... MODIFY LIVE VERSION SET SPECIFICATION = $$...$$` replaces the "
    "LIVE version's spec in one atomic step (fields omitted are removed). Tag each promoted build with a "
    "COMMENT so you can trace what shipped.\n\n"
    "```sql\n"
    "-- Replace the LIVE version's spec (whole-spec replacement):\n"
    f"ALTER AGENT {AGENT} MODIFY LIVE VERSION SET SPECIFICATION = $$ ...updated spec... $$;\n"
    "```"),
 sql("tag_version", "Version: Tag the Promoted Build",
     f"ALTER AGENT {AGENT} SET COMMENT = 'v1 - passed evaluation; promoted to prod';"),
 md("## Step 3: Deploy to the Prod Target (same spec)\n"
    "Create the prod-scoped schema and deploy **the identical spec** with `CREATE OR REPLACE AGENT "
    "... FROM SPECIFICATION`. In a real cross-account promotion this runs in the prod account and the "
    "`tool_resources` point at prod data; here we reuse the demo objects to show the mechanics."),
 sql("create_prod_schema", "Create Prod-Scoped Schema",
     f"USE ROLE {ADMIN};\n"
     f"CREATE SCHEMA IF NOT EXISTS {DB}.AGENTS_PROD\n"
     "  COMMENT = 'Promotion target (prod-scoped) for the CoWork enterprise demo';"),
 sql("promote_agent", "Promote: Deploy Agent from the Same Spec",
     create_agent_sql(AGENT_PROD, "DEMO_AGENT promoted from dev - identical specification")
     + "\nSELECT 'Agent promoted to AGENTS_PROD.DEMO_AGENT' AS STATUS;"),
 sql("grant_prod_usage", "Grant Agent USAGE on the Promoted Agent",
     f"USE ROLE ACCOUNTADMIN;\n"
     f"GRANT USAGE ON AGENT {AGENT_PROD} TO ROLE {SIUSER};\n"
     f"USE ROLE {ADMIN};\nSELECT 'USAGE granted on promoted agent' AS STATUS;"),
 md("## Step 4: Promotion Gate = Evaluation Pass\n"
    "Only promote a build that clears the evaluation threshold (Notebook 05's `EXECUTE_AI_EVALUATION` on "
    "the golden-question bank). Here we smoke-test the promoted agent to confirm it answers before we "
    "publish it. **If it fails the gate, do not publish - fix the spec in git and redeploy.**"),
 sql("gate_eval", "Gate: Smoke-Test the Promoted Agent",
     "SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(\n"
     f"  '{AGENT_PROD}',\n"
     "  '{\"messages\": [{\"role\": \"user\", \"content\": [{\"type\": \"text\", "
     "\"text\": \"Who are our top 5 clients by AUM?\"}]}], \"stream\": false}'\n) AS resp;"),
 md("## Step 5: Publish the Promoted Agent to CoWork (cut over)\n"
    "Add the **promoted** agent to the CoWork object. To cut over cleanly, remove the dev agent so users "
    "see only the promoted build. Requires `MODIFY` on the object, so we use ACCOUNTADMIN."),
 sql("publish_prod", "Go Live: Publish the Promoted Agent",
     f"USE ROLE ACCOUNTADMIN;\n"
     f"ALTER SNOWFLAKE INTELLIGENCE {COOBJ} ADD AGENT {AGENT_PROD};\n"
     f"-- Cut over: remove the dev build so only the promoted agent is visible.\n"
     f"ALTER SNOWFLAKE INTELLIGENCE {COOBJ} DROP AGENT {AGENT};"),
 sql("verify_prod_published", "Verify: Promoted Agent Published",
     f"SHOW AGENTS IN SNOWFLAKE INTELLIGENCE {COOBJ};"),
 md("## Environment strategy (reference)\n\n"
    "| Concern | Pattern |\n"
    "| --- | --- |\n"
    "| Environments | Separate **accounts** (or DBs) for dev / prod - the CoWork object is one per account |\n"
    "| Source of truth | The `FROM SPECIFICATION` spec, checked into **git** (agent-as-code) |\n"
    "| Deploy | `CREATE OR REPLACE AGENT ... FROM SPECIFICATION` (or `ALTER AGENT MODIFY LIVE VERSION`) |\n"
    "| Promotion gate | Evaluation threshold (Notebook 05) must pass **before** publish |\n"
    "| Cut over | Publish the promoted agent to the CoWork object; remove the prior build |\n"
    "| Change safety | Clone-before-change on prod; never hand-edit a live agent |\n"
    "| CI/CD | Script the deploy in a task / pipeline; version + review the spec like any code |"),
 md(nb_complete("06",
    ["The dev agent spec captured as code and versioned with a traceable COMMENT",
     f"The identical spec deployed to `{AGENT_PROD}` and smoke-tested through the gate",
     "The promoted agent published to CoWork with a clean cut-over from the dev build"],
    ["You promote the spec, not the running agent — the spec is the git source of truth.",
     "The evaluation threshold is the promotion gate: no pass, no publish.",
     "The CoWork object is one per account, so dev/prod belong in separate accounts (or schemas)."],
    "Continue to **Notebook 07 — Continuous Improvement**: mine real usage, re-evaluate, and optimize "
    "the agent's instructions in a governed loop. (Run **Notebook 08** last to clean up.)")),
]

# =====================================================================
# NOTEBOOK 08 - CLEANUP
# =====================================================================
n08 = [
 md(nb_header("Cleanup", "08", "Cleanup",
    ["Removes **only** the demo footprint (agents, budget, quota, masking, DB, warehouse, roles)",
     "Removes our agents from the shared CoWork object **without dropping the object**",
     "Verifies the account is back to its prior state"],
    "This Notebook Is Deliberately Narrow",
    "📌 **This notebook must NOT touch** shared state: the CoWork object "
    "`SNOWFLAKE_INTELLIGENCE_OBJECT_DEFAULT` (it only removes *our* agents from it), "
    "`CORTEX_USER`/`PUBLIC`, `CORTEX_ENABLED_CROSS_REGION`, or account `AI_SETTINGS` — all pre-existed "
    "and are shared with other teams.\n\n"
    "🔹 It removes both the dev agent (`DEMO_AGENT`) and the promoted agent (`AGENTS_PROD.DEMO_AGENT`). "
    "If a notebook that added one of them wasn't run, that DROP simply reports it isn't present — "
    "continue to the next cell.\n\n"
    "📌 The CoWork interface branding from Notebook 05 is intentionally **left in place**; re-run the "
    "`ALTER SNOWFLAKE INTELLIGENCE ... SET BRAND_NAME = ...` with your own values to revert it.",
    "5 minutes",
    ["Run this **last**, after you're done with Notebooks 00–07"])),
 md("## Step 1: Remove Our Agents from the CoWork Object\n\n🛠️ Detach both agents from the shared "
    "singleton — the object itself is preserved for other teams."),
 sql("remove_from_cowork", "Remove Dev Agent from CoWork Object (keep the object)",
     f"USE ROLE ACCOUNTADMIN;\n"
     f"ALTER SNOWFLAKE INTELLIGENCE {COOBJ} DROP AGENT {AGENT};"),
 sql("remove_prod_from_cowork", "Remove Promoted Agent from CoWork Object",
     f"USE ROLE ACCOUNTADMIN;\n"
     f"ALTER SNOWFLAKE INTELLIGENCE {COOBJ} DROP AGENT {AGENT_PROD};"),
 md("## Step 2: Reset the CoWork Object Branding\n\n🛠️ The CoWork object "
    f"(`{COOBJ}`) is a shared singleton. At go-live (Notebook 05) we set its `BRAND_NAME`, "
    "`WELCOME_MESSAGE`, and accent colours. Because branding is **account-global**, cleanup "
    "reverts it to Snowflake defaults so no demo branding lingers for other teams.\n\n"
    "🔹 `UNSET` resets each property to its system default (the object itself is never dropped)."),
 sql("reset_branding", "Cleanup: Reset CoWork Object Branding to Defaults",
     "-- Reset the shared CoWork object branding to Snowflake defaults (undoes NB05 go-live branding).\n"
     f"USE ROLE ACCOUNTADMIN;\n"
     f"ALTER SNOWFLAKE INTELLIGENCE {COOBJ}\n"
     "  UNSET BRAND_NAME, WELCOME_MESSAGE, ACCENT_COLOR_LIGHT, ACCENT_COLOR_DARK;\n"
     f"USE ROLE {ADMIN};\n"
     "SELECT 'CoWork object branding reset to Snowflake defaults' AS STATUS;"),
 md("## Step 3: Drop the Demo Objects\n\n🛠️ Drop the budget, quota, and masking policy, then the "
    "database (CASCADE), warehouse, and roles. Dropping the database removes the agents, semantic view, "
    "search service, eval dataset, and stage in one step."),
 sql("drop_budget", "Drop Resource Budgets",
     f"DROP SNOWFLAKE.CORE.BUDGET IF EXISTS {DB}.AGENTS.DEMO_AGENT_BUDGET;\n"
     f"DROP SNOWFLAKE.CORE.BUDGET IF EXISTS {SHARED_BUDGET};"),
 sql("drop_quota", "Drop Per-User Quota",
     f"USE ROLE ACCOUNTADMIN;\nDROP SNOWFLAKE.CORE.QUOTA IF EXISTS {QUOTA};\nUSE ROLE {ADMIN};"),
 sql("unset_masking", "Unset Masking Policy from Column",
     f"ALTER TABLE IF EXISTS {DB}.ANALYTICS.CLIENTS MODIFY COLUMN EMAIL UNSET MASKING POLICY;"),
 sql("drop_objects", "Drop Demo Database, Warehouse, User & Roles",
     f"USE ROLE ACCOUNTADMIN;\n"
     f"DROP USER IF EXISTS {BIZUSER};\n"
     f"DROP DATABASE IF EXISTS {DB} CASCADE;\n"
     f"DROP WAREHOUSE IF EXISTS {WH};\n"
     f"DROP ROLE IF EXISTS {SIUSER};\n"
     f"DROP ROLE IF EXISTS {ADMIN};"),
 md("## Step 4: Verify Clean\n\n📌 All should return no rows / gone. The shared CoWork object should "
    "still exist (we only removed our agents from it)."),
 sql("verify_db_gone", "Verify: Demo Database Gone", f"SHOW DATABASES LIKE '{DB}';"),
 sql("verify_role_gone", "Verify: Demo Roles Gone", f"SHOW ROLES LIKE 'COWORK_ENTERPRISE_DEMO%';"),
 sql("verify_object_kept", "Verify: Shared CoWork Object Preserved",
     "SHOW SNOWFLAKE INTELLIGENCES;"),
 md(nb_complete("08",
    ["A clean account — all `COWORK_ENTERPRISE_DEMO*` objects removed",
     "The shared CoWork object preserved, with our agents detached and its branding reset to Snowflake defaults"],
    ["The demo is fully isolated, so cleanup is a handful of drops plus detaching our agents.",
     "Shared, pre-existing state (CoWork object, PUBLIC grants, guardrails) is never touched."],
    "That's the full lifecycle: context → govern → build → cost → evaluate/go-live → dev→prod → "
    "continuous improvement → cleanup. In a real deployment, also apply account-level hardening "
    "— network policies, SSO/IdP, SCIM, MFA, PrivateLink, and revoking `CORTEX_USER` from PUBLIC "
    "— in the customer's own account.")),
]

# =====================================================================
# NOTEBOOK 07 - CONTINUOUS IMPROVEMENT (self-improving loop)
# =====================================================================
n07 = [
 md(nb_header("Continuous Improvement", "07", "Continuous Improvement (Self-Improving Loop)",
    ["**Observes** real production usage to find failure patterns",
     "**Mines** failing questions into the curated evaluation dataset",
     "Runs an **Agent GPA baseline**, then **optimizes instructions only** (not tools)",
     "**Re-evaluates** to prove the change helped with no regressions, then promotes"],
    "a Self-Improving Agent Is Human-in-the-Loop",
    "🔹 Go-live is the start, not the end. A **self-improving agent** is a governed closed loop — **not** "
    "autonomous self-modification. You mine real usage for failures, score them with Agent GPA, improve "
    "the agent's **instructions** (the #1 lever — not more tools), and re-evaluate to prove it helped.\n\n"
    "```\n"
    "  observe traces  ->  mine failures  ->  curate eval set  ->  Agent GPA baseline\n"
    "        ^                                                          |\n"
    "        |                                                          v\n"
    "   re-evaluate  <-  optimize INSTRUCTIONS only  <-  analyze failure patterns\n"
    "```\n\n"
    "📌 **Fast path (recommended): CoCo.** The Cortex Code CLI drives this whole loop with the "
    "`cortex-agent` skill — `dataset-curation` to mine traces, `evaluate-cortex-agent` to score, and "
    "`optimize-cortex-agent` to draft + apply improved instructions. This notebook shows the SQL-native "
    "equivalent so you can see and schedule each step.",
    "25–30 minutes",
    ["Notebooks 00–05 complete (agent + registered eval dataset `DEMO_AGENT_EVALSET` + config stage)"])),
 sql("set_context", "Set Context",
     f"USE ROLE {ADMIN};\nUSE DATABASE {DB};\nUSE SCHEMA AGENTS;\nUSE WAREHOUSE {WH};"),
 md("## Step 1: Observe Production Usage\n"
    "Start from real interactions. Usage/latency/volume come from Account Usage; full step-by-step "
    "**traces** (planning, tool calls, errors) are in **AI & ML -> Agents -> DEMO_AGENT -> Monitoring** "
    "(AI Observability). Use those traces to spot wrong tool selection, redundant calls, and incomplete "
    "answers."),
 sql("observe_usage", "Observe: Recent Agent Traffic",
     "SELECT START_TIME, USER_NAME, AGENT_NAME, TOKENS, TOKEN_CREDITS\n"
     "FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_AGENT_USAGE_HISTORY\n"
     "WHERE AGENT_NAME = 'DEMO_AGENT'\nORDER BY START_TIME DESC\nLIMIT 25;"),
 md("## Step 2: Mine Failures into the Eval Set\n"
    "In CoCo: *\"Use the cortex agent dataset-curation skill to pull production traces for "
    f"{AGENT} and add the failing queries to {EVAL_DATASET} with ground truth.\"* "
    "The SQL equivalent: append the previously-failing question (with ground truth) to the curated "
    "table, then re-register the dataset. Here we add a harder synthesis question that tends to expose "
    "redundant tool calls."),
 sql("add_failing_case", "Curate: Append a Failing Case to the Bank",
     f"INSERT INTO {EVAL_TABLE} (INPUT_QUERY, GROUND_TRUTH)\n"
     "  SELECT 'Which region has the highest AUM, and are there compliance concerns for clients there?',\n"
     "    PARSE_JSON('{\"ground_truth_output\": \"Identifies the top region by AUM from structured data "
     "AND summarizes any compliance concerns for that region from research notes, citing both sources. "
     "Should make one Analyst call and one Search call - not repeated calls.\", "
     "\"ground_truth_invocations\": [{\"tool_name\": \"nexus_analytics\"}, {\"tool_name\": \"nexus_research\"}]}');"),
 sql("reregister_eval_dataset", "Curate: Re-Register the Updated Dataset",
     f"DROP DATASET IF EXISTS {EVAL_DATASET};\n"
     f"CALL SYSTEM$CREATE_EVALUATION_DATASET(\n"
     f"  'Cortex Agent',\n  '{EVAL_TABLE}',\n  '{EVAL_DATASET}',\n"
     "  OBJECT_CONSTRUCT('query_text', 'INPUT_QUERY', 'expected_tools', 'GROUND_TRUTH')\n);"),
 md("## Step 3: Baseline Evaluation (Agent GPA)\n"
    "Run the scored evaluation from Notebook 05 against the updated dataset to establish a **baseline** "
    "for the current LIVE spec. (Uses the config staged in Notebook 05.)\n\n"
    "```sql\n"
    "CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', 'baseline'),\n"
    f"  '@{EVAL_STAGE}/agent_eval.yaml');\n"
    "-- Poll STATUS until COMPLETED, then read scores + find the lowest-scoring queries:\n"
    "SELECT INPUT, METRIC_NAME, EVAL_AGG_SCORE\n"
    "FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(\n"
    f"  '{DB}', 'AGENTS', 'DEMO_AGENT', 'CORTEX AGENT', 'baseline'))\n"
    "ORDER BY EVAL_AGG_SCORE ASC;\n"
    "```"),
 md("## Step 4: Optimize — Instructions Only\n"
    "The lever is **instructions, not tools**. In CoCo: *\"Based on the failure analysis, generate "
    "improved orchestration and response instructions... only update the instructions... apply the "
    "changes.\"* The SQL equivalent replaces the LIVE version's spec - here we add explicit efficiency "
    "and routing rules to `instructions.orchestration` and keep every tool identical.\n\n"
    "> `MODIFY LIVE VERSION SET SPECIFICATION` is whole-spec replacement (omitted fields are removed), "
    "so we submit the full spec with only the instructions changed. Version the change with a COMMENT."),
 sql("optimize_instructions", "Optimize: Update Instructions (tools unchanged)",
     f"ALTER AGENT {AGENT} MODIFY LIVE VERSION SET SPECIFICATION =\n$$\n" + AGENT_SPEC_BODY_V2 + "$$;\n"
     f"ALTER AGENT {AGENT} SET COMMENT = 'v2 - instruction-only optimization (efficiency + routing rules)';"),
 sql("verify_spec", "Verify: Updated Spec Is Live", f"DESCRIBE AGENT {AGENT};"),
 md("## Step 5: Re-Evaluate and Compare\n"
    "Re-run the same dataset and compare to baseline. Ship the change only if the target metric "
    "improves **and** there are no regressions on previously-passing queries.\n\n"
    "```sql\n"
    "CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', 'after_optimize'),\n"
    f"  '@{EVAL_STAGE}/agent_eval.yaml');\n"
    "-- Side-by-side once both runs are COMPLETED:\n"
    "WITH b AS (SELECT METRIC_NAME, AVG(EVAL_AGG_SCORE) s FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(\n"
    f"    '{DB}','AGENTS','DEMO_AGENT','CORTEX AGENT','baseline')) GROUP BY 1),\n"
    "  a AS (SELECT METRIC_NAME, AVG(EVAL_AGG_SCORE) s FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(\n"
    f"    '{DB}','AGENTS','DEMO_AGENT','CORTEX AGENT','after_optimize')) GROUP BY 1)\n"
    "SELECT b.METRIC_NAME, b.s AS BASELINE, a.s AS AFTER_OPT, a.s - b.s AS DELTA\n"
    "FROM b JOIN a USING (METRIC_NAME) ORDER BY DELTA;\n"
    "```\n\n"
    "**If it improved:** promote the new spec to prod via Notebook 06 (the spec is the source of "
    "truth). **If not:** revert (`ALTER AGENT ... MODIFY LIVE VERSION SET SPECIFICATION = $$ <prior "
    "spec> $$`) and try a different instruction change. Schedule this loop (e.g. a monthly `TASK`) to "
    "keep the agent improving on real usage."),
 md("## What This Is (and Isn't)\n"
    "- **Is:** a governed, auditable loop - every change is a versioned spec edit, gated by evaluation, "
    "promoted through dev->prod.\n"
    "- **Isn't:** the agent editing itself. A human reviews the proposed instruction change and the "
    "before/after scores before anything ships.\n"
    "- **Primary lever:** instruction quality and data/semantic-model quality - not adding tools."),
 md(nb_complete("07",
    ["A failing case mined into the eval dataset and re-registered",
     "An instruction-only optimization applied to the LIVE spec (tools unchanged), versioned by COMMENT",
     "A baseline-vs-after comparison pattern to prove improvement without regressions"],
    ["Instructions - not more tools - are the primary improvement lever.",
     "Every change is a versioned, evaluated spec edit; a human approves before it ships.",
     "Schedule the loop (e.g. a monthly TASK) so the agent keeps improving on real usage."],
    "That completes the build lifecycle. Promote a validated improvement to prod via **Notebook 06**, "
    "and when you're done, run **Notebook 08** to clean up.")),
]


write_nb("Notebook_00_Lab_Setup.ipynb", n00)
write_nb("Notebook_01_Context_Layer.ipynb", n01)
write_nb("Notebook_02_Govern_Access.ipynb", n02)
write_nb("Notebook_03_Build_Harden_Agent.ipynb", n03)
write_nb("Notebook_04_Control_Cost.ipynb", n04)
write_nb("Notebook_05_Evaluate_GoLive_Operate.ipynb", n05)
write_nb("Notebook_06_Dev_to_Prod.ipynb", n06)
write_nb("Notebook_07_Continuous_Improvement.ipynb", n07)
write_nb("Notebook_08_Cleanup.ipynb", n08)
print("DONE")
