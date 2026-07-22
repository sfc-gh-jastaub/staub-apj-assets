---
name: staub-live-demo-driver
description: "Live demo driver for building Snowflake use-case demos with CoCo. Preloads account facts, behavior rails, and hard-won gotchas so in-demo prompts stay short and every build runs first-try — for ANY use case. Load this ONCE at the top of a demo session. Triggers: demo driver, load demo rails, start the demo, preload gotchas, demo flow, new use case demo."
---

# CoCo Demo Driver

Load this once at the start of a live demo session. It sets the behavior rails and preloads the gotchas so the presenter can paste short prompts and each build runs cleanly in front of an audience. The presenter runs each prompt here, then pastes it into Slack for people to follow along — so keep prompts and confirmations clean and copyable.

This skill is **use-case agnostic**: account-level facts are fixed, but the database, schema, and object names come from whatever use case you're building this session (see Session setup).

## Session setup (confirm once, then reuse all session)

At the first build request, establish and remember for the rest of the session:

- **Target database + schema** for this use case (create if needed). Do not hardcode — take it from the user's prompt or the design doc; ask once only if truly absent.
- **Working folders**: `01_Context/` (canvas, narrative), `02_Design/` (design doc), `03_Build/` (numbered build scripts `NN_*`).

Everything in **Account facts** below is fixed and should never be asked.

## Behavior rails (apply to EVERY build request this session)

- **Move fast, minimal narration.** One sentence before the first tool call; short updates at key moments; a **one-line confirmation** at the end (+ any URL/link). No long summaries — the presenter narrates.
- **No clarifying questions.** Make reasonable assumptions and proceed. If a genuinely ambiguous choice exists, state the assumption in one line and keep going — do not stop and ask.
- **Skip plan mode.** These are pre-scoped builds; implement directly.
- **Author → execute → fix-in-file → keep in sync.** Write scripts to `03_Build/` (numbered `NN_*`), execute against Snowflake, and if a statement fails, fix the file and re-run so the artifact always matches what ran.
- **Execute for real** against the account — don't just draft SQL. The audience needs live results.
- **Set-based SQL only** for data work (no row-by-row loops). For AI functions, call them as **column expressions over the table**, never loop per row.

## Account facts (fixed — never ask)

| Thing | Value |
|---|---|
| Account | `SFSEEUROPE-DEMO_STAUB_US_WEST_2_PRIMARY` (org `sfseeurope`, account `demo_staub_us_west_2_primary`) |
| Default warehouse | `ADHOC_WH` (override only if the use case specifies another) |
| Role | `ACCOUNTADMIN` |
| Region | `AWS_US_WEST_2` |
| `snow` CLI connection (PUT / deploy / upload) | `staub_uswest_primary` |

> Database, schema, and object names are **per use case** — never hardcoded here. Placeholders below: `<DB>`, `<SCHEMA>`, `<VIEW>`, `<STAGE>`.

## Gotchas (the things that cost a retry last time — do these up front)

### Synthetic data
- `RANDOM(seed)` **rejects a per-row column** as its seed ("argument must be constant"). Generate deterministic synthetic data with **`HASH`** instead: `ABS(HASH(n)) % k` for buckets, `lo + ABS(HASH(n, salt)) % range` for ranges. Deterministic = reproducible across rebuilds (no demo surprises).
- Give each field a distinct salt (`HASH(n, 7)`, `HASH(n, 11)`, …) so columns aren't correlated.

### Cortex AI functions
- **Verify the model before relying on it**: `SELECT AI_COMPLETE('<model>', 'Say OK')`. In this account `claude-3-5-sonnet` is often unavailable — **`llama3.1-8b`** is broadly available and fast.
- **`AI_COMPLETE` output must be cast `::string`** (and ideally `TRIM(..., '" ')` to strip model quote-wrapping) **before** feeding it into `AI_CLASSIFY` / `AI_SENTIMENT` — otherwise you get *"Failed to cast variant value … to OBJECT"*.
- Extraction paths (confirmed structures):
  - `AI_CLASSIFY(text, ['A','B'])` → `{"labels":["A"]}` → `AI_CLASSIFY(...):labels[0]::string`
  - `AI_SENTIMENT(text)` → `{"categories":[{"name":"overall","sentiment":"negative"}]}` → `AI_SENTIMENT(...):categories[0]:sentiment::string`
- **Keep the working set small** (`LIMIT ~20`) for AI calls — latency is the #1 on-stage risk. Persist AI output to a table once, then read it downstream instead of recomputing.

### Streamlit in Snowflake
- Deploy via **stage + `CREATE STREAMLIT`**; in the app use `get_active_session()` (not `st.connection` secrets). Upload files with `snow stage copy <file> @<DB>.<SCHEMA>.<STAGE> --overwrite -c staub_uswest_primary`.
- Theme via **`.streamlit/config.toml`** on the stage: Snowflake blue `#29B5E8`, text `#11567F`, `base="light"`.
- When using the `developing-with-streamlit-in-snowflake` skill, load only the **`sf/` sub-skill**, name the scaffold (e.g. `dashboard-metrics-snowflake`) + the `snowflake` theme, and **skip the OSS/env-detection path** (we deploy to SiS, not local).
- Caveat: newer Streamlit APIs (`st.container(horizontal=...)`, `segmented_control`) may error on an older SiS runtime — if a panel breaks, swap to `st.columns`.

### Cortex Agent
- `CREATE AGENT … FROM SPECIFICATION` **does not accept a custom dollar tag** like `$spec$` — use **`$$`** (safe as long as the spec JSON has no `$$`).
- Wire the text-to-SQL tool to this use case's **semantic view** (`<DB>.<SCHEMA>.<VIEW>`); add `data_to_chart` for visual answers. A brand-new agent needs no clone.

### Snowflake Workspace notebooks
- The `write` tool **refuses `.ipynb`**, and `notebook_add_cell` **can't set SiS SQL-cell metadata** (`%%sql -r`, `resultVariableName`). So author the notebook by **writing the `.ipynb` JSON directly via a bash heredoc**, then validate with `python3 -c "import json; json.load(...)"`.
- Default = **Workspace notebook, no connection code**; SQL cells with `%%sql -r <var>` + matching `"name"`/`"resultVariableName"` metadata; every cell needs a unique 8-char `id`.
- Upload with `cortex artifact create notebook "<Name>" "<abs path>" -c staub_uswest_primary`. Deeplink: `https://app.snowflake.com/sfseeurope/demo_staub_us_west_2_primary/#/workspaces/ws/USER%24/PUBLIC/DEFAULT%24/<file>.ipynb`.

## Skill activation (load only what's needed, fast)

| Build | Load | Notes |
|---|---|---|
| Streamlit app | `developing-with-streamlit-in-snowflake` | `sf/` sub-skill only; name scaffold + `snowflake` theme; skip OSS/env-detection |
| Notebook | `snowflake-notebooks` | load create + deploy guidance only |
| Cortex Agent | `cortex-agent` | CREATE intent; new agent, no clone |
| Semantic view | `semantic-view` | when building/debugging a semantic view |

## Layer pattern (typical build order for a use case)

Adapt names to the use case; the shape is reusable:

`RAW sources → curated unified view/dynamic table → scored/enriched view (+ explainable reasons) → governance (masking policy, roles) → semantic view → Cortex Agent (wired to the semantic view) → Streamlit app → notebook (Cortex AI functions)`. All build scripts numbered in `03_Build/NN_*`.

## How the presenter uses this

1. Load this skill once at the top of the session; confirm the target `<DB>.<SCHEMA>` for this use case.
2. For each step, paste a short prompt naming just the artifact + intent (e.g. *"Build & deploy the Streamlit dashboard on `<DB>.<SCHEMA>.<VIEW>`."*). The rails and gotchas above are already in effect — no need to repeat them.
3. CoCo confirms in one line + link; presenter pastes the prompt into Slack for the audience.
