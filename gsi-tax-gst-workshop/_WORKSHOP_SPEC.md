# WORKSHOP SPEC — GST Analytics & AI on Snowflake for Global Solution Integrators

This is the approved master plan. All subagents MUST follow it exactly. Do not invent object
names, row counts, or column names. Everything you need is here.

---

## 0. GLOBAL CONSTANTS

| Constant | Value |
|---|---|
| Workshop title | GST Analytics & AI on Snowflake for Global Solution Integrators |
| Audience | Indirect tax practitioners at a Global Solution Integrator. Strong SQL / Excel / Alteryx. New to Snowflake. Mixed technical + business. |
| Vendor neutrality | **Never name a specific GSI.** The participants' firm is always "your firm". Reusable across firms. |
| Client | **Brindabella Group** — fictional acquisitive Australian group, ~$4B revenue, 14 entities, monthly BAS. **The client IS named; the GSI is NOT.** See §0.2. |
| Region | Australia. AU is the working jurisdiction and **every worked example is Australian**. NZ and SG entities exist in the group structure only, to make cross-border and consolidation realistic. |
| Account type | Client-owned **Enterprise** account. NOT a trial. Masking policies, extended Time Travel, secure shares all available. |
| Database | `GSI_TAX_WORKSHOP` |
| Warehouse | `GSI_TAX_WH` — SIZE=SMALL, AUTO_SUSPEND=60, AUTO_RESUME=TRUE, INITIALLY_SUSPENDED=TRUE |
| Schemas | `RAW_DATA`, `CURATED`, `TAX`, `AI_INSIGHTS`, `AGENTS`, `APPS`, `AUDIT` |
| Role | `SYSADMIN` for setup. Note `SNOWFLAKE.CORTEX_USER` needed for Lab 2. |
| Labs | 2 |
| Core duration | 60 min per lab = 120 min |
| With optionals | ~88 min (Lab 1) + ~94 min (Lab 2) = ~182 min |
| Cortex model | `claude-sonnet-4-6` |
| localStorage key | `workshop_gsi_tax_lab{N}_progress` |
| Output directory | `~/Documents/COCO/HOL/gsi_tax/GSI_TAX_WorkshopMaterial/` |
| Footer | `© 2026 Snowflake Inc. All Rights Reserved.` |


### Repository layout — BINDING

`GSI_TAX_WorkshopMaterial/` is the only folder an attendee opens. It contains
**nothing but build output** plus the one file they upload by hand. Everything
else in the repo is source or internal.

```
~/Documents/COCO/HOL/gsi_tax/
├── GSI_TAX_WorkshopMaterial/            ← attendee-facing. ALL generated.
│   ├── gsi_tax_workshop_index.html      ← entry point (hand-authored, see below)
│   ├── gsi_tax_workshop_lab1_foundation.html
│   ├── gsi_tax_workshop_lab2_cortex_ai.html
│   ├── gsi_tax_lab0_setup.ipynb
│   ├── gsi_tax_lab1_foundation.ipynb
│   ├── gsi_tax_lab2_cortex_ai.ipynb
│   ├── gsi_tax_reset.ipynb
│   ├── gst_control_tower.py             ← copy published by stage 1c
│   └── gsi_tax_rule_update.csv          ← attendees upload this in Lab 1 Step 7
├── sql/                                 ← SOURCE. Stage 1 reads, stage 1b writes 06.
├── apps/gst_control_tower.py            ← SOURCE of the app. Never edit the copy.
├── _build/                              ← fragments, assemblers, CSS/JS
├── _archive/                            ← superseded material, not built, not shipped
└── _WORKSHOP_SPEC.md                    ← this file
```

**Three rules that follow from this.**

1. **Never write a generated artefact to the repo root.** All four output paths
   resolve through `DIST` (defined in `assemble.py`, `assemble_nb.py`, `build.py`
   and `run_notebook.py`). `CFG["out"]` and `NB_OUT` stay **bare filenames** —
   the guides cross-link each other and the notebooks link the guides relatively,
   so only the filesystem join carries the prefix.
2. **`sql/` and `apps/` are inputs, not artefacts.** Moving either out of the root
   breaks stage 1 / 1a immediately. `apps/gst_control_tower.py` is the single
   source of truth: stage 1a syncs it into the Lab 1 Step 6 fragment, stage 1c
   copies it into the attendee folder, and `check_apps_compile` compile-checks it.
3. **Participant-facing paths must be relative to the attendee folder.** Lab 1
   Step 7 names `gsi_tax_rule_update.csv` with no directory prefix, because that
   is what the attendee sees.

**`gsi_tax_workshop_index.html` is the one exception** — it is hand-authored and
lives inside the attendee folder rather than being generated into it, so the
parity check does not cover it. Edit it directly. This has already caused drift
twice; bringing it into the fragment pattern is outstanding work.

### Two delivery surfaces — HTML narrates, notebook executes

Both surfaces are generated from the **same** `_build/*.html` step fragments, so the SQL can never
drift between them. Regenerate both after editing any fragment:

```
python3 _build/assemble.py lab1 && python3 _build/assemble.py lab2   # HTML guides
python3 _build/assemble_nb.py all                                   # notebooks
```

| Surface | Owns | Built by |
|---|---|---|
| HTML guide | the full narrative, expected-results tables, architecture notes, sidebar nav, progress tracker | `_build/assemble.py` |
| Notebook | execution — every statement is already a cell, nothing is pasted | `_build/assemble_nb.py` |

**Rules for the notebook emitter — binding.**

1. **Markdown cells cannot render HTML.** Snowflake Notebooks strip it. All prose goes through
   `nbutil.html_to_md`. Never hand-write HTML into a notebook cell.
2. **Prose is condensed, not duplicated.** `mode='tight'` (default) keeps every heading, list, table
   and callout headline, reduces each run of paragraphs to its first and last, and cuts callout
   bodies to two sentences. The dropped middle is what the HTML guide is for, and every step header
   cell links to `<guide>.html#step-N`. `--full` emits a faithful port if that is ever wanted.
3. **Statements are split only where each result matters.** The policy lives in the `SPLIT` dict in
   `_build/assemble_nb.py`, one commented line per block. DDL runs, grant sequences and
   `USE`-plus-verify blocks stay in a single cell — a SQL cell renders only its *last* result, which
   is correct for those and wrong for anything where an intermediate result is the teaching point.
   Lab 1 Step 3 Block 1 (`TO_DATE` fails, `TRY_TO_DATE` survives) is the canonical must-split.
   **Every block listed in `SPLIT` must number its statements `-- 1.`, `-- 2.` … in the fragment.**
   The notebook gets separate cells; the guide reader does not, and a guide reader who runs the whole
   block sees only the last result. The numbering is what the Step 1 guide-only callout tells them to
   run one at a time, so an unnumbered `SPLIT` block silently loses a teaching point on the guide
   surface. Do **not** solve this by splitting the guide block — that spends query budget (§0.1).
4. **Step 1's setup script stays one cell.** All 27 statements, one run, ~65s. Its final statement is
   the verification `SELECT`, so the row-count proof is what renders.
5. **Streamlit blocks are stripped of `st.set_page_config`** by `prep_python` — it raises inside a
   notebook. The HTML keeps the canonical app code for the standalone Projects → Streamlit path.
6. **Fragments must stay surface-neutral.** No "paste this into a worksheet" — it is wrong in the
   notebook. Say "run the script" and let each surface be itself.
7. **Verification after any change:** every SQL block must round-trip. Compare whitespace- and
   comment-stripped SQL from the notebook cells against the fragment for every block; they must be
   identical, and every fragment block must map to at least one cell.

### Deviations from the snowflake-hol-generator skill

1. **DROP the Snowflake Community Colombia CTA** (skill Lessons Learned #9). This is an APJ audience.
2. **No cleanup step in Lab 1.** Lab 2 depends on Lab 1 objects. Cleanup appears once, as the final
   step of Lab 2, after the optionals.
3. **No Marketplace module.** Removed from scope — it does not serve the single use case.

---

## 0.1 DESIGN PRINCIPLE — QUERY BUDGET (BINDING)

The purpose of this workshop is that participants leave **impressed by the Snowflake platform**,
not that they exhaustively solve an indirect tax problem. Every step must make its point in the
fewest possible executions and then move on.

**Each step has a hard maximum number of code blocks. It is stated in the step heading and in
the step table. Do not exceed it. If content does not fit, cut the content — do not add a block.**

| Rule | Detail |
|---|---|
| One point, one query | If two queries make the same point, keep the better one and delete the other. |
| Prefer one wide query over several narrow ones | A single diagnostic returning one row per problem beats four separate counts. This is the highest-leverage rule in the workshop — apply it aggressively. |
| Static content is free | Comparison tables, defect summaries, architecture notes and rule explanations belong in **HTML prose and tables**, not in queries. Participants read those; they do not execute them. |
| DDL counts as a block | `CREATE DYNAMIC TABLE` is one block even though it is long. |
| Combine setup + proof | Where a `CREATE` is immediately followed by a one-line sanity `SELECT`, put both in the same block. |
| Never repeat a technique | If `TRY_TO_DATE` was demonstrated in Step 3, later steps use it without re-teaching it. |
| No "explore further" queries | Cut anything phrased as "you might also want to look at…". That is what the optionals are for. |

**A participant who runs only the required blocks must still see the entire story.** Everything
else is prose.

---

## 0.2 THE ENGAGEMENT — NAMING CONVENTION (BINDING)

There are two parties in this workshop and they must never blur. Brindabella Group is the client;
the participants are tax transformation consultants their firm has engaged to build the solution.

| Concept | Term | Notes |
|---|---|---|
| The client group | **Brindabella Group** on first mention in a step, **Brindabella** thereafter | Fictional. Stated as such once, on the index page. |
| The client's tax function | **Brindabella's tax team** | Owns the rule tables. Sends the Lab 1 Step 7 rate change. |
| The participants | **you**, **your team** | Tax transformation consultants on the engagement. |
| The consultancy | **your firm** | Carries the reusable-IP argument in Lab 1 Step 4. |
| Future clients | **your next client** | Never "every client" — the plural is what makes the IP point land. |
| A specific GSI | *never named* | Unchanged non-negotiable. |

**Banned as client references:** "the client", "the business", "the organisation", and "the group"
used as a bare noun where Brindabella is meant. "The group position" and "group GST" remain correct —
those are tax terms of art, not references to the company.

**Why the two-party split matters.** Rule ownership sitting with Brindabella's tax team rather than
with you is what makes Lab 1 Step 7 a handover proof point: a rate change arrives *from* the client
*to* the consultant, and the rules absorb it without a code deployment. Collapse the two parties and
that step has no sender.

---

## 1. VERIFIED CORTEX AI SYNTAX

These forms are verified working. Use them **verbatim**. Do not substitute.

| Purpose | Exact syntax |
|---|---|
| Classification | `AI_CLASSIFY(txt, ['A','B','C']):labels[0]::VARCHAR` |
| Extraction | `SNOWFLAKE.CORTEX.EXTRACT_ANSWER(txt, question)[0]:answer::VARCHAR` |
| Generation | `AI_COMPLETE('claude-sonnet-4-6', prompt)` |
| Sentiment label | `AI_SENTIMENT(txt):categories[0]:sentiment::VARCHAR` |
| Summarize | `SNOWFLAKE.CORTEX.SUMMARIZE(txt)` |

> **VERIFIED**: `AI_SENTIMENT` returns one of `'positive'`, `'negative'`, `'mixed'`, `'neutral'`.
> It returns **`mixed`**, not just neutral. Any `CASE` mapping MUST handle all four values.

### BANNED — do not emit these anywhere

- `SNOWFLAKE.CORTEX.COMPLETE()` — superseded, use `AI_COMPLETE`
- `SNOWFLAKE.CORTEX.SENTIMENT()` — superseded, use `AI_SENTIMENT`
- `AI_CLASSIFY_TEXT()` — does not exist
- `AI_EXTRACT_ANSWER()` — does not exist
- Any numeric comparison on `AI_SENTIMENT` output (e.g. `> 0.5`) — it returns a label, not a score

### NULL safety — MANDATORY

Every column concatenated into a prompt with `||` MUST be wrapped in `COALESCE(...)`.
A single NULL silently nulls the entire prompt and the AI call returns NULL.

```sql
-- CORRECT
AI_COMPLETE('claude-sonnet-4-6',
  'Explain this exception: ' || COALESCE(EXCEPTION_REASONS, 'none') ||
  ' for supplier ' || COALESCE(SUPPLIER_NAME, 'unknown'))
```

### Cost control — MANDATORY

Every AI function call in this workshop MUST be bounded. Apply the `LIMIT` inside a CTE
so it constrains the rows fed to the model, not just the rows displayed.

```sql
WITH sample AS (SELECT * FROM ... WHERE ... LIMIT 25)
SELECT ..., AI_COMPLETE('claude-sonnet-4-6', ...) FROM sample
```

---

## 2. VERIFIED FACTS — SNOWFLAKE FEATURES

| Fact | Detail |
|---|---|
| Dynamic Table refresh | `TARGET_LAG` is a freshness objective, not a schedule. `ALTER DYNAMIC TABLE ... REFRESH` forces one. |
| Anti-fan-out pattern | A CTE with `DISTINCT` before joining guarantees **correctness**. It does **not** guarantee `INCREMENTAL` refresh mode — never claim it does. Check actual mode with `SHOW DYNAMIC TABLES`. |
| Time Travel | `SELECT ... AT(OFFSET => -3600)` (seconds, negative). Also `AT(TIMESTAMP => ...)` and `BEFORE(STATEMENT => '<query_id>')`. Enterprise = up to 90 days retention. |
| Zero-copy clone | `CREATE TABLE x CLONE y AT(OFFSET => -3600)` and `CREATE DATABASE x CLONE y`. No storage cost until divergence. Metadata-only operation. |
| UNDROP | `UNDROP TABLE x` restores within the retention window. |
| Secure share | `CREATE SHARE`, `GRANT USAGE ON DATABASE`, `GRANT SELECT ON TABLE`, `ALTER SHARE ... ADD ACCOUNTS`. Read-only, live, revocable, no data copy. |
| Snowsight chart | Run query → **Chart** tab beside Results. No SQL required. |
| Streamlit in Snowflake | `from snowflake.snowpark.context import get_active_session` then `session = get_active_session()`. Never build a connection. |
| Semantic View | Snowsight: **AI & ML → Cortex Analyst → Create new**. Autopilot suggests dimensions/metrics. SQL DDL path also provided. |
| Cortex Agent | Snowsight: **AI & ML → Agents → Create agent**. Attach the semantic view as an Analyst tool. |

---

## 2.5 VALIDATED BUILD — MEASURED RESULTS (2026-08-03)

**Every statement in `sql/01`–`sql/05` was executed against
`SFSEEUROPE-DEMO_STAUB_US_WEST_2_PRIMARY`. Where this section conflicts with anything below,
THIS SECTION WINS.** The working SQL is on disk in `sql/` — subagents must transcribe from those
files, not re-derive it.

### Object inventory as built

| Object | Type | Rows |
|---|---|---|
| `RAW_DATA.ERP_SAP_GL` | TABLE | 1,200,000 |
| `RAW_DATA.ERP_ORACLE_GL` | TABLE | 800,000 |
| `RAW_DATA.ERP_LEGACY_AP` | TABLE | 400,000 |
| `RAW_DATA.DIM_LEGAL_ENTITY` | TABLE | 14 |
| `RAW_DATA.DIM_ACCOUNT_MAPPING` | TABLE | 180 (60 per system) |
| `RAW_DATA.DIM_SUPPLIER` | TABLE | 2,000 |
| `RAW_DATA.FCT_BAS_LODGED` | TABLE | 532 (14 entities x 38 complete months) |
| `RAW_DATA.DOC_TAX_INVOICE` | TABLE | 300 |
| `TAX.TAX_RULE_DETERMINATION` | TABLE | 16 |
| `TAX.TAX_RULE_RATE` | TABLE | 19 |
| `CURATED.GL_HARMONISED` | **DYNAMIC TABLE** | 2,400,000 (57 MB) |
| `TAX.V_GST_DETERMINED` | VIEW | 2,400,000 |
| `TAX.V_GST_VS_BAS` | VIEW | 532 |
| `TAX.V_GST_EXCEPTIONS` | VIEW | 258,145 |

### Six corrections forced by execution

**1. The exception register CANNOT be a Dynamic Table.** Verified error:
`Dynamic Tables do not support reading from views containing objects of type DYNAMIC_TABLE`.
`V_GST_EXCEPTIONS -> V_GST_DETERMINED (view) -> GL_HARMONISED (DT)` is illegal. It is now
**`TAX.V_GST_EXCEPTIONS`, a VIEW**. Rename it everywhere. Inlining the rule join to dodge this was
rejected: it would duplicate determination logic in two places, which is what we tell them not to do.
**Consequence: the workshop has exactly ONE Dynamic Table, `CURATED.GL_HARMONISED`.** That is a
simpler story for a beginner audience and removes the concept-doubling in Step 4.

**2. `LOADED_AT = CURRENT_TIMESTAMP()` forces `REFRESH_MODE = FULL`.** Verified reason:
*"change tracking is not supported on queries with non-deterministic functions"*. The column is
removed from the DDL. Do not reintroduce it.

**3. The determination join must be a `LEFT JOIN`.** With an inner join the ~8,074 unparseable-date
lines were silently dropped — the exact rows exception E2 exists to catch, which is why E2 returned
zero. As a `LEFT JOIN` all 2,400,000 lines survive and `TAX_TREATMENT` is NULL **only** where
`IS_DATE_PARSED = FALSE`. That is semantically right and a genuine teaching point: *you cannot
determine the tax treatment of a transaction whose date you do not know.*

**4. The group is now 14 Australian entities.** Previously 10 AU / 2 NZ / 2 SG. The ERPs book a flat
10% while the rate table varies by jurisdiction, so every NZ and SG line produced a systemic
variance and the exception register flagged 71% of the ledger. Since the user requires all examples
to be Australian and no example used NZ or SG, an all-AU group removes the entire defect class.
`IS_CROSS_BORDER` still works — it compares **supplier** country to entity jurisdiction, and ~35% of
suppliers are offshore. All currency is `AUD`. `TAX_RULE_RATE` retains its NZ and SG rows as unused
extensibility, which supports the Step 4 closing panel.

**5. Booked tax must derive from the account's supply category.** Random tax codes made almost every
line disagree with its determined treatment. Each ERP now joins `DIM_ACCOUNT_MAPPING` and
`DIM_SUPPLIER` during generation and books accordingly, with defects injected at controlled rates.

**6. Exception E6 must exclude `NON_DEDUCTIBLE`.** Entertainment legitimately carries GST — the error
is *claiming* the credit, which this data does not model. Flagging every entertainment line was a
false positive worth ~150,000 rows.

### Measured numbers the labs must quote

| Metric | Verified value |
|---|---|
| Conformance: date parsed | **99.66%** |
| Conformance: entity resolved | **100.00%** |
| Conformance: account mapped | **96.76%** (3.24% unmapped) |
| Conformance: supplier resolved | **100.00%** |
| Fan-out check | `COUNT(*) = COUNT(DISTINCT GL_LINE_ID) = 2,400,000` on BOTH curated and determined |
| Rules firing | all **16** |
| NULL treatment | **8,074** — unparseable dates only |
| Catch-all rule 15 volume | **73,484** (3.1%) |
| **Rule 9, before 1 Jul 2024** | **2,521 lines, `GST_FREE`, 0.00%, $0 expected GST** |
| **Rule 16, from 1 Jul 2024** | **4,858 lines, `REVERSE_CHARGE`, 10.00%, $25,539,866 expected GST** |
| Reconciliation | **514 `MATCHED` at exactly $0.00 variance, 18 `INVESTIGATE`** |
| Exception register | **258,145 lines = 10.76% of the ledger** |
| Exceptions by code | E1 77,737 / E2 8,074 / E3 64,781 / E4 30,573 / E5 108,191 / E6 36,500 / E7 12,313 |
| Step 2 wrong answer | **12 of 14 entities visible, 95,785 lines scanned, $175,942,290 GST** |
| Generation time | 1.2M rows in **6.45s**; full setup **~65s** on SMALL |

> **The hook is stronger than predicted.** The corrected reverse-charge position creates
> **$25.5 million** of expected GST from 1 July 2024 that did not exist before it, on an otherwise
> identical population. Hard-code that treatment and you restate three years of lodged BAS. Quote
> the dollar figure — it is what makes a tax partner sit forward.

> **Step 2's wrong answer is now provably wrong.** Querying SAP alone returns a confident
> $175.9 million covering **12 of 14 entities**. Two entities do not exist in SAP at all.

### Two gotchas for whoever writes the SQL blocks

- `UNIFORM` needs **constant** bounds. `UNIFORM(0, DATEDIFF(...), RANDOM())` does not compile. Use
  the verified fraction-and-scale form in §5.0.1.
- `ROWS` is a reserved word and cannot be a column alias.

---

### 2.5.1 RE-MEASURED AFTER SEEDING + DATE PIN (2026-08-03) — AUTHORITATIVE

All `RANDOM()` calls in `sql/01..03` now carry unique seeds (1001-1051), and the data
window is pinned to **2023-06-01 .. 2026-07-31** instead of `CURRENT_DATE()`. The build is
therefore byte-reproducible on any day, in any account, at any warehouse size. Verified by
rebuilding and comparing checksums, and across SMALL and MEDIUM warehouses.

These figures supersede every number in 2.5 and every earlier section:

| Measure | Value |
|---|---|
| GL rows / distinct GL_LINE_ID | 2,400,000 / 2,400,000 (no fan-out) |
| Conformance: date / entity / account / supplier | 99.66% / 100.00% / 96.77% / 100.00% |
| Unparseable legacy dates | 8,088 (NULL treatment on the same 8,088) |
| Malformed date shapes | 31/02/2024 = 2,871, N/A = 2,799, empty = 2,418 |
| Unmapped GL lines | 77,484 (3.23%) |
| Suppliers with no ABN | 102 of 2,000 (5.10%) |
| Entities missing from >=1 ERP | 6 of 14 (42.86%) |
| Exception register | 253,394 lines = 10.56% of ledger |
| Exceptions by code | E1 77,484 / E2 8,088 / E3 60,097 / E4 31,039 / E5 107,808 / E6 36,718 / E7 11,754 |
| BAS reconciliation | 514 MATCHED at $0.00, 18 INVESTIGATE (532 rows, 38 periods) |
| Distinct rules fired | 16 |
| Step 2 SAP-only slice | 96,025 lines, 12 of 14 entities, $176,904,538 |
| THE HOOK - before 1 Jul 2024 | rule 9, GST_FREE, 0.00%, 2,429 lines, $0 expected GST |
| THE HOOK - from 1 Jul 2024 | rule 16, REVERSE_CHARGE, 10.00%, 4,690 lines, $26,247,261 expected GST |
| Invoice remarks | 198 of 300 contain an ABN, 102 do not |

**Build discipline (binding):** the guide, the notebook and `sql/` all carry the same SQL.
Build ONLY with `python3 _build/build.py`, which regenerates the setup block from `sql/`,
emits both HTML and both notebooks, and FAILS if the SQL in the finished guide differs from
the SQL in the finished notebook. Never run `assemble.py` or `assemble_nb.py` alone.

**Full rebuild order:** `01_setup_raw` `02_setup_erp` `03_setup_rules_bas_docs`
`04_curated_tax` `05_exceptions` `06_lab2_ai_objects` (generated) `07_agent`.
`CREATE AGENT` does NOT validate that its semantic view exists, so 06 must precede 07 or the
agent is created but fails at question time.

## 3. VERIFIED FACTS — AUSTRALIAN INDIRECT TAX

Do not embellish. These are the only tax facts the workshop asserts.

| Fact | Detail |
|---|---|
| AU GST rate | **10% since 1 July 2000 — it has never changed.** State this plainly; it is the reason the effective-dating lesson is built on a *rule* change rather than a rate change. |
| NZ GST rate | 15% since 1 October 2010 (context only — not used in examples) |
| SG GST rate | 9% (context only — not used in examples) |
| Reverse charge | Div 84. An offshore supply of something other than goods or real property, acquired **other than solely for a creditable purpose**, requires the Australian recipient to account for the GST. **Simplified in this workshop to:** imported services from a non-registered offshore supplier. The synthetic-data disclaimer covers the simplification. |
| Unrecognised reverse charge | One of the most common findings in an Australian GST review — imported services treated as out of scope when the recipient should have accounted for the GST. **This is the workshop's effective-dating hook.** |
| Financial year | Australian tax changes take effect on **1 July**. Any effective-dated change in this workshop uses 1 July as its `VALID_FROM`. |
| GST fraction | GST on a taxable supply = 1/11 of the GST-inclusive amount |
| BAS labels | `G1` total sales, `G11` non-capital purchases, `1A` GST on sales (payable), `1B` GST on purchases (credits) |
| Net GST | `1A − 1B` |
| Input tax credit | Requires a valid tax invoice. For supplies over $82.50 the invoice must show the supplier's ABN. No ABN → no ITC. |
| GST-free (AU) | Basic food, most medical, most education, exports |
| Input taxed | Residential rent, financial supplies. No ITC on related acquisitions. |
| Entertainment | GST is charged, but the credit is **denied** where the expense is non-deductible |
| Reverse charge | Imported services from a non-registered offshore supplier — recipient accounts for the GST |
| Lodgement | Monthly or quarterly. This workshop uses **monthly** periods throughout. |

**Synthetic data disclaimer** — must appear as a warning callout immediately before Step 1 in
both labs:

> All data in this workshop is synthetically generated for training purposes. Entity names,
> ABNs, suppliers and transactions are fictitious. Tax treatments shown are simplified for
> illustration and are not tax advice.

---

## 4. ARCHITECTURE — THE CORE TEACHING POINT

This is the intellectual spine of the workshop. Both labs must reinforce it.

```
RAW_DATA                 CURATED                  TAX                       AI_INSIGHTS / AGENTS
(as landed)              (conformance only)       (tax logic only)
──────────────────       ──────────────────       ──────────────────        ────────────────────
ERP_SAP_GL       ┐                                TAX_RULE_DETERMINATION    V_AI_SUPPLY_CLASSIFIED
ERP_ORACLE_GL    ├─────► DT_GL_HARMONISED ──────► TAX_RULE_RATE             V_AI_DOC_EXTRACTED
ERP_LEGACY_AP    ┘         · dates normalised            │                  V_AI_EXCEPTION_RATIONALE
                           · signs conformed             ▼                          │
DIM_LEGAL_ENTITY ┐         · entities resolved     V_GST_DETERMINED  (VIEW)         │
DIM_ACCOUNT_MAPPING ├────► · accounts mapped             │                          │
DIM_SUPPLIER     ┘         · conformance flags           ├──► V_GST_VS_BAS  (VIEW)  │
                                                          │                          │
FCT_BAS_LODGED ──────────────────────────────────────────┤                          │
                                                          ▼                          │
                                                   V_GST_EXCEPTIONS ◄───────────────┤
                                                          │                          │
DOC_TAX_INVOICE ─────────────────────────────────────────┴──► SV_GST_COMPLIANCE + Agent

                              AUDIT.GL_AS_LODGED_<date>  ◄── zero-copy clone AT(OFFSET)
```

### Materialisation choices — implementation note, NOT a teaching topic

These choices still have to be made correctly, but **do not teach the comparison.** A tax audience
does not care about view-versus-Dynamic-Table trade-offs, and the earlier draft of this spec was
wrong to make it the headline takeaway. Build each object as specified, describe what it does in
one sentence, and move on.

| Object | Type | One-line framing for the lab (do not expand) |
|---|---|---|
| `CURATED.GL_HARMONISED` | **Dynamic Table** | "One governed ledger that keeps itself up to date as the source systems change." |
| `TAX.V_GST_DETERMINED` | **View** | "Applies the current rules every time you query it — change a rule and the answer changes." |
| `TAX.V_GST_EXCEPTIONS` | **Dynamic Table** | "Your standing exception work queue." |

**`V_GST_DETERMINED` must remain a view.** Not for architectural reasons but because Step 4's
best moment depends on it: edit a rate row, re-run the query, watch the number change with no
rebuild. A materialised object breaks that.

**Banned from the lab text:** the phrase "volatility of logic versus cost of computation", any
side-by-side view/DT comparison table, and any paragraph justifying why one object is materialised
and another is not.

### Separation of concerns — keep, but keep it brief

1. **`CURATED.GL_HARMONISED` contains no tax logic.** One sentence in Step 3: the same conformed
   ledger feeds statutory reporting, management reporting and tax, so tax assumptions must not be
   baked into it.

2. **Conformance flags live in CURATED.** `IS_DATE_PARSED`, `IS_ENTITY_RESOLVED`,
   `IS_ACCOUNT_MAPPED`, `IS_SUPPLIER_RESOLVED` answer "is the data complete". No commentary needed
   beyond that.

3. **Tax judgements live in TAX.** Whether GST was computed correctly, whether an ABN supports a
   credit, whether a cross-border service should have been reverse charged — these belong in
   `V_GST_EXCEPTIONS`.

4. **Rules are data, not code.** ⭐ **This is now the central message of Step 4 and the workshop's
   main architectural point.** Rates and treatment mappings are effective-dated rows Brindabella's tax team
   owns and can change themselves — not `CASE` statements buried in a query that need a developer
   and a release. Also state briefly that we do not store SQL fragments in a `VARCHAR` and evaluate
   them: it cannot be tested and it is an injection surface.

---

## 5. SHARED DATA MODEL

All `RAW_DATA` objects are created by **one paste-and-run setup script** in Lab 1 Step 1.
Target runtime under 90 seconds on a SMALL warehouse.

### 5.0 Scale — the data must not fit in a spreadsheet

**Total GL volume: 2,400,000 lines.** This is deliberate and it is the workshop's cheapest, most
well-targeted wow. Microsoft Excel stops at **1,048,576 rows**. This audience thinks in row
limits, so a dataset that physically cannot be opened in the tool they use today makes the point
before a single feature is demonstrated.

`ERP_SAP_GL` alone is 1,200,000 rows — **one of the three source systems, on its own, will not
open in Excel.** Use that line.

| Table | Rows |
|---|---|
| `ERP_SAP_GL` | 1,200,000 |
| `ERP_ORACLE_GL` | 800,000 |
| `ERP_LEGACY_AP` | 400,000 |
| **Total GL** | **2,400,000** |
| `DIM_SUPPLIER` | 2,000 |
| `DIM_ACCOUNT_MAPPING` | 165 |
| `DIM_LEGAL_ENTITY` | 14 |
| `FCT_BAS_LODGED` | 360 |
| `DOC_TAX_INVOICE` | 300 |

Dimensions do **not** scale with transaction volume — a chart of accounts has the same number of
rows whether you post a thousand journals or a million. `FCT_BAS_LODGED` is a lodged return, not a
transaction table. Both stay as specified.

**Setup script runtime — VERIFIED.** 1,200,000 rows with the full column set generated in
**6.45 seconds** on a SMALL warehouse (executed 2026-08-03). All 2.4M GL rows plus dimensions
should complete in **well under 30 seconds**. If generation exceeds 2 minutes something is wrong
with the SQL, not the volume — investigate rather than reducing row counts.

**Do not scale beyond 2.4M.** Generation is cheap, but `TAX.V_GST_DETERMINED` performs a range
join against 15 rules followed by a `QUALIFY` window — roughly a 36M-row intermediate at 2.4M base
rows. Ten million base rows would put that near 150M on a SMALL warehouse. 2.4M clears the Excel
line with margin and keeps every object responsive.

**Where the scale wow is demonstrated:** Lab 1 Step 2, Block 1 — against `ERP_SAP_GL` or
`CURATED.GL_HARMONISED`. **Do not** stage a scale demonstration on `TAX.V_GST_DETERMINED`; it is a
view containing a range join and a window function, and a full unfiltered scan of it is the one
query in this workshop that could be slow. Aggregate the Dynamic Table for scale, and query the
view with entity or period filters.

---

### 5.0.1 Date window — IMPORTANT

Transaction dates span **2023-06-01 through `CURRENT_DATE()`**. Generate with:

```sql
DATEADD('day',
        (DATEDIFF('day', '2023-06-01'::DATE, CURRENT_DATE())
         * UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()))::INT,
        '2023-06-01'::DATE)
```

> **VERIFIED — EXECUTED ON ACCOUNT.** `UNIFORM` requires **constant** bounds. The obvious form
> `UNIFORM(0, DATEDIFF('day','2023-06-01'::DATE, CURRENT_DATE()), RANDOM())` **fails to compile**
> with `argument 2 to function UNIFORM needs to be constant`. Use the fraction-and-scale form above:
> `UNIFORM(0::FLOAT, 1::FLOAT, RANDOM())` has constant bounds and returns a fraction, which is then
> multiplied by the day count outside the function. **Do not substitute another form.**

**Why a fixed anchor, not `DATEADD('day', -UNIFORM(1,730,...))`:** the window must straddle
**2024-07-01** so the reverse-charge rule change (§5.9, rules 9 and 16) is visible in the data. A
window measured backwards from `CURRENT_DATE()` stops straddling it as time passes. The fixed anchor
is permanently correct.

**VERIFIED output** at 1,200,000 rows generated 2026-08-03: range `2023-06-01` to `2026-08-02`,
evenly distributed across 1,158 days. **VERIFIED on a 200,000-row sample:** the 1 July 2024 boundary
splits the window **34% before / 66% after**.

**Expected rule 9 / rule 16 population.** Those rules require `PROFESSIONAL_FEES` (1 of 11
categories) AND `SUPPLIER_GST_REGISTERED = FALSE` (15%) AND `IS_CROSS_BORDER = TRUE` (~35% of
suppliers are offshore relative to an AU entity):

```
2,400,000 × 0.09 × 0.15 × 0.35 ≈ 11,300 lines
   ≈ 3,900 on rule 9  (before 2024-07-01)
   ≈ 7,400 on rule 16 (from 2024-07-01)
```

Thousands of lines each side — enough for a convincing Block 3 demonstration. **Re-verify at
generation time.** If either side falls below ~500 rows the demonstration is weak: raise the
`PROFESSIONAL_FEES` weighting in `DIM_ACCOUNT_MAPPING` rather than changing the boundary date.

---

### 5.1 `RAW_DATA.DIM_LEGAL_ENTITY` — 14 rows

Hand-written `INSERT ... VALUES`. This is the crosswalk that resolves three ERP entity
identifiers to one group entity — exactly what a legal entity master exists to do.

| Column | Type | Notes |
|---|---|---|
| ENTITY_ID | VARCHAR(10) | PK. `'ENT001'` … `'ENT014'` |
| ENTITY_NAME | VARCHAR(100) | Fictitious. e.g. `'Southern Cross Industrial Pty Ltd'` |
| ABN | VARCHAR(14) | Formatted `'51 824 753 556'` style. Fictitious. |
| JURISDICTION | VARCHAR(2) | `'AU'` ×10, `'NZ'` ×2, `'SG'` ×2 — Australia-weighted, because every example is Australian |
| GST_REGISTERED | BOOLEAN | TRUE for all 14 |
| FUNCTIONAL_CURRENCY | VARCHAR(3) | AUD / NZD / SGD matching jurisdiction |
| SAP_BUKRS | VARCHAR(4) | `'1010'`…`'1140'`. NULL for 3 entities that exist only in Oracle/legacy |
| ORACLE_LEDGER_ID | VARCHAR(10) | `'LED_2001'`… NULL for entities not in Oracle |
| LEGACY_ENTITY_CD | VARCHAR(6) | `'AU01'`, `'NZ01'`… NULL for entities not in legacy |

At least 3 entities must appear in only two of the three source systems. That is realistic and
it makes the entity-resolution step non-trivial.

---

### 5.2 `RAW_DATA.DIM_ACCOUNT_MAPPING` — 165 rows

Maps each ERP's native account code to the group chart of accounts and, critically, to a
**supply category** — the tax-relevant attribute.

| Column | Type | Notes |
|---|---|---|
| MAPPING_ID | NUMBER | `SEQ4() + 1` |
| SOURCE_SYSTEM | VARCHAR(10) | `'SAP'` \| `'ORACLE'` \| `'LEGACY'` |
| NATIVE_ACCOUNT_CODE | VARCHAR(20) | see below |
| GROUP_ACCOUNT_CODE | VARCHAR(10) | `'GL' \|\| LPAD(...)` |
| GROUP_ACCOUNT_NAME | VARCHAR(100) | |
| SUPPLY_CATEGORY | VARCHAR(30) | one of the 11 values below |

**Native code pools — the mapping is deliberately incomplete:**

| System | GL uses codes | Mapping covers | Result |
|---|---|---|---|
| SAP | `'4' \|\| LPAD(1..62, 5, '0')` → `400001`–`400062` | `400001`–`400055` | 7/62 unmapped |
| ORACLE | `'5100-' \|\| LPAD(1..62, 4, '0')` | `5100-0001`–`5100-0055` | 7/62 unmapped |
| LEGACY | `'AP' \|\| LPAD(1..62, 3, '0')` | `AP001`–`AP055` | 7/62 unmapped |

→ **≈11.3% of GL lines carry an account code with no mapping.** This drives
`IS_ACCOUNT_MAPPED = FALSE` and exception E1.

**The 11 `SUPPLY_CATEGORY` values** (distribute across the 55 mapped codes per system):
`STANDARD_GOODS`, `STANDARD_SERVICES`, `PROFESSIONAL_FEES`, `ENTERTAINMENT`,
`RESIDENTIAL_RENT`, `FINANCIAL_SUPPLY`, `EXPORT_SALES`, `FOOD_BASIC`, `MEDICAL`,
`EDUCATION`, `CAPITAL_EQUIPMENT`

---

### 5.3 `RAW_DATA.DIM_SUPPLIER` — 2,000 rows

| Column | Type | Generation |
|---|---|---|
| SUPPLIER_ID | VARCHAR(10) | `'SUP' \|\| LPAD((SEQ4()+1)::VARCHAR, 6, '0')` → `SUP000001`–`SUP002000` |
| SUPPLIER_NAME | VARCHAR(100) | `ARRAY_CONSTRUCT` of ~20 prefixes × ~15 suffixes |
| SUPPLIER_ABN | VARCHAR(14) | **NULL for ~15%.** Use `CASE WHEN UNIFORM(1,100,RANDOM()) <= 15 THEN NULL ELSE ... END` |
| GST_REGISTERED | BOOLEAN | TRUE ~85%, FALSE ~15% |
| SUPPLIER_COUNTRY | VARCHAR(2) | `AU` 65%, `NZ` 10%, `SG` 10%, `US` 8%, `GB` 7% |

2,000 suppliers against 2.4M GL lines is roughly 1,200 lines per supplier — realistic for a mid‑size
group. All FK generation uses `UNIFORM(1, 2000, RANDOM())`.

> `SEQ4() + 1` — **not** `SEQ4()`. FK generation starts at 1, so PKs must too, for zero orphans.
> This is a repeat finding; do not regress it.

---

### 5.4 `RAW_DATA.ERP_SAP_GL` — 1,200,000 rows

SAP-native shape. Everything as landed — no cleaning.

| Column | Type | Generation |
|---|---|---|
| BELNR | VARCHAR(10) | `'SAP' \|\| LPAD((SEQ4()+1)::VARCHAR, 7, '0')` |
| BUZEI | NUMBER(3) | `UNIFORM(1, 8, RANDOM())` |
| BUKRS | VARCHAR(4) | picked from the 11 non-NULL `SAP_BUKRS` values |
| HKONT | VARCHAR(10) | `'4' \|\| LPAD(UNIFORM(1,62,RANDOM())::VARCHAR, 5, '0')` |
| BUDAT | **VARCHAR(8)** | `TO_VARCHAR(<date expr>, 'YYYYMMDD')` — **stored as text, format 1 of 3** |
| DMBTR | NUMBER(15,2) | **signed**. DR positive, CR negative. `UNIFORM(50, 250000, RANDOM())` × sign |
| MWSTS | NUMBER(15,2) | tax amount, same sign as DMBTR |
| WAERS | VARCHAR(3) | AUD/NZD/SGD from the entity |
| MWSKZ | VARCHAR(2) | booked tax code: `'S1'`,`'S0'`,`'ZF'`,`'IT'`,`'RC'`,`'EX'` |
| LIFNR | VARCHAR(10) | `'SUP' \|\| LPAD(UNIFORM(1,2000,RANDOM())::VARCHAR, 6, '0')` |
| DOC_TYPE | VARCHAR(20) | `AP_INVOICE` 65%, `AR_INVOICE` 30%, `CREDIT_NOTE` 5% |
| SGTXT | VARCHAR(200) | short line text from an `ARRAY_CONSTRUCT` pool |

---

### 5.5 `RAW_DATA.ERP_ORACLE_GL` — 800,000 rows

Oracle-native shape. **Separate debit and credit columns** — the second amount convention.

| Column | Type | Generation |
|---|---|---|
| JE_HEADER_ID | NUMBER | `SEQ4() + 1` |
| JE_LINE_NUM | NUMBER(3) | `UNIFORM(1, 8, RANDOM())` |
| LEDGER_ID | VARCHAR(10) | from the non-NULL `ORACLE_LEDGER_ID` values |
| CODE_COMBINATION | VARCHAR(30) | `'5100-' \|\| LPAD(UNIFORM(1,62,RANDOM())::VARCHAR, 4, '0')` |
| GL_DATE | **DATE** | proper DATE type — **format 2 of 3** |
| ENTERED_DR | NUMBER(15,2) | populated OR NULL |
| ENTERED_CR | NUMBER(15,2) | the other one populated. Exactly one of the pair is non-NULL. |
| TAX_AMOUNT | NUMBER(15,2) | |
| CURRENCY_CODE | VARCHAR(3) | |
| TAX_CLASSIFICATION | VARCHAR(30) | `'STANDARD'`,`'ZERO_RATED'`,`'EXEMPT'`,`'REVERSE_CHARGE'`,`'OUT_OF_SCOPE'` |
| VENDOR_ID | VARCHAR(10) | `'SUP' \|\| LPAD(UNIFORM(1,2000,RANDOM())::VARCHAR, 6, '0')` |
| DOC_TYPE | VARCHAR(20) | same distribution as SAP |
| DESCRIPTION | VARCHAR(200) | |

---

### 5.6 `RAW_DATA.ERP_LEGACY_AP` — 400,000 rows

Lower-case, loosely typed, **GST-inclusive amounts** — the third convention. This is the table
that hurts, and that is the point.

| Column | Type | Generation |
|---|---|---|
| doc_ref | VARCHAR(20) | `'LEG' \|\| LPAD((SEQ4()+1)::VARCHAR, 7, '0')` |
| entity_cd | VARCHAR(6) | from the non-NULL `LEGACY_ENTITY_CD` values |
| acct | VARCHAR(10) | `'AP' \|\| LPAD(UNIFORM(1,62,RANDOM())::VARCHAR, 3, '0')` |
| txn_dt | **VARCHAR(10)** | `TO_VARCHAR(<date expr>, 'DD/MM/YYYY')` — **format 3 of 3, and ambiguous with MM/DD** |
| amt_incl_tax | NUMBER(15,2) | **GST-INCLUSIVE**, always positive |
| tax_amt | NUMBER(15,2) | |
| curr_cd | VARCHAR(3) | |
| tax_flag | VARCHAR(1) | `'Y'` 70%, `'N'` 25%, `'X'` 5% (`'X'` is undocumented — nobody left knows) |
| vendor_ref | VARCHAR(10) | `'SUP' \|\| LPAD(UNIFORM(1,2000,RANDOM())::VARCHAR, 6, '0')` |
| doc_type | VARCHAR(20) | `AP_INVOICE` 95%, `CREDIT_NOTE` 5% |
| narrative | VARCHAR(200) | |

**Malformed dates — deliberate.** ~2% of `txn_dt` values must be unparseable. Inject with a
`CASE`: `'31/02/2024'` (invalid day), `'N/A'`, `''`. This makes `TRY_TO_DATE` vs `TO_DATE` a
lived lesson rather than a footnote, and gives `IS_DATE_PARSED` something to find.

**Total GL lines across the three systems: 2,400,000.**

---

### 5.7 `RAW_DATA.FCT_BAS_LODGED` — 360 rows

The lodged position. 10 AU entities × 36 months. Only AU entities lodge a BAS.

| Column | Type | Notes |
|---|---|---|
| LODGEMENT_ID | NUMBER | `SEQ4() + 1` |
| ENTITY_ID | VARCHAR(10) | the 10 AU entities |
| TAX_PERIOD | DATE | first day of month. 36-month spine ending with the **previous** completed month |
| G1_TOTAL_SALES | NUMBER(15,2) | |
| G11_NON_CAP_PURCHASES | NUMBER(15,2) | |
| LABEL_1A_GST_ON_SALES | NUMBER(15,2) | |
| LABEL_1B_GST_CREDITS | NUMBER(15,2) | |
| NET_GST | NUMBER(15,2) | `1A − 1B` |
| LODGED_DATE | DATE | ~21 days after period end |
| LODGED_BY | VARCHAR(50) | fictitious names |

**Generation method — important.** Do **not** generate independent random values, or every
period shows a variance and the reconciliation step teaches nothing. Instead, in the setup
script, aggregate the three raw ERP tables by AU entity × month and derive the BAS from that,
then distort a small number of periods:

```sql
-- conceptually:
LABEL_1A_GST_ON_SALES = ROUND(<derived AR tax> * DISTORTION, 2)
where DISTORTION = CASE
  WHEN MOD(ABS(HASH(ENTITY_ID, TAX_PERIOD)), 36) = 0 THEN 0.85   -- understated
  WHEN MOD(ABS(HASH(ENTITY_ID, TAX_PERIOD)), 36) = 1 THEN 1.12   -- overstated
  ELSE 1.0 END
```

Result: **~8 entity-periods with a material variance** against the computed position; the rest
agree to within rounding. Deterministic via `HASH`, so it reproduces on every run.

---

### 5.8 `RAW_DATA.DOC_TAX_INVOICE` — 300 rows

Free-text source for Lab 2. **Generate this last**, by selecting 300 real rows from the ERP
tables, so referential integrity is guaranteed.

> **Why 300 and not 300,000.** AI function cost scales linearly with rows. 300 documents is
> explicitly framed in Lab 2 as a sample — you would not run a language model across 2.4 million
> ledger lines in a workshop, and saying so out loud is a credibility point, not a limitation.
> Lab 2 Step 2 must state this.

| Column | Type | Notes |
|---|---|---|
| DOC_ID | VARCHAR(20) | `'DOC' \|\| LPAD((SEQ4()+1)::VARCHAR, 6, '0')` |
| SOURCE_SYSTEM | VARCHAR(10) | from the selected row |
| SOURCE_DOC_REF | VARCHAR(20) | from the selected row — joins back to curated |
| SUPPLIER_ID | VARCHAR(10) | from the selected row |
| BOOKED_SUPPLY_CATEGORY | VARCHAR(30) | as booked — **may be wrong** |
| INVOICE_NARRATIVE | VARCHAR(1000) | 12-variant pool, see below |
| SUPPLIER_REMARKS | VARCHAR(1000) | includes an ABN in ~70% of rows, omits it in ~30% |
| CORRESPONDENCE_TEXT | VARCHAR(1000) | 8-variant pool with varied tone — for the optional `AI_SENTIMENT` step |

**The 12 narrative variants** — each must be classifiable to exactly one supply category, and
the booked category must **disagree** for roughly 25% of rows so miscoding detection has
something to find:

1. Client dinner and drinks, 6 attendees, city restaurant → `ENTERTAINMENT`
2. Monthly external audit fees → `PROFESSIONAL_FEES`
3. Forklift purchase, capitalised → `CAPITAL_EQUIPMENT`
4. Sea freight, Melbourne to Auckland, export consignment → `EXPORT_SALES`
5. Residential apartment lease for a relocated employee → `RESIDENTIAL_RENT`
6. Corporate health screening for staff → `MEDICAL`
7. Unprocessed produce for the staff canteen → `FOOD_BASIC`
8. Annual SaaS subscription billed from a US entity → `STANDARD_SERVICES` (cross-border)
9. Bank facility arrangement fee → `FINANCIAL_SUPPLY`
10. Steel stock purchase → `STANDARD_GOODS`
11. Accredited training course for the finance team → `EDUCATION`
12. Corporate box hospitality at a sporting fixture → `ENTERTAINMENT`

---

### 5.9 `TAX.TAX_RULE_DETERMINATION` — 16 rows

The decision table. `NULL` = wildcard (matches anything). Lower `PRIORITY` wins.
**This table is effective-dated** — it carries the workshop's hook.

| Column | Type |
|---|---|
| RULE_ID | NUMBER |
| PRIORITY | NUMBER |
| JURISDICTION | VARCHAR(2) NULL |
| SUPPLY_CATEGORY | VARCHAR(30) NULL |
| SUPPLIER_GST_REGISTERED | BOOLEAN NULL |
| IS_CROSS_BORDER | BOOLEAN NULL |
| TAX_TREATMENT | VARCHAR(20) |
| RECOVERABLE | BOOLEAN |
| VALID_FROM | DATE |
| VALID_TO | DATE |
| RULE_DESCRIPTION | VARCHAR(200) |

**Exact contents — insert verbatim.** All rows are `2000-07-01` → `9999-12-31` except rules 9a and
9b, which are the effective-dated pair.

| RULE_ID | PRIORITY | JURIS | SUPPLY_CATEGORY | SUP_REG | X_BORDER | TREATMENT | RECOV | VALID_FROM | VALID_TO | DESCRIPTION |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 10 | NULL | ENTERTAINMENT | NULL | NULL | NON_DEDUCTIBLE | FALSE | 2000-07-01 | 9999-12-31 | Entertainment is taxable but the credit is denied |
| 2 | 10 | NULL | RESIDENTIAL_RENT | NULL | NULL | INPUT_TAXED | FALSE | 2000-07-01 | 9999-12-31 | Residential rent is input taxed |
| 3 | 10 | NULL | FINANCIAL_SUPPLY | NULL | NULL | INPUT_TAXED | FALSE | 2000-07-01 | 9999-12-31 | Financial supplies are input taxed |
| 4 | 10 | NULL | EXPORT_SALES | NULL | NULL | EXPORT | TRUE | 2000-07-01 | 9999-12-31 | Exports are GST-free |
| 5 | 15 | AU | FOOD_BASIC | NULL | NULL | GST_FREE | TRUE | 2000-07-01 | 9999-12-31 | Basic food is GST-free |
| 6 | 15 | AU | MEDICAL | NULL | NULL | GST_FREE | TRUE | 2000-07-01 | 9999-12-31 | Most medical supplies are GST-free |
| 7 | 15 | AU | EDUCATION | NULL | NULL | GST_FREE | TRUE | 2000-07-01 | 9999-12-31 | Most education is GST-free |
| 8 | 20 | NULL | STANDARD_SERVICES | FALSE | TRUE | REVERSE_CHARGE | TRUE | 2000-07-01 | 9999-12-31 | Imported service, unregistered offshore supplier — reverse charge |
| **9** | **20** | NULL | **PROFESSIONAL_FEES** | **FALSE** | **TRUE** | **GST_FREE** | **FALSE** | **2000-07-01** | **2024-06-30** | **Imported professional fees — treated as out of scope (position superseded 1 Jul 2024)** |
| **16** | **20** | NULL | **PROFESSIONAL_FEES** | **FALSE** | **TRUE** | **REVERSE_CHARGE** | **TRUE** | **2024-07-01** | **9999-12-31** | **Imported professional fees — reverse charge applies (corrected position, from 1 Jul 2024)** |
| 10 | 30 | NULL | NULL | FALSE | FALSE | GST_FREE | FALSE | 2000-07-01 | 9999-12-31 | Domestic unregistered supplier cannot charge GST — no credit |
| 11 | 40 | NULL | STANDARD_GOODS | NULL | NULL | TAXABLE | TRUE | 2000-07-01 | 9999-12-31 | Standard goods are taxable |
| 12 | 40 | NULL | STANDARD_SERVICES | NULL | NULL | TAXABLE | TRUE | 2000-07-01 | 9999-12-31 | Standard services are taxable |
| 13 | 40 | NULL | PROFESSIONAL_FEES | NULL | NULL | TAXABLE | TRUE | 2000-07-01 | 9999-12-31 | Professional fees are taxable |
| 14 | 40 | NULL | CAPITAL_EQUIPMENT | NULL | NULL | TAXABLE | TRUE | 2000-07-01 | 9999-12-31 | Capital acquisitions are taxable, credit available |
| 15 | 99 | NULL | NULL | NULL | NULL | TAXABLE | TRUE | 2000-07-01 | 9999-12-31 | Catch-all default — review these |

> Rule 15 is the safety net. Because it matches everything, **every GL line resolves to exactly
> one rule** and the join never produces a NULL treatment. Call this out — a decision table
> without a catch-all silently drops rows.

### ⭐ The hook — the rule 9 / rule 16 pair

**This replaces the Singapore rate-change hook and it is a better fit for an Australian room.**

The Australian GST rate has been 10% since 1 July 2000 and has never changed, so a rate-change
story would be fiction. What genuinely *does* change, constantly, is the group's own determination
position — and unrecognised reverse charge on imported services is one of the most common findings
in an Australian GST review.

The story: following a review, the group corrected its position on imported professional services
**with effect from 1 July 2024**. Before that date those acquisitions were treated as out of scope
(rule 9). From that date the reverse charge applies (rule 16). Same predicates, same priority,
adjacent non-overlapping validity windows.

**Two IDs, not `9a`/`9b`.** `RULE_ID` is a `NUMBER`. Use 9 and 16. Refer to them in the lab text as
"the same rule with two effective-dated versions" — never as `9a` and `9b`.

Why it lands harder than a rate change:

> If you hard-code the corrected treatment, you do not just get next quarter wrong — **you silently
> restate every BAS you have already lodged.** Your computed position for closed periods moves, your
> reconciliation lights up for periods that were correct when filed, and you cannot tell a genuine
> variance from one you manufactured.

That consequence ties Step 4 directly into the Step 5 reconciliation and audit narrative, which the
Singapore version never did. Every Australian practitioner in the room understands the horror of
accidentally restating a lodged period.

---

### 5.10 `TAX.TAX_RULE_RATE` — 18 rows

Rates by jurisdiction and treatment. Every combination of 3 jurisdictions × 6 treatments exists so
the rate join never misses: **18 rows.**

| Column | Type |
|---|---|
| RATE_ID | NUMBER |
| JURISDICTION | VARCHAR(2) |
| TAX_TREATMENT | VARCHAR(20) |
| RATE_PCT | NUMBER(5,2) |
| VALID_FROM | DATE |
| VALID_TO | DATE |

| JURIS | TREATMENT | RATE | VALID_FROM | VALID_TO |
|---|---|---|---|---|
| AU | TAXABLE | 10.00 | 2000-07-01 | 9999-12-31 |
| AU | GST_FREE | 0.00 | 2000-07-01 | 9999-12-31 |
| AU | INPUT_TAXED | 0.00 | 2000-07-01 | 9999-12-31 |
| AU | EXPORT | 0.00 | 2000-07-01 | 9999-12-31 |
| AU | REVERSE_CHARGE | 10.00 | 2000-07-01 | 9999-12-31 |
| AU | NON_DEDUCTIBLE | 10.00 | 2000-07-01 | 9999-12-31 |
| NZ | TAXABLE | 15.00 | 2010-10-01 | 9999-12-31 |
| NZ | GST_FREE | 0.00 | 2010-10-01 | 9999-12-31 |
| NZ | INPUT_TAXED | 0.00 | 2010-10-01 | 9999-12-31 |
| NZ | EXPORT | 0.00 | 2010-10-01 | 9999-12-31 |
| NZ | REVERSE_CHARGE | 15.00 | 2010-10-01 | 9999-12-31 |
| NZ | NON_DEDUCTIBLE | 15.00 | 2010-10-01 | 9999-12-31 |
| SG | TAXABLE | 9.00 | 2024-01-01 | 9999-12-31 |
| SG | GST_FREE | 0.00 | 2024-01-01 | 9999-12-31 |
| SG | INPUT_TAXED | 0.00 | 2024-01-01 | 9999-12-31 |
| SG | EXPORT | 0.00 | 2024-01-01 | 9999-12-31 |
| SG | REVERSE_CHARGE | 9.00 | 2024-01-01 | 9999-12-31 |
| SG | NON_DEDUCTIBLE | 9.00 | 2024-01-01 | 9999-12-31 |

**The rate table is still date-effective, and this is worth one sentence in Step 4:** the Australian
rate has not moved since 2000, but the table is structured so that it *could*, without anyone
editing a query. The demonstrated change lives in `TAX_RULE_DETERMINATION` (rules 9 and 16), because
in Australia it is the treatment position that moves, not the rate.

**Do not** build any example, query or agent question on the Singapore or New Zealand rows. They
exist so the group consolidates realistically and so `IS_CROSS_BORDER` has meaning.

---

### 5.11 Deliberate data defects — summary table

Reproduce this table in Lab 1 Step 2 so participants can see the shape of the problem.

| # | Defect | Volume | Drives |
|---|---|---|---|
| 1 | Three date formats: `YYYYMMDD` text, native DATE, `DD/MM/YYYY` text | all 2,400,000 | Step 3 date normalisation |
| 2 | Malformed legacy dates | ~2% of 400,000 ≈ 8,000 | `IS_DATE_PARSED`, exception E2, `TRY_TO_DATE` |
| 3 | Three amount conventions: signed / DR-CR pair / GST-inclusive | all 2,400,000 | Step 3 sign + gross-up conformance |
| 4 | Three entity identifier schemes | all 2,400,000 | Step 3 entity resolution |
| 5 | Account codes absent from the mapping | ~11.3% ≈ 271,000 | `IS_ACCOUNT_MAPPED`, exception E1 |
| 6 | Suppliers with no ABN | ~15% of 2,000 ≈ 300 suppliers | Exception E3, ITC exposure |
| 7 | Unregistered suppliers charging GST | ~15% of suppliers × taxable lines | Exception E4 |
| 8 | Booked GST ≠ expected GST beyond $1 | ~6% ≈ 144,000 | Exception E5 |
| 9 | Credits claimed on non-recoverable treatments | entertainment + input-taxed lines | Exception E6 |
| 10 | Cross-border services with no reverse charge | subset of offshore suppliers | Exception E7 |
| 11 | Lodged BAS diverges from computed | ~8 entity-periods | Step 5 reconciliation and audit |
| 12 | Entities missing from one or two source systems | 3 of 14 | Step 3 outer-join reasoning |
| 13 | Booked supply category disagrees with the narrative | ~25% of 300 docs | Lab 2 Step 2 miscoding detection |

> At this scale the defect counts themselves become part of the wow. "271,000 ledger lines have an
> account code nobody has mapped" is a materially more alarming sentence than "6,000 lines do", and
> it is the kind of number a tax partner reacts to.

---

### 5.12 `CURATED.GL_HARMONISED` — Dynamic Table

```
TARGET_LAG = '1 hour'   WAREHOUSE = GSI_TAX_WH   REFRESH_MODE = AUTO
```

**Contains no tax logic.** Conformance and enrichment only.

| Column | Derivation |
|---|---|
| GL_LINE_ID | `SOURCE_SYSTEM \|\| '-' \|\| SOURCE_DOC_REF \|\| '-' \|\| SOURCE_LINE_NUM` |
| SOURCE_SYSTEM | literal `'SAP'` / `'ORACLE'` / `'LEGACY'` per branch |
| SOURCE_DOC_REF | `BELNR` / `JE_HEADER_ID::VARCHAR` / `doc_ref` |
| SOURCE_LINE_NUM | `BUZEI` / `JE_LINE_NUM` / `1` |
| ENTITY_ID, ENTITY_NAME, JURISDICTION, ENTITY_ABN | `LEFT JOIN DIM_LEGAL_ENTITY` on the matching source key |
| DOC_DATE | `TRY_TO_DATE(BUDAT,'YYYYMMDD')` / `GL_DATE` / `TRY_TO_DATE(txn_dt,'DD/MM/YYYY')` |
| TAX_PERIOD | `DATE_TRUNC('month', DOC_DATE)` |
| DOC_TYPE | passthrough |
| NATIVE_ACCOUNT_CODE | `HKONT` / `CODE_COMBINATION` / `acct` |
| GROUP_ACCOUNT_CODE, GROUP_ACCOUNT_NAME, SUPPLY_CATEGORY | `LEFT JOIN DIM_ACCOUNT_MAPPING` on `(SOURCE_SYSTEM, NATIVE_ACCOUNT_CODE)` |
| SUPPLIER_ID, SUPPLIER_NAME, SUPPLIER_ABN, SUPPLIER_GST_REGISTERED, SUPPLIER_COUNTRY | `LEFT JOIN DIM_SUPPLIER` |
| IS_CROSS_BORDER | `SUPPLIER_COUNTRY <> JURISDICTION` |
| CURRENCY | `WAERS` / `CURRENCY_CODE` / `curr_cd` |
| NET_AMOUNT | SAP `DMBTR` · Oracle `COALESCE(ENTERED_DR,0) - COALESCE(ENTERED_CR,0)` · Legacy `amt_incl_tax - tax_amt` |
| BOOKED_TAX_AMOUNT | `MWSTS` / `TAX_AMOUNT` / `tax_amt` |
| GROSS_AMOUNT | `NET_AMOUNT + BOOKED_TAX_AMOUNT` |
| BOOKED_TAX_CODE | `MWSKZ` / `TAX_CLASSIFICATION` / `tax_flag` |
| LINE_NARRATIVE | `SGTXT` / `DESCRIPTION` / `narrative` |
| IS_DATE_PARSED | `DOC_DATE IS NOT NULL` |
| IS_ENTITY_RESOLVED | `ENTITY_ID IS NOT NULL` |
| IS_ACCOUNT_MAPPED | `SUPPLY_CATEGORY IS NOT NULL` |
| IS_SUPPLIER_RESOLVED | `SUPPLIER_ID IS NOT NULL` |
| LOADED_AT | `CURRENT_TIMESTAMP()` |

Structure: three `SELECT` branches `UNION ALL`'d in a CTE, then the dimension joins applied
once over the union. Do not repeat the joins per branch.

**Expected row count: 2,400,000.** A verification query must confirm this and that
`COUNT(DISTINCT GL_LINE_ID) = COUNT(*)` — no fan-out.

---

### 5.13 `TAX.V_GST_DETERMINED` — VIEW

Decision-table match plus effective-dated rate join. **Must be a view** for the reason in §4.

```sql
CREATE OR REPLACE VIEW TAX.V_GST_DETERMINED AS
WITH matched AS (
    SELECT
        g.*,
        r.RULE_ID          AS APPLIED_RULE_ID,
        r.RULE_DESCRIPTION AS APPLIED_RULE_DESCRIPTION,
        r.TAX_TREATMENT,
        r.RECOVERABLE
    FROM CURATED.GL_HARMONISED g
    JOIN TAX.TAX_RULE_DETERMINATION r
      ON (r.JURISDICTION            IS NULL OR r.JURISDICTION            = g.JURISDICTION)
     AND (r.SUPPLY_CATEGORY         IS NULL OR r.SUPPLY_CATEGORY         = g.SUPPLY_CATEGORY)
     AND (r.SUPPLIER_GST_REGISTERED IS NULL OR r.SUPPLIER_GST_REGISTERED = g.SUPPLIER_GST_REGISTERED)
     AND (r.IS_CROSS_BORDER         IS NULL OR r.IS_CROSS_BORDER         = g.IS_CROSS_BORDER)
     AND  g.DOC_DATE BETWEEN r.VALID_FROM AND r.VALID_TO
    QUALIFY ROW_NUMBER() OVER (PARTITION BY g.GL_LINE_ID
                               ORDER BY r.PRIORITY, r.RULE_ID) = 1
)
SELECT
    m.*,
    rt.RATE_PCT AS APPLIED_RATE_PCT,
    ROUND(m.NET_AMOUNT * rt.RATE_PCT / 100, 2) AS EXPECTED_TAX_AMOUNT,
    ROUND(m.BOOKED_TAX_AMOUNT
          - ROUND(m.NET_AMOUNT * rt.RATE_PCT / 100, 2), 2) AS TAX_VARIANCE
FROM matched m
LEFT JOIN TAX.TAX_RULE_RATE rt
       ON rt.JURISDICTION   = m.JURISDICTION
      AND rt.TAX_TREATMENT  = m.TAX_TREATMENT
      AND m.DOC_DATE BETWEEN rt.VALID_FROM AND rt.VALID_TO;
```

Notes to carry into the lab prose:
- **Both joins are date-ranged on `DOC_DATE`, not `CURRENT_DATE()`.** This is the whole point: a
  transaction is judged by the rules that applied when it happened. Rules 9 and 16 differ only in
  their validity window, so a line's treatment depends on which side of 1 July 2024 it falls.
- `QUALIFY` is the most-specific-wins tiebreak. Explain it — most attendees will not have met it.
- Rules 9 and 16 share `PRIORITY = 20` but their windows do not overlap, so only one can ever match
  a given line and the `RULE_ID` tiebreak never fires between them.
- Lines with `SUPPLY_CATEGORY IS NULL` (unmapped accounts) can only satisfy wildcard predicates
  and therefore land on rule 15. They are already flagged `IS_ACCOUNT_MAPPED = FALSE`.
- **No date gaps.** Rule 9 runs to 2024-06-30 and rule 16 starts 2024-07-01; every other rule is
  `2000-07-01` → `9999-12-31`. Verify no line returns a NULL treatment.

---

### 5.14 `TAX.V_GST_VS_BAS` — VIEW

AU entities only, by entity × tax period.

| Column | Derivation |
|---|---|
| ENTITY_ID, ENTITY_NAME, TAX_PERIOD | grouping keys |
| COMPUTED_1A | `SUM(EXPECTED_TAX_AMOUNT)` where `DOC_TYPE = 'AR_INVOICE'` |
| COMPUTED_1B | `SUM(EXPECTED_TAX_AMOUNT)` where `DOC_TYPE = 'AP_INVOICE'` AND `RECOVERABLE` |
| COMPUTED_NET_GST | `COMPUTED_1A - COMPUTED_1B` |
| LODGED_1A, LODGED_1B, LODGED_NET_GST | from `FCT_BAS_LODGED` |
| VARIANCE_1A, VARIANCE_1B, VARIANCE_NET | computed − lodged |
| VARIANCE_PCT | `VARIANCE_NET / NULLIF(ABS(LODGED_NET_GST), 0) * 100` — **`NULLIF` is mandatory** |
| RECON_STATUS | `'MATCHED'` if `ABS(VARIANCE_NET) <= 100`, `'REVIEW'` if `<= 1000`, else `'INVESTIGATE'` |

`FULL OUTER JOIN` on `(ENTITY_ID, TAX_PERIOD)` so a period present in one side only still
appears. Wrap all sums in `COALESCE(..., 0)`.

---

### 5.15 `TAX.V_GST_EXCEPTIONS` — Dynamic Table

```
TARGET_LAG = '1 hour'   WAREHOUSE = GSI_TAX_WH
```

Seven rule evaluations, each a CTE emitting long-format `(GL_LINE_ID, EXCEPTION_CODE,
EXCEPTION_REASON, SEVERITY)`, `UNION ALL`'d, then aggregated to one row per line.

| Code | Test | Severity |
|---|---|---|
| E1 | `NOT IS_ACCOUNT_MAPPED` | MEDIUM |
| E2 | `NOT IS_DATE_PARSED` | HIGH |
| E3 | `SUPPLIER_ABN IS NULL AND DOC_TYPE='AP_INVOICE' AND RECOVERABLE AND GROSS_AMOUNT > 82.50` | HIGH |
| E4 | `NOT SUPPLIER_GST_REGISTERED AND BOOKED_TAX_AMOUNT <> 0` | HIGH |
| E5 | `ABS(TAX_VARIANCE) > 1.00` | MEDIUM |
| E6 | `NOT RECOVERABLE AND DOC_TYPE='AP_INVOICE' AND BOOKED_TAX_AMOUNT <> 0` | HIGH |
| E7 | `TAX_TREATMENT='REVERSE_CHARGE' AND BOOKED_TAX_CODE NOT IN ('RC','REVERSE_CHARGE')` | MEDIUM |

Final projection, one row per `GL_LINE_ID`:

| Column | Derivation |
|---|---|
| GL_LINE_ID | grouping key |
| ENTITY_ID, ENTITY_NAME, TAX_PERIOD, SUPPLIER_ID, SUPPLIER_NAME | carried from `V_GST_DETERMINED` |
| SOURCE_SYSTEM, SOURCE_DOC_REF, DOC_TYPE, SUPPLY_CATEGORY | carried |
| NET_AMOUNT, BOOKED_TAX_AMOUNT, EXPECTED_TAX_AMOUNT, TAX_VARIANCE | carried |
| TAX_TREATMENT, APPLIED_RULE_ID | carried — rule lineage for the auditor |
| EXCEPTION_COUNT | `COUNT(*)` |
| EXCEPTION_CODES | `LISTAGG(DISTINCT EXCEPTION_CODE, ', ') WITHIN GROUP (ORDER BY EXCEPTION_CODE)` |
| EXCEPTION_REASONS | `LISTAGG(EXCEPTION_REASON, ' \| ') WITHIN GROUP (ORDER BY EXCEPTION_CODE)` |
| MAX_SEVERITY | `MAX` over an ordered severity rank mapped back to a label |
| RISK_SCORE | `EXCEPTION_COUNT * 10 + LEAST(ABS(COALESCE(TAX_VARIANCE,0)) / 100, 50)` |

Verification: `EXCEPTION_COUNT >= 1` for every row; `COUNT(*) < 2400000`. Expect roughly
400,000–600,000 exception rows at this scale — which is exactly why `RISK_SCORE` ranking matters
and why the lab always queries this table with `ORDER BY RISK_SCORE DESC LIMIT n`.

---

### 5.16 Lab 2 objects

| Object | Type | Contents |
|---|---|---|
| `AI_INSIGHTS.V_AI_SUPPLY_CLASSIFIED` | VIEW | `AI_CLASSIFY(INVOICE_NARRATIVE, [...6 categories...]):labels[0]::VARCHAR` vs `BOOKED_SUPPLY_CATEGORY`, plus `MISCODING_FLAG` |
| `AI_INSIGHTS.V_AI_DOC_EXTRACTED` | VIEW | `EXTRACT_ANSWER` × 2 — supplier ABN and GST amount — from `SUPPLIER_REMARKS`, reconciled to the ledger |
| `AI_INSIGHTS.V_AI_EXCEPTION_RATIONALE` | VIEW | `AI_COMPLETE` working-paper narrative per flagged exception. `LIMIT 25` inside the CTE. |
| `AGENTS.V_GST_INTELLIGENCE` | VIEW | Flattened wide view over `V_GST_DETERMINED` + exceptions + BAS variance, for the semantic view |
| `AGENTS.SV_GST_COMPLIANCE` | SEMANTIC VIEW | dimensions: entity, jurisdiction, tax period, supply category, treatment, source system, recon status. metrics: net amount, booked tax, expected tax, variance, exception count, line count |
| `GST_COMPLIANCE_AGENT` | AGENT | Analyst tool on `SV_GST_COMPLIANCE` |
| `AI_INSIGHTS.DT_AI_EXCEPTION_REVIEW` | DYNAMIC TABLE (optional) | `TARGET_LAG = '24 hours'` — materialises AI output for cost control |
| `AI_INSIGHTS.V_AI_CORRESPONDENCE_TRIAGE` | VIEW (optional) | `AI_SENTIMENT` over `CORRESPONDENCE_TEXT`. **Must handle all four labels.** |

The six `AI_CLASSIFY` categories, exactly:
`['taxable supply','GST-free supply','input taxed supply','export','entertainment','capital acquisition']`

---

## 6. LAB 1 — TAX DATA FOUNDATION: RAW TO RETURN-READY

**File:** `gsi_tax_workshop_lab1_foundation.html`
**Core:** 60 min across 5 steps · **Optional:** 28 min across 3 steps · **Total: 88 min**
**Hero duration text:** `60 minutes core + 28 minutes optional`

### Step table

| # | id | Title | Min | Blocks (max) | Type |
|---|---|---|---|---|---|
| 1 | `step-1` | Land the raw data and look around | 8 | **2** | CORE |
| 2 | `step-2` | Prove you cannot answer the question | 8 | **3** | CORE |
| 3 | `step-3` | Conform three ERPs into one governed ledger | 14 | **4** | CORE |
| 4 | `step-4` | The tax rules layer | 15 | **5** | CORE |
| 5 | `step-5` | Reconcile, then survive the audit | 15 | **5** | CORE |
| 6 | `step-6` | ⭐ OPTIONAL · Streamlit tax control tower | 12 | **2** | OPTIONAL |
| 7 | `step-7` | OPTIONAL · Brindabella's tax team sends you a rate change | 10 | **4** | OPTIONAL |
| 8 | `step-8` | OPTIONAL · Share the snapshot with the auditor | 6 | **2** | OPTIONAL |

`coreSteps = 5`, `totalSteps = 8`. **Core total: 60 min, 19 code blocks.**

> `TAX.V_GST_VS_BAS` has moved from Step 4 into Step 5. The reconciliation is the natural opening
> of the audit story — the variance is what makes the auditor's question land — and moving it
> keeps Step 4 to five blocks instead of seven.

---

### Step 1 — Land the raw data and look around · 8 min · **MAX 2 BLOCKS**

**Narrative.** Your client's tax function spends most of its time finding, cleaning and
reconciling data before any analysis begins. We are going to skip the part where that takes six
weeks. One script, one paste, and you will have three ERP extracts that describe the same
business — in three incompatible shapes.

**Block 1 — the entire setup.** `CREATE WAREHOUSE`, `CREATE DATABASE`, the 7 schemas, all 8
`RAW_DATA` tables with data, and a closing verification `SELECT` returning object names and row
counts. One paste, ~90 seconds, nothing else to type.

**Block 2 — the three shapes, in one result grid.** A single query that `UNION ALL`s three rows
from each ERP with everything cast to `VARCHAR`, labelled by source system, exposing the date
column, the amount column(s) and the tax code column. Three date formats and three amount
conventions visible simultaneously in nine rows.

```sql
-- shape of it (agent to complete):
SELECT 'SAP' AS SRC, BELNR AS DOC, BUDAT AS DATE_AS_LANDED,
       DMBTR::VARCHAR AS AMT_1, NULL AS AMT_2, MWSKZ AS TAX_CODE
FROM RAW_DATA.ERP_SAP_GL LIMIT 3
UNION ALL SELECT 'ORACLE', ... GL_DATE::VARCHAR, ENTERED_DR::VARCHAR, ENTERED_CR::VARCHAR, ...
UNION ALL SELECT 'LEGACY', ... txn_dt, amt_incl_tax::VARCHAR, NULL, tax_flag ...
```

**Prose, not queries.** The source-shape comparison table from §5.4–5.6 is rendered as an HTML
table. Do not add per-table `SELECT *` blocks.

**Verification.** Expected row counts: 1,200,000 / 800,000 / 400,000 / 14 / 165 / 2,000 / 360 / 300.

**Platform callout — do not skip this.** Two sentences, immediately after Block 1: you just
provisioned compute, created a database and generated 2.4 million ledger lines in under two
minutes. No server was sized, no storage was allocated, no index was built, and nothing needs to
be maintained. Then note that the warehouse will suspend itself in 60 seconds and stop costing
anything.

**Teaching point.** Nothing here has been cleaned. That is deliberate. This is what the data
actually looks like when it lands.

---

### Step 2 — Prove you cannot answer the question · 8 min · **MAX 3 BLOCKS**

**Narrative.** A partner asks a question a client would ask: *what was the group's GST payable
for the last full quarter, by entity?* It is a completely reasonable question. Right now it is
unanswerable — and the point of this step is to prove that in three queries, not to catalogue
every flaw in the data.

**Block 1 — the plausible wrong answer, and the scale moment.** Answer the partner's question
against `ERP_SAP_GL` alone. It aggregates **1.2 million rows and returns in about a second**, and
it gives a clean, confident, formatted number covering **11 of 14 entities**.

This single block does two jobs, which is why it must not be split:

> **The wow.** That table has 1.2 million rows. Excel stops at 1,048,576 — one of your three
> source systems, on its own, will not open in the tool your team uses today. That aggregate ran
> on the smallest warehouse Snowflake sells, with no index, no tuning and no preparation.
>
> **The problem.** It is still the wrong answer. It is missing a third of the group, and nothing
> in the result tells you that.

**Free platform moment, zero blocks — Snowsight column profiling.** With the results on screen,
have them click a column header in the results pane. Snowsight shows the distribution, the null
count and the distinct count for that column without anyone writing a query. For an Excel or
Alteryx user who profiles columns manually, this is a genuine "I didn't know it did that" — and it
does this step's job better than SQL does.

**Block 2 — the naive union fails.** `UNION ALL` the three extracts on the columns that look
equivalent. It errors on type mismatch. Explain the four reasons in **prose** — date types,
amount conventions, entity keys, account codes — do not query them individually.

**Block 3 — one query, the whole diagnosis.** A single scorecard returning **one row per defect**
with a count and a percentage, scanning all 2.4 million rows. This is the impact shot: the entire
data-quality problem on one screen, with numbers large enough to alarm a partner.

```sql
-- shape of it (agent to complete, one row per defect):
SELECT 'Legacy dates that will not parse' AS ISSUE, COUNT(*) AS AFFECTED, ...
FROM RAW_DATA.ERP_LEGACY_AP WHERE TRY_TO_DATE(txn_dt,'DD/MM/YYYY') IS NULL
UNION ALL SELECT 'GL lines with no account mapping', ...
UNION ALL SELECT 'Suppliers with no ABN', ...
UNION ALL SELECT 'Entities missing from at least one ERP', ...
ORDER BY AFFECTED DESC;
```

**Prose, not queries.** The full defect table from §5.11 is an HTML table placed after Block 3.

**Teaching point.** The work is not the analysis. The work is making the analysis possible.

**Hard limit.** Three blocks. This step is diagnosis, not exploration. If a fourth query feels
necessary, fold it into the Block 3 scorecard as another `UNION ALL` row.

---

### Step 3 — Conform three ERPs into one governed ledger · 14 min · **MAX 4 BLOCKS**

**Narrative.** One object. Every line from every system, in one shape, with the dimensions
attached and the data-quality problems labelled rather than hidden.

**Block 1 — `TRY_TO_DATE` in one query.** Select the malformed legacy dates with `TO_DATE` and
`TRY_TO_DATE` side by side so the error and the fix appear together. The single most immediately
useful thing many attendees will take away, in one block.

**Block 2 — build `CURATED.GL_HARMONISED`.** The full Dynamic Table DDL per §5.12. This is the
centrepiece of the step. The amount conventions, the entity crosswalk and the account mapping
join are all **visible in the DDL and explained in prose around it** — they do not get their own
queries.

**Platform callout.** One `CREATE` statement produced a pipeline that unions three systems,
resolves four dimensions across 2.4 million rows, and **keeps itself up to date** as the sources
change. There is no scheduler, no orchestration tool, no dependency graph to maintain and nothing
to deploy. Frame it as a capability, not as a design trade-off — see §4.

**Free platform moments, zero blocks.**
- After the DDL runs, open **Monitoring → Dynamic Tables** in Snowsight and show the refresh
  history and the dependency graph. The pipeline draws its own diagram.
- On the verification query in Block 3, open the **Query Profile** tab. A visual execution plan
  with partition pruning statistics is disproportionately impressive to people who have never seen
  one, and it costs nothing.
- Re-run Block 3 a second time. It returns instantly from the result cache, at no compute cost.
  One sentence.

**Block 3 — one verification query.** Row count, distinct `GL_LINE_ID` (proving no fan-out), and
the conformance pass rate for each of the four flags — all in a single result row.

```sql
SELECT COUNT(*) AS TOTAL_ROWS,
       COUNT(DISTINCT GL_LINE_ID) AS DISTINCT_LINES,
       ROUND(100.0 * SUM(IFF(IS_DATE_PARSED,1,0))     / COUNT(*), 1) AS PCT_DATE_OK,
       ROUND(100.0 * SUM(IFF(IS_ENTITY_RESOLVED,1,0)) / COUNT(*), 1) AS PCT_ENTITY_OK,
       ROUND(100.0 * SUM(IFF(IS_ACCOUNT_MAPPED,1,0))  / COUNT(*), 1) AS PCT_ACCOUNT_OK,
       ROUND(100.0 * SUM(IFF(IS_SUPPLIER_RESOLVED,1,0))/COUNT(*), 1) AS PCT_SUPPLIER_OK
FROM CURATED.GL_HARMONISED;
```

**Block 4 — `SHOW DYNAMIC TABLES`.** Inspect the actual refresh mode. Report what it is; do
**not** claim it will be `INCREMENTAL`.

**Teaching points — prose, keep both short.**
- **What a Dynamic Table gives you:** a pipeline that maintains itself, declared once. Per §4 —
  frame as capability, **not** as a view-versus-Dynamic-Table comparison.
- **Why there is no tax logic in this table.** One sentence, per §4 item 1.

---

### Step 4 — The tax rules layer · 15 min · **MAX 5 BLOCKS**

The most important step in the lab, and the one with a single clear message: **the rules live in a
table that Brindabella's tax team owns, not in code that a developer owns.**

**Narrative.** Tax logic is not a `CASE` statement. It is a body of rules with jurisdictions,
effective dates and precedence, and it changes without warning — usually at short notice, usually
not by anyone in IT. So we hold it as data Brindabella's tax team can read, review and change themselves.

**Block 1 — the rules, as data.** Both rule tables in one block, two `SELECT`s. A tax person reads
these two result grids and understands the entire determination logic of the system without
reading any SQL — **say that out loud, it is the point.** Let the room find **rules 9 and 16** — the
same rule with two validity windows either side of 1 July 2024 — then ask: *what happens to three
years of lodged BAS if that corrected treatment is hard-coded?*

Also worth one sentence: the Australian GST rate has been 10% since 2000 and has never changed. The
rate table is still date-effective anyway, so that if it ever does, nobody edits a query.

**Block 2 — build `TAX.V_GST_DETERMINED`.** Full SQL per §5.13. Note in prose that the SQL is
thin and generic — it contains no rates, no jurisdictions and no treatments, only the mechanism
for applying whatever the tables say. Explain `QUALIFY` briefly; most attendees will not have met
it.

**Block 3 — prove the effective dating.** One query over Australian imported professional fees from
non-registered offshore suppliers, grouped either side of 2024-07-01, showing `GST_FREE` before and
`REVERSE_CHARGE` after — from the same view, with no conditional logic anywhere. Include
`APPLIED_RULE_ID` in the output so the room can see which rule fired.

Then make the consequence explicit: had the corrected treatment been hard-coded, the pre-July-2024
column would show reverse charge too — **silently restating every BAS already lodged.**

**Block 4 — the moment.** `UPDATE` one rate row, re-run the same aggregate, roll it back — one
block. The group GST position changes immediately. No code was edited, nothing was rebuilt, nothing
was redeployed, and no developer was involved. **This is the payoff of the whole step**, and the
framing is ownership, not architecture: *the person who owns the rule can change the rule.*

**Block 5 — build `TAX.V_GST_EXCEPTIONS` and read the work queue.** DDL per §5.15 plus the top
exceptions by `RISK_SCORE` in the same block. Frame it in one sentence — a standing exception
register that maintains itself — and move on. **Do not** compare it to the view built in Block 2.

**Prose, not queries — both short.**
- **Why two rule tables and not one.** Different grain: determination is keyed on transaction
  characteristics, rate on jurisdiction, treatment and date. One table would turn a single rate
  change into an update across every rule that mentions it.
- **Why rules are not stored as SQL strings.** Two sentences, per §4 item 4. Answer it before
  someone asks.

**Banned from this step:** any view-versus-Dynamic-Table comparison, and the phrase "volatility of
logic versus cost of computation". The audience does not care and it dilutes the message that the
rules are theirs.

---

### Step 4 closing panel — "This is one rule set, not the rule set"

**Static diagram and prose. ZERO code blocks. ~1 minute of narration.** Place it as the final
element of the Step 4 card, after Block 5. This is the "so what do we do on Monday" answer and it is
the most commercially useful thirty seconds in Lab 1 — do not cut it, and do not turn it into an
exercise.

```
                        ┌────────────────────────────────────┐
                        │   CURATED.GL_HARMONISED            │
                        │   one conformed ledger             │  ◀── you built this
                        │   contains no tax logic            │
                        └─────────────────┬──────────────────┘
                                          │
        ┌──────────────┬──────────────────┼──────────────────┬──────────────┐
        │              │                  │                  │              │
   ┌────▼─────┐  ┌─────▼──────┐   ┌───────▼──────┐   ┌───────▼──────┐  ┌────▼──────┐
   │   GST    │  │    FBT     │   │  Fuel tax    │   │   Payroll    │  │Withholding│
   │  rules   │  │   rules    │   │   credits    │   │     tax      │   │    tax   │
   │          │  │            │   │              │   │              │  │           │
   │  BUILT   │  │    next    │   │     next     │   │     next     │  │    next   │
   └──────────┘  └────────────┘   └──────────────┘   └──────────────┘  └───────────┘
```

**Rendering:** the `GST rules` box uses Snowflake Blue `#29B5E8` with white text; the four `next`
boxes are outlined in `#C9C9C9` with `#9A9A9A` text to read as greyed-out and future. The ledger box
uses Mid Blue `#11567F`. Render as styled `<div>`s in a flex row, **not** as ASCII in a `<pre>` — the
ASCII above is the layout brief, not the output.

**The three sentences that go with it.**

1. What you built is not "the tax rules" — it is **one rule set, for one tax**, sitting beside a
   ledger that knows nothing about GST. That is exactly why we kept tax logic out of the curated
   layer in Step 3.
2. Every other indirect tax your practice touches has the same shape: rules the tax team owns,
   effective-dated, applied by thin generic SQL. Fuel tax credits reindex twice a year. Payroll tax
   is eight jurisdictions each with its own rate, threshold and grouping rules. Withholding tax is a
   treaty rate by country and income type. Same pattern, different table.
3. **Brindabella's ledger is bespoke. The rule sets are not.** The payroll tax rule set you build
   for one client is most of the payroll tax rule set for the next one.

**The commercial point — say this one out loud, it is the partner's takeaway.**

> Most of this work today is billed by the hour and thrown away when the engagement closes. Build it
> this way and the rule libraries become your firm's IP — something you deploy repeatedly rather
> than rebuild.

**Honest boundary — include it, briefly.** Not everything is a rule table. Anything requiring
iterative or circular computation — thin capitalisation, Pillar Two top-up, consolidation
eliminations with circular ownership — needs procedural logic. Say so. Acknowledging the limit is
what makes the rest credible, and it heads off the objection rather than being caught by it.

**Optional facilitator depth — the three rule shapes.** Only if the room is technical and asks. Do
**not** put this in the HTML as a table; keep it as a facilitator note.

| Shape | Mechanism | Examples |
|---|---|---|
| Decision table | Wildcard predicates, priority, most-specific-wins | GST determination, WHT treaty rates, payroll tax grouping |
| Effective-dated lookup | Keyed lookup with date ranges, no predicate matching | Fuel tax credit rates, FBT gross-up, car cost limit |
| Banded lookup | Value falls in a numeric range, usually date-ranged too | Payroll tax thresholds, progressive scales |

Resist the temptation to claim everything is a decision table. It is not, and a sharp person will
push back.

---

### Step 5 — Reconcile, then survive the audit · 15 min · **MAX 5 BLOCKS**

**Narrative.** You now have a computed GST position. Brindabella has a lodged one. Compare them —
then discover that someone has posted a backdated adjustment since lodgement, and the auditor
asks the question every tax practitioner dreads: *show me the ledger exactly as it stood when we
lodged.*

**Block 1 — build `TAX.V_GST_VS_BAS` and reconcile.** DDL per §5.14 plus the reconciliation query
in the same block. ~8 entity-periods light up as `REVIEW` or `INVESTIGATE`. This is the moment the
whole data pipeline pays for itself, and it is now the hook for everything that follows.

**Block 2 — the adjustment lands.** `INSERT` a backdated adjustment against a raw table for one
entity-period, refresh the Dynamic Table, and re-run the reconciliation — all in one block. The
variance for that period moves. The lodged figure no longer ties.

**Block 3 — `AT(OFFSET)`.** Query the ledger as it stood before the adjustment. The as-lodged
figure returns. One line of SQL, no backup, no restore, no ticket to IT.

**Block 4 — clone and `UNDROP`.** `CREATE TABLE AUDIT.GL_AS_LODGED_<date> CLONE ... AT(OFFSET
=> ...)`, then `DROP` it and `UNDROP` it, in one block.

**Platform callout — the scale makes this one land.** You just took an immutable snapshot of a
2.4-million-row ledger. It completed instantly and it consumed no storage, because a clone copies
metadata rather than data — you only pay for what subsequently changes. Ask the room what that
operation would cost them today, in time and in disk, and let the silence do the work.

**Block 5 — the visual close.** Re-run the reconciliation and use the Snowsight **Chart** tab —
net GST variance by entity. Screenshot-guided, no new SQL beyond re-running Block 1's query.
Everyone gets a visual payoff whether or not they go on to the Streamlit optional.

**Teaching point.** None of this required a backup strategy, a restore, or a conversation with
IT. It is a property of the platform.

**No cleanup step. Lab 2 depends on these objects.** End with a "what you built" summary table
and a pointer to the optionals and to Lab 2.

**One-line callback to the Step 4 closing panel.** In the summary, label the rules layer as *"the
first rule set of many — see the end of Step 4"*. One clause, no repetition of the diagram.

---

### Step 6 — ⭐ OPTIONAL · Streamlit tax control tower · 12 min · **MAX 2 BLOCKS**

Badge this **⭐ RECOMMENDED FIRST**. It is the wow.

**Block 1 — the app.** One complete paste-and-run Streamlit app created through Snowsight
(**Projects → Streamlit → + Streamlit App**), with three tabs:
1. **BAS reconciliation** — variance by entity and period, RAG coloured
2. **Exception register** — filterable by severity, entity, exception code
3. **Entity heatmap** — exception count by entity × tax period

**Block 2 — optional grant**, only if the app cannot see the objects.

Requirements: `get_active_session()`; `@st.cache_data(ttl=600)` on every query function;
`st.metric` tiles across the top; no `pip install`; runs unmodified with zero edits.

---

### Step 7 — OPTIONAL · Brindabella's tax team sends you a rate change · 10 min · **MAX 4 BLOCKS**

**Narrative.** This is how tax logic actually arrives: a spreadsheet, by email, from the person
who owns the rule. Following the imported-services review, Brindabella's tax team wants the same reverse-charge
correction extended to another supply category from the start of next quarter. You have been asked
what it does to the group position — *before* it happens.

1. **Upload** `assets/gsi_tax_rule_update.csv` through Snowsight (**Data → Database → schema →
   Create → Table → From File**) into `TAX.STG_RULE_UPDATE`. A handful of determination rows with a
   future `VALID_FROM`. UI only, no block.
2. **Block 1** — `CREATE DATABASE GSI_TAX_SCENARIO CLONE GSI_TAX_WORKSHOP;` The entire
   environment, instantly, at no storage cost.
3. **Block 2** — apply the staged rules to the **clone only**.
4. **Block 3** — one query comparing the group GST position across both databases side by side.
5. **Block 4** — `DROP DATABASE GSI_TAX_SCENARIO;`

**Teaching point.** Brindabella's tax team's spreadsheet became governed, effective-dated reference data,
and modelling its impact cost one clone and four minutes — with production untouched and no lodged
period restated.

**Facilitator note.** For a more technical room the CSV load can move into Step 1 core —
pre-stage the files if you do. It is optional here deliberately: Snowsight file upload is the
most likely thing to stall a mixed-skill room, and here a hiccup costs one person, not everyone.

---

### Step 8 — OPTIONAL · Share the snapshot with the auditor · 6 min · **MAX 2 BLOCKS**

**Block 1** — `CREATE SHARE`, grant `USAGE` on the database and the `AUDIT` schema, grant
`SELECT` on the clone only. **Block 2** — `SHOW GRANTS TO SHARE`.

Prose: the auditor sees the snapshot and nothing else — read-only, live, revocable, no data
copied, no extract emailed.

Use a placeholder consumer account with a callout that `ALTER SHARE ... ADD ACCOUNTS` needs a
real account identifier. Do not fabricate one.

---

## 7. LAB 2 — CORTEX AI FOR INDIRECT TAX

**File:** `gsi_tax_workshop_lab2_cortex_ai.html`
**Core:** 60 min across 5 steps · **Optional:** 34 min across 4 steps · **Total: 94 min**
**Hero duration text:** `60 minutes core + 34 minutes optional`

**Prerequisite callout at the top:** Lab 1 must be complete. `SNOWFLAKE.CORTEX_USER` database
role required.

### Step table

| # | id | Title | Min | Blocks (max) | Type |
|---|---|---|---|---|---|
| 1 | `step-1` | Verify your Lab 1 foundation | 3 | **1** | CORE |
| 2 | `step-2` | Classify the supply from the narrative | 15 | **4** | CORE |
| 3 | `step-3` | Extract structured fields from free text | 12 | **3** | CORE |
| 4 | `step-4` | Draft the working papers | 14 | **3** | CORE |
| 5 | `step-5` | Ask in plain English | 16 | **2** + UI | CORE |
| 6 | `step-6` | OPTIONAL · Materialise AI output for cost control | 8 | **2** | OPTIONAL |
| 7 | `step-7` | OPTIONAL · Triage taxpayer correspondence | 8 | **2** | OPTIONAL |
| 8 | `step-8` | OPTIONAL · Add an AI review queue to the app | 10 | **1** | OPTIONAL |
| 9 | `step-9` | OPTIONAL · A second tool on the agent | 8 | **1** | OPTIONAL |
| — | `step-10` | Cleanup | 2 | **1** | CLEANUP |

`coreSteps = 5`, `totalSteps = 9`. Cleanup is a separate card, excluded from progress.
**Core total: 60 min, 13 code blocks.**

> Lab 2 is deliberately lighter on blocks than Lab 1. Step 5 is mostly Snowsight UI, and the AI
> functions are one-liners — the wow is in the output, not the volume of SQL.

---

### Step 1 — Verify your Lab 1 foundation · 3 min · **MAX 1 BLOCK**

One query: row counts across all four layers via `UNION ALL`, with an expected-count column so
participants self-diagnose. A warning callout: if counts are zero, re-run the Lab 1 Step 1 setup
script. Do not add `SHOW DYNAMIC TABLES` here — it was covered in Lab 1.

---

### Step 2 — Classify the supply from the narrative · 15 min · **MAX 4 BLOCKS**

**Narrative.** Supply category drives treatment, and it is a human judgement made at data entry
by someone who is not in Brindabella's tax team. That is where miscoding is born.

**Block 1 — the narratives and the AI call together.** Select 10 rows showing
`INVOICE_NARRATIVE`, `BOOKED_SUPPLY_CATEGORY` and `AI_CLASSIFY(...)` side by side. One block does
the "look at the raw text" job and the "watch AI read it" job at once — and the disagreements are
visible immediately in the third column. This is the wow; do not split it.

**Sample-size callout — mandatory.** State plainly that `DOC_TAX_INVOICE` holds 300 documents, not
2.4 million, because language model cost scales with rows. In production you would classify on
arrival, not retrospectively across the whole ledger. Saying this earns credibility; leaving it
unsaid invites the question at the worst moment.

**Block 2 — build `AI_INSIGHTS.V_AI_SUPPLY_CLASSIFIED`** with the `MISCODING_FLAG`.

**Block 3 — the miscoding pattern.** Aggregate disagreements by booked category. Entertainment
booked as professional fees is the one that costs money.

**Block 4 — close the loop.** Join flagged docs back to `TAX.V_GST_EXCEPTIONS` on
`(SOURCE_SYSTEM, SOURCE_DOC_REF)` so AI findings land in the same work queue Brindabella's tax team already
uses.

**Teaching point.** AI did not replace the rules. It supplied a missing attribute *to* the rules.
The determination logic is unchanged and still auditable.

---

### Step 3 — Extract structured fields from free text · 12 min · **MAX 3 BLOCKS**

**Block 1** — `EXTRACT_ANSWER` twice over `SUPPLIER_REMARKS` on 10 rows: the supplier's ABN and
the GST amount stated on the invoice, next to the raw text.

**Block 2** — build `AI_INSIGHTS.V_AI_DOC_EXTRACTED`.

**Block 3 — one reconciliation query, three findings.** Extracted ABN vs
`DIM_SUPPLIER.SUPPLIER_ABN`, extracted GST vs `BOOKED_TAX_AMOUNT`, and the total input tax credit
at risk where no ABN can be found anywhere. One result set, three columns of bad news.

**Teaching point.** The invoice is the primary evidence. Until now nobody could query it.

---

### Step 4 — Draft the working papers · 14 min · **MAX 3 BLOCKS**

**Block 1 — bad prompt vs good prompt, side by side in one query.** Two `AI_COMPLETE` calls over
the same 5 exceptions so the quality difference is undeniable in one result grid. The good prompt
specifies role, audience, length and required elements, and passes `APPLIED_RULE_DESCRIPTION` so
the output is grounded in the rule that actually fired.

**Block 2** — build `AI_INSIGHTS.V_AI_EXCEPTION_RATIONALE` with `LIMIT 25` inside the CTE and
every concatenated column wrapped in `COALESCE`.

**Block 3** — read the generated working papers for the highest-risk exceptions.

**Teaching point.** Explaining an exception is the reviewer's bottleneck, not finding it. And
because `APPLIED_RULE_ID` is carried through, every generated sentence traces back to a rule row
a human can inspect.

**Cost callout.** State plainly that this is the most expensive operation in the workshop and
that in production you would materialise it — which is the optional step that follows.

---

### Step 5 — Ask in plain English · 16 min · **MAX 2 BLOCKS + UI**

This step is mostly Snowsight. Keep SQL to two blocks; the time goes into the agent conversation,
which is the payoff of the entire workshop.

**Block 1** — build `AGENTS.V_GST_INTELLIGENCE`.

**Block 2** — `CREATE SEMANTIC VIEW AGENTS.SV_GST_COMPLIANCE`, provided as the fallback path.

**UI, primary path** — create the semantic view via Snowsight Autopilot (**AI & ML → Cortex
Analyst → Create new**), accept and refine the suggestions. Lead with this: it is faster and far
more convincing in a room than reading DDL. Emphasise synonyms — a tax person types "input tax
credits", not `LABEL_1B_GST_CREDITS`. The synonyms are the product.

**UI** — create `GST_COMPLIANCE_AGENT` (**AI & ML → Agents**) with the semantic view attached as
an Analyst tool. Response instructions: answer, then the SQL, then any assumptions about period
or entity.

**Eight test questions**, easy to hard:
1. What was our total GST payable last quarter?
2. Which entities have exceptions this month?
3. Show me net GST by entity for the last six months
4. Which suppliers are missing an ABN on claimed credits?
5. What is our total exposure from unmapped accounts?
6. Compare computed GST to lodged GST by period
7. Which supply categories generate the most exceptions?
8. Show imported professional fees before and after 1 July 2024

**Demonstrate question 8 live.** It exercises the effective-dated determination rules built in Lab 1
— the answer changes across the 1 July 2024 boundary — and it closes the whole workshop on itself in
one sentence of plain English.

**Teaching point.** The agent is only as good as the semantic layer, and the semantic layer is
only as good as the governed data underneath it. Lab 1 was the prerequisite for this working.

---

### Steps 6–9 — Optionals

| Step | Blocks | Content |
|---|---|---|
| 6 | **2** | `AI_INSIGHTS.DT_AI_EXCEPTION_REVIEW` — Dynamic Table with `TARGET_LAG = '24 hours'` wrapping the AI classification and rationale (block 1), then a query showing it returns instantly with no model invocation (block 2). The materialisation lesson from Lab 1, now applied to AI. |
| 7 | **2** | `AI_SENTIMENT` over `CORRESPONDENCE_TEXT` for triage. **`CASE` must handle `positive`, `negative`, `mixed`, `neutral`.** Explicit callout that `mixed` exists and is commonly missed. |
| 8 | **1** | Add a fourth tab to the Lab 1 Streamlit app: AI review queue with generated rationale, applied rule, and approve/reject radio buttons. Full replacement app code in one block. |
| 9 | **1** | Add a second Analyst tool to the agent over a supplier-risk view, and show how the agent chooses between tools. |

---

### Step 10 — Cleanup · 2 min · **MAX 1 BLOCK**

One block:
`DROP DATABASE IF EXISTS GSI_TAX_WORKSHOP;`
`DROP DATABASE IF EXISTS GSI_TAX_SCENARIO;`
`DROP WAREHOUSE IF EXISTS GSI_TAX_WH;`
`DROP SHARE IF EXISTS ...;`
Plus a note that an agent created through the UI must be removed from the Agents page.

Warning callout: this is irreversible beyond the Time Travel window.

---

## 8. HTML / CSS / JS REQUIREMENTS

Applies to all three files. **Agent A owns the shell; all other agents produce body fragments
only.**

### Structure

- **Single self-contained HTML file.** No external CSS or JS files. No CDN dependencies except
  the Google Fonts link.
- **ALL CSS in one `<style>` block** in `<head>`. **ALL JS in one `<script>` block** before
  `</body>`. Do not scatter either.
- **Reuse the proven stylesheet.** Start from
  `/Users/jacksonstaub/Documents/COCO/HOL/fsi_generic/_extracted_lab1.css`. The user has already
  approved that visual treatment; matching it guarantees consistency and removes a QA cycle.

### Brand

| Token | Value |
|---|---|
| Mid Blue | `#11567F` |
| Snowflake Blue | `#29B5E8` |
| Body text | `#5B5B5B` |
| Hero gradient | `linear-gradient(135deg, #11567F 0%, #0a3a5c 100%)` |
| Headings | Montserrat, uppercase, `letter-spacing: 0.5px` |
| Body | Lato |

### Step cards

```html
<div class="step-card" id="step-N">
```

**Hyphen. `id="step-3"`, never `id="step3"`.** The nav, `toggleStep()` and
`markStepComplete()` all resolve on this pattern. This has broken before.

Optional steps additionally carry `class="step-card optional-step"` and a visible
`OPTIONAL` badge in the header. Step 6 of Lab 1 also carries a `⭐ RECOMMENDED` badge.

### Code blocks — exact markup

```html
<div class="code-block">
  <div class="code-header">
    <span class="code-lang">sql</span>
    <button class="btn-copy" onclick="copyCode(this)">Copy</button>
  </div>
  <pre><code>SELECT ...</code></pre>
</div>
```

`code-lang` is one of `sql`, `python`, `bash`. **Escape HTML entities inside code blocks** —
`&lt;`, `&gt;`, `&amp;`. An unescaped `<` in SQL silently destroys the rest of the page.

### JavaScript

Required: `const coreSteps`, `const totalSteps`, `copyCode(btn)`, `toggleStep(n)`,
`markStepComplete(n)`, `updateProgress()`.

localStorage shape, key `workshop_gsi_tax_lab{N}_progress`:

```json
{ "started": "<ISO timestamp>", "completed": [], "steps": {} }
```

Progress bar reflects **core steps only** — completing 5 of 5 core steps shows 100%. Optional
steps persist their state but do not gate completion. Someone who does only the core lab must
not be shown 62%.

### Content rules

- Nav sidebar times, step-header times, and the hero duration must all agree. Sum the step
  table and check.
- Synthetic-data warning callout immediately before Step 1 in both labs.
- Prerequisite callout at the top of Lab 2.
- No competitor product names anywhere.
- No credentials, no real account identifiers, no real ABNs, no real PII.
- No specific GSI named. "Your firm", "your team". The client is **Brindabella Group** — see §0.2.
- Footer: `© 2026 Snowflake Inc. All Rights Reserved.`
- **No Colombia community CTA.** APJ audience.

### Index page

`gsi_tax_workshop_index.html` — hero, the workshop premise in three sentences, two lab cards
with duration and topic list, a prerequisites block, the shared-database note explaining that
Lab 2 depends on Lab 1, and the synthetic-data disclaimer. Same brand tokens.

**Also include a short "where this goes next" section** near the foot of the index, reusing the
Step 4 closing-panel diagram (§6, Step 4 closing panel) at smaller scale: the conformed ledger with
GST built and FBT, fuel tax credits, payroll tax and withholding tax greyed out beside it. One
sentence beneath it — Brindabella's ledger is bespoke, the rule sets are reusable IP. This is
the page a partner will still have open after the session, so the extensibility story belongs here
as well as in the lab.

---

## 9. QA GATE — BEFORE DELIVERY

1. Every SQL statement executed against `SFSEEUROPE-DEMO_STAUB_US_WEST_2_PRIMARY`, in order,
   from a clean state. Not compiled — **executed**.
2. Row counts match §5 exactly: 1,200,000 / 800,000 / 400,000 / 14 / 165 / 2,000 / 360 / 300 / 16 /
   18 and `CURATED.GL_HARMONISED` = 2,400,000.
3. **Setup script completes in under 2 minutes** on a SMALL warehouse. Time it. Reference: 1.2M
   rows measured at 6.45s, so the whole script should be well under 30s. If it is not, the SQL is
   at fault, not the volume.
4. **`UNIFORM` bounds are constants everywhere.** Grep for `UNIFORM(0, DATEDIFF` and any
   non-literal second argument. This form does not compile — see §5.0.1.
5. **`TAX.V_GST_DETERMINED` performance.** Time an unfiltered aggregate over the view. If it
   exceeds ~15 seconds on SMALL, the lab must only ever query it with an entity or period filter,
   and every example block must be rewritten accordingly. Report the measured time.
6. `COUNT(DISTINCT GL_LINE_ID) = COUNT(*)` on `GL_HARMONISED` and on `V_GST_DETERMINED` — the
   decision-table join must not fan out.
7. No row in `V_GST_DETERMINED` has a NULL `TAX_TREATMENT` or NULL `APPLIED_RATE_PCT`.
8. **The rule boundary works.** Imported professional fees from non-registered offshore suppliers
   resolve to `GST_FREE` (rule 9) before 2024-07-01 and `REVERSE_CHARGE` (rule 16) on or after it.
   Confirm both sides return a material number of rows.
9. ~8 entity-periods in `V_GST_VS_BAS` have `RECON_STATUS <> 'MATCHED'`.
10. Every exception code E1–E7 returns at least one row.
11. **No Singapore or New Zealand worked examples.** Grep both HTML files for "Singapore" and "New
    Zealand". Permitted only in the entity list and the jurisdiction dimension — never in a query,
    a callout, a narrative or an agent question. Every example is Australian.
12. All five Cortex functions return non-NULL on real workshop data.
13. `AI_SENTIMENT` `CASE` handles all four labels.
14. Streamlit app runs unmodified against 2.4M rows without timing out. Verify the cached queries
    are aggregates, not row-level scans.
15. Agent answers all eight test questions, including question 8.
16. No banned function anywhere in either file. Grep for all five.
17. Times sum correctly in both files.
18. **Query budget respected.** Count `<div class="code-block">` occurrences per step card and
    compare against the Blocks column in the step tables. Lab 1 core ≤ 19 total; Lab 2 core ≤ 13
    total. **A step over budget fails QA and must be cut, not justified.**
19. No step re-teaches a technique already taught in an earlier step of either lab.
20. **Step 4 closing panel present**, rendered as styled `<div>`s (not ASCII in a `<pre>`), with the
    GST box highlighted and four greyed-out future rule sets. Adds **zero** code blocks — confirm
    Step 4 is still at 5.
21. **Index page "where this goes next" section present**, reusing the same diagram at smaller scale.
22. **No view-versus-Dynamic-Table comparison anywhere.** Grep both files for "volatility",
    "materialise", "materialize" and "Dynamic Table instead". Per §4, this comparison is banned.
23. `id="step-N"` hyphenated everywhere; no `id="stepN"`.
24. Copy buttons work; no unescaped `<` inside any code block.
25. `snowflake-brand-guidelines` skill applied after assembly.
```
