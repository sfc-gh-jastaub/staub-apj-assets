# gsi-tax-gst-workshop

Half-day hands-on workshop: **GST Analytics & AI on Snowflake for Global Solution Integrators**.
Built for a tax practice at a GSI — strong SQL/Excel/Alteryx skills, new to Snowflake. Your firm is
never named; participants are the tax transformation consultants on the engagement.

**The premise.** **Brindabella Group**, an Australian group, runs three general ledgers after a decade
of acquisitions. Their tax team rebuilds the group GST position in Excel every month, cannot reconcile
it to what was lodged, and cannot reproduce a prior filing when the ATO asks. Your firm has been
engaged to fix that end to end, across two labs.

## Start here

Everything a participant needs is in **[`GSI_TAX_WorkshopMaterial/`](GSI_TAX_WorkshopMaterial)** and
nothing else. Open `gsi_tax_workshop_index.html` in that folder first. The rest of this repository is
source and build tooling — you do not need to read it to run the workshop.

The **notebooks are the primary surface** — every cell is ready to run, nothing to copy or paste.

| File | Duration | Covers |
|---|---|---|
| `gsi_tax_lab0_setup.ipynb` | ~75 sec | Builds the warehouse, database, layered schemas and the deterministic data both labs run on. Run once, before the day. |
| `gsi_tax_lab1_foundation.ipynb` | 57 min core + 28 optional | 2.4M ledger lines, three-ERP conformance, rules-as-data, BAS reconciliation, Streamlit control tower, Time Travel, zero-copy audit clone |
| `gsi_tax_lab2_cortex_ai.ipynb` | 60 min core + 34 optional | AI_CLASSIFY, EXTRACT_ANSWER, AI_COMPLETE working papers, semantic view + Cortex Agent |
| `gsi_tax_reset.ipynb` | ~1 min | Drops Lab 1, Lab 2 or the whole workshop. Safe to run twice and safe against a half-built environment. **Do not Run All** — the sections are ordered least to most destructive. |

Both labs are self-directed: every cell is ready to run and each step carries its
own orientation, so a participant who falls behind can still work forward alone.

The three `gsi_tax_workshop_*.html` files are the matching read-along guides — narrative, expected
results and architecture notes. Keep the guide open beside the notebook; the notebook cross-links to it
per step, which is why the guides sit alongside the notebooks rather than in a subfolder.

Two more files are in there for the participant: `gsi_tax_rule_update.csv`, which they upload by hand
in Lab 1 step 7, and `gst_control_tower.py`, the Streamlit app they paste into Projects → Streamlit in
step 6.

## Repository layout

```
GSI_TAX_WorkshopMaterial/   attendee-facing. Generated, plus the CSV they upload.
  streamlit_app/            deployable app root. Config committed, app generated.
sql/                        source. Schema and deterministic data generation.
apps/                       source of the Streamlit app.
_build/                     step fragments, assemblers, CSS/JS.
_archive/                   superseded material. Not built, not shipped.
_WORKSHOP_SPEC.md           the design contract.
```

Nothing generated is ever written to the repository root — all output paths resolve through `DIST` in
the build scripts.

## The Streamlit app

`apps/gst_control_tower.py` is the GST control tower from Lab 1 step 6: a single-file dark dashboard
(live KPI tiles, BAS reconciliation panel, risk distribution, entity heatmap, filterable worklist).
It is a real file so it can be compiled, run locally against an account and `PUT` to a stage — the
copies in the guide, the notebook and `GSI_TAX_WorkshopMaterial/streamlit_app/` are all **generated
from it** by `build.py`, so they cannot drift.

### Deploying it

`GSI_TAX_WorkshopMaterial/streamlit_app/` is a complete, committed app root. Open `streamlit_app.py`
from there and click **Run** — a fresh clone deploys with **zero manual file creation**.

Set this baseline in the session before deploying, so role and warehouse are not inherited from
whatever the session happened to hold:

```sql
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE GSI_TAX_WH;
```

After the first deploy, set the warehouse to `GSI_TAX_WH` in **App Settings**.

Two caveats to carry forward:

- **`ACCOUNTADMIN` is a reproducible workshop baseline, not a production posture.** Anything promoted
  beyond the lab should use a role holding only `USAGE` on `GSI_TAX_WORKSHOP` and its `TAX` and
  `CURATED` schemas, plus `SELECT` on `V_GST_VS_BAS`, `V_GST_EXCEPTIONS` and `GL_HARMONISED`. Lab 0
  builds everything as `SYSADMIN`, so `SYSADMIN` also works without extra grants.
- **`GSI_TAX_WH` is SMALL and created by Lab 0.** An X-Small such as `COMPUTE_WH` will work but loads
  noticeably slower against the 2.4M-row ledger.

The folder carries its own `snowflake.yml`, `pyproject.toml` and `.streamlit/config.toml`, all
tracked in git. This matters: Workspaces will otherwise generate them at first Run from the ambient
session, which is how the app once ended up querying `USER$<you>.TAX`. `build.py` fails the build if
any of the three is missing or still contains a `<placeholder>`. `pyproject.toml` must stay at its
defaults — adding a dependency triggers a PyPI fetch and therefore an external access integration.
Nothing above `streamlit_app/` may contain a `snowflake.yml`; an app root cannot nest inside another.

### Two implementation rules the app follows

**Every object is named in full.** `GSI_TAX_WORKSHOP.TAX.V_GST_EXCEPTIONS`, never
`TAX.V_GST_EXCEPTIONS`. A two-part name resolves against the session's current database, which for a
deployed app is not necessarily this one. A `USE SCHEMA` at startup is not a substitute — it moves the
hidden dependency rather than removing it.

**The session bootstrap differs by surface, and the build owns the difference.** The source file uses
`st.connection("snowflake")`, which is supported on both warehouse and container runtimes.
`get_active_session()` is warehouse-only and not thread-safe, but it is the only pattern available in
a notebook cell, so `assemble_nb.prep_python` rewrites the bootstrap for the Lab 1 step 6 cell
alongside stripping `st.set_page_config`. That rewrite is asserted — reword those lines and the build
fails rather than ship a cell that cannot get a session.

Everything is drawn with CSS grid and inline SVG rather than a plotting library: `matplotlib` is not
in the Streamlit in Snowflake warehouse runtime, and anything depending on it — including pandas'
`Styler.background_gradient` — fails at render time rather than at import. `build.py` guards against
reintroducing those APIs.

To run it on a laptop before deploying:

```bash
streamlit run _build/local_streamlit.py -- apps/gst_control_tower.py   # from the project root
```

## Prerequisites

- Snowflake **Enterprise** account (Time Travel beyond 1 day, secure sharing)
- ACCOUNTADMIN or a role that can create a warehouse and a database
- `SNOWFLAKE.CORTEX_USER` database role for Lab 2
- Notebook role `SYSADMIN` or above; `gsi_tax_lab0_setup.ipynb` cell 1 creates `GSI_TAX_WH` and
  switches to it, so any warehouse will do to start

Run Lab 0 before the day. Lab 1 then creates everything Lab 2 depends on, and there is **no cleanup
until the end of Lab 2**.

## Running it non-interactively

Stand the whole stack up without opening a notebook. Order matters — `CREATE AGENT` does not validate
that its semantic view exists, so `06` must precede `07`:

```
sql/01_setup_raw  02_setup_erp  03_setup_rules_bas_docs
   04_curated_tax  05_exceptions  06_lab2_ai_objects  07_agent
```

`sql/99_validate.sql` checks the result. A full build takes about 75 seconds on a SMALL warehouse.

## Data is deterministic on purpose

Every `RANDOM()` in `sql/01..03` carries a unique seed, and the ledger window is **pinned** to
2023-06-01 … 2026-07-31 rather than `CURRENT_DATE()`. The guides and notebooks quote exact figures
(253,394 exceptions, $26,247,261 of expected GST on the reverse-charge hook, 514 MATCHED / 18
INVESTIGATE), so the numbers on screen must match the numbers in the text on any day, in any account,
at any warehouse size. **Do not remove the seeds or unpin the dates** without re-measuring and
re-sweeping every quoted figure.

## Two cells are designed to fail

Lab 1 step 2 (naive `UNION ALL`, type mismatch) and step 3 (strict `TO_DATE` on a malformed legacy
date) raise on purpose — the error *is* the lesson, and the next cell fixes it. Each is preceded by a
callout saying so. If either ever succeeds, the teaching point has been lost.

## Editing

Everything generated comes from one source. Edit the `_build/lab{N}_step{M}.html` fragments and `sql/`,
then run:

```bash
python3 _build/build.py                # fragments+sql+apps -> guides, notebooks, sql/06; proves they agree
python3 _build/run_notebook.py setup   # executes every cell against Snowflake
python3 _build/run_notebook.py lab1
python3 _build/run_notebook.py lab2
python3 _build/run_notebook.py reset
```

Everything in `GSI_TAX_WorkshopMaterial/` is generated and must never be hand-edited — the
`gsi_tax_*.ipynb` notebooks, the `gsi_tax_workshop_*.html` guides and the `gst_control_tower.py` copy
— along with `sql/06_lab2_ai_objects.sql`. Their sources are the `_build/*_step*.html` fragments,
`sql/01..03`, and `apps/*.py`.

The one exception is `GSI_TAX_WorkshopMaterial/gsi_tax_workshop_index.html`, which is hand-authored
and therefore outside the parity check. Edit it directly.

`build.py` fails if the SQL in the finished guide differs from the SQL in the finished notebook, if a
step exceeds its code-block budget, if HTML entities are unescaped, or if a superseded figure
reappears. Never hand-edit the generated `.ipynb` or `.html` — they are overwritten.

Expected gate results: setup **4 pass**, Lab 1 **40 pass / 2 fail-as-designed / 1 skip**, Lab 2
**20 pass / 3 skip**, reset section 4 **3 pass**. The skips are the Streamlit app cells (nothing to
assert headlessly — `build.py` compiles the app file instead) and the Lab 2 cleanup, which drops the
workshop and so is only ever run deliberately.

`_WORKSHOP_SPEC.md` is the design contract, including the repository layout, the measured figures and
the per-step query budget. `_archive/TAX_HOL_BLUEPRINT.md` is the condensed version — enough to
regenerate a workshop of this shape from scratch.
