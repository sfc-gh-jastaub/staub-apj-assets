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

NB_OUT = {"lab1": "gsi_tax_lab1_foundation.ipynb", "lab2": "gsi_tax_lab2_cortex_ai.ipynb"}

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
    "lab1": (
        "Work through the cells top to bottom. Every SQL cell is ready to run - "
        "there is nothing to copy or paste.\n\n"
        "**Before you start**, set the notebook's role to `SYSADMIN` and pick any warehouse. "
        "Cell 1 creates `GSI_TAX_WH` and switches to it."
    ),
    "lab2": (
        "This lab depends on the objects you built in Lab 1. Run the verification cell first - "
        "if anything is missing, go back and finish Lab 1.\n\n"
        "**Before you start**, you need the `SNOWFLAKE.CORTEX_USER` database role. "
        "Set the notebook role to `SYSADMIN` and the warehouse to `GSI_TAX_WH`."
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

    st.set_page_config() is required for a standalone SiS app but raises inside a
    notebook, so it is stripped here. The HTML guide keeps the canonical app code
    for anyone deploying it to Projects -> Streamlit.
    """
    stripped = re.sub(r"^st\.set_page_config\([^)]*\)\s*\n", "", code, flags=re.M)
    note = (
        "# Streamlit app code. Run this cell to preview the app inline, or paste it\n"
        "# into Projects -> Streamlit to deploy it standalone (add st.set_page_config\n"
        "# back at the top when you do).\n"
    )
    return note + stripped


def build(lab, mode="tight"):
    cfg = {k: (html.unescape(v) if isinstance(v, str) else v) for k, v in CFG[lab].items()}
    html_guide = cfg["out"]
    cells = [
        md_cell(
            "lab_header",
            f"# {cfg['hero_title']}\n\n"
            f"**{cfg['badge']}** \u00b7 {cfg['duration']} \u00b7 {cfg['difficulty']}\n\n"
            f"{cfg['hero_sub']}\n\n"
            f"{INTRO[lab]}\n\n"
            f"> Full narrative, expected results and architecture notes: **`{html_guide}`** "
            f"— keep it open alongside this notebook.\n\n"
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
                f"---\n\n## Step {step} \u2014 {title}\n\n"
                f"*~{mins}{optional}* \u00b7 "
                f"[narrative & expected results]({html_guide}#step-{step})",
            )
        )

        block_no = 0
        prose_no = 0
        for kind, payload in nbutil.parse_fragment(frag.read_text()):
            if kind == "prose":
                chunks = nbutil.html_to_md(payload, mode=mode)
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
    out = ROOT / NB_OUT[lab]
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
    mode = "full" if "--full" in sys.argv else "tight"
    arg = args[0] if args else "all"
    labs = ["lab1", "lab2"] if arg == "all" else [arg]
    for lab in labs:
        name, total, md, sql, py, words = build(lab, mode=mode)
        print(
            f"wrote {name}: {total} cells "
            f"({md} markdown / {sql} sql / {py} python), {words} words of prose [{mode}]"
        )
