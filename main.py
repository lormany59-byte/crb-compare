"""Root entry point for platforms that auto-detect a Python web app via a
root-level main.py/app.py + requirements.txt (the actual app lives in
crb_compare/app.py; this just re-exports it under that name).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "crb_compare"))

from app import app  # noqa: E402

if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
