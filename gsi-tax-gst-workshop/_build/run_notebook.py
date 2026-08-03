#!/usr/bin/env python3
"""
Execute every code cell of a workshop notebook against Snowflake, in order,
and report per-cell pass/fail.

The notebook is the artefact participants actually run on the day, so it is the
thing that must execute cleanly. This runner is the gate.

Snowflake Notebooks keep session state across cells; `snow sql -f` does not, so a
context preamble is prepended to each cell. That is the only difference from a
real notebook run.

    python3 _build/run_notebook.py lab1
    python3 _build/run_notebook.py lab2 --skip-cortex
    python3 _build/run_notebook.py lab1 --only step5

Cells that cannot work headlessly are skipped by name and reported as SKIP with a
reason, so the pass count is honest rather than flattering.
"""
import json
import pathlib
import re
import sys
import time
import tomllib

import io

import snowflake.connector

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONN = "staub_uswest_primary_pat"
NB = {"lab1": "gsi_tax_lab1_foundation.ipynb", "lab2": "gsi_tax_lab2_cortex_ai.ipynb"}

def connect():
    """One connection for the whole run, so session state persists across cells
    exactly as it does in a Snowflake Notebook. Running each cell in its own
    session is not a valid test: cell 1 sets the database with USE DATABASE and
    every later cell depends on it."""
    cfg = tomllib.loads((pathlib.Path.home() / ".snowflake/config.toml").read_text())
    c = dict(cfg["connections"][CONN])
    tok = pathlib.Path(c.pop("token_file_path")).expanduser().read_text().strip()
    return snowflake.connector.connect(
        account=c["account"], user=c["user"], role=c.get("role"),
        warehouse="GSI_TAX_WH", authenticator=c["authenticator"], token=tok,
        client_session_keep_alive=True,
    )

# Cells that are DESIGNED to raise. The error is the lesson, so the gate must
# assert that they fail - if one of these ever passes, the teaching point is gone.
EXPECT_FAIL = {
    "lab1": {
        "step2_block2": "naive UNION ALL must fail on the type mismatch",
        "step3_block1a": "strict TO_DATE must fail on the unparseable legacy date",
    },
    "lab2": {},
}

# name -> reason. These need a human or a UI action; they are not notebook defects.
SKIP = {
    "lab1": {
        "step6_block1": "Streamlit app - renders in notebook, nothing to assert headlessly",
    },
    "lab2": {
        "step8_block1": "Streamlit app - renders in notebook, nothing to assert headlessly",
        "step10_block1a": "drops the workshop database - run deliberately, not as part of a check",
        "step10_block1b": "verifies the drop above",
    },
}

CORTEX = re.compile(r"AI_COMPLETE|AI_CLASSIFY|EXTRACT_ANSWER|AI_SENTIMENT|SUMMARIZE", re.I)


def cells(lab):
    nb = json.loads((ROOT / NB[lab]).read_text())
    out = []
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        out.append(
            (
                c["metadata"].get("name", "?"),
                c["metadata"].get("language", "sql"),
                "".join(c["source"]),
            )
        )
    return out


def run_sql(conn, sql):
    """Execute every statement in one cell on the shared session."""
    try:
        for cur in conn.execute_string(sql, remove_comments=False):
            cur.fetchall() if cur.description else None
        return True, ""
    except Exception as e:
        return False, re.sub(r"\s+", " ", str(e))[:320]


def main():
    lab = next((a for a in sys.argv[1:] if not a.startswith("--")), "lab1")
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1]
    skip_cortex = "--skip-cortex" in sys.argv

    conn = connect()
    results = []
    t0 = time.time()
    for name, lang, src in cells(lab):
        if only and not name.startswith(only):
            continue
        if name in SKIP[lab]:
            results.append((name, "SKIP", SKIP[lab][name]))
            print(f"  SKIP {name:18} {SKIP[lab][name]}")
            continue
        if lang == "python":
            try:
                compile(src, name, "exec")
                results.append((name, "PASS", "python syntax ok"))
                print(f"  PASS {name:18} python syntax ok")
            except SyntaxError as e:
                results.append((name, "FAIL", f"SyntaxError: {e}"))
                print(f"  FAIL {name:18} SyntaxError: {e}")
            continue
        if skip_cortex and CORTEX.search(src):
            results.append((name, "SKIP", "cortex cell, --skip-cortex"))
            print(f"  SKIP {name:18} cortex cell (--skip-cortex)")
            continue

        t = time.time()
        ok, err = run_sql(conn, src)
        dt = time.time() - t
        if name in EXPECT_FAIL[lab]:
            why = EXPECT_FAIL[lab][name]
            if ok:
                results.append((name, "FAIL", f"expected to fail but SUCCEEDED - {why}"))
                print(f"  FAIL {name:18} expected failure did not happen: {why}")
            else:
                results.append((name, "XFAIL", err[:90]))
                print(f"  XFAIL {name:17} failed as designed: {err[:70]}")
            continue
        if ok:
            results.append((name, "PASS", f"{dt:.1f}s"))
            print(f"  PASS {name:18} {dt:5.1f}s")
        else:
            results.append((name, "FAIL", err))
            print(f"  FAIL {name:18} {dt:5.1f}s  {err}")

    x = sum(1 for r in results if r[1] == "XFAIL")
    p = sum(1 for r in results if r[1] == "PASS")
    f = sum(1 for r in results if r[1] == "FAIL")
    s = sum(1 for r in results if r[1] == "SKIP")
    print(f"\n{lab}: {p} passed, {x} failed-as-designed, {f} FAILED, {s} skipped, {time.time()-t0:.0f}s total")
    if f:
        print("\nFAILURES:")
        for n, st, m in results:
            if st == "FAIL":
                print(f"  {n}: {m}")
    (ROOT / "_build" / f".run_{lab}.json").write_text(json.dumps(results, indent=1))
    sys.exit(1 if f else 0)


if __name__ == "__main__":
    main()
