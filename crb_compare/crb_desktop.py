"""Desktop launcher used to build the standalone .exe (PyInstaller).

Starts the Flask server on localhost and pops the browser open so staff can
use the app by simply double-clicking the .exe — no Python install needed.
"""

import sys
import threading
import time
import webbrowser
from pathlib import Path

# The frozen .exe console defaults to a legacy codepage (cp1252) that cannot
# encode Lao text — force UTF-8 so the status messages don't crash startup.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# Make the crb_compare modules importable both in dev and when frozen.
_base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
sys.path.insert(0, str(_base / "crb_compare"))
sys.path.insert(0, str(_base))

from app import app  # noqa: E402  (crb_compare/app.py)

HOST = "127.0.0.1"
PORT = 5000


def _open_browser() -> None:
    time.sleep(1.5)
    webbrowser.open(f"http://{HOST}:{PORT}")


if __name__ == "__main__":
    print("=" * 56)
    print(f"  ລະບົບສົມທຽບເງິນຝາກ CRB ກຳລັງເປີດ...")
    print(f"  ເປີດ browser ໄປທີ່:  http://{HOST}:{PORT}")
    print(f"  ປິດໂປຣແກຣມ: ປິດໜ້າຕ່າງນີ້ ຫຼື ກົດ Ctrl+C")
    print("=" * 56)
    threading.Thread(target=_open_browser, daemon=True).start()
    app.run(host=HOST, port=PORT)
