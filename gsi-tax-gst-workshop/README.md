# gsi-tax-gst-workshop

Half-day hands-on workshop: **GST Analytics & AI on Snowflake for Global Solution Integrators**.
Built for a tax practice at a GSI — strong SQL/Excel/Alteryx skills, new to Snowflake. Vendor-neutral
throughout ("your firm", "the tax practice", "your client").

**The premise.** An Australian group runs three general ledgers after a decade of acquisitions. The tax
team rebuilds the group GST position in Excel every month, cannot reconcile it to what was lodged, and
cannot reproduce a prior filing when the ATO asks. Two labs fix that end to end.

## What participants run

The **notebooks are the primary surface** — every cell is ready to run, nothing to copy or paste.

| File | Duration | Covers |
|---|---|---|
| `gsi_tax_lab1_foundation.ipynb` | 60 min core + 28 optional | 2.4M ledger lines, three-ERP conformance, rules-as-data, BAS reconciliation, Time Travel, zero-copy audit clone |
| `gsi_tax_lab2_cortex_ai.ipynb` | 60 min core + 34 optional | AI_CLASSIFY, EXTRACT_ANSWER, AI_COMPLETE working papers, semantic view + Cortex Agent |

The three `gsi_tax_workshop_*.html` files are the matching read-along guides — narrative, expected
results and architecture notes. Keep the guide open beside the notebook; the notebook cross-links to it
per step, which is why the guides sit alongside the notebooks rather than in a subfolder.

Start at `gsi_tax_workshop_index.html`.

## Prerequisites

- Snowflake **Enterprise** account (Time Travel beyond 1 day, secure sharing)
- ACCOUNTADMIN or a role that can create a warehouse and a database
- `SNOWFLAKE.CORTEX_USER` database role for Lab 2
- Notebook role `SYSADMIN` or above; Lab 1 cell 1 creates `GSI_TAX_WH` and switches to it

Lab 1 creates everything Lab 2 depends on. There is **no cleanup until the end of Lab 2**.

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
python3 _build/build.py               # fragments+sql -> guides, notebooks, sql/06; proves they agree
python3 _build/run_notebook.py lab1   # executes every cell against Snowflake
python3 _build/run_notebook.py lab2
```

`build.py` fails if the SQL in the finished guide differs from the SQL in the finished notebook, if a
step exceeds its code-block budget, if HTML entities are unescaped, or if a superseded figure
reappears. Never hand-edit the generated `.ipynb` or `.html` — they are overwritten.

Expected gate results: Lab 1 **40 pass / 2 fail-as-designed / 0 fail**, Lab 2 **20 pass / 0 fail**.
Skips are the Streamlit app cells and the Lab 2 cleanup.

`_build/_WORKSHOP_SPEC.md` is the design contract, including the measured figures and the per-step
query budget.
