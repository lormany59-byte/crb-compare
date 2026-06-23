"""Root entry point named app.py (re-exports the Flask app from
crb_compare/app.py) for platforms/buildpacks that specifically look for
app.py + requirements.txt at the repo root and run e.g. `gunicorn app:app`.

Loaded via importlib under a distinct module name ("crb_compare_app")
since this file is also named app.py — a plain `from app import app`
would collide with this module's own name in sys.modules.
"""

import importlib.util
import sys
from pathlib import Path

_crb_dir = Path(__file__).resolve().parent / "crb_compare"
sys.path.insert(0, str(_crb_dir))

_spec = importlib.util.spec_from_file_location("crb_compare_app", _crb_dir / "app.py")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

app = _module.app

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
