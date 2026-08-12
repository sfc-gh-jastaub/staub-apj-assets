#!/usr/bin/env python3
"""
Emit Snowflake Notebook (.ipynb) versions of the GSI Tax labs.

Reads the SAME step fragments in _build/ that assemble.py uses for the HTML, so
the notebook and the HTML guide never drift. The HTML remains the read-along
narrative (sidebar nav, progress bar, styling); the notebook is the execution
surface, so participants never copy-paste.

Snowflake constraint: markdown cells do NOT render HTML, so all prose is
converted to real markdown.

Usage:  python3 _build/assemble_nb.py lab1
        python3 _build/assemble_nb.py lab2
        python3 _build/assemble_nb.py all
"""
import html
import json
import pathlib
import re
import sys

import nbutil
from assemble import CFG

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
DIST = ROOT / "GSI_TAX_WorkshopMaterial"

NB_OUT = {
    "setup": "gsi_tax_lab0_setup.ipynb",
    "lab1": "gsi_tax_lab1_foundation.ipynb",
    "lab2": "gsi_tax_lab2_cortex_ai.ipynb",
    "reset": "gsi_tax_reset.ipynb",
}

# ---------------------------------------------------------------------------
# ORIENTATION
#
# One stage name per core step, so the reader can see where the current step
# sits in the arc with no mapping table: stage index == step - 1 for core steps.
# len(stages) must equal cfg["core"]; build.py asserts it. Optional steps are
# labelled as extensions instead of being forced onto the arc.
# ---------------------------------------------------------------------------
STAGES = {
    "setup": ["Architecture", "Load", "Rules", "Verify"],
    "lab1": ["Inspect", "Diagnose", "Conform", "Determine", "Reconcile"],
    "lab2": ["Verify", "Classify", "Extract", "Draft", "Ask"],
    "reset": ["Lab 2 only", "Lab 1 only", "Everything", "Verify"],
}

# ---------------------------------------------------------------------------
# VALUE LEDGER
#
# What the tax practice can do that it could not before, and the step that
# earned it. Rendered only at the milestone steps in LEDGER_AT - a checklist
# repeated after every step becomes furniture people skim past.
#
# Each list must reach a complete state at the last core step, so anyone who
# stops at the end of core sees a finished ledger, not a half-done one.
# ---------------------------------------------------------------------------
LEDGER = {
    "lab1": [
        (1, "see all three ERP extracts side by side, unmodified"),
        (2, "show exactly why the group GST position cannot be answered today"),
        (3, "query 2,400,000 lines as one governed ledger that maintains itself"),
        (4, "read the entire determination logic without reading SQL"),
        (5, "reconcile the computed position against what was actually lodged"),
        (5, "reproduce any prior filing on demand, and prove nothing moved"),
    ],
    "lab2": [
        (2, "read a supply category out of a free-text invoice narrative"),
        (3, "pull ABNs and GST wording out of unstructured remarks"),
        (4, "draft a defensible working paper for every exception"),
        (5, "answer a partner's question in plain English, with the SQL shown"),
        (5, "hand Brindabella's tax team a governed way to ask their own questions"),
    ],
}
LEDGER_AT = {"lab1": [2, 5, 8], "lab2": [3, 5, 9]}


def ledger_md(lab, upto):
    """Render the value ledger, ticking everything earned by step `upto`."""
    rows = [
        "> - [%s] %s%s" % (
            "x" if step <= upto else " ",
            text,
            " \u2014 *Step %d*" % step if step <= upto else "",
        )
        for step, text in LEDGER[lab]
    ]
    return "> **What you can do now**\n>\n" + "\n".join(rows)


def step_orientation(lab, step, cfg):
    """The 'where am I' line that sits under a step heading."""
    stages = STAGES.get(lab, [])
    if step <= cfg["core"] and len(stages) == cfg["core"]:
        return " \u2192 ".join(
            ("**%s**" % s) if i == step - 1 else s for i, s in enumerate(stages)
        )
    return "*Optional extension \u2014 the core flow is complete without this.*"

# ---------------------------------------------------------------------------
# EDITORIAL SPLIT POLICY  ("split only where each result matters")
#
#   (lab, step, block) -> "all"        every statement becomes its own cell
#                      -> [[1,2],[3]] explicit 1-based statement grouping
#   Absent            -> one cell, statements run in sequence, last result shown.
#
# Rationale is on each line. Blocks NOT listed are DDL/grant/context sequences
# where no intermediate result is worth rendering.
# ---------------------------------------------------------------------------
SPLIT = {
    # Lab 1
    ("lab1", 3, 1): "all",            # TO_DATE fails / TRY_TO_DATE survives - the lesson IS the two results
    ("lab1", 4, 1): "all",            # determination table, then rate table - both read on screen
    ("lab1", 4, 4): "all",            # UPDATE rate -> re-query (answer moves) -> UPDATE back
    ("lab1", 4, 5): "all",            # CREATE exception view, then rank the register
    ("lab1", 5, 1): "all",            # CREATE recon view, then the recon summary
    ("lab1", 5, 2): "all",            # inject variance -> force DT refresh -> see the variance appear
    ("lab1", 5, 4): "all",            # clone -> count -> drop -> undrop -> count: five beats
    ("lab1", 7, 1): "all",            # clone the database, then prove it matches production
    ("lab1", 7, 2): [[1, 2], [3, 4], [5]],  # staging fallback; the rule change; read the rule set back
    # Lab 2
    ("lab2", 6, 2): "all",            # AI results, then SHOW DYNAMIC TABLES
    ("lab2", 7, 2): "all",            # CREATE triage view, then the triage summary
    ("lab2", 10, 1): [[1, 2, 3, 4], [5, 6]],  # drop everything, then verify it is gone
}

INTRO = {
    "setup": (
        "Run this once before the workshop. It builds the environment and generates the "
        "data both labs work on, which takes about 75 seconds on a SMALL warehouse.\n\n"
        "**Before you start**, set the notebook's role to `SYSADMIN` and pick any warehouse. "
        "Cell 1 creates `GSI_TAX_WH` and switches to it.\n\n"
        "Nothing here is throwaway. The four cells build the layered architecture the labs "
        "then use, so it is worth reading what each one creates and why."
    ),
    "lab1": (
        "Work through the cells top to bottom. Every SQL cell is ready to run - "
        "there is nothing to copy or paste.\n\n"
        "**Before you start**, run `gsi_tax_lab0_setup.ipynb` if you have not already. "
        "Set this notebook's role to `SYSADMIN` and the warehouse to `GSI_TAX_WH`. "
        "Step 1 verifies the foundation is present before you go any further."
    ),
    "lab2": (
        "This lab depends on the objects you built in Lab 1. Run the verification cell first - "
        "if anything is missing, go back and finish Lab 1.\n\n"
        "**Before you start**, you need the `SNOWFLAKE.CORTEX_USER` database role. "
        "Set the notebook role to `SYSADMIN` and the warehouse to `GSI_TAX_WH`."
    ),
    "reset": (
        "**Run only the section you need. Do not use Run All** - section 3 drops the entire "
        "workshop, and on a Run All it would fire straight after the two partial resets.\n\n"
        "The sections are ordered least to most destructive. Every statement uses `IF EXISTS`, so "
        "each one is safe to run twice and safe against a half-built environment.\n\n"
        "**Before you start**, set the notebook's role to `SYSADMIN` and the warehouse to "
        "`GSI_TAX_WH`. If the warehouse has already been dropped, pick any other warehouse."
    ),
}


def md_cell(name, source):
    return {
        "cell_type": "markdown",
        "id": name,
        "metadata": {"name": name, "collapsed": False},
        "source": source,
    }


def code_cell(name, lang, source):
    return {
        "cell_type": "code",
        "id": name,
        "execution_count": None,
        "metadata": {"name": name, "language": lang, "collapsed": False},
        "outputs": [],
        "source": source,
    }


def statements_for(lab, step, block_no, code):
    """Apply the split policy to one SQL block. Returns a list of cell sources."""
    stmts = nbutil.attach_leading_comments(nbutil.split_sql(code))
    if len(stmts) < 2:
        return [code]
    policy = SPLIT.get((lab, step, block_no))
    if policy is None:
        return [code]
    if policy == "all":
        groups = [[i] for i in range(1, len(stmts) + 1)]
    else:
        groups = policy
        flat = [i for g in groups for i in g]
        assert sorted(flat) == list(range(1, len(stmts) + 1)), (
            f"{lab} step{step} block{block_no}: policy covers {sorted(flat)} "
            f"but block has {len(stmts)} statements"
        )
    return [";\n\n".join(stmts[i - 1] for i in g) + ";" for g in groups]


def prep_python(code):
    """Adapt Streamlit-in-Snowflake app code so it also runs inside a notebook cell.

    Two rewrites, both one-directional:

    st.set_page_config() is required for a standalone SiS app but raises inside a
    notebook, so it is stripped.

    st.connection("snowflake") is the supported session pattern for a deployed
    app and does not work in a notebook cell, where get_active_session() is the
    only pattern available. The source file therefore holds the deployable form
    and the notebook form is generated here. Only blocks that actually use
    st.connection are rewritten - Lab 2 Step 8 carries its own app that already
    uses get_active_session and is left alone. Where the bootstrap IS present the
    rewrite must succeed, so rewording it in apps/*.py fails the build loudly
    rather than silently emitting a cell that cannot acquire a session.
    """
    stripped = re.sub(r"^st\.set_page_config\([^)]*\)\s*\n", "", code, flags=re.M)
    if "st.set_page_config" in stripped:
        raise SystemExit("prep_python: st.set_page_config survived the strip")

    note_deploy = ""
    if "st.connection(" in stripped:
        stripped, n = re.subn(
            r"^conn = st\.connection\([^\n]*\)\nsession = conn\.session\(\)$",
            "from snowflake.snowpark.context import get_active_session\n"
            "session = get_active_session()",
            stripped,
            flags=re.M,
        )
        if n != 1:
            raise SystemExit(
                "prep_python: could not find the st.connection bootstrap to rewrite "
                "for the notebook - check the session lines in apps/*.py"
            )
        note_deploy = (
            "# Deploy the real thing from GSI_TAX_WorkshopMaterial/streamlit_app/ -\n"
            "# open streamlit_app.py and Run. This cell is the same code adapted for a\n"
            "# notebook: st.set_page_config removed, session from get_active_session().\n"
        )

    note = (
        "# The control tower app. Running the cell here renders the dashboard inline,\n"
        "# but the theme assumes a full page, so the deployed app is the one to look at.\n"
    ) + note_deploy
    return note + stripped


def build(lab, mode="auto"):
    cfg = {k: (html.unescape(v) if isinstance(v, str) else v) for k, v in CFG[lab].items()}
    html_guide = cfg["out"]
    cells = [
        md_cell(
            "lab_header",
            f"# {cfg['hero_title']}\n\n"
            f"**{cfg['badge']}** \u00b7 {cfg['duration']} \u00b7 {cfg['difficulty']}\n\n"
            f"{cfg['hero_sub']}\n\n"
            f"{INTRO[lab]}\n\n"
            f"> Architecture, the business process behind it and how the notebooks fit "
            f"together: **`{html_guide}`**. You do not need it open to work through this "
            f"notebook - everything you need to run and interpret each step is here.\n\n"
            "---\n\n"
            "> \u26a0\ufe0f **Synthetic data**\n>\n"
            "> All data in this workshop is synthetically generated for training purposes. "
            "Entity names, ABNs, suppliers and transactions are fictitious. Tax treatments "
            "shown are simplified for illustration and are not tax advice.",
        )
    ]

    for step, (title, mins) in enumerate(cfg["build"], start=1):
        frag = BUILD / f"{lab}_step{step}.html"
        if not frag.exists():
            continue
        optional = " \u00b7 OPTIONAL" if step > cfg["core"] else ""
        cells.append(
            md_cell(
                f"step{step}_header",
                f"---\n\n## Step {step} of {len(cfg['build'])} \u2014 {title}\n\n"
                f"{step_orientation(lab, step, cfg)}\n\n"
                f"*~{mins}{optional}* \u00b7 "
                f"[architecture & background]({html_guide}#step-{step})",
            )
        )

        block_no = 0
        prose_no = 0
        frag_text = frag.read_text()
        # Decide the mode once per FRAGMENT, not per prose chunk. A fragment on
        # the beat contract is authored to length throughout, so condensing some
        # of its chunks and not others would read inconsistently.
        frag_mode = mode
        if mode == "auto":
            frag_mode = "full" if 'data-beat="' in frag_text else "tight"
        for kind, payload in nbutil.parse_fragment(frag_text):
            if kind == "prose":
                chunks = nbutil.html_to_md(payload, mode=frag_mode)
                if not chunks:
                    continue
                prose_no += 1
                cells.append(
                    md_cell(f"step{step}_note{prose_no}", "\n\n".join(chunks))
                )
            else:
                lang, code = payload
                block_no += 1
                sources = (
                    statements_for(lab, step, block_no, code)
                    if lang == "sql"
                    else [prep_python(code)]
                )
                for n, src in enumerate(sources):
                    suffix = chr(ord("a") + n) if len(sources) > 1 else ""
                    cells.append(
                        code_cell(f"step{step}_block{block_no}{suffix}", lang, src)
                    )

        if step in LEDGER_AT.get(lab, []):
            cells.append(md_cell(f"step{step}_ledger", ledger_md(lab, step)))

    for c in cells:
        c["source"] = [l + "\n" for l in c["source"].split("\n")[:-1]] + [
            c["source"].split("\n")[-1]
        ]

    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Streamlit Notebook",
                "name": "streamlit",
            },
            "language_info": {
                "name": "python",
                "pygments_lexer": "ipython3",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    out = DIST / NB_OUT[lab]
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n")

    n_md = sum(1 for c in cells if c["cell_type"] == "markdown")
    n_sql = sum(1 for c in cells if c["metadata"].get("language") == "sql")
    n_py = sum(1 for c in cells if c["metadata"].get("language") == "python")
    words = sum(
        len("".join(c["source"]).split()) for c in cells if c["cell_type"] == "markdown"
    )
    return out.name, len(cells), n_md, n_sql, n_py, words


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    mode = "full" if "--full" in sys.argv else "auto"
    arg = args[0] if args else "all"
    labs = ["setup", "lab1", "lab2"] if arg == "all" else [arg]
    for lab in labs:
        name, total, md, sql, py, words = build(lab, mode=mode)
        print(
            f"wrote {name}: {total} cells "
            f"({md} markdown / {sql} sql / {py} python), {words} words of prose [{mode}]"
        )
