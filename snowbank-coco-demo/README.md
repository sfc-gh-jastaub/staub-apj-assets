# SnowBank — Cortex Code Demo

A 30-minute live demo showing how a real business problem becomes a working Snowflake analytics and AI solution — without writing SQL by hand.

**The scenario.** SnowBank, a mid-size retail bank, has a pain point: the Head of Risk can't get clean answers out of her data fast enough, and the Data Platform Lead is stuck stitching together half-built layers in a half-migrated warehouse. Two short discovery sessions are written up — one with each stakeholder — and that's the entire starting point.

**What Cortex Code does with it.** Reads the discovery notes, drafts a solution design, builds a three-layer Snowflake database, stands up a Cortex Analyst semantic view, creates a Cortex Agent in Snowflake Intelligence, attaches a reusable HTML-report skill and an email tool, delivers a polished report to the user's inbox, and writes the runbook to hand the engagement over. All in one session.

> Originally presented at Deloitte TechWeek 2026 — New Zealand. [Slides (PDF)](./Techweek%202026_Snowflake_v2.pdf)

---

## Architecture

```
+------+     +---------+     +-----------+     +----------+     +----------+     +----------+
| Raw  | --> | Curated | --> | Analytics | --> |  Cortex  | --> |  Cortex  | --> | Snowflake|
| land |     | conform |     |  aggs &   |     | Analyst  |     |  Agent   |     |   Intel  |
| zone |     | entities|     |   views   |     | (sem-vw) |     | + skills |     |   chat   |
+------+     +---------+     +-----------+     +----------+     +----------+     +----------+
```

## How the demo flows

| Scene | What happens | Time |
|---|---|---|
| **1 · Design** | Cortex Code reads the stakeholder notes and produces a solution brief. | ~4 min |
| **2 · Build** | In Plan mode, the Raw → Curated → Analytics layers are written and executed. Two business questions are asked of the gold layer — one of them surfaces a real problem buried in the data. | ~6 min |
| **3 · Intelligence** | A semantic view and a Cortex Agent are stood up in Snowflake Intelligence. A chart is saved as an artefact and a deep-research investigation is kicked off. | ~9 min |
| **4 · Deliver** | A prebuilt report skill and an email tool are activated on the agent. One sentence in chat — *"summarise, format, email"* — and a polished HTML report lands in your inbox. The engagement is then documented end-to-end. | ~8 min |

---

## Prerequisites

| Requirement | Notes |
|---|---|
| **Snowflake account** | Any commercial region. ACCOUNTADMIN role used throughout to avoid privilege issues. |
| **Snowflake Intelligence enabled** | Required for Scenes 3 & 4. Deep research / swarm should be enabled in your tenant. |
| **Cortex Code installed** | <https://docs.snowflake.com/en/user-guide/cortex-code/cortex-code> |
| **Snowflake CLI connection configured** | Cortex Code uses the Snowflake CLI's connection store — set up a connection: <https://docs.snowflake.com/en/developer-guide/snowflake-cli/connecting/connect> |
| **Email integration** | An email address on the `ALLOWED_RECIPIENTS` list of a notification integration (created during Scene 4). Update `Demo/04_Assets/tools/send_email_tool.sql` to point at *your* email before you start. |

---

## Folder layout

```
Demo/
├── 01_Context/
│   ├── head_of_risk_notes.md        # Sarah Chen — business persona
│   └── data_platform_lead_notes.md  # Raj Patel — technical persona
├── 02_Design/
│   └── solution_brief_template.md   # Coco fills this in Scene 1
├── 03_Build/
│   ├── 01_database_setup.sql        # DB / schemas / WH / asset stage
│   └── 02_raw.sql                   # Set-based raw seed (~16k rows, ~2 sec)
└── 04_Assets/
    ├── skills/html_report/          # Prebuilt HTML report skill
    └── tools/send_email_tool.sql    # Prebuilt email custom tool

DemoNarrative/
├── demo_intro_onepager.md           # Audience-facing one-pager
└── demo_presenter_narrative.md      # Full presenter script with stage directions
```

---

## One-time setup (~5 min)

1. **Clone this repo** and open it in your Cortex Code workspace.
2. **Edit your email** in `Demo/04_Assets/tools/send_email_tool.sql`:
   ```sql
   ALLOWED_RECIPIENTS = ('your.email@example.com')
   ```
3. **Open Cortex Code** in your IDE with the project root as the working directory. Confirm your Snowflake connection is active.
4. **Open Snowflake Intelligence** in a separate browser tab and sign in.

You don't need to run any SQL by hand — Coco will execute the database setup as part of Scene 2.

---

## Run the demo — exact prompts

Run these in order. Switch contexts (Cortex Code ↔ Snowflake Intelligence) where noted.

### Scene 1 · Build the solution design from discovery notes (~4 min)

*Two markdown files of stakeholder input become a structured solution brief.*

> *In Cortex Code:*

**Prompt 1**
```
Read everything in Demo/01_Context/. Using the template at
Demo/02_Design/solution_brief_template.md, produce
Demo/02_Design/solution_brief.md — persona, objective, scope, high-level
flow, and skeleton design (pseudo-DDL only). Demo-grade.
```

---

### Scene 2 · Build the data layer (~6 min)

*Coco builds Raw → Curated → Analytics in Plan mode, then we ask the gold layer two questions.*

> *In Cortex Code, **toggle Plan mode ON** before submitting Prompt 2.*

**Prompt 2**
```
Using Demo/02_Design/solution_brief.md, build the data layer in Snowflake.
Use the sql-author skill to validate columns and table shape before
writing each new script.

Execute these in order:
  1. Demo/03_Build/01_database_setup.sql  (already exists — run as-is)
  2. Demo/03_Build/02_raw.sql             (already exists — run as-is,
     it generates all four raw tables in one set-based pass)
  3. Demo/03_Build/03_curated.sql         (you write this — conformed,
     cleansed entities derived from raw)
  4. Demo/03_Build/04_analytics.sql       (you write this — aggregations
     and behavioural views ready for Cortex Analyst)

For 03 and 04: write set-based SQL only. No row-by-row INSERTs. No
Python. If a script fails, debug and re-run.
```

*Approve the plan. Coco builds the layers.*

**Prompt 3** — *the warm-up*
```
Quick question — using the analytics views you just built, show me the
headline trends in SnowBank's transactions over the last 6 months. One
short answer.
```

**Prompt 4** — *the discovery*
```
Quick question — zoom in on the last 90 days. Are there any customer
segments whose transaction behaviour has shifted versus their historical
baseline? Be specific.
```

> Q4 surfaces concentrated structuring activity, an international-transfer spike, and elevated decline rates in private wealth — exactly the signal Sarah's been chasing.

---

### Bridge · Kick off the intelligence build (~60–90 sec)

> *Still in Cortex Code. **Plan mode OFF.***

**Prompt 5**
```
Use the semantic-view skill to build a Cortex Analyst semantic view
called SNOWBANK_SEMANTIC_VIEW over the analytics layer.

Then use the cortex-agent skill to create a Cortex Agent called
SNOWBANK_RISK_AGENT that uses the semantic view. Make sure the agent is
registered and active in Snowflake Intelligence.
```

> **Tip:** while this runs, tour the new database in Snowsight — `SNOWBANK_DEMO` → `RAW` / `CURATED` / `ANALYTICS`. It buys time and proves the data layer is real.

---

### Scene 3 · Use the agent in Snowflake Intelligence (~9 min)

*The agent is live. Three questions take it from re-confirmation to a chart artefact to a deep investigation.*

> *Switch to the Snowflake Intelligence tab and select `SNOWBANK_RISK_AGENT`.*
>
> **If the agent isn't visible in SI:** open it in Snowsight (AI & ML → Cortex Agents → `SNOWBANK_RISK_AGENT`) and click **Add to Snowflake Intelligence** at the top of the page, then refresh the SI tab.

**SI Question 1** — *the broader team can ask the same question now*
```
Which customer segments show the most unusual transaction behaviour in
the last 90 days?
```

**SI Question 2** — *save the chart as an artefact*
```
Show me the monthly trend of international transfer volume by customer
segment for the last 12 months.
```

**SI Question 3** — *triggers deep research / swarm*
```
Investigate the structuring patterns we're seeing. Profile the customers
involved, characterise the transactions, and recommend three immediate
actions for the Risk team. Be thorough.
```

> **As soon as deep research starts running**, switch back to Cortex Code and fire **Prompt 6** below. Leave it running, then return to SI. By the time deep research finishes, the new skill and tool will be live on the agent.

---

### Scene 4 · Reporting & documentation (~8 min)

*Activate the prebuilt report skill and email tool on the live agent, then ship the report and document the engagement.*

> *In Cortex Code:*

**Prompt 6**
```
Use the cortex-agent skill to extend SNOWBANK_RISK_AGENT.

1. Activate the prebuilt HTML report skill at
   Demo/04_Assets/skills/html_report/ — upload it to the agent's stage
   and add it via the Skills tab.

2. Run Demo/04_Assets/tools/send_email_tool.sql to create the email
   notification integration and SEND_REPORT_EMAIL stored procedure, then
   attach that procedure as a generic tool on the agent.

Confirm both are live in Snowflake Intelligence.
```

> *Switch back to Snowflake Intelligence — same chat thread as Scene 3.*

**SI Question 4** — *summarise, format, email, all in one*
```
Summarise that analysis, use the html_report skill to format it into a
concise report, and email it to me at your.email@example.com.
```

> *Switch back to Cortex Code:*

**Prompt 7** — *close the loop*
```
Document the engagement. Update Demo/02_Design/solution_brief.md with
what was actually deployed (data layers, semantic view, agent, tools,
skills). Then generate a runbook in
Demo/02_Design/runbook.md covering how the SnowBank team operates and
extends this. Save the email HTML output into Demo/02_Design/artefacts/.
```

---

## Teardown

```sql
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS SNOWBANK_DEMO;
DROP WAREHOUSE IF EXISTS SNOWBANK_DEMO_WH;
DROP NOTIFICATION INTEGRATION IF EXISTS SNOWBANK_EMAIL_INT;
-- Drop the agent and semantic view via the Snowsight UI.
```

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| `02_raw.sql` runs slowly | Confirm warehouse is at least XSMALL and not suspended. |
| Coco rewrites `02_raw.sql` from scratch | Re-emphasise *"already exists — run as-is"* in Prompt 2. |
| Agent doesn't appear in Snowflake Intelligence | Open it in Snowsight and click **Add to Snowflake Intelligence**, then refresh the SI tab. |
| Email isn't delivered | Confirm `ALLOWED_RECIPIENTS` matches your address; smoke-test the notification integration. |
| Plan mode plan looks off | Reject and re-prompt with corrections — that's the auditability story. |

---

## Bundled skills used

This demo intentionally uses only **bundled** Cortex Code skills — no custom plugins required.

- `sql-author` — SQL authoring with column/table validation
- `semantic-view` — Cortex Analyst semantic-view authoring
- `cortex-agent` — Cortex Agent CRUD + tool/skill attachment

---

## Credits

Built with Snowflake Cortex Code. **SnowBank**, **Sarah Chen**, and **Raj Patel** are fictional; data is synthetic.
