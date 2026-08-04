# Tax HOL Blueprint

Brief for `/snowflake-hol-generator`. Describes the flow this workshop landed on, not its contents.

## Use case — one only

An Australian group has grown by acquisition and runs **three general ledgers** (SAP, Oracle, a legacy
AP system) that have never agreed. The tax practice rebuilds the group **GST** position in Excel every
month, cannot reconcile it to what was lodged with the ATO, and cannot reproduce a prior filing when
asked. Audience: indirect-tax practitioners at a consulting firm — strong SQL and Excel, new to
Snowflake. Vendor-neutral throughout ("your firm", "the tax practice", "your client").

Australian GST only. No second tax domain — a second thread pollutes the story.

## Four notebooks

| Notebook | Role | Duration |
|---|---|---|
| `lab0_setup` | Builds the platform and generates the data. Run before the workshop. | 5 min |
| `lab1_foundation` | Raw to return-ready. The data and governance lab. | ~57 min core |
| `lab2_cortex_ai` | Reads the text the ledger cannot. The AI lab. | ~60 min core |
| `reset` | Clear Lab 2 / clear Lab 1 / drop everything / verify. Run any time. | <1 min |

Notebooks are the primary surface — participants run cells, never copy-paste. Each lab is **5 core
steps plus optional extensions**, and the value ledger completes at the last core step so anyone who
stops there feels finished.

## Layered architecture

`RAW_DATA` (as landed, never edited) → `CURATED` (conformance only, no tax logic) → `TAX` (rules,
determination, exceptions) → `AI_INSIGHTS` / `AGENTS` / `APPS` / `AUDIT`.

The separation is the teaching point: "did this date parse" and "is this supply GST-free" are different
questions with different owners.

## Lab 1 arc — Inspect → Diagnose → Conform → Determine → Reconcile

1. **Inspect** — verify the foundation, then read the three raw shapes side by side.
2. **Diagnose** — answer the partner's question against one ERP, get a confidently wrong number, then
   quantify every defect in one query. Includes a cell **designed to fail** (naive `UNION ALL`).
3. **Conform** — one Dynamic Table unions all three, resolves dimensions, and *labels* data-quality
   problems rather than dropping rows. Includes a cell **designed to fail** (strict `TO_DATE`).
4. **Determine** — tax rules as **data the tax team owns**: a decision table with wildcard predicates,
   effective-dated rates, most-specific-wins precedence via `QUALIFY`. Change one row, watch the group
   position move, put it back. Then a standing exception register.
5. **Reconcile** — computed position against lodged BAS; post a backdated adjustment and watch a tied
   period break; recover the as-lodged ledger with Time Travel; take a zero-copy audit clone.

Optional: Streamlit control tower, scenario modelling on a cloned database, secure share to the auditor.

## Lab 2 arc — Verify → Classify → Extract → Draft → Ask

1. **Verify** — confirm Lab 1's objects exist before spending a model call.
2. **Classify** — `AI_CLASSIFY` reads the invoice narrative, disagrees with the booked category, and
   surfaces entertainment miscoded as professional fees. AI supplies a *missing attribute* to the rules;
   it does not replace them.
3. **Extract** — `EXTRACT_ANSWER` pulls the supplier ABN and stated GST out of free text, reconciles
   against the supplier master, and quantifies input tax credit at risk.
4. **Draft** — `AI_COMPLETE` writes the working paper, grounded in the rule that actually fired. Show a
   lazy prompt beside a specified one.
5. **Ask** — semantic view plus a Cortex Agent so a tax partner asks in plain English. The closing
   question demonstrates the effective-dated rule boundary.

Optional: materialise AI output for cost control, correspondence triage, AI review queue in the app,
a second agent tool.

## Step shape

Illustrative, not mandatory — combine or drop beats where they do not apply:

**business step → technical decision → do → prove**

- *Business* — what the tax practice does today and why it hurts.
- *Decision* — the Snowflake feature **and the alternative it beat**. Omit where nothing was rejected.
- *Prove* — what the result demonstrates, with expected figures inline; name the feature here if the
  decision beat was skipped.

Deep background goes in the guide, not the notebook. No notebook prose block beyond ~120 words.

## Voice

Plain, specific, professional. Scannability comes from bold lead-in clauses, short paragraphs and
tables — **not** from emoji legends. Banned: manufactured-drama headings ("The scale moment"),
formulaic openers that announce a point rather than making it ("The teaching point — X"), marketing
verbs (unlock, leverage, seamless, powerful), and instructor asides in a participant notebook ("ask the
room", "say this out loud"). State the finding and let the number carry it.

## Non-negotiables

- **Seed every `RANDOM()` and pin the date window.** Quoted figures must reproduce on any day, in any
  account, at any warehouse size. Never derive the data window from `CURRENT_DATE()`.
- **Two cells are designed to fail.** The error is the lesson; the next cell fixes it. Precede each with
  a callout so a red cell never looks like the participant's mistake.
- **Every statement idempotent.** `CREATE OR REPLACE` / `IF EXISTS` everywhere, and undo anything a
  re-run would stack (a fixed-key `INSERT`, a rate `UPDATE` pair).
- **Drop a share before the database it grants on** — it pins the database otherwise.
- **Post-teardown checks must not need a warehouse.** Plain `SHOW`, no `RESULT_SCAN`.
- **Generate the guide and the notebook from one source** and fail the build if their SQL differs.
- **Execute before delivering.** A notebook that has not been run is not finished.
