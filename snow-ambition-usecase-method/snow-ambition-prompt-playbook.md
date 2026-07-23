# Demo Prompt Playbook — Snowflake Use-Case Build (CoCo)

A reusable sequence for building a full Snowflake demo (data → intelligence → app → notebook) by pasting prompts into CoCo. Works for **any** use case — fill the placeholders below, then paste each block in order. Run it in CoCo, then paste the same block into Slack for your audience to follow.

---

> ## 🎬 FOR DEMO PRESENTER ONLY
>
> **Do NOT share or paste this block to the audience** — it's a personal accelerator that makes the live run fast and reliable. Everyone else skips straight to Step 1 and gets the full narrative experience.
>
> Paste this **once** at the very top of your CoCo session, before Step 1:
>
> ```
> Load /staub-live-demo-driver. For the rest of this conversation: Live demo — move fast, minimal narration, no clarifying questions, skip plan mode, one-line confirmations. Rails and gotchas from the driver skill apply to every step from here on.
> ```
>
> With this loaded you can trim the `Live demo — …` rails line from each build prompt below (it's already in effect). The audience-facing prompts stay exactly as written so their experience is unchanged.

---

## Step 1 — Load context (folders + use case canvas)

Attach your use-case canvas screenshot to this message before sending.

```
Create 3 folders: 01_Context, 02_Design, 03_Build. Turn this screenshot into a clean .md file and put it in 01_Context.
```

---

## Step 2 — Construct the demo narrative

Attach (or reference) the canvas .md from Step 1.

```
Act as a Senior Partner at a Big4 consultancy pitching a high-stakes 10-minute demo to an executive audience (Budget Owners, CxOs). You have deep industry domain knowledge and expert-level understanding of Snowflake's data cloud and native capabilities.

Transform the use case canvas in 01_Context into a compelling, logical, highly persuasive 10-minute demo narrative. Output a polished .md file in 01_Context. Follow this EXACT 6-part structure and headings:

1. The Issue ("The Crisis") — the client's current problem: broken processes, siloed data, lost time, executive pain. Set the stakes.
2. The Solution ("The Architecture") — high-level Snowflake architecture; how data flows raw → curated → intelligent action, replacing their "sticky tape" solutions.
3. Demo Part 1: [custom title] — Business Workflow / Snowflake Capability / Impact.
4. Demo Part 2: [custom title] — builds on Part 1, same three-part style.
5. Demo Part 3: [custom title] — the climax, same style.
6. Solution Benefits & Summary — recap metrics moved (Before vs After) for the board.

Emphasize Before vs After with quantifiable metrics; weave domain knowledge with specific Snowflake features; keep one continuous narrative thread from crisis to board-level outcome.
```

---

## Step 3 — High-level design document

```
Based on that narrative, design the SIMPLEST demo that still illustrates every point. Write a concise high-level design doc in 02_Design. Cover architecture, data flow, and demo flow (mapped to the narrative parts, with rough timings). Code at pseudo-code level only. Don't include a governance feature demo, just use sysadmin for entire thing. 
```

---

## Step 4 — Build the data layer

```
Build the data layer per 02_Design. Use/create database snow_ambition_demo_db, schema {SCHEMA}, warehouse {WAREHOUSE}.
Author scripts to {BUILD_DIR}/ (numbered) → execute against Snowflake → fix-in-file if it fails → keep in sync.
Set-based SQL only. No row-by-row INSERTs. No Python. Generate synthetic data deterministically (HASH-based, not RANDOM with a per-row seed). One-line confirmation when done.
Don't need huge datasets, just what is reasonable for a concise demo. 
Should be bronze -> silver -> gold. Use dynamic tables for integration + presentation. Should be only 1 or two tables in gold. 
```

---

## Step 5 — Build the AI / intelligence layer (semantic view + Cortex Agent)

```
Build the rest of the core solution per 02_Design, on top of the data layer in {DB}.{SCHEMA} (warehouse {WAREHOUSE}). 
At minimum: a semantic view over the relevant gold table (s), and a Cortex Agent wired to that semantic view. Do NOT build Streamlit or any ML model yet — that's the final phase.
Author each script to {BUILD_DIR}/ (numbered) → execute → fix-in-file if it fails → keep in sync. Set-based SQL only. No Python. Make reasonable assumptions. One-line confirmation per layer. Only pause if something needs my decision or credentials.
```

---

## Step 6 — Build & deploy the Streamlit dashboard

```
Use the developing-with-streamlit-in-snowflake skill → sf/ sub-skill only. Load just the {SCAFFOLD} scaffold + the snowflake theme. Skip the OSS/env-detection path (we deploy to SiS, not local).
Build & deploy a {APP_PURPOSE} dashboard on {DB}.{SCHEMA}.{TABLE_OR_VIEW}, warehouse {WAREHOUSE}. Adapt the scaffold's KPI-card + chart/table-toggle + popover-filter patterns to this data; apply the snowflake theme via .streamlit/config.toml. Deploy via stage + CREATE STREAMLIT using get_active_session().
Author to {BUILD_DIR}/ → deploy → fix-in-file if it fails. One-line confirmation + URL.
```

---

## Step 7 — (New thread) Upgrade the dashboard to a React app

Start a **fresh CoCo thread** for this step (skills/context don't carry across threads).

```
Rebuild the Streamlit {APP_PURPOSE} dashboard as an awesome modern React app and run it locally. Add a few high-WOW features and make it sleek and modern. Read the deployed Streamlit app in {BUILD_DIR} for the data + layout to match. State your framework + WOW-feature choices in one line, then build.
```

---

## Step 8 — Build a Snowflake notebook showcasing Cortex AI functions

```
Use the snowflake-notebooks skill — load only create + deploy guidance, skip general authoring/exploration.
Build, deploy & run a Snowflake notebook in {DB}.{SCHEMA} (warehouse {WAREHOUSE}) that showcases Cortex AI functions on {TABLE_OR_VIEW}. Pick the most interesting, demo-worthy analysis and choose from AI_CLASSIFY, AI_SENTIMENT, AI_EXTRACT, AI_SUMMARIZE_AGG, AI_COMPLETE, AI_FILTER. If the data has no free text, generate a synthetic text column first so the AI functions have something rich to work on. Aim for a clear "so what" business insight at the end.
Concise & easy to follow: short markdown intro per section, one AI step per cell, show the result, ~6-8 cells. Call AI functions as column expressions over the table (never loop per row). Keep the working set small (~20 rows) so it runs fast. Author to {BUILD_DIR}/ → deploy → run top-to-bottom → fix-in-file if a cell errors. State your chosen analysis in one line, then build. Notebook link when done.
```

---

## Reset (optional) — tear down between rehearsals

```
Drop and recreate schema {DB}.{SCHEMA} so we can re-run the whole playbook clean. One-line confirmation.
```

---

## Cross-use-case gotchas (tips, not prompts)

Reusable across any use case — good to know when a step needs a nudge:

- **Synthetic data:** `RANDOM(seed)` rejects a per-row column as its seed. Use `HASH`-based generation (`ABS(HASH(n, salt)) % range`) — deterministic and reproducible.
- **Cortex Agent DDL:** `CREATE AGENT … FROM SPECIFICATION` uses `$$ … $$`, not a custom `$tag$`.
- **AI functions:** confirm your model is available (`SELECT AI_COMPLETE('<model>','Say OK')`); `llama3.1-8b` is broadly available. Cast `AI_COMPLETE` output `::string` (and `TRIM(…, '" ')`) before feeding `AI_CLASSIFY` / `AI_SENTIMENT`. Extraction: `AI_CLASSIFY(…):labels[0]::string`, `AI_SENTIMENT(…):categories[0]:sentiment::string`.
- **Streamlit in Snowflake:** deploy via stage + `CREATE STREAMLIT` with `get_active_session()`; theme via `.streamlit/config.toml` (Snowflake blue `#29B5E8`). Newer Streamlit APIs may error on older SiS runtimes — fall back to `st.columns`.
- **Notebooks:** author the `.ipynb` JSON directly (SiS SQL-cell metadata `%%sql -r` / `resultVariableName` can't be set by the notebook tools); upload with `cortex artifact create notebook`.

