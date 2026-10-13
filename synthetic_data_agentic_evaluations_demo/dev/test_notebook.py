"""Executes the notebook cell by cell against a Snowflake connection to prove it runs (run setup_1_core.sql first).
SQL cells become Snowpark DataFrames (same as Workspace runtime >= 2.6). Charts are saved to /tmp.
Usage: python3 dev/test_notebook.py [path/to/notebook.ipynb] [--skip-generate]
  SNOWFLAKE_CONNECTION_NAME  connection to use (default: your default connection)
  DB_PREFIX                  optional, e.g. ZT_ to test against ZT_MORTGAGE_PROD / ZT_MORTGAGE_DEV copies
Note: the notebook starts a live evaluation run; delete it afterwards if you want Snowsight to stay tidy.
"""
import json, os, sys, time, pathlib, traceback
import snowflake.snowpark.context as ctx
from snowflake.snowpark import Session

_args = [a for a in sys.argv[1:] if a.endswith(".ipynb")]
NB = pathlib.Path(_args[0]) if _args else pathlib.Path(__file__).resolve().parent.parent / "synthetic_data_agentic_evaluations.ipynb"
PREFIX = os.getenv("DB_PREFIX", "")
_builder = Session.builder
if os.getenv("SNOWFLAKE_CONNECTION_NAME"):
    _builder = _builder.config("connection_name", os.environ["SNOWFLAKE_CONNECTION_NAME"])
session = _builder.create()
ctx.get_active_session = lambda: session

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
chart_n = [0]
def _show(*a, **k):
    chart_n[0] += 1
    plt.savefig(f"/tmp/{NB.stem}_chart_{chart_n[0]}.png", dpi=80)
    plt.close("all")
plt.show = _show

def display(x):
    if hasattr(x, "data") and hasattr(x, "to_html"):   # pandas Styler
        x = x.data
    print(x.to_string() if hasattr(x, "to_string") else x)

def prefixed(src):
    if not PREFIX:
        return src
    return (src.replace("MORTGAGE_PROD", PREFIX + "MORTGAGE_PROD").replace("MORTGAGE_DEV", PREFIX + "MORTGAGE_DEV")
               .replace("DEMO_DEV_ROLE", PREFIX + "DEMO_DEV_ROLE"))

ns = {"display": display, "__name__": "__main__"}
skip_gen = "--skip-generate" in sys.argv
cells = json.loads(NB.read_text())["cells"]
fails = 0
for i, c in enumerate(cells):
    if c["cell_type"] != "code":
        continue
    src = prefixed("".join(c["source"]))
    if src.strip().startswith("#") and "\n" not in src.strip():
        continue
    if skip_gen and "GENERATE_SYNTHETIC_DATA" in src:
        print(f"[{i}] SKIP generation (CORE_LIVE keeps the last generated tables)")
        continue
    t0 = time.time()
    try:
        if c["metadata"].get("language") == "sql":
            name = c["metadata"]["resultVariableName"]
            body = src.split("\n", 1)[1]
            df = session.sql(body)
            df.collect()  # force execution like the UI does
            ns[name] = df
            out = None
        else:
            lines = src.rstrip().split("\n")
            last = lines[-1]
            exec("\n".join(lines[:-1]), ns) if not last.startswith((" ", "\t", ")", "'")) else exec(src, ns)
            out = None
            if not last.startswith((" ", "\t", ")", "'")):
                try:
                    out = eval(last, ns)
                except SyntaxError:
                    exec(last, ns)
        if out is not None:
            display(out)
        print(f"[{i}] OK {time.time()-t0:.1f}s  :: {src.splitlines()[0][:70]}")
    except Exception:
        fails += 1
        print(f"[{i}] FAIL :: {src.splitlines()[0][:70]}")
        traceback.print_exc(limit=2)
print(f"\nDONE: {fails} failing cells; charts: {chart_n[0]}")
sys.exit(1 if fails else 0)
