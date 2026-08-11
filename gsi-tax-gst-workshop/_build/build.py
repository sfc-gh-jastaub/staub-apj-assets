#!/usr/bin/env python3
"""
THE build command for the GSI Tax workshop. Run this and nothing else.

    python3 _build/build.py

Why this file exists
--------------------
The workshop has three generated artefacts and they must never disagree:

    sql/*.sql  ->  _build/lab1_step1.html  (the setup script is transcribed
                   into Lab 1 Step 1 Block 1, so the SQL files are the source
                   of truth for it)

    apps/*.py  ->  the python code block in its step fragment (the Streamlit
                   app is a real, runnable, syntax-checked file; the copy in
                   the guide and notebook is generated from it)

    _build/lab{N}_step{M}.html  ->  gsi_tax_workshop_lab{N}_*.html   (assemble.py)
                                ->  gsi_tax_lab{N}_*.ipynb           (assemble_nb.py)

Running one assembler and not the other silently ships a notebook that
disagrees with the guide. This script runs every stage in order and then
PROVES they agree: it re-extracts the SQL from both the finished HTML and the
finished notebook and fails if a single statement differs.

Edit fragments in _build/ and SQL in sql/. Never edit the generated
gsi_tax_*.html or gsi_tax_*.ipynb by hand - this script overwrites them.
"""
import html
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
DIST = ROOT / "GSI_TAX_WorkshopMaterial"
sys.path.insert(0, str(BUILD))

SETUP_SQL = ["01_setup_raw.sql", "02_setup_erp.sql", "03_setup_rules_bas_docs.sql"]

# Setup notebook step -> the SQL file that step runs. One file per step, so the
# setup notebook is a 1:1 view of sql/01..03 and a failure points at a stage.
# Step 4 is the verification query and is authored in setup_step4.html, since it
# is not part of any generator.
SETUP_STEP_SQL = {
    1: "01_setup_raw.sql",
    2: "02_setup_erp.sql",
    3: "03_setup_rules_bas_docs.sql",
}


# ---------------------------------------------------------------------------
# Stage 1 - sql/*.sql  ->  setup notebook step fragments
# ---------------------------------------------------------------------------
def sync_setup_block():
    """Rebuild each setup fragment's code block from its SQL file.

    The fragment owns the prose; the SQL file owns the code. Everything between
    <pre><code> and </code></pre> is replaced wholesale, so the SQL files stay the
    single source of truth for the generated data and the seeds cannot drift out
    of the notebook.
    """
    changed = []
    for step, name in SETUP_STEP_SQL.items():
        frag_path = BUILD / f"setup_step{step}.html"
        frag = frag_path.read_text()
        text = (ROOT / "sql" / name).read_text()
        # drop the "-- NOTE: every RANDOM() ..." maintainer preamble
        if "NOTE: every RANDOM" in text[:400]:
            text = re.sub(r"\A(?:--[^\n]*\n)+\n?", "", text)
        body = text.strip()

        blocks = re.findall(r"<pre><code>(.*?)</code></pre>", frag, re.S)
        if not blocks:
            raise SystemExit(f"setup_step{step}.html has no code block to populate")
        esc = body.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if esc == blocks[0]:
            continue
        frag_path.write_text(frag.replace(blocks[0], esc, 1))
        changed.append(f"setup_step{step} <- sql/{name}")
    return changed


# ---------------------------------------------------------------------------
# Stage 1a - apps/*.py  ->  the python code block in a step fragment
#
# The Streamlit app is a real file so it can be syntax-checked, run locally
# against the account and PUT to a stage. Keeping a second hand-maintained copy
# inside the fragment guarantees the two drift, and the copy in the guide is the
# one a participant pastes. So the file is the source of truth and the fragment
# block is generated, exactly as sql/*.sql feeds the setup fragments.
# ---------------------------------------------------------------------------
APP_BLOCK = {"lab1_step6.html": "apps/gst_control_tower.py"}

PY_BLOCK_RE = re.compile(
    r'(<span class="code-lang">python</span>.*?<pre><code>)(.*?)(</code></pre>)', re.S)


def sync_app_block():
    changed = []
    for frag_name, app_rel in APP_BLOCK.items():
        frag_path = BUILD / frag_name
        app_path = ROOT / app_rel
        frag = frag_path.read_text()
        m = PY_BLOCK_RE.search(frag)
        if not m:
            raise SystemExit(f"{frag_name} has no python code block to populate")
        esc = (app_path.read_text().strip()
               .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        if esc == m.group(2):
            continue
        frag_path.write_text(frag[:m.start(2)] + esc + frag[m.end(2):])
        changed.append(f"{frag_name} <- {app_rel}")
    return changed


def publish_app_files():
    """Copy each app into the attendee folder so the .py is there to open.

    The file under apps/ stays the single source of truth: it feeds the fragment
    in sync_app_block and it is what gets compile-checked. This is a generated
    copy, which is why it is never edited in place.
    """
    published = []
    for app_rel in APP_BLOCK.values():
        src = ROOT / app_rel
        dst = DIST / pathlib.Path(app_rel).name
        if not dst.exists() or dst.read_text() != src.read_text():
            dst.write_text(src.read_text())
            published.append(dst.name)
    return published


def check_apps_compile():
    """Compile every app file. A syntax error here reaches the room as a dead app."""
    import py_compile
    import tempfile
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        for app_rel in APP_BLOCK.values():
            try:
                py_compile.compile(str(ROOT / app_rel), doraise=True,
                                   cfile=str(pathlib.Path(tmp) / "a.pyc"))
            except py_compile.PyCompileError as e:
                problems.append(f"{app_rel}: {e.msg.strip().splitlines()[-1]}")
    return problems


# ---------------------------------------------------------------------------
# Stage 1b - fragments -> sql/06_lab2_ai_objects.sql
# ---------------------------------------------------------------------------
LAB2_HEADER = """-- ============================================================================
-- GENERATED FILE - DO NOT EDIT.
-- Produced by _build/build.py from the Lab 2 step fragments.
-- These are the AI_INSIGHTS / AGENTS objects a participant creates by working
-- through Lab 2. This file exists so a facilitator can stand the whole stack up
-- non-interactively, and so sql/07_agent.sql has its semantic view to point at.
--
-- Full rebuild order:
--   01_setup_raw  02_setup_erp  03_setup_rules_bas_docs
--   04_curated_tax  05_exceptions  06_lab2_ai_objects  07_agent
-- ============================================================================
USE ROLE ACCOUNTADMIN;
USE WAREHOUSE GSI_TAX_WH;
USE DATABASE GSI_TAX_WORKSHOP;

"""


def emit_lab2_objects():
    """Extract every CREATE ... statement from the Lab 2 fragments, in step order."""
    import assemble
    out = [LAB2_HEADER]
    n = 0
    for step in range(1, len(assemble.CFG["lab2"]["build"]) + 1):
        frag = BUILD / f"lab2_step{step}.html"
        if not frag.exists():
            continue
        for lang, code in [
            (m[0], html.unescape(m[1]))
            for m in re.findall(
                r'<span class="code-lang">(\w+)</span>.*?<pre><code>(.*?)</code></pre>',
                frag.read_text(), re.S)
        ]:
            if lang != "sql":
                continue
            for stmt in [x.strip() for x in re.split(r";\s*\n", code) if x.strip()]:
                if re.match(r"\s*(--[^\n]*\n\s*)*CREATE", stmt, re.I):
                    out.append(f"-- Lab 2 Step {step}\n{stmt.rstrip(';')};\n")
                    n += 1
    (ROOT / "sql" / "06_lab2_ai_objects.sql").write_text("\n".join(out))
    return n


# ---------------------------------------------------------------------------
# Stage 4 - prove the artefacts agree
# ---------------------------------------------------------------------------
def norm(sql):
    """Normalise SQL so formatting differences do not register as drift."""
    s = re.sub(r"--[^\n]*", " ", sql)          # strip line comments
    s = re.sub(r"/\*.*?\*/", " ", s, flags=re.S)
    s = re.sub(r"\s+", " ", s)
    s = s.replace(" ;", ";").strip().rstrip(";")
    return s.upper()


def html_sql_by_step(path, n_steps):
    doc = path.read_text()
    out = {}
    for i in range(1, n_steps + 1):
        m = re.search(
            r'id="step-%d">(.*?)(?=<div class="step-card|</main>)' % i, doc, re.S
        )
        seg = m.group(1) if m else ""
        sql = []
        for blk in re.findall(
            r'<span class="code-lang">(\w+)</span>.*?<pre><code>(.*?)</code></pre>',
            seg,
            re.S,
        ):
            if blk[0] == "sql":
                sql.append(html.unescape(blk[1]))
        out[i] = sql
    return out


def nb_sql_by_step(path):
    nb = json.loads(path.read_text())
    out = {}
    for c in nb["cells"]:
        if c["cell_type"] != "code" or c["metadata"].get("language") != "sql":
            continue
        m = re.match(r"step(\d+)_block", c["metadata"].get("name", ""))
        if not m:
            continue
        out.setdefault(int(m.group(1)), []).append("".join(c["source"]))
    return out


def check_parity(lab, cfg):
    h = html_sql_by_step(DIST / cfg["out"], len(cfg["build"]))
    nbmap = {"lab1": "gsi_tax_lab1_foundation.ipynb", "lab2": "gsi_tax_lab2_cortex_ai.ipynb"}
    n = nb_sql_by_step(DIST / nbmap[lab])
    problems = []
    for step in sorted(h):
        a = norm(" ".join(h[step]))
        b = norm(" ".join(n.get(step, [])))
        if a != b:
            # locate the divergence for a useful message
            i = next((k for k in range(min(len(a), len(b))) if a[k] != b[k]), min(len(a), len(b)))
            problems.append(
                f"  step {step}: SQL differs at char {i}\n"
                f"    guide:    ...{a[max(0,i-60):i+60]}...\n"
                f"    notebook: ...{b[max(0,i-60):i+60]}..."
            )
    return problems


def check_staleness():
    """Fail if any generated artefact is older than a source it derives from."""
    srcs = list((ROOT / "sql").glob("*.sql")) + list(BUILD.glob("lab*_step*.html")) \
        + list((ROOT / "apps").glob("*.py")) \
        + [BUILD / "assemble.py", BUILD / "assemble_nb.py"]
    newest = max(p.stat().st_mtime for p in srcs)
    stale = []
    for out in ["gsi_tax_workshop_lab1_foundation.html", "gsi_tax_workshop_lab2_cortex_ai.html",
                "gsi_tax_lab1_foundation.ipynb", "gsi_tax_lab2_cortex_ai.ipynb"]:
        p = DIST / out
        if not p.exists() or p.stat().st_mtime < newest - 1:
            stale.append(out)
    return stale


# ---------------------------------------------------------------------------
# Stage 5 - regression guard on superseded figures
#
# The labs quote exact measured figures. When the dataset is re-measured, every
# artefact must be swept. These are the values that have ALREADY been retired -
# if one reappears, a fragment was edited from a stale source.
#
# Matching is boundary-aware on purpose: an unanchored search for "10.76" also
# hits "110.767652" inside the Snowflake logo's SVG path data, and blindly
# replacing that corrupts the logo.
# ---------------------------------------------------------------------------
RETIRED = [
    "258,145", "25,539,866", "175,942,290", "108,191", "12,313", "30,573",
    "36,500", "64,781", "77,737", "95,785", "8,074", "4,858", "2,521",
    "2,814", "2,803", "2,457", "10.76%", "96.76%", "3.24%", "1.27%", "5.45%",
    # Retired when the Lab 1 Step 2 window was pinned to the dataset as-of date.
    # These two were measured against a CURRENT_DATE() window and never matched
    # the pinned data - the only wrong figures the validation sweep found.
    "96,025", "176,904,538",
    # Word-form figures derived from the retired 25,539,866 base. The digit-form
    # guard missed these because the prose spelled them out in millions, so a
    # figure sweep that only greps exact digit strings is not sufficient.
    "$25.5 million", "$38.3 million",
]

ARTEFACTS = [
    "gsi_tax_workshop_index.html",
    "gsi_tax_workshop_lab1_foundation.html",
    "gsi_tax_workshop_lab2_cortex_ai.html",
    "gsi_tax_lab1_foundation.ipynb",
    "gsi_tax_lab2_cortex_ai.ipynb",
]


def find_retired():
    hits = []
    for name in ARTEFACTS:
        path = DIST / name
        if not path.exists():
            continue
        text = path.read_text()
        for fig in RETIRED:
            for m in re.finditer(re.escape(fig), text):
                before = text[m.start() - 1] if m.start() else " "
                after = text[m.end()] if m.end() < len(text) else " "
                if before.isdigit() or before == ".":
                    continue          # inside a longer number (SVG coords, CSS)
                if after not in '%<" ,)\n' and not fig.endswith("%"):
                    continue
                hits.append(f"{name}: retired figure {fig}")
    return hits


# ---------------------------------------------------------------------------
# Stage 5b - packages the Streamlit warehouse runtime does not have
#
# These pandas Styler methods import matplotlib lazily and raise at RENDER time,
# not at import time, so a py_compile check passes and the app dies in front of
# the room. matplotlib is not in the Streamlit in Snowflake warehouse runtime.
# Found the hard way: "ImportError: background_gradient requires matplotlib".
# ---------------------------------------------------------------------------
UNAVAILABLE = [
    ("background_gradient", "needs matplotlib - shade with .apply() instead"),
    ("text_gradient", "needs matplotlib - set colour in .apply() instead"),
    ("style.bar(", "needs matplotlib - use st.column_config.ProgressColumn"),
    ("import matplotlib", "matplotlib is not in the warehouse runtime"),
    ("import seaborn", "seaborn is not in the warehouse runtime"),
]


def check_python_runtime():
    """Fail on APIs that compile fine and then raise inside Streamlit.

    Comments are stripped first: the app code carries a comment explaining why
    background_gradient is avoided, and a guard that trips on its own
    documentation is worse than no guard.
    """
    problems = []
    for frag in sorted(BUILD.glob("lab*_step*.html")):
        text = frag.read_text()
        for lang, code in re.findall(
            r'<span class="code-lang">(\w+)</span>.*?<pre><code>(.*?)</code></pre>',
            text, re.S,
        ):
            if lang != "python":
                continue
            body = html.unescape(code)
            body = "\n".join(re.sub(r"#.*$", "", ln) for ln in body.split("\n"))
            for bad, why in UNAVAILABLE:
                if bad in body:
                    problems.append(f"{frag.name}: '{bad}' {why}")
    return problems


def main():
    print("stage 1  sql/*.sql -> setup notebook fragments")
    changed = sync_setup_block()
    for line in changed:
        print("         " + line)
    if not changed:
        print("         already current")

    print("stage 1a apps/*.py -> step fragment python blocks")
    app_changed = sync_app_block()
    for line in app_changed:
        print("         " + line)
    if not app_changed:
        print("         already current")

    print("stage 1c apps/*.py -> GSI_TAX_WorkshopMaterial/")
    published = publish_app_files()
    for name in published:
        print("         " + name)
    if not published:
        print("         already current")

    import assemble
    import importlib
    importlib.reload(assemble)

    print("stage 1b fragments -> sql/06_lab2_ai_objects.sql")
    print(f"         {emit_lab2_objects()} CREATE statements extracted from Lab 2")

    print("stage 2  fragments -> HTML guides")
    for lab in ("lab1", "lab2"):
        name, lines, blocks = assemble.assemble(lab)
        print(f"         {name}: {lines} lines, {blocks} code blocks")

    print("stage 3  fragments -> notebooks")
    import assemble_nb
    importlib.reload(assemble_nb)
    for lab in ("setup", "lab1", "lab2", "reset"):
        name, total, md, sql, py, words = assemble_nb.build(lab)
        print(f"         {name}: {total} cells ({md} md / {sql} sql / {py} py), {words} words")

    print("stage 4  parity + integrity")
    failures = []
    for lab in ("lab1", "lab2"):
        p = check_parity(lab, assemble.CFG[lab])
        if p:
            failures.append(f"{lab} SQL parity FAILED:\n" + "\n".join(p))
        else:
            print(f"         {lab}: guide and notebook SQL identical")

    # per-step block budgets and escaping, on the finished HTML
    for lab in ("lab1", "lab2"):
        cfg = assemble.CFG[lab]
        doc = (DIST / cfg["out"]).read_text()
        per = []
        for i in range(1, len(cfg["build"]) + 1):
            m = re.search(r'id="step-%d">(.*?)(?=<div class="step-card|</main>)' % i, doc, re.S)
            per.append((m.group(1) if m else "").count('class="code-block"'))
        core = sum(per[: cfg["core"]])
        bad_esc = sum(
            1
            for c in re.findall(r"<pre><code>(.*?)</code></pre>", doc, re.S)
            if re.search(r"<(?!/?(code|pre)\b)", c)
        )
        print(f"         {lab}: blocks {per} core={core} unescaped={bad_esc}")
        if bad_esc:
            failures.append(f"{lab}: {bad_esc} code blocks contain a raw '<'")
        for banned, label in [
            ("volatility", "banned phrase 'volatility'"),
            ("DT_GST_EXCEPTIONS", "stale object DT_GST_EXCEPTIONS"),
            ("Singapore", "non-Australian jurisdiction"),
            ("New Zealand", "non-Australian jurisdiction"),
            ("SNOWFLAKE.CORTEX.COMPLETE(", "banned Cortex function"),
            ("SNOWFLAKE.CORTEX.SENTIMENT(", "banned Cortex function"),
        ]:
            if banned in doc:
                failures.append(f"{lab}: {label} ({banned})")

    retired = find_retired()
    if retired:
        failures.extend(sorted(set(retired)))
    else:
        print("         no retired figures present in any artefact")

    runtime = check_python_runtime()
    if runtime:
        failures.extend(runtime)
    else:
        print("         app code uses no package missing from the warehouse runtime")

    bad_py = check_apps_compile()
    if bad_py:
        failures.extend(bad_py)
    else:
        print(f"         {len(APP_BLOCK)} app file(s) compile")

    stale = check_staleness()
    if stale:
        failures.append("generated files older than their sources: " + ", ".join(stale))

    print()
    if failures:
        print("BUILD FAILED")
        for f in failures:
            print(" - " + f)
        sys.exit(1)
    print("BUILD OK - guide, notebook and SQL all agree")


if __name__ == "__main__":
    main()
