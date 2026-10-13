# Synthetic data for agentic evaluations

How do you build and test an AI agent properly **without putting real customers into dev**?

This demo answers that for a mortgage origination agent, end to end in one Snowflake account:

| Step | What it shows |
|---|---|
| **1. Protect** | Prod customer data is masked for the dev team (masking policies) |
| **2. Generate** | One `GENERATE_SYNTHETIC_DATA` call creates fully artificial, joined tables, with a built-in privacy filter and stable synthetic IDs |
| **3. Scorecard** | 23 checks that the synthetic data matches prod (mix, spread, shape), joins up, and contains nothing real |
| **4. Test** | A golden set of 20 questions whose answers are **computed by SQL** from the data, so the answer key refreshes with the data |
| **5. Evaluate** | Cortex Agent v1 vs v2 scored with Agent Evaluations, including a custom LLM judge for lending conduct |
| **6. Promote** | The tested agent goes to prod unchanged (only the data location swaps) and must score inside the dev range on real data |
| **7. At scale** *(optional)* | A 20M-row table, over the 14M-rows-per-call limit, generated in two calls that still agree on one ID per customer |

`MORTGAGE_PROD` and `MORTGAGE_DEV` stand in for separate environments. All data is generated; nothing here is real.

## What's in this folder

| File | What it is |
|---|---|
| `setup_1_core.sql` | **Required.** Builds everything the notebook needs, in one run |
| `setup_2_at_scale.sql` | Optional. The 20M-row two-call build for notebook section 7 |
| `synthetic_data_agentic_evaluations.ipynb` | The demo notebook. Every code cell is SQL except the two charts |
| `dev/` | Maintainer tools: the script that generates the notebook, and a test harness that runs it cell by cell |

## Before you start

- A role with **ACCOUNTADMIN** (setup creates databases, a role, warehouses, a secret and masking policies)
- **Enterprise edition** or higher (masking policies and synthetic data generation)
- **Anaconda terms accepted** for the account (needed by synthetic data generation); setup checks this first and stops if they are not
- **Cortex** models `claude-sonnet-4-5` (agent) and `claude-sonnet-4-6` (judge). If they are not in your region, enable cross-region inference:
  `ALTER ACCOUNT SET CORTEX_ENABLED_CROSS_REGION = 'ANY_REGION';`

## Quick start

### 1. Get the files into a Snowflake Workspace

**Option A: connect a workspace to this repo (recommended).** Once, as ACCOUNTADMIN:

```sql
CREATE API INTEGRATION IF NOT EXISTS GITHUB_STAUB_APJ_ASSETS
  API_PROVIDER = git_https_api
  API_ALLOWED_PREFIXES = ('https://github.com/sfc-gh-jastaub/')
  ENABLED = TRUE;
```

Then in Snowsight: **Projects » Workspaces » From Git repository**, paste `https://github.com/sfc-gh-jastaub/staub-apj-assets`, pick the `GITHUB_STAUB_APJ_ASSETS` integration, choose **Public repository**, and create. Open the `synthetic_data_agentic_evaluations_demo` folder.

**Option B: import the files.** Download this folder and upload the two `.sql` files and the `.ipynb` into any workspace.

### 2. Run setup 1 (about 20-30 minutes)

Open `setup_1_core.sql` and **Run All** (make sure the role is ACCOUNTADMIN). It:

1. creates the warehouses (`AI_WH`, `SYNTH_GEN_WH`), databases, masking policies, consistency secret and `DEMO_DEV_ROLE` (granted to you)
2. seeds "prod": 5,000 applicants, applications and properties
3. generates the frozen synthetic copy the agent uses (`MORTGAGE_DEV.CORE_SYNTH`)
4. creates the scorecard procedure and prints a status summary
5. creates the semantic view and the agent with two versions
6. builds the golden questions, evaluation dataset and configs, and starts 4 dev baseline runs (v1 ×2, v2 ×2)
7. promotes the tested agent to prod (definition only), recomputes the golden answers on prod and starts 2 prod runs
8. waits for all 6 runs to finish (most of the time goes here)

The run names are recorded in `MORTGAGE_DEV.CORE_EVAL.BASELINE_RUNS`; the notebook reads them from there.

From a terminal instead: `snow sql -c <connection> --enable-templating NONE -f setup_1_core.sql`

### 3. Optional: run setup 2 (about 30-40 minutes, about 2-3 credits)

Only needed for section 7. Open `setup_2_at_scale.sql` and **Run All**. Skip it and the rest of the notebook still runs.

### 4. Run the notebook

Open `synthetic_data_agentic_evaluations.ipynb`, connect it to a notebook service when prompted, and run the cells top to bottom. The markdown cells carry the talking points.

- Section 2 generates a fresh synthetic copy live (about 2 minutes) into the scratch schema `CORE_LIVE`; the frozen copy, agent and baseline runs are never touched, so the notebook is safe to rerun.
- Section 5 starts a live evaluation run; the last cells of the notebook show its scores once it completes (a few minutes).
- Cells that chain statements use Snowflake's `->>` operator: in the statement after `->>`, `$1` is the result of the statement just before it, and `$2` the one before that.

## Good to know

- **The privacy filter removes rows per table**, so the finishing step (`MORTGAGE_PROD.ADMIN.FINISH_SYNTHETIC`) keeps only complete applications and recalculates derived values. How many rows the filter removes varies by run, so a fresh copy occasionally shows one or two "Same mix" checks AMBER (5-8 points off). Setup prints the scorecard summary; rerun setup section 3 if you want the frozen copy all GREEN.
- **Same customer, same synthetic ID, every run**: the consistency secret is created once (`IF NOT EXISTS`). Rerunning setup keeps the same IDs.
- **Rerunning setup 1** replaces the agents, so it starts a fresh set of baseline runs and updates `BASELINE_RUNS`. Old runs can be removed in Snowsight (AI & ML » Agents » APPLICATION_AGENT » Evaluations).
- **Limits** (per call): up to 14M rows and 100 columns per input table, up to 5 tables. Setup 2 shows how to go beyond that.

## Clean up

```sql
USE ROLE ACCOUNTADMIN;
DROP DATABASE IF EXISTS MORTGAGE_PROD;
DROP DATABASE IF EXISTS MORTGAGE_DEV;
DROP ROLE IF EXISTS DEMO_DEV_ROLE;
DROP WAREHOUSE IF EXISTS SYNTH_GEN_WH;
DROP WAREHOUSE IF EXISTS SCALE_GEN_WH;   -- only if you ran setup 2
-- AI_WH is a common name: drop it only if setup created it for you
```

## Maintaining the notebook

The notebook is generated: edit `dev/build_notebook.py`, then run `python3 dev/build_notebook.py`. To prove every cell runs, after setup 1:

```bash
SNOWFLAKE_CONNECTION_NAME=<connection> python3 dev/test_notebook.py              # full run, includes live generation
SNOWFLAKE_CONNECTION_NAME=<connection> python3 dev/test_notebook.py --skip-generate
```
