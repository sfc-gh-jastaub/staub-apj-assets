# staub-golden-demos

Reusable, battle-tested methods for building Snowflake use-case demos with Cortex Code (CoCo).

## snow-ambition-usecase-method

- `snow-ambition-prompt-playbook.md` — paste-in-order prompt playbook: context → narrative → design → data layer → AI/agent layer → Streamlit → React app → notebook.
- `staub-live-demo-driver/SKILL.md` — CoCo skill that preloads account facts, behavior rails, and gotchas so in-demo prompts stay short and builds run first-try.

## gsi-tax-gst-workshop

Half-day hands-on workshop for a tax practice at a GSI: Australian GST analytics and Cortex AI over a
three-ERP general ledger. Two Snowflake Notebooks (the primary surface participants run) plus matching
HTML read-along guides, deterministic seeded data, and a build that proves the guides and notebooks
never drift.

## synthetic_data_agentic_evaluations_demo

Test a Cortex Agent properly without real customers in dev: mask prod, generate a fully synthetic copy with
`GENERATE_SYNTHETIC_DATA`, prove it looks like prod with a 23-check scorecard, score agent v1 vs v2 on a golden set
whose answers are computed from the data, then promote the tested agent to prod and gate on prod scores. One setup
script (plus an optional 20M-row at-scale script) and a SQL-first Snowflake Notebook; connect a Workspace to this repo
and run setup, then the notebook.
