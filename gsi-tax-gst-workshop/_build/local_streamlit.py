"""Run a Streamlit-in-Snowflake app on this machine, unmodified.

The app calls get_active_session(), which only exists inside SiS. This harness
creates a real Snowpark session from ~/.snowflake/config.toml and patches it in
BEFORE executing the app source, so the app's own
`from snowflake.snowpark.context import get_active_session` picks up the patch.

    streamlit run _build/local_streamlit.py -- <path-to-app.py>

Nothing here is uploaded to Snowflake; it exists purely to surface runtime errors
locally instead of in front of the room.
"""
import pathlib
import sys
import tomllib

import snowflake.snowpark.context as ctx
from snowflake.snowpark import Session

CONN = "staub_uswest_primary_pat"
DATABASE = "GSI_TAX_WORKSHOP"
WAREHOUSE = "GSI_TAX_WH"

app_path = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/gst_control_tower.py")

cfg = tomllib.loads((pathlib.Path.home() / ".snowflake/config.toml").read_text())
c = dict(cfg["connections"][CONN])
token = pathlib.Path(c.pop("token_file_path")).expanduser().read_text().strip()

_session = Session.builder.configs({
    "account": c["account"],
    "user": c["user"],
    "role": c.get("role"),
    "warehouse": WAREHOUSE,
    "database": DATABASE,
    "authenticator": c["authenticator"],
    "token": token,
}).create()

ctx.get_active_session = lambda: _session

source = app_path.read_text()
exec(compile(source, str(app_path), "exec"), {"__name__": "__main__", "__file__": str(app_path)})
