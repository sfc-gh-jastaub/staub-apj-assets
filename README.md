# staub-apj-assets

Ready-to-run Snowflake demos, hands-on workshops and Cortex Code (CoCo) build methods, from Partner Solutions Engineering in APJ.
The demos and workshops run end to end in a single Snowflake account on generated data; each folder is self-contained and has its own README.

## What's here

| Asset | Type | What it shows | Snowflake features | Time | Start here |
|---|---|---|---|---|---|
| [**Synthetic data for agentic evaluations**](synthetic_data_agentic_evaluations_demo) | Demo | Build and test a Cortex Agent without real customers in dev: mask prod, generate a synthetic copy, prove it matches prod, score agent v1 vs v2, promote to prod behind a score gate | Synthetic data generation, masking policies, semantic views, Cortex Agents, Agent Evaluations (incl. custom LLM judge) | ~20-30 min one-off setup, then the notebook | [README](synthetic_data_agentic_evaluations_demo/README.md) |
| [**GST analytics & AI workshop**](gsi-tax-gst-workshop) | Hands-on workshop | A tax team's monthly GST position across three ERPs: conform the ledgers, reconcile to the lodged BAS, then add AI-assisted classification, working papers and an agent | Snowflake Notebooks, Streamlit, Time Travel, zero-copy clone, AI_CLASSIFY, AI_COMPLETE, semantic views, Cortex Agents | Half day (2 labs) | [README](gsi-tax-gst-workshop/README.md) |
| [**CoWork enterprise runbook**](cowork_enterprise_guide) | Notebook series | A production runbook that takes a CoWork (Snowflake Intelligence) agent from raw tables to a governed, cost-controlled, evaluated, business-user-ready deployment, for a fictional buy-side firm ("Strive Capital") | Semantic views, Cortex Search, Cortex Agents, AI_REDACT, budgets, cost-centre tags, per-user quotas, Agent Evaluations, CoWork | 9 SQL notebooks, run in order | [README](cowork_enterprise_guide/README.md) |
| [**SnowBank CoCo demo**](snowbank-coco-demo) | Live demo | A retail bank's Head of Risk and Data Platform Lead discovery notes become a full solution in one CoCo session: design brief → Raw/Curated/Analytics layers → semantic view + agent → HTML report emailed from Snowflake Intelligence | Cortex Code, Cortex Analyst, Cortex Agents, Snowflake Intelligence, agent skills + custom email tool | ~30 min | [README](snowbank-coco-demo/README.md) |
| [**Snow Ambition use-case method**](snow-ambition-usecase-method) | CoCo method | A paste-in-order prompt playbook that turns a one-page use case canvas into a full demo: narrative → design → data → semantic view + agent → Streamlit → React app → notebook | Cortex Code, Cortex Agents, Streamlit, Snowflake Notebooks | One session | [Playbook](snow-ambition-usecase-method/snow-ambition-prompt-playbook.md) |

### In a little more detail

**[synthetic_data_agentic_evaluations_demo](synthetic_data_agentic_evaluations_demo)**: answers *"how do we test an agent properly without putting real customers into dev?"* for a mortgage origination agent. One setup script builds everything (an optional second script adds a 20M-row "at scale" section). The notebook is SQL-first, Python only draws the two charts, and its markdown carries the talking points.

**[gsi-tax-gst-workshop](gsi-tax-gst-workshop)**: a self-directed, half-day workshop for tax consultants with strong SQL/Excel skills who are new to Snowflake. Participants work from `GSI_TAX_WorkshopMaterial/`: a setup notebook, two lab notebooks with matching HTML read-along guides, and a reset notebook. The rest of the folder is source and build tooling.

**[cowork_enterprise_guide](cowork_enterprise_guide)**: nine Snowflake Workspace SQL notebooks (`Notebook_00`–`Notebook_08`) following *Govern → Build → Go Live*: context layer, least-privilege access with `AI_REDACT` masking, a hardened agent, layered cost controls, an evaluation gate, dev→prod promotion and a continuous-improvement loop. Everything lives in an isolated `COWORK_ENTERPRISE_DEMO` database and is safe on shared accounts. `CoWork_Enterprise_Overview.html` is the narrative companion; `build_notebooks.py` regenerates the notebooks.

**[snowbank-coco-demo](snowbank-coco-demo)**: a 30-minute, four-scene live demo (Design, Build, Intelligence, Deliver) originally presented at Deloitte TechWeek 2026 NZ. `Demo/` holds the stakeholder notes, brief template, seed SQL and the prebuilt report skill and email tool; `DemoNarrative/` holds the audience one-pager and presenter script. Set your own email in `Demo/04_Assets/tools/send_email_tool.sql` before running.

**[snow-ambition-usecase-method](snow-ambition-usecase-method)**: two pieces for building a new use-case demo live with CoCo:
- `snow-ambition-prompt-playbook.md`: the prompts, in order, written so an audience can paste along.
- `staub-live-demo-driver/SKILL.md`: a CoCo skill the presenter loads once to preload behaviour rails and known gotchas, so each build runs first time. Edit its *Account facts* table for your own account before using it.

## How to use an asset

**Option A: connect a Snowflake Workspace to this repo (recommended).** Once, as ACCOUNTADMIN:

```sql
CREATE API INTEGRATION IF NOT EXISTS GITHUB_STAUB_APJ_ASSETS
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/sfc-gh-jastaub/')
  ENABLED = TRUE;
```

Then in Snowsight: **Projects » Workspaces » From Git repository**, paste `https://github.com/sfc-gh-jastaub/staub-apj-assets`, pick the `GITHUB_STAUB_APJ_ASSETS` integration and choose **Public repository**. Every asset's files are then available in the workspace; use **Pull** to pick up updates.

**Option B: download.** Clone or download the repo and upload the files for the asset you want into a workspace.

Then open the asset's README and follow its run order (usually: run a setup script or notebook once, then the demo or lab notebooks).

## Conventions

- **Self-contained folders.** Each asset creates its own databases, warehouses and roles, and its README lists them and explains how to clean up.
- **Generated data only.** No customer or personal data is used anywhere; every "real" dataset is seeded deterministically.
- **ACCOUNTADMIN is a demo baseline**, chosen so setup is reproducible in a trial or demo account. It is not a production posture: anything taken beyond a demo should use a role with only the grants it needs.
- **Prerequisites vary by asset** (for example Enterprise edition, Anaconda terms, or Cortex cross-region inference). Check the asset README before running setup.

## Notes

These are field-built examples shared to help partners and customers get hands-on quickly. They are not official Snowflake product documentation and are provided as-is. Feature availability can vary by edition, cloud and region; check the [Snowflake documentation](https://docs.snowflake.com) for the current state of any feature used here.

Questions or suggestions: open an issue on this repo.
