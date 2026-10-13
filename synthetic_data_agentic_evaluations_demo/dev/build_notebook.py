"""Builds ../synthetic_data_agentic_evaluations.ipynb (Snowflake Workspace notebook, nbformat 4.5).
Every code cell is SQL except the two charts. Edit the CELLS list below, then run: python3 dev/build_notebook.py
Test end to end (after setup_1_core.sql): python3 dev/test_notebook.py [--skip-generate]
"""
import json, hashlib, pathlib, re

OUT = pathlib.Path(__file__).resolve().parent.parent / "synthetic_data_agentic_evaluations.ipynb"
CELLS = []


def md(text):
    CELLS.append(("markdown", None, text.strip("\n")))


def py(text):
    CELLS.append(("python", None, text.strip("\n")))


def sql(name, text):
    CELLS.append(("sql", name, text.strip("\n")))


# Shared SQL fragments (pasted into cells as plain text, so each cell reads on its own)
METRIC_LABEL = """DECODE(SPLIT_PART(metric_name, ':', 1),
                  'answer_correctness',        'Answer correctness',
                  'logical_consistency',       'Logical consistency',
                  'tool_selection_accuracy',   'Tool selection',
                  'lending_policy_compliance', 'Lending policy')"""
METRIC_ORDER = "DECODE(\"Metric\", 'Answer correctness', 1, 'Logical consistency', 2, 'Tool selection', 3, 4)"


def eval_rows(label_col, label, db, run_var):
    # run_var: a session variable set in the setup cell from MORTGAGE_DEV.CORE_EVAL.BASELINE_RUNS
    return (f"SELECT '{label}' AS {label_col}, ${run_var} AS run, metric_name, eval_agg_score\n"
            f"    FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA('{db}', 'CORE_AGENT', 'APPLICATION_AGENT', 'CORTEX AGENT', ${run_var}))")


def ask_agent(question):
    body = json.dumps({"stream": False, "messages": [{"role": "user", "content": [{"type": "text", "text": question}]}]})
    call = lambda v: f"PARSE_JSON(SNOWFLAKE.CORTEX.DATA_AGENT_RUN('MORTGAGE_DEV.CORE_AGENT.APPLICATION_AGENT!{v}',\n        $${body}$$))"
    return f"""
-- Ask both versions of the dev agent the same question; keep only the text parts of each reply
WITH replies AS (
    SELECT 'VERSION$1' AS version, {call('VERSION$1')} AS reply
    UNION ALL
    SELECT 'VERSION$2', {call('VERSION$2')}
)
SELECT version AS "Agent version", LISTAGG(part.value:text::STRING, ' ') AS "Answer"
FROM replies, LATERAL FLATTEN(reply:content) AS part
WHERE part.value:type::STRING = 'text'
GROUP BY version
ORDER BY version"""


# --------------------------------------------------------------------------------------
md("""
# Synthetic test data for mortgage agents
## Prod → synthetic → scorecard → agent evaluation → promote to prod

**The question:** how do you build and test an origination agent properly *without* putting real customers into dev?

| Step | What we'll show |
|---|---|
| **1. Protect** | Prod customer data is masked for the dev team |
| **2. Generate** | One call creates fully artificial data, with a built-in privacy filter |
| **3. Scorecard** | The synthetic data matches prod, joins up, and contains nothing real |
| **4. Test** | A golden question set with answers computed from the synthetic data |
| **5. Evaluate** | Agent v1 vs v2, scored automatically: the improvement loop |
| **6. Promote** | The tested agent goes to prod unchanged, and scores the same on real data |

> Everything runs in **one Snowflake account**, with `MORTGAGE_PROD` and `MORTGAGE_DEV` standing in for separate environments.

**Before you start:** run `setup_1_core.sql` once (it builds the data, agent and baseline evaluations). `setup_2_at_scale.sql` is optional and only needed for section 7.
""")

md("""
### Setup
Sets the role and warehouse, loads the names of the baseline evaluation runs that setup recorded, and picks a name for the live evaluation run started in section 5. Every code cell in this notebook is **SQL**, except the two charts.

> **Reading the SQL:** `->>` runs several statements in order inside one cell. In the statement after `->>`, `$1` means *the result of the statement just before it* (`$2` the one before that).
""")

sql("setup", """
USE ROLE ACCOUNTADMIN
->> USE WAREHOUSE AI_WH
->> SET (DEV_V1_R1, DEV_V1_R2, DEV_V2_R1, DEV_V2_R2, PROD_R1, PROD_R2) = (
        SELECT MAX(IFF(run_key = 'DEV_V1_R1', run_name, NULL)), MAX(IFF(run_key = 'DEV_V1_R2', run_name, NULL)),
               MAX(IFF(run_key = 'DEV_V2_R1', run_name, NULL)), MAX(IFF(run_key = 'DEV_V2_R2', run_name, NULL)),
               MAX(IFF(run_key = 'PROD_R1', run_name, NULL)),   MAX(IFF(run_key = 'PROD_R2', run_name, NULL))
        FROM MORTGAGE_DEV.CORE_EVAL.BASELINE_RUNS)
->> SET LIVE_RUN = 'live_v2_' || TO_CHAR(SYSDATE(), 'YYYYMMDD_HH24MISS')
->> SELECT CURRENT_ACCOUNT() AS "Account", CURRENT_ROLE() AS "Role", CURRENT_WAREHOUSE() AS "Warehouse",
           $DEV_V1_R1 || ', ' || $DEV_V2_R1 || ', ' || $PROD_R1 || ' ...' AS "Baseline runs (from setup)",
           $LIVE_RUN AS "Live evaluation run name"
""")

# --------------------------------------------------------------------------------------
md("""
---
## 1 · Protect: prod is masked for the dev team

The same query as **`DEMO_DEV_ROLE`** (the consultancy) and as **`ACCOUNTADMIN`** (the bank's data owner).

> **Talking point:** masking is a policy on the column, so it applies to every tool and every query, not just this notebook.
""")

PROTECT_QUERY = """SELECT CURRENT_ROLE() AS "Running as", applicant_id, full_name, email, date_of_birth, employment_type, declared_income
    FROM MORTGAGE_PROD.CORE.APPLICANT
    ORDER BY applicant_id
    LIMIT 3"""

sql("protect_as_dev_team", f"""
-- The consultancy's role: names, emails and dates of birth come back masked
USE ROLE DEMO_DEV_ROLE
->> {PROTECT_QUERY}
""")

sql("protect_as_data_owner", f"""
-- The bank's data owner: same query, real values (this also switches the notebook back to ACCOUNTADMIN)
USE ROLE ACCOUNTADMIN
->> {PROTECT_QUERY}
""")

# --------------------------------------------------------------------------------------
md("""
---
## 2 · Generate: one call, fully artificial data

`GENERATE_SYNTHETIC_DATA` learns the statistical profile of the three prod tables (5,000 rows each) and writes **brand-new rows** into the `CORE_LIVE` scratch schema.

| Setting | Why |
|---|---|
| `join_key` on the IDs | Synthetic IDs still join across all three tables |
| `replace: name / email` | Realistic-looking but fake names and emails |
| `similarity_filter: TRUE` | Built-in privacy filter: drops any synthetic row that is too close to a real customer |
| `consistency_secret` | Same synthetic IDs every run, so test cases stay stable |

> **While this runs (~2 minutes):** this is exactly how setup built the frozen copy the agent uses (`CORE_SYNTH`). Live runs only write to `CORE_LIVE`, so the demo is safe to rerun.
""")

sql("generate", """
USE WAREHOUSE SYNTH_GEN_WH            -- Snowpark-optimised, nothing else runs on it
->> USE SCHEMA MORTGAGE_PROD.ADMIN    -- the secret reference below is session-scoped
->> CALL SNOWFLAKE.DATA_PRIVACY.GENERATE_SYNTHETIC_DATA({
      'datasets': [
        { 'input_table': 'MORTGAGE_PROD.CORE.APPLICANT',   'output_table': 'MORTGAGE_DEV.CORE_LIVE.APPLICANT',
          'columns': { 'applicant_id': {'join_key': TRUE, 'replace': 'uuid'},
                       'full_name': {'replace': 'name'}, 'email': {'replace': 'email'} } },
        { 'input_table': 'MORTGAGE_PROD.CORE.APPLICATION', 'output_table': 'MORTGAGE_DEV.CORE_LIVE.APPLICATION',
          'columns': { 'application_id': {'join_key': TRUE, 'replace': 'uuid'}, 'applicant_id': {'join_key': TRUE, 'replace': 'uuid'} } },
        { 'input_table': 'MORTGAGE_PROD.CORE.SECURITY',    'output_table': 'MORTGAGE_DEV.CORE_LIVE.SECURITY',
          'columns': { 'security_id': {'join_key': TRUE, 'replace': 'uuid'}, 'application_id': {'join_key': TRUE, 'replace': 'uuid'} } }
      ],
      'similarity_filter': TRUE,
      'consistency_secret': SYSTEM$REFERENCE('SECRET', 'SYNTH_SECRET', 'SESSION', 'READ')::STRING,
      'replace_output_tables': TRUE
    })
""")

md("""
**Finishing step:** keep only **complete applications** (applicant + application + property) and recalculate the property value from loan and LVR.
""")

sql("finish_generation", """
USE WAREHOUSE AI_WH
->> CALL MORTGAGE_PROD.ADMIN.FINISH_SYNTHETIC('CORE_LIVE')
->> SELECT table_name                AS "Table",
           rows_after_privacy_filter AS "Rows after privacy filter",
           rows_kept                 AS "Complete applications kept"
    FROM $1
""")

md("**Check the fresh copy:** it joins up and contains nothing real.")

sql("live_copy_checks", """
-- Run the scorecard on the new copy, then keep just the two areas that matter here
CALL MORTGAGE_DEV.CORE_EVAL.BUILD_SCORECARD('CORE_LIVE')
->> SELECT "Check area", "Check", "Synthetic", "Status"
    FROM $1
    WHERE "Check area" IN ('Tables join', 'Nothing real')
""")

md("""
**Same customer, same fake ID, every run.** The copy we just made and the frozen copy were generated separately, but the `consistency_secret` maps each real ID to the same synthetic ID every time. (The privacy filter keeps a slightly different set of rows each run, so we compare the applications present in both.)

> **Talking point:** test cases that point at a specific application keep working after every refresh, and the links between tables are identical.
""")

sql("consistency_check", """
SELECT (SELECT COUNT(*) FROM MORTGAGE_DEV.CORE_LIVE.APPLICATION)  AS "Applications: new copy",
       (SELECT COUNT(*) FROM MORTGAGE_DEV.CORE_SYNTH.APPLICATION) AS "Applications: frozen copy",
       COUNT(*)                                                    AS "In both, same synthetic ID",
       COUNT_IF(l.applicant_id = f.applicant_id)                   AS "...and same synthetic applicant",
       COUNT_IF(l.applicant_id <> f.applicant_id)                  AS "Mismatched links"
FROM MORTGAGE_DEV.CORE_LIVE.APPLICATION l
JOIN MORTGAGE_DEV.CORE_SYNTH.APPLICATION f USING (application_id)
""")

# --------------------------------------------------------------------------------------
md("""
---
## 3 · Scorecard: does the synthetic data look like prod?

The full scorecard for the frozen copy the agent and evaluations use. Five areas, each with a stated tolerance:

| Area | Question |
|---|---|
| **Same mix** | Broker share, self-employed share, approvals, loan purpose, LVR bands within 5 points |
| **Same spread** | Loan, income and property value percentiles within 5% |
| **Same shape** | Whole distributions match (K-S distance ≤ 0.05) |
| **Tables join** | Every application has an applicant and a property |
| **Nothing real** | No copied applications, names, emails or IDs |

> **Talking point:** this is what you hand a model-risk or test lead before anyone tests against the data.
""")

sql("scorecard", """
CALL MORTGAGE_DEV.CORE_EVAL.BUILD_SCORECARD('CORE_SYNTH')
""")

# --------------------------------------------------------------------------------------
md("""
---
## 4 · Test: a golden question set built from the synthetic data

20 questions of three types: **aggregate** ("How many applications have an LVR above 90%?"), **entity** ("What's the LVR on application `<id>`?") and **behaviour** ("Will my application be approved?").

> **Talking point:** the expected answers are **computed by SQL, not typed in**. Refresh the synthetic data and the answer key refreshes with it.
""")

sql("golden_questions", """
SELECT t.q_type AS "Type", d.input_query AS "Question", d.ground_truth:ground_truth_output::STRING AS "A correct answer must say"
FROM MORTGAGE_DEV.CORE_EVAL.EVAL_TEMPLATE t JOIN MORTGAGE_DEV.CORE_EVAL.EVAL_DATA d USING (id)
WHERE t.id IN (2, 3, 5, 12, 17, 19)
ORDER BY t.id
""")

# --------------------------------------------------------------------------------------
md("""
---
## 5 · Evaluate: agent v1 vs v2

The agent answers questions through a semantic view over the synthetic data. **VERSION$1** has basic instructions; **VERSION$2** adds lending conduct (no approval promises, no personal advice, never share another applicant's data).

> **Talking point:** both get the numbers right. The difference is on **behaviour**, where the real risk for a lender sits.
""")

md("**A numbers question:** *How many applications have an LVR above 90%?*")
sql("ask_lvr_question", ask_agent("How many applications have an LVR above 90%?"))

md("**A behaviour question:** *Will my application be approved?*")
sql("ask_approval_question", ask_agent("Will my application be approved?"))

md("""
### Scored on all 20 questions, twice per version

| Metric | What it checks |
|---|---|
| **Answer correctness** | Matches the computed answer, within tolerance |
| **Logical consistency** | Instructions, plan and tool calls make sense together |
| **Tool selection** | Uses the data tool when it should, and not when it shouldn't |
| **Lending policy** | *Custom judge:* no promises, no advice, no leaking other people's data |

> **Talking point:** the improvement loop: **evaluate → read the failures → fix the instructions → re-evaluate → compare.**
""")

sql("dev_scores", f"""
-- Average score per metric for v1 and v2, from the two baseline evaluation runs per version that setup started.
-- The custom lending judge scores 0-10, so it is divided by 10 to sit on the same 0-1 scale.
WITH results AS (
    {eval_rows('version', 'v1', 'MORTGAGE_DEV', 'DEV_V1_R1')}
    UNION ALL
    {eval_rows('version', 'v1', 'MORTGAGE_DEV', 'DEV_V1_R2')}
    UNION ALL
    {eval_rows('version', 'v2', 'MORTGAGE_DEV', 'DEV_V2_R1')}
    UNION ALL
    {eval_rows('version', 'v2', 'MORTGAGE_DEV', 'DEV_V2_R2')}
),
run_scores AS (
    SELECT version, run,
           {METRIC_LABEL} AS metric,
           AVG(eval_agg_score) / IFF(metric = 'Lending policy', 10, 1) AS score
    FROM results
    WHERE metric_name IS NOT NULL
    GROUP BY version, run, metric
)
SELECT metric                                        AS "Metric",
       ROUND(AVG(IFF(version = 'v1', score, NULL)), 2) AS "v1",
       ROUND(AVG(IFF(version = 'v2', score, NULL)), 2) AS "v2"
FROM run_scores
GROUP BY metric
ORDER BY {METRIC_ORDER}
""")

py('''
# Chart of the table above (Python is only used for drawing)
import matplotlib.pyplot as plt

scores = dev_scores.to_pandas().set_index("Metric")
ax = scores.plot(kind="bar", figsize=(9, 3.6), rot=0, width=0.7, ylim=(0.6, 1.05), color=["#8A9BA8", "#29B5E8"])
for bars in ax.containers:
    ax.bar_label(bars, fmt="%.2f", fontsize=9)
ax.set_title("Average score by metric: v1 vs v2", fontsize=13, loc="left")
ax.set_xlabel(None)
ax.legend(title=None, frameon=False, loc="lower right")
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.show()
''')

md("""
**Start a fresh run live** on VERSION$2 (named in the setup cell, a few minutes). Meanwhile in Snowsight: **AI & ML → Agents → `APPLICATION_AGENT` → Evaluations** → tick a v1 and a v2 run → **Compare** → click a record for the trace and the judge's reasoning.
""")

sql("start_live_evaluation", """
USE SCHEMA MORTGAGE_DEV.CORE_EVAL    -- evaluation runs execute in the session schema
->> CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', $LIVE_RUN), '@MORTGAGE_DEV.CORE_EVAL.EVAL_CONFIG/eval_v2.yaml')
""")

# --------------------------------------------------------------------------------------
md("""
---
## 6 · Promote: the tested agent goes to prod unchanged

**Promote the definition, not the data.** The prod semantic view and agent are the tested dev `VERSION$2`, with only the data location swapped (`MORTGAGE_DEV.CORE_SYNTH` → `MORTGAGE_PROD.CORE`). The same 20 questions then get their correct answers from prod's own data.

> **Talking point:** nothing is rewritten by hand for prod. If anyone edited prod directly, these checks would show it.
""")

sql("promote_semantic_view", r"""
-- Compare the dev and prod semantic view definitions line by line; show only the lines that differ
WITH dev  AS (SELECT index, value AS line FROM TABLE(SPLIT_TO_TABLE(GET_DDL('SEMANTIC_VIEW', 'MORTGAGE_DEV.CORE_AGENT.APPLICATION_SV'), '\n'))),
     prod AS (SELECT index, value AS line FROM TABLE(SPLIT_TO_TABLE(GET_DDL('SEMANTIC_VIEW', 'MORTGAGE_PROD.CORE_AGENT.APPLICATION_SV'), '\n')))
SELECT REGEXP_SUBSTR(dev.line,  'MORTGAGE_[A-Z_]+[.][A-Z_]+[.][A-Z_]+') AS "Dev reads",
       REGEXP_SUBSTR(prod.line, 'MORTGAGE_[A-Z_]+[.][A-Z_]+[.][A-Z_]+') AS "Prod reads",
       COUNT(*) OVER () || ' of ' || (SELECT COUNT(*) FROM dev) || ' lines differ' AS "Lines that differ"
FROM dev JOIN prod USING (index)
WHERE dev.line <> prod.line
""")

sql("promote_agent_spec", """
-- Prod agent VERSION$1 vs the tested dev VERSION$2: identical once the semantic view location is swapped
SHOW VERSIONS IN AGENT MORTGAGE_DEV.CORE_AGENT.APPLICATION_AGENT
->> SHOW VERSIONS IN AGENT MORTGAGE_PROD.CORE_AGENT.APPLICATION_AGENT
->> SELECT PARSE_JSON(prod."agent_spec") = PARSE_JSON(dev."agent_spec")
               AS "Prod spec = dev spec, as is",
           PARSE_JSON(prod."agent_spec") = PARSE_JSON(REPLACE(dev."agent_spec", 'MORTGAGE_DEV.CORE_AGENT', 'MORTGAGE_PROD.CORE_AGENT'))
               AS "Prod spec = dev spec, with only the semantic view swapped"
    FROM $2 AS dev, $1 AS prod      -- $2 = dev versions, $1 = prod versions
    WHERE dev."name" = 'VERSION$2' AND prod."name" = 'VERSION$1'
""")

md("""
**Promotion gate:** the rule a CI pipeline would apply. Prod scores (real data) must land inside the range measured in dev (synthetic data).

> **Talking point:** testing on synthetic data predicted how the agent behaves in production, without the consultancy ever seeing a real customer.
""")

sql("promotion_gate", f"""
-- PASS if the prod average (real data) is no lower than the lowest dev v2 run (synthetic data), allowing 0.05
WITH results AS (
    {eval_rows('env', 'dev', 'MORTGAGE_DEV', 'DEV_V2_R1')}
    UNION ALL
    {eval_rows('env', 'dev', 'MORTGAGE_DEV', 'DEV_V2_R2')}
    UNION ALL
    {eval_rows('env', 'prod', 'MORTGAGE_PROD', 'PROD_R1')}
    UNION ALL
    {eval_rows('env', 'prod', 'MORTGAGE_PROD', 'PROD_R2')}
),
run_scores AS (
    SELECT env, run,
           {METRIC_LABEL} AS metric,
           AVG(eval_agg_score) / IFF(metric = 'Lending policy', 10, 1) AS score
    FROM results
    WHERE metric_name IS NOT NULL
    GROUP BY env, run, metric
),
summary AS (
    SELECT metric,
           MIN(IFF(env = 'dev', score, NULL))  AS dev_low,
           MAX(IFF(env = 'dev', score, NULL))  AS dev_high,
           AVG(IFF(env = 'prod', score, NULL)) AS prod_avg
    FROM run_scores
    GROUP BY metric
)
SELECT metric                 AS "Metric",
       ROUND(dev_low, 2)      AS "Dev lowest run (synthetic)",
       ROUND(dev_high, 2)     AS "Dev highest run (synthetic)",
       ROUND(prod_avg, 2)     AS "Prod average (real)",
       IFF(prod_avg >= dev_low - 0.05, 'PASS', 'REVIEW') AS "Status"
FROM summary
ORDER BY {METRIC_ORDER}
""")

# --------------------------------------------------------------------------------------
md("""
---
## 7 · At scale: a table bigger than one call allows

One call handles **up to 14 million rows per table** (5 tables, 100 columns per call). So what happens with a bigger table?

Ahead of time, `setup_2_at_scale.sql` built a **20 million-row** applications table (about 12 million applicants, many with several applications) and generated it the way you would in production:

```
MORTGAGE_PROD.SCALE.APPLICATION_20M  (20M rows: over the limit)
      │  split by a hash of application_id  →  every row in exactly one half
      ├── half 1 (~10M) ──► call 1 ─┐   same consistency_secret on both calls,
      └── half 2 (~10M) ──► call 2 ─┤   so a real applicant gets ONE fake ID
                                    ▼   even if their applications are in different halves
MORTGAGE_DEV.SCALE_SYNTH.APPLICATION_20M  (stitched: 20M rows, generation_call = 1 or 2)
```
""")

sql("scale_runs", """
-- The two generation calls (recorded by setup_2_at_scale.sql), plus a total row
SELECT 'Call ' || generation_call AS "Generation call", input_rows AS "Rows in", synthetic_rows AS "Synthetic rows out",
       minutes AS "Minutes", warehouse_size || ' Snowpark-optimised' AS "Warehouse", NULL AS "Credits"
FROM MORTGAGE_DEV.CORE_EVAL.SCALE_SPLIT_RUN
UNION ALL
SELECT 'Total', SUM(input_rows), SUM(synthetic_rows), SUM(minutes), NULL, ANY_VALUE(credits_both_calls)
FROM MORTGAGE_DEV.CORE_EVAL.SCALE_SPLIT_RUN
ORDER BY 1
""")

md("""
### Do the statistics hold up across the two calls?

Each call only ever saw its own half. If splitting caused problems, the halves would drift from prod or from each other. The scorecard (computed over all 40M rows when the run finished) compares prod with **each call separately** and with the **combined** table, using the same tolerances as before (the status is the worst of the three).

> **Talking point:** both calls land on prod's numbers independently, so stitching them back together changes nothing. And every applicant whose applications were split across the two calls still has exactly one synthetic ID: the shared secret does that.
""")

sql("split_scorecard", """
SELECT * EXCLUDE sort_order
FROM MORTGAGE_DEV.CORE_EVAL.SPLIT_SCORECARD
ORDER BY sort_order
""")

sql("loan_distribution", """
-- Loan amount histogram (60 buckets from $150k to $2M) as a % of each source's rows, ready to chart
SELECT source AS "Source", loan_k AS "Loan amount ($k)", pct AS "% of applications"
FROM (SELECT source, bucket,
             (150 + (bucket - 0.5) * (1850 / 60))::FLOAT  AS loan_k,
             (100 * n / SUM(n) OVER (PARTITION BY source))::FLOAT AS pct    -- share of ALL rows for that source
      FROM MORTGAGE_DEV.CORE_EVAL.SPLIT_LOAN_DIST)
WHERE bucket BETWEEN 1 AND 60
ORDER BY source, bucket
""")

py('''
# Chart of the table above (Python is only used for drawing)
import matplotlib.pyplot as plt

dist = loan_distribution.to_pandas()
fig, ax = plt.subplots(figsize=(9, 3.4))
for source, style in (("Prod (20M)", dict(color="#8A9BA8", lw=5, alpha=0.6)),
                      ("Call 1", dict(color="#29B5E8", lw=1.8)),
                      ("Call 2", dict(color="#11567F", lw=1.8, ls="--"))):
    rows = dist[dist["Source"] == source]
    ax.plot(rows["Loan amount ($k)"], rows["% of applications"], label=source, **style)
ax.set_title("Loan amount distribution: prod vs each generation call", fontsize=13, loc="left")
ax.set_xlabel("Loan amount ($k)")
ax.set_ylabel("% of applications")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)
plt.tight_layout()
plt.show()
''')

md("""
| If you need… | Do this |
|---|---|
| **Test data for agents** (this demo) | A representative sample is enough. Agent evaluations need hundreds of well-chosen cases, not billions of rows |
| **Realistic data for the whole estate** | Exactly the pattern above: split big tables into pieces of up to 14M rows, one call per piece (max 5 tables per call), **same `consistency_secret`** everywhere, stitch. Schedule it as a task |
| **Volume for load or performance tests** | Generate once, then multiply in SQL (`GENERATOR()` + `UUID_STRING()` for new IDs). Fast and cheap; adds volume rather than new statistics |
""")

# --------------------------------------------------------------------------------------
md("""
---
## Questions you'll get

| Question | Answer |
|---|---|
| **"What about unstructured documents?"** | Generate payslips, bank statements and employer letters from each synthetic application with `AI_COMPLETE`, plant known problems (income mismatch, missing document) at the rates seen in prod's missing-information history, and score a verification agent on what it catches |
| **"Our lodgement data is JSON."** | Flatten the JSON into columns before generating, then rebuild the payload from the synthetic columns with `OBJECT_CONSTRUCT` |
| **"What about free-text notes?"** | High-cardinality text is redacted by the function, by design. Regenerate notes from each synthetic row with `AI_COMPLETE` |
| **"We need more hard cases than prod has."** | Pick the test set from the synthetic data by segment (self-employed, LVR right on 80% or 90%, declines) and oversample the hard groups; report scores per group |
| **"Dev and prod are separate accounts."** | Same pattern: generate in prod, share the synthetic tables to the dev account through a secure share or organisation listing. The consultancy's account never has prod access |
| **"How often do we refresh it?"** | Schedule generation + scorecard as a task (e.g. quarterly); the golden answers recompute automatically |
""")

md("""
---
## How you'd run this for real

| Piece | Tool |
|---|---|
| Generation + scorecard | A scheduled **task** in prod; the scorecard is the release check for each refresh |
| Semantic views, schemas, grants per environment | **DCM Projects** with `{{env}}` templating: `plan` shows the diff, `deploy` promotes dev → test → prod |
| Agent definition | Spec in **git**; prod version created from the reviewed file (`ALTER AGENT … ADD VERSION FROM @repo/…`) |
| Evidence | **CI** runs the same evaluation in each environment and blocks promotion if prod falls outside the dev range |
""")

md("""
---
## Live evaluation result
Check the status; once it shows **COMPLETED**, run the next cell. Scores should sit inside the v2 range above.
""")

sql("live_evaluation_status", """
USE SCHEMA MORTGAGE_DEV.CORE_EVAL
->> CALL EXECUTE_AI_EVALUATION('STATUS', OBJECT_CONSTRUCT('run_name', $LIVE_RUN), '@MORTGAGE_DEV.CORE_EVAL.EVAL_CONFIG/eval_v2.yaml')
""")

sql("live_evaluation_scores", f"""
SELECT {METRIC_LABEL} AS "Metric",
       ROUND(AVG(eval_agg_score) / IFF("Metric" = 'Lending policy', 10, 1), 2) AS "Live run score"
FROM TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA('MORTGAGE_DEV', 'CORE_AGENT', 'APPLICATION_AGENT', 'CORTEX AGENT', $LIVE_RUN))
WHERE metric_name IS NOT NULL
GROUP BY "Metric"
ORDER BY {METRIC_ORDER}
""")

md("""
---
## Recap

| | |
|---|---|
| **Protect** | Real PII is masked by policy; dev only ever works on synthetic data |
| **Generate** | One call, three joined tables, built-in privacy filter, stable IDs |
| **Scorecard** | Mix, spread and shape match prod; tables join; nothing real carried over |
| **Test** | 20 golden questions with answers computed from the data |
| **Evaluate** | Repeatable scores; v1 → v2 improvement measured |
| **Promote** | Same definition in prod; prod scores inside the dev range |
| **Scale** | A 20M-row table, over the per-call limit, generated in two calls; both match prod and keep one ID per applicant |
""")

md("""
### Appendix: reset the scratch schema
Only clears the live-generated tables. Frozen data, agent and evaluations are untouched. Paste into a SQL cell to run:

```sql
CREATE OR REPLACE SCHEMA MORTGAGE_DEV.CORE_LIVE
->> GRANT USAGE ON SCHEMA MORTGAGE_DEV.CORE_LIVE TO ROLE DEMO_DEV_ROLE
```
""")


# --------------------------------------------------------------------------------------
def to_cell(kind, name, src):
    cid = hashlib.md5((kind + (name or "") + src).encode()).hexdigest()[:8]
    if kind == "sql":
        # Workspace SQL cells are Jinja templates: a stray {{ }} {% %} {# #} would be mangled
        assert not re.search(r"\{\{|\}\}|\{%|%\}|\{#|#\}", src), f"Jinja-like token in SQL cell {name}"
        src = f"%%sql -r {name}\n{src}"
    lines = src.split("\n")
    source = [l + "\n" for l in lines[:-1]] + [lines[-1]]
    if kind == "markdown":
        return {"cell_type": "markdown", "id": cid, "metadata": {}, "source": source}
    meta = {"codeCollapsed": False}
    if kind == "sql":
        meta.update({"language": "sql", "name": name, "resultVariableName": name})
    return {"cell_type": "code", "id": cid, "execution_count": None, "metadata": meta, "outputs": [], "source": source}


nb = {
    "cells": [to_cell(*c) for c in CELLS],
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"codemirror_mode": {"name": "ipython", "version": 3}, "file_extension": ".py",
                          "mimetype": "text/x-python", "name": "python", "nbconvert_exporter": "python",
                          "pygments_lexer": "ipython3", "version": "3.11.0"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
ids = [c["id"] for c in nb["cells"]]
assert len(ids) == len(set(ids)), "duplicate cell ids"
OUT.write_text(json.dumps(nb, indent=1, ensure_ascii=False))
n_sql = sum(1 for c in CELLS if c[0] == "sql")
n_py = sum(1 for c in CELLS if c[0] == "python")
print(f"wrote {OUT} ({len(CELLS)} cells: {n_sql} SQL, {n_py} Python)")
