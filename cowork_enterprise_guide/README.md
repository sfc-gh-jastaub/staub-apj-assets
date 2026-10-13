# CoWork Enterprise Demo — Notebook Series

**CoWork** (Snowflake Intelligence) lets business users chat with a governed AI agent over their
Snowflake data. This repo is a **production runbook** — not a feature tour — that takes a CoWork
agent from raw tables all the way to a governed, cost-controlled, evaluated, business-user-ready
deployment, delivered as nine runnable **Snowflake Workspace SQL notebooks** (SQL kernel, `%%sql` cells).

Everything runs against a fictional buy-side firm, **"Strive Capital,"** entirely inside an isolated
`COWORK_ENTERPRISE_DEMO` database — so it never collides with other objects and tears down cleanly.
The narrative companion (the *why* behind the sequencing) is
[`CoWork_Enterprise_Overview.html`](CoWork_Enterprise_Overview.html).

### What you'll build

A governed **Cortex Analyst → Cortex Search → Cortex Agent → CoWork** solution: a semantic view and
search services over the data, a least-privilege access model with `AI_REDACT` PII masking, a hardened
agent published to the account's CoWork object, layered cost controls (budgets, cost-centre tags,
per-user quotas), an evaluation gate, and a dev→prod promotion plus continuous-improvement loop.

### Three ideas behind every decision

1. **The agent runs with caller's rights** — it inherits the invoking user's grants, masking, and
   row-access, so getting RBAC right *is* your CoWork security posture.
2. **Govern → Build → Go Live** — meaning and access are established *before* the agent exists, so
   the agent is born into an already-governed environment.
3. **Evaluation is the gate** — the same scored eval gates go-live, dev→prod promotion, and every
   continuous-improvement change.

### Repository layout

| Path | What it is |
|------|------------|
| [`notebooks/`](notebooks/) | The nine `Notebook_00`–`Notebook_08` SQL notebooks (run these). |
| [`build_notebooks.py`](build_notebooks.py) | Self-contained generator that produces the notebooks. |
| [`CoWork_Enterprise_Overview.html`](CoWork_Enterprise_Overview.html) | Narrative companion — the reasoning behind the sequencing. |

## Run order

| # | Notebook | Guide phase | What it does |
|---|----------|-------------|--------------|
| 00 | `Notebook_00_Lab_Setup` | Phase 0 (build the sandbox) | Role, DB + schemas, XS warehouse, grants, self-contained sample data |
| 01 | `Notebook_01_Context_Layer` | Phase 1 | Governed semantic view + Cortex Search; validate before building the agent |
| 02 | `Notebook_02_Govern_Access` | Phase 2 | SI-only role, four-layer access grants, `AI_REDACT` masking |
| 03 | `Notebook_03_Build_Harden_Agent` | Phase 3 | `CREATE AGENT`, agent test, read-only guardrails check, MCP (illustrative) |
| 04 | `Notebook_04_Control_Cost` | Phase 4 | Observe → Attribute → Control: usage views, cost-centre tags (agent + warehouse), warehouse timeout, resource budget + threshold, per-user quota |
| 05 | `Notebook_05_Evaluate_GoLive_Operate` | Phase 5 | Golden smoke tests + Agent GPA eval (curated dataset, `EXECUTE_AI_EVALUATION`), publish to the CoWork object, branding, health check |
| 06 | `Notebook_06_Dev_to_Prod` | Phase 5+ | Agent-as-code: capture spec, version, promote via `CREATE OR REPLACE … FROM SPECIFICATION`, eval gate, publish |
| 07 | `Notebook_07_Continuous_Improvement` | Phase 5+ | Self-improving loop: mine traces → curate eval set → Agent GPA baseline → optimize **instructions only** → re-evaluate → promote |
| 08 | `Notebook_08_Cleanup` | — | Removes only the demo footprint; leaves shared objects intact |

Run **00 → 07 in order** (objects build on each other), then **08** (cleanup) last.

> Account-level identity/network hardening (network policies, SSO/IdP, SCIM, MFA, PrivateLink,
> revoking `CORTEX_USER`/`EXECUTE AGENT TASK` from `PUBLIC`) is intentionally **not** run in these
> notebooks — run that checklist in the customer's own account.

## Prerequisites

- `ACCOUNTADMIN` (used for account-scoped steps: publishing to the CoWork object, grants).
- Cross-region inference enabled (`CORTEX_ENABLED_CROSS_REGION`) — Notebook 00 sets it (no-op if already on).
- Enterprise Edition for Cortex AI Guardrails (Notebook 03 reads the setting; it does not change it).

## Shared-account safety (built in)

These notebooks were verified on a shared SE account and are deliberately non-destructive to
shared state:

- **Isolated namespace** — everything is `COWORK_ENTERPRISE_DEMO*`; nothing else is touched.
- **`CORTEX_USER` is not revoked from `PUBLIC`** — the production hardening pattern is shown in
  markdown only (revoking would break other users).
- **The CoWork object is never created or dropped** — it is a singleton that pre-exists and is
  shared. Notebooks 05/06/07 only `ADD`/modify our agents; Notebook 08 only `DROP`s our agents from it.
- **Account `AI_SETTINGS` (guardrails) is read-only** — already enabled account-wide; Notebook 03
  displays it and shows the enable command for reference only.
- **`ALLOWED_INTERFACES` / IdP redirect** are shown as reference (no real user is locked).
- **Per-user quota (NB04)** is created in **monitoring mode only** (no block enforcement, no email
  notifications) so it never blocks or emails anyone on the shared account; it is dropped in NB07.

## Running the notebooks in Snowsight

The simplest way to run these is a **Git-connected Workspace** — Snowsight syncs this repo directly, so you
open and run the notebooks in place (and pull updates later) without uploading anything.

1. In Snowsight, go to **Projects » Workspaces**.
2. Open the Workspaces menu and select **From Git repository**.
3. Paste the repository URL: `https://github.com/sfc-gh-jastaub/cowork_enterprise_guide`
4. Select an **API integration** that allows access to the repo (creating one needs `CREATE API INTEGRATION`;
   otherwise pick one you have `USAGE` on).
5. For **authentication**, choose **Public repository** — this repo is public, so no secret or token is needed.
6. Select **Create**, then open the `notebooks/` folder and run **00 → 07** in order, then **08** last.

> Each `.ipynb` runs on the SQL kernel. Set the notebook warehouse to `COWORK_ENTERPRISE_DEMO_WH`
> (created in Notebook 00) once it exists, or any warehouse you can use for the first run.

**Alternative — upload manually.** If you'd rather not connect Git, upload each notebook via the CLI:

```bash
cortex artifact create notebook "CoWork Demo 00 - Lab Setup" "notebooks/Notebook_00_Lab_Setup.ipynb"
```

## Regenerating

The notebooks are generated by [`build_notebooks.py`](build_notebooks.py), a self-contained
builder that defines all SQL and markdown inline (in the `COWORK_ENTERPRISE_DEMO` namespace) and
assembles the nine phase notebooks — it reads no external files. Re-run `python3 build_notebooks.py` to rebuild.

## Verification status

Every notebook was test-deployed to a live Snowflake account and verified end to end
(objects created, semantic view returns correct numbers, agent answers via `DATA_AGENT_RUN`,
budget + tag created, agent published to and removed from the CoWork object, account left clean).
