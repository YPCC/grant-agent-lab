"""Native window around the Python workbench.

  python -m src.desktop
  grant-harness desktop

Uses pywebview when installed (`pip install -e '.[desktop]'`). Otherwise
opens the system browser. Same GrantGraph as the lab; LLM is configured
in the Settings tab or config/runtime.yaml `llm:`.
"""
from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _free_port() -> int:
    env = os.environ.get("GRANT_DESKTOP_PORT") or os.environ.get("PORT")
    if env:
        return int(env)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def main(argv: list[str] | None = None) -> int:
    os.chdir(ROOT)
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from src.control_plane.gates import assert_runtime_ready
    from src.control_plane.profile import current
    from src.llm.config import load_llm

    # serve_workbench.py is a script, not a package.
    ui_dir = ROOT / "ui-copilotkit"
    if str(ui_dir) not in sys.path:
        sys.path.insert(0, str(ui_dir))
    import serve_workbench as wb  # type: ignore

    assert_runtime_ready()
    port = _free_port()
    httpd = ThreadingHTTPServer(("127.0.0.1", port), wb.Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    url = f"http://127.0.0.1:{port}/"
    llm = load_llm()
    print(
        f"Grant Agent Lab desktop {url}  profile={current().name}  "
        f"llm={llm.provider}:{llm.model}"
    )
    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                break
        except OSError:
            time.sleep(0.05)
    try:
        import webview  # type: ignore

        webview.create_window("Grant Agent Lab", url, width=1280, height=860)
        webview.start()
    except ImportError:
        print("pywebview not installed — opening the system browser. pip install -e '.[desktop]'")
        webbrowser.open(url)
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
    finally:
        httpd.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
