import streamlit as st
import bisect
import html

import pandas as pd
from datetime import datetime, timezone
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Brindabella Group · GST Control Tower", layout="wide")

session = get_active_session()

# =====================================================================
# THEME
#
# One dark theme, defined once, applied with injected CSS so the whole
# app stays a SINGLE file - no .streamlit/config.toml to copy alongside it.
#
# Because the background is forced dark, every foreground colour is set
# explicitly too. Streamlit's own widgets default to the light theme's dark
# text, which would be invisible here, so widget labels, inputs and dropdowns
# are all given an explicit light colour below.
# =====================================================================
BG      = "#0B1220"   # page
PANEL   = "#111C2E"   # cards
EDGE    = "#1E2D45"   # borders
INK     = "#E6EDF6"   # primary text
MUTED   = "#8A9BB0"   # secondary text
BLUE    = "#29B5E8"   # Snowflake accent
RED     = "#F76B7C"   # investigate / high
AMBER   = "#E8B23A"   # review / medium
GREEN   = "#4ED8A0"   # matched / clean

CSS = """
<style>
:root {
  --bg:#0B1220; --panel:#111C2E; --edge:#1E2D45;
  --ink:#E6EDF6; --muted:#8A9BB0;
  --blue:#29B5E8; --red:#F76B7C; --amber:#E8B23A; --green:#4ED8A0;
}
/* page + base text -------------------------------------------------- */
.stApp, [data-testid="stAppViewContainer"] { background: var(--bg); }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding: 1.1rem 1.4rem 3rem; max-width: 1500px; }
.stApp, .stApp p, .stApp span, .stApp div, .stApp label {
  color: var(--ink);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
/* every Streamlit widget label, explicitly light ---------------------- */
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p,
.stSlider label, .stSelectbox label, .stTextInput label, .stMultiSelect label {
  color: var(--muted) !important;
  font-size: .68rem !important; font-weight: 700 !important;
  letter-spacing: .09em !important; text-transform: uppercase !important;
}
/* Inputs: dark field, light text.
   Streamlit changed its widget internals: older builds (which is what the
   Snowflake warehouse runtime ships) render selects with BaseWeb and expose
   data-baseweb="select"; newer builds use react-aria and expose neither. We
   target both, plus the stable data-testid wrappers, so the dashboard stays
   dark whichever build it lands on. The wrapper is what carries the default
   light fill, so styling only the <input> leaves a white box around it. */
.stTextInput input, .stNumberInput input,
[data-testid="stTextInputRootElement"],
[data-testid="stTextInputRootElement"] > div {
  background: #0D1728 !important;
  color: var(--ink) !important;
  -webkit-text-fill-color: var(--ink) !important;
  border-color: var(--edge) !important;
  border-radius: 8px !important;
}
.stTextInput input::placeholder { color: #5E7189 !important; opacity: 1 !important; }
/* select shell: BaseWeb (older) and react-aria (newer) */
[data-baseweb="select"] > div,
[data-testid="stSelectbox"] [role="group"],
[data-testid="stMultiSelect"] [role="group"],
.react-aria-ComboBox [role="group"] {
  background: #0D1728 !important; border-color: var(--edge) !important;
  color: var(--ink) !important; border-radius: 8px !important;
}
[data-baseweb="select"] div, [data-baseweb="select"] span,
[data-testid="stSelectbox"] input, [data-testid="stMultiSelect"] input,
[data-testid="stSelectbox"] [role="combobox"] {
  color: var(--ink) !important; -webkit-text-fill-color: var(--ink) !important;
  background: transparent !important;
}
/* dropdown panel */
[data-baseweb="popover"], [data-baseweb="menu"], [role="listbox"],
.react-aria-Popover, .react-aria-ListBox {
  background: #0D1728 !important; border: 1px solid var(--edge) !important;
}
[role="option"], .react-aria-ListBoxItem {
  background: #0D1728 !important; color: var(--ink) !important;
}
[role="option"]:hover, .react-aria-ListBoxItem[data-focused] { background: #16243A !important; }
[data-baseweb="tag"] { background: #16243A !important; color: var(--ink) !important; }
/* slider ------------------------------------------------------------- */
.stSlider [data-baseweb="slider"] div[role="slider"],
.stSlider [role="slider"] { background: var(--blue) !important; }
.stSlider [data-testid="stTickBar"], .stSlider [data-testid="stTickBarMin"],
.stSlider [data-testid="stTickBarMax"] { color: var(--muted) !important; background: transparent !important; }
/* kill Streamlit chrome we are replacing ----------------------------- */
[data-testid="stToolbar"], footer, #MainMenu { visibility: hidden; }
hr { border-color: var(--edge); }

/* ---------------- our own components ------------------------------- */
.topbar {
  display:flex; align-items:center; gap:14px;
  background:linear-gradient(135deg,#12243C 0%,#0E1A2C 55%,#141B33 100%);
  border:1px solid var(--edge); border-radius:14px; padding:14px 18px; margin-bottom:14px;
}
.logo {
  width:38px;height:38px;border-radius:10px;flex:0 0 38px;
  background:linear-gradient(135deg,var(--blue),#1273A8);
  display:flex;align-items:center;justify-content:center;font-size:19px;
}
.t-title { font-size:1.28rem; font-weight:800; letter-spacing:-.02em; line-height:1.15; }
.t-meta  { font-size:.76rem; color:var(--muted); margin-top:3px; }
.dot { height:7px;width:7px;border-radius:50%;display:inline-block;margin-right:5px;
       background:var(--green); box-shadow:0 0 0 3px rgba(78,216,160,.16); }

.kpis { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:14px; }
.kpi { background:var(--panel); border:1px solid var(--edge); border-radius:14px;
       padding:15px 17px 13px; position:relative; overflow:hidden; }
.kpi-l { font-size:.65rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); }
.kpi-v { font-size:2.15rem; font-weight:800; letter-spacing:-.03em; line-height:1.12; margin:5px 0 2px; }
.kpi-s { font-size:.74rem; color:var(--muted); min-height:2.5em; }
.kpi-track { position:absolute; left:17px; right:17px; bottom:9px; height:3px;
             background:#1B2942; border-radius:3px; overflow:hidden; }
.kpi-fill { height:100%; border-radius:3px; animation:grow 1.05s cubic-bezier(.22,1,.36,1) both; }
@keyframes grow { from { width:0 } }

.card { background:var(--panel); border:1px solid var(--edge); border-radius:14px;
        padding:15px 17px 17px; height:100%; }
.card-h { display:flex; justify-content:space-between; align-items:baseline; gap:14px; margin-bottom:14px; }
.card-t { font-size:.95rem; font-weight:700; white-space:nowrap; }
.card-n { font-size:.71rem; color:var(--muted); text-align:right; }

.brow { margin-bottom:13px; }
.brow-top { display:flex; justify-content:space-between; align-items:baseline; font-size:.82rem; }
.brow-track { height:8px; background:#1B2942; border-radius:5px; margin-top:6px; overflow:hidden; }
.brow-fill { height:100%; border-radius:5px; animation:grow 1.15s cubic-bezier(.22,1,.36,1) both; }

table.tt { width:100%; border-collapse:collapse; font-size:.79rem; }
table.tt th { text-align:left; font-size:.63rem; letter-spacing:.09em; text-transform:uppercase;
              color:var(--muted); font-weight:700; padding:0 9px 8px; border-bottom:1px solid var(--edge); }
table.tt td { padding:8px 9px; border-bottom:1px solid #16223A; color:var(--ink); }
table.tt tr:hover td { background:#16243A; }
.num { font-variant-numeric:tabular-nums; text-align:right;
       font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }
.pill { display:inline-block; padding:2px 9px; border-radius:999px;
        font-size:.66rem; font-weight:700; letter-spacing:.03em; }

.hm { display:grid; gap:2px; }
.hm-c { height:19px; border-radius:3px; }
.hm-c:hover { outline:1.5px solid var(--ink); z-index:6; }

/* Instant hover tooltip, shared by the heatmap cells and the histogram buckets.
   The browser's native title attribute waits about a second and renders in OS
   chrome, so in a room people conclude hover is broken before it ever appears. */
[data-tip] { position:relative; }
[data-tip]:hover::after {
  content:attr(data-tip); position:absolute; bottom:calc(100% + 7px); left:50%;
  transform:translateX(-50%); background:#050A14; color:var(--ink);
  border:1px solid var(--edge); padding:6px 10px; border-radius:6px;
  font-size:.7rem; white-space:nowrap; z-index:30; pointer-events:none;
  box-shadow:0 8px 22px rgba(0,0,0,.6);
}
/* Clamp the first and last columns. A centred tooltip on the final period runs
   past the viewport, and Streamlit's app container is overflow:hidden, so it
   would be cut in half rather than just overhanging. */
[data-tip].tip-r:hover::after { left:0; transform:none; }
[data-tip].tip-l:hover::after { left:auto; right:0; transform:none; }

/* Transparent hit targets laid over the histogram, one per bucket, so the bars
   get the same instant tooltip as the heatmap without rewriting the SVG. */
.hx { position:relative; }
.hx-c { position:absolute; top:0; border-radius:4px; }
.hx-c:hover { background:rgba(230,237,246,.06); }
.hm-lbl { font-size:.7rem; color:var(--muted); padding-right:9px; text-align:right;
          white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# =====================================================================
# DATA
# Every query aggregates or bounds its result. Nothing returns a row per
# ledger line: the register is 253,394 rows and the browser does not want them.
# =====================================================================
@st.cache_data(ttl=600)
def recon_summary():
    return session.sql("""
        SELECT RECON_STATUS, COUNT(*) AS N, ROUND(SUM(ABS(VARIANCE_NET)),2) AS ABS_VAR
        FROM TAX.V_GST_VS_BAS GROUP BY 1
    """).to_pandas()


@st.cache_data(ttl=600)
def ledger_scale():
    """Header and KPI figures, read live rather than hardcoded.

    Lab 1 posts a correcting entry, which moves the ledger count off the round
    2,400,000 and shifts one entity-period out of MATCHED. A hardcoded number
    would quietly start lying the moment a participant runs that step.
    """
    return session.sql("""
        SELECT (SELECT COUNT(*) FROM CURATED.GL_HARMONISED) AS LINES,
               COUNT(DISTINCT ENTITY_ID)                    AS ENTITIES,
               COUNT(DISTINCT TAX_PERIOD)                   AS PERIODS
        FROM TAX.V_GST_VS_BAS
    """).to_pandas().iloc[0]


@st.cache_data(ttl=600)
def exception_summary():
    return session.sql("""
        SELECT COUNT(*) AS FLAGGED, SUM(IFF(MAX_SEVERITY='HIGH',1,0)) AS HIGH,
               ROUND(AVG(RISK_SCORE),2) AS AVG_RISK
        FROM TAX.V_GST_EXCEPTIONS
    """).to_pandas().iloc[0]


@st.cache_data(ttl=600)
def score_histogram():
    return session.sql("""
        SELECT FLOOR(RISK_SCORE/10)*10 AS BUCKET, MAX_SEVERITY, COUNT(*) AS N
        FROM TAX.V_GST_EXCEPTIONS GROUP BY 1,2 ORDER BY 1
    """).to_pandas()


@st.cache_data(ttl=600)
def entities():
    return session.sql(
        "SELECT DISTINCT ENTITY_NAME FROM TAX.V_GST_EXCEPTIONS ORDER BY 1"
    ).to_pandas()["ENTITY_NAME"].tolist()


@st.cache_data(ttl=600)
def severities():
    """Severity levels that actually occur, ordered high to low.

    Hardcoding HIGH/MEDIUM/LOW offered a LOW filter that returns an empty table,
    because the rule set only ever lands on MEDIUM or HIGH. A dead filter option
    reads as a broken app. Reading the levels from the data means the control
    always matches reality, and a LOW option appears by itself if the rules ever
    start producing one.
    """
    have = session.sql(
        "SELECT DISTINCT MAX_SEVERITY FROM TAX.V_GST_EXCEPTIONS"
    ).to_pandas()["MAX_SEVERITY"].tolist()
    return [s for s in ("HIGH", "MEDIUM", "LOW") if s in have]


@st.cache_data(ttl=600)
def heatmap():
    return session.sql("""
        SELECT ENTITY_NAME, TO_VARCHAR(TAX_PERIOD,'YYYY-MM') AS P, COUNT(*) AS N
        FROM TAX.V_GST_EXCEPTIONS WHERE TAX_PERIOD IS NOT NULL
        GROUP BY 1,2 ORDER BY 1,2
    """).to_pandas()


@st.cache_data(ttl=600)
def worklist(min_score, sev, entity, search, limit):
    where = [f"RISK_SCORE >= {int(min_score)}"]
    if sev != "All":
        where.append(f"MAX_SEVERITY = '{sev}'")
    if entity != "All entities":
        where.append(f"ENTITY_NAME = '{entity}'")
    if search:
        safe = search.replace("'", "''").upper()
        where.append(f"(UPPER(SUPPLIER_NAME) LIKE '%{safe}%' OR UPPER(GL_LINE_ID) LIKE '%{safe}%')")
    clause = "WHERE " + " AND ".join(where)
    return session.sql(f"""
        SELECT GL_LINE_ID, ENTITY_NAME, SUPPLIER_NAME, SUPPLY_CATEGORY,
               TAX_TREATMENT, APPLIED_RULE_ID, TAX_VARIANCE, EXCEPTION_CODES,
               MAX_SEVERITY, RISK_SCORE
        FROM TAX.V_GST_EXCEPTIONS {clause}
        ORDER BY RISK_SCORE DESC, ABS(TAX_VARIANCE) DESC
        LIMIT {int(limit)}
    """).to_pandas(), clause


@st.cache_data(ttl=600)
def filtered_totals(clause):
    return session.sql(f"""
        SELECT COUNT(*) AS N, ROUND(SUM(ABS(COALESCE(TAX_VARIANCE,0))),2) AS ABS_VAR
        FROM TAX.V_GST_EXCEPTIONS {clause}
    """).to_pandas().iloc[0]


def txt(v):
    """NULL-safe cell text for the hand-rolled table.

    Snowflake NULLs arrive as float nan through to_pandas(), and dropping one
    straight into an f-string renders the literal string 'nan'. Unmapped GL
    accounts genuinely have no supply category, so this is the common case
    rather than an edge one. Values are escaped because they land in raw HTML.
    """
    if v is None or pd.isna(v):
        return "<span style='opacity:.5'>&mdash;</span>"
    return html.escape(str(v))


def money(v):
    v = float(v or 0)
    for cut, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if abs(v) >= cut:
            return f"${v / cut:,.1f}{suf}"
    return f"${v:,.0f}"


# =====================================================================
# HEADER
# =====================================================================
rs = recon_summary()
sc = ledger_scale()
ex = exception_summary()
total_periods = int(rs["N"].sum())
investigate = int(rs.loc[rs.RECON_STATUS == "INVESTIGATE", "N"].sum())
abs_var = float(rs["ABS_VAR"].sum())
flagged = int(ex["FLAGGED"])
stamp = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")

st.markdown(f"""
<div class="topbar">
  <div class="logo">&#128202;</div>
  <div style="flex:1">
    <div class="t-title">Brindabella Group &middot; GST Control Tower</div>
    <div class="t-meta"><span class="dot"></span>Live &nbsp;&middot;&nbsp;
      GSI_TAX_WORKSHOP.TAX &nbsp;&middot;&nbsp; {int(sc['LINES']):,} ledger lines
      &nbsp;&middot;&nbsp; Streamlit on Snowflake &nbsp;&middot;&nbsp; {stamp}</div>
  </div>
</div>
""", unsafe_allow_html=True)


def kpi(label, value, sub, colour, pct):
    return (f'<div class="kpi"><div class="kpi-l">{label}</div>'
            f'<div class="kpi-v" style="color:{colour}">{value}</div>'
            f'<div class="kpi-s">{sub}</div>'
            f'<div class="kpi-track"><div class="kpi-fill" '
            f'style="width:{pct:.1f}%;background:{colour}"></div></div></div>')


st.markdown(
    '<div class="kpis">'
    + kpi("Entity-periods reconciled", f"{total_periods:,}",
          f"{int(sc['ENTITIES'])} entities across {int(sc['PERIODS'])} complete months",
          BLUE, 100)
    + kpi("Investigate", f"{investigate:,}",
          "variance above the $1,000 threshold", RED,
          100 * investigate / max(total_periods, 1))
    + kpi("Flagged ledger lines", f"{flagged:,}",
          f"avg risk score {float(ex['AVG_RISK']):.1f}", AMBER,
          100 * flagged / max(int(sc["LINES"]), 1))
    + kpi("Absolute variance", money(abs_var),
          "computed against lodged BAS", GREEN, 100)
    + "</div>", unsafe_allow_html=True)


# =====================================================================
# FILTERS - native widgets, explicitly styled above so the text is legible
# =====================================================================
f1, f2, f3, f4 = st.columns([1, 1.4, 1.6, 1.1])
sev = f1.selectbox("Severity", ["All"] + severities())
entity = f2.selectbox("Entity", ["All entities"] + entities())
min_score = f3.slider("Minimum risk score", 0, 100, 0, 5)
search = f4.text_input("Search supplier or line", placeholder="e.g. Ridgeline")

rows, clause = worklist(min_score, sev, entity, search, 150)
tot = filtered_totals(clause)

# =====================================================================
# PANELS
# =====================================================================
left, right = st.columns([1, 1.25])

SEV_COLOUR = {"MATCHED": GREEN, "REVIEW": AMBER, "INVESTIGATE": RED}

with left:
    bars = ""
    top = int(rs["N"].max())
    for status in ("MATCHED", "REVIEW", "INVESTIGATE"):
        n = int(rs.loc[rs.RECON_STATUS == status, "N"].sum())
        c = SEV_COLOUR[status]
        bars += (
            f'<div class="brow"><div class="brow-top">'
            f'<span><span class="dot" style="background:{c};box-shadow:none"></span>'
            f'{status.title()}</span>'
            f'<span><b>{n:,}</b> <span style="color:{MUTED}">&middot; '
            f'{100 * n / max(total_periods, 1):.1f}%</span></span></div>'
            f'<div class="brow-track"><div class="brow-fill" '
            f'style="width:{100 * n / max(top, 1):.1f}%;background:{c}"></div></div></div>')
    st.markdown(
        f'<div class="card"><div class="card-h">'
        f'<span class="card-t">Reconciliation against lodged BAS</span>'
        f'<span class="card-n">{total_periods:,} entity-periods</span></div>'
        f'{bars}<div class="card-n" style="margin-top:6px">Matched means variance of '
        f'exactly $0.00 &mdash; not within tolerance, nil.</div></div>',
        unsafe_allow_html=True)

with right:
    hist = score_histogram()
    grid = hist.pivot_table(index="BUCKET", columns="MAX_SEVERITY",
                            values="N", aggfunc="sum").fillna(0)
    buckets = list(range(0, 100, 10))
    peak = max(int(grid.sum(axis=1).max()), 1)
    W, H, PAD = 560, 250, 26
    bw = (W - PAD) / len(buckets)
    svg = [f'<svg viewBox="0 0 {W} {H + 34}" width="100%" height="{H + 34}">']
    for gl in (0, 0.5, 1):
        y = H - gl * (H - PAD)
        svg.append(f'<line x1="{PAD}" y1="{y:.0f}" x2="{W}" y2="{y:.0f}" '
                   f'stroke="#1B2942" stroke-width="1"/>')
        svg.append(f'<text x="0" y="{y - 4:.0f}" fill="{MUTED}" font-size="10">'
                   f'{int(peak * gl):,}</text>')
    for i, b in enumerate(buckets):
        x = PAD + i * bw
        stack = 0.0
        for s, c in (("LOW", GREEN), ("MEDIUM", AMBER), ("HIGH", RED)):
            n = float(grid.loc[b, s]) if (b in grid.index and s in grid.columns) else 0.0
            if n <= 0:
                continue
            h = (n / peak) * (H - PAD)
            stack += h
            svg.append(f'<rect x="{x + 3:.1f}" y="{H - stack:.1f}" width="{bw - 6:.1f}" '
                       f'height="{h:.1f}" fill="{c}" rx="2"><title>score {b}-{b + 9} '
                       f'&middot; {s} &middot; {int(n):,} lines</title></rect>')
        svg.append(f'<text x="{x + bw / 2:.0f}" y="{H + 15}" fill="{MUTED}" font-size="10" '
                   f'text-anchor="middle">{b}</text>')
    svg.append(f'<text x="{W / 2:.0f}" y="{H + 31}" fill="{MUTED}" font-size="10" '
               f'text-anchor="middle">risk score</text></svg>')
    # Legend covers only the severities present in the chart. Listing a level
    # with no bars invites the reader to hunt for a colour that is not there.
    legend = "".join(
        f'<span style="margin-left:11px"><span class="dot" style="background:{c};'
        f'box-shadow:none"></span><span style="color:{MUTED};font-size:.71rem">{s.title()}'
        f'</span></span>'
        for s, c in (("HIGH", RED), ("MEDIUM", AMBER), ("LOW", GREEN))
        if s in grid.columns and float(grid[s].sum()) > 0)
    # One transparent hit target per bucket, laid over the SVG. Carries the whole
    # severity split in a single tooltip, which reads better than hovering each
    # stacked segment in turn.
    ov = ""
    for i, b in enumerate(buckets):
        parts, tot_b = [], 0
        for s in ("HIGH", "MEDIUM", "LOW"):
            n = int(grid.loc[b, s]) if (b in grid.index and s in grid.columns) else 0
            tot_b += n
            if n:
                parts.append(f"{s.title()} {n:,}")
        tip = f"score {b}&ndash;{b + 9} &middot; {tot_b:,} lines"
        if parts:
            tip += " &middot; " + " &middot; ".join(parts)
        edge = "tip-r" if i <= 1 else ("tip-l" if i >= len(buckets) - 2 else "")
        ov += (f'<div class="hx-c {edge}" style="left:{100 * (PAD + i * bw) / W:.2f}%;'
               f'width:{100 * bw / W:.2f}%;height:{100 * H / (H + 34):.2f}%" '
               f'data-tip="{tip}"></div>')
    st.markdown(
        f'<div class="card" style="overflow:visible"><div class="card-h">'
        f'<span class="card-t">Risk score distribution</span>'
        f'<span class="card-n">10-point bins{legend}</span>'
        f'</div><div class="hx">{"".join(svg)}{ov}</div></div>', unsafe_allow_html=True)


# =====================================================================
# HEATMAP - entity x period, shaded with our own scale (no matplotlib)
# =====================================================================
hm = heatmap()
piv = hm.pivot(index="ENTITY_NAME", columns="P", values="N").fillna(0).astype(int)
hi = max(int(piv.to_numpy().max()), 1)
# Endpoints for the legend. The shading itself is rank-based (see below).
lo = int(piv.to_numpy().min())


def rag(t):
    """Green-amber-red ramp for a 0..1 position in the observed range.

    The scale is comparative, not absolute. Every entity-period carries a few
    hundred flagged lines, so green means "quietest month in this population",
    never "clean" - which is why the caption says fewest rather than good. A
    reviewer who reads green as clean would draw exactly the wrong conclusion.
    """
    stops = ((0.0, (78, 216, 160)), (0.5, (232, 178, 58)), (1.0, (247, 107, 124)))
    for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
        if t <= t1:
            f = (t - t0) / (t1 - t0)
            return tuple(round(a + (b - a) * f) for a, b in zip(c0, c1))
    return stops[-1][1]


periods = list(piv.columns)
# Shade by rank within the grid, not by linear position in the range. The
# distribution is left-skewed - the median entity-period sits at 0.73 of the
# range - so a linear ramp puts three quarters of the grid in the red and the
# whole thing reads as one alarming block with no signal in it. Ranking spends
# the full green-to-red spread on the ordering that matters. The caption says
# "by rank" for exactly this reason: green is the quietest cell here, not a
# clean one, and a reviewer must not read it as clean.
flat = sorted(int(v) for v in piv.to_numpy().ravel())


def pct(n):
    """Position of n in the observed distribution, 0..1, ties averaged."""
    a, b = bisect.bisect_left(flat, n), bisect.bisect_right(flat, n)
    return ((a + b - 1) / 2) / max(len(flat) - 1, 1)


median = flat[len(flat) // 2]
cells = ""
for ent in piv.index:
    cells += f'<div class="hm-lbl">{html.escape(str(ent))}</div>'
    for i, p in enumerate(periods):
        n = int(piv.loc[ent, p])
        r, g, b = rag(pct(n))
        edge = "tip-r" if i <= 1 else ("tip-l" if i >= len(periods) - 2 else "")
        cells += (f'<div class="hm-c {edge}" style="background:rgb({r},{g},{b})" '
                  f'data-tip="{html.escape(str(ent))} &middot; {p} &middot; '
                  f'{n:,} flagged lines"></div>')
ramp = "".join(
    f'<span style="display:inline-block;width:15px;height:9px;background:'
    f'rgb{rag(i / 6)};border-radius:2px;margin-left:2px"></span>' for i in range(7))
st.markdown(
    f'<div class="card" style="margin-top:14px;overflow:visible">'
    f'<div class="card-h"><span class="card-t">Flagged lines by entity and period'
    f'</span><span class="card-n">{len(piv.index)} entities &times; {len(periods)} '
    f'periods &middot; hover a cell for detail<br>fewest {lo:,}{ramp} most {hi:,}'
    f' &middot; shaded by rank &middot; median {median:,}</span></div>'
    f'<div class="hm" style="grid-template-columns:150px repeat({len(periods)},1fr)">'
    f'{cells}</div></div>', unsafe_allow_html=True)


# =====================================================================
# WORKLIST - rendered as our own table, so no st.dataframe theming fight
# =====================================================================
PILL = {"HIGH": (RED, "rgba(247,107,124,.14)"),
        "MEDIUM": (AMBER, "rgba(232,178,58,.14)"),
        "LOW": (GREEN, "rgba(78,216,160,.14)")}
body = ""
for _, r in rows.iterrows():
    fg, bg = PILL.get(r.MAX_SEVERITY, (MUTED, "rgba(138,155,176,.14)"))
    var = float(r.TAX_VARIANCE or 0)
    body += (
        f"<tr><td style='font-family:ui-monospace,Menlo,monospace;color:{MUTED}'>"
        f"{txt(r.GL_LINE_ID)}</td><td>{txt(r.ENTITY_NAME)}</td><td>{txt(r.SUPPLIER_NAME)}</td>"
        f"<td style='color:{MUTED}'>{txt(r.SUPPLY_CATEGORY)}</td><td>{txt(r.TAX_TREATMENT)}</td>"
        f"<td class='num' style='color:{MUTED}'>{txt(r.APPLIED_RULE_ID)}</td>"
        # Direction matters to a tax reviewer: under-declared GST is ATO
        # exposure, over-declared is Brindabella's own money sitting with the ATO.
        f"<td class='num' style='color:{RED if var < 0 else AMBER}'>{var:,.2f}</td>"
        f"<td style='color:{MUTED};font-size:.72rem'>{txt(r.EXCEPTION_CODES)}</td>"
        f"<td><span class='pill' style='color:{fg};background:{bg}'>{r.MAX_SEVERITY}</span></td>"
        f"<td class='num'><b>{int(r.RISK_SCORE)}</b></td></tr>")

st.markdown(
    f'<div class="card" style="margin-top:14px"><div class="card-h">'
    f'<span class="card-t">Exception worklist</span>'
    f'<span class="card-n">{int(tot["N"]):,} lines match &middot; '
    f'{money(tot["ABS_VAR"])} absolute variance &middot; showing top {len(rows)} '
    f'by risk</span></div>'
    '<table class="tt"><thead><tr>'
    '<th>GL line</th><th>Entity</th><th>Supplier</th><th>Category</th>'
    '<th>Treatment</th><th class="num">Rule</th><th class="num">Variance</th>'
    '<th>Codes</th><th>Severity</th><th class="num">Risk</th>'
    f'</tr></thead><tbody>{body}</tbody></table></div>', unsafe_allow_html=True)

st.markdown(
    f'<div style="color:{MUTED};font-size:.72rem;margin-top:14px;text-align:center">'
    'Every figure traces back to a rule row in <code>TAX.TAX_RULE_DETERMINATION</code> '
    'and a source document reference. Compute stays where the data is; only the '
    'answer travels.</div>', unsafe_allow_html=True)
