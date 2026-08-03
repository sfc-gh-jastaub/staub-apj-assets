#!/usr/bin/env python3
"""
Assembler for the GSI Tax workshop labs.

Reuses the approved FSI workshop stylesheet and JS verbatim (835 lines CSS,
172 lines JS) so the visual treatment matches a lab the user has already
signed off. Step bodies are read from _build/*.html fragments so no full
lab HTML is ever held in memory by the agent.

Usage:  python3 _build/assemble.py lab1
"""
import re, sys, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
TEMPLATE = pathlib.Path.home() / "Documents/COCO/HOL/fsi_generic/fsi_workshop_lab1_foundation.html"

CFG = {
    "lab1": {
        "out": "gsi_tax_workshop_lab1_foundation.html",
        "title": "Lab 1 · Tax Data Foundation — GST Analytics on Snowflake",
        "badge": "Lab 1 of 2",
        "hero_title": "Tax Data Foundation: Raw to Return-Ready",
        "hero_sub": "Three incompatible ERP extracts, 2.4 million ledger lines, one governed GST position — and an audit trail you can reproduce on demand.",
        "duration": "60 min core + 28 min optional",
        "difficulty": "Beginner &rarr; Intermediate",
        "storage": "workshop_gsi_tax_lab1_progress",
        "core": 5,
        "footer_line": "GST Analytics &amp; AI on Snowflake for Global Solution Integrators &middot; Lab 1 of 2",
        "build": [
            ("Land the raw data and look around", "8 min"),
            ("Prove you cannot answer the question", "8 min"),
            ("Conform three ERPs into one governed ledger", "14 min"),
            ("The tax rules layer", "15 min"),
            ("Reconcile, then survive the audit", "15 min"),
            ("Streamlit tax control tower", "12 min"),
            ("The tax team sends you a rate change", "10 min"),
            ("Share the snapshot with the auditor", "6 min"),
        ],
        "whatyoubuild": [
            "Load three deliberately incompatible ERP extracts — 2,400,000 general ledger lines — with one paste-and-run script.",
            "Prove in three queries that the group GST position is currently unanswerable, and quantify exactly why.",
            "Conform all three systems into <code>CURATED.GL_HARMONISED</code>, a Dynamic Table that maintains itself and contains no tax logic.",
            "Build the tax rules layer as data the tax team owns: a decision table, effective-dated rates, and thin generic SQL that applies them.",
            "Reconcile the computed GST position against the lodged BAS and find the periods that do not tie.",
            "Reproduce the ledger exactly as it stood at lodgement using Time Travel, and take a zero-copy audit snapshot.",
        ],
        "tech": ["Snowflake SQL", "Dynamic Tables", "Time Travel", "Zero-Copy Cloning",
                 "Secure Data Sharing", "Streamlit in Snowflake"],
        "usecase": "An Australian group runs three general ledgers after a decade of acquisitions. The tax team rebuilds the group GST position in Excel every month, cannot reconcile it to what was lodged, and cannot reproduce a prior filing when the ATO asks. This lab fixes that end to end.",
    },
    "lab2": {
        "out": "gsi_tax_workshop_lab2_cortex_ai.html",
        "title": "Lab 2 · Cortex AI for Indirect Tax — GST Analytics on Snowflake",
        "badge": "Lab 2 of 2",
        "hero_title": "Cortex AI for Indirect Tax",
        "hero_sub": "Read the invoice narrative, catch the miscoding, draft the working paper, and answer the partner in plain English — all inside Snowflake.",
        "duration": "60 min core + 34 min optional + 2 min cleanup",
        "difficulty": "Intermediate",
        "storage": "workshop_gsi_tax_lab2_progress",
        "core": 5,
        "footer_line": "GST Analytics &amp; AI on Snowflake for Global Solution Integrators &middot; Lab 2 of 2",
        "build": [
            ("Verify your Lab 1 foundation", "3 min"),
            ("Classify the supply from the narrative", "15 min"),
            ("Extract structured fields from free text", "12 min"),
            ("Draft the working papers", "14 min"),
            ("Ask in plain English", "16 min"),
            ("Materialise AI output for cost control", "8 min"),
            ("Triage taxpayer correspondence", "8 min"),
            ("Add an AI review queue to the app", "10 min"),
            ("A second tool on the agent", "8 min"),
            ("Clean up", "2 min"),
        ],
        "whatyoubuild": [
            "Classify the supply type from an invoice narrative with <code>AI_CLASSIFY</code> and compare it to what was booked.",
            "Detect miscoding at scale and feed the findings into the same exception register the tax team already uses.",
            "Pull the supplier ABN and stated GST amount out of free text with <code>EXTRACT_ANSWER</code> and reconcile them to the ledger.",
            "Draft a plain-English working paper for every flagged exception with <code>AI_COMPLETE</code>, grounded in the rule that actually fired.",
            "Publish a semantic view and a Cortex Agent so a tax partner can ask questions without writing SQL.",
        ],
        "tech": ["Cortex AI_CLASSIFY", "EXTRACT_ANSWER", "AI_COMPLETE", "AI_SENTIMENT",
                 "Semantic Views", "Cortex Agents", "Streamlit in Snowflake"],
        "usecase": "The exception register from Lab 1 tells the tax team which lines to look at. It cannot tell them what the invoice actually said, whether the coding was right, or why the line was flagged. This lab closes that gap.",
    },
}


def nav_html(build):
    out = []
    core = None
    for i, (title, t) in enumerate(build, start=1):
        out.append(
            f'            <a class="step-nav-item" href="#step-{i}" data-step="{i}">\n'
            f'                <span class="nav-index">{i}</span>\n'
            f'                <span class="nav-text">{title}</span>\n'
            f'                <span class="nav-time">{t}</span>\n'
            f'            </a>'
        )
    return "\n".join(out)


def assemble(lab):
    cfg = CFG[lab]
    tpl = TEMPLATE.read_text()

    head = tpl.split("</style>", 1)[0] + "</style>"
    head = re.sub(r"<title>.*?</title>", f"<title>{cfg['title']}</title>", head, flags=re.S)

    header = tpl[tpl.find("<!-- ==================== HEADER"):tpl.find("<!-- ==================== HERO")]
    header = header.replace("AI-Powered Financial Analytics on Snowflake",
                            "GST Analytics &amp; AI on Snowflake")
    header = header.replace("Hands-On Workshop &middot; Lab 1 of 3",
                            f"Hands-On Workshop for Global Solution Integrators &middot; {cfg['badge']}")

    steps_html = []
    for i, (title, t) in enumerate(cfg["build"], start=1):
        frag = BUILD / f"{lab}_step{i}.html"
        if not frag.exists():
            body = f'<p><em>[fragment {frag.name} not yet generated]</em></p>'
        else:
            body = frag.read_text().strip()
        opt = " optional-step" if i > cfg["core"] else ""
        steps_html.append(
            f'<div class="step-card{opt}" id="step-{i}">\n'
            f'    <div class="step-header" onclick="toggleStep({i})">\n'
            f'        <span class="step-number">{i}</span>\n'
            f'        <h2 class="step-title">{title}</h2>\n'
            f'        <span class="step-duration">~{t}</span>\n'
            f'    </div>\n'
            f'    <div class="step-content">\n{body}\n'
            f'    <label class="completion-checkbox"><input type="checkbox" '
            f'onchange="markStepComplete({i})"> Mark step {i} complete</label>\n'
            f'    </div>\n'
            f'</div>'
        )

    li = "\n".join(f"                    <li>{x}</li>" for x in cfg["whatyoubuild"])
    tags = "\n".join(f'                    <span class="tech-tag">{x}</span>' for x in cfg["tech"])

    body = f"""
</head>
<body>

{header}<!-- ==================== HERO ==================== -->
<section class="hero-section">
    <div class="hero-container">
        <span class="hero-badge">{cfg['badge']}</span>
        <h1 class="hero-title">{cfg['hero_title']}</h1>
        <p class="hero-subtitle">{cfg['hero_sub']}</p>
        <div class="hero-meta">
            <div class="meta-item">
                <span class="meta-label">Duration</span>
                <span class="meta-value">{cfg['duration']}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Difficulty</span>
                <span class="meta-value">{cfg['difficulty']}</span>
            </div>
            <div class="meta-item">
                <span class="meta-label">Steps</span>
                <span class="meta-value">{cfg['core']} core + {len(cfg['build']) - cfg['core']} optional</span>
            </div>
        </div>
    </div>
</section>

<!-- ==================== BREADCRUMB ==================== -->
<div class="breadcrumb-bar">
    <div class="breadcrumb-inner">
        <a href="gsi_tax_workshop_index.html">&larr; Back to workshop index</a>
    </div>
</div>

<!-- ==================== OVERVIEW ==================== -->
<section id="overview" class="content-section alt-bg">
    <div class="section-container">
        <h2 class="section-title">Overview</h2>
        <div class="overview-grid">
            <div class="overview-card">
                <h3>What you will build</h3>
                <ul class="learning-list">
{li}
                </ul>
            </div>
            <div class="overview-card highlight">
                <h3>Technologies used</h3>
                <div class="tech-tags">
{tags}
                </div>
                <h3 style="margin-top:var(--space-xl);">Use case</h3>
                <p>{cfg['usecase']}</p>
            </div>
        </div>
    </div>
</section>

<!-- ==================== LAB BODY ==================== -->
<div class="lab-layout">

    <!-- ---------- Sidebar nav ---------- -->
    <nav class="sidebar-nav" aria-label="Lab steps">
        <div class="progress-header">
            <span class="progress-label">Core progress</span>
            <span class="progress-percent" id="progressPercent">0%</span>
        </div>
        <div class="progress-bar">
            <div class="progress-fill" id="progressFill"></div>
        </div>
        <div class="steps-nav" id="stepsNav">
{nav_html(cfg['build'])}
        </div>
    </nav>

    <!-- ---------- Steps ---------- -->
    <main class="steps-container" id="steps">

<div class="info-box warning">
    <span class="icon">&#9888;&#65039;</span>
    <div>
        <strong>Synthetic data</strong>
        <p>All data in this workshop is synthetically generated for training purposes. Entity names, ABNs, suppliers and transactions are fictitious. Tax treatments shown are simplified for illustration and are not tax advice.</p>
    </div>
</div>

{chr(10).join(steps_html)}

    </main>
</div>

<!-- ==================== FOOTER ==================== -->
<footer class="hol-footer">
    <p>{cfg['footer_line']}</p>
    <p>&copy; 2026 Snowflake Inc. All Rights Reserved.</p>
</footer>
"""

    js = re.search(r"<script>(.*?)</script>", tpl, re.S).group(1)
    js = js.replace("Lab 1 — interactivity", f"{cfg['badge']} — interactivity")
    js = js.replace("const totalSteps = 6;",
                    f"const totalSteps = {len(cfg['build'])};\nconst coreSteps  = {cfg['core']};")
    js = js.replace("'workshop_fsi_lab1_progress'", f"'{cfg['storage']}'")
    # progress bar reflects CORE steps only: finishing the 5 core steps shows 100%
    js = js.replace("""    const completed = countCompleted(state);
    const pct = Math.round((completed / totalSteps) * 100);""",
                    """    let coreDone = 0;
    for (let i = 1; i <= coreSteps; i++) { if (isDone(state, i)) { coreDone++; } }
    const pct = Math.round((coreDone / coreSteps) * 100);""")

    html = head + body + "\n<script>" + js + "</script>\n\n</body>\n</html>\n"
    (ROOT / cfg["out"]).write_text(html)
    return cfg["out"], html.count("\n"), html.count('class="code-block"')


if __name__ == "__main__":
    lab = sys.argv[1] if len(sys.argv) > 1 else "lab1"
    name, lines, blocks = assemble(lab)
    print(f"wrote {name}: {lines} lines, {blocks} code blocks")
