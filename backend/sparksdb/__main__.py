import argparse
import os
import sys
import time
import urllib.request
from pathlib import Path

import webview

from . import pool_manager
from .api import Api

DEV_URL = "http://localhost:1420"
PACKAGE_DIR = Path(__file__).resolve().parent


def _dist_index() -> str:
    dist = os.environ.get("SPARKSDB_DIST") or PACKAGE_DIR.parents[1] / "dist"
    index = Path(dist) / "index.html"
    if not index.exists():
        sys.exit(f"Frontend nao encontrado em {index}. Rode 'npm run build:vite'.")
    return str(index)


def _wait_for(url: str, timeout: float = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except OSError:
            time.sleep(0.3)
    sys.exit(f"Vite nao respondeu em {url}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="sparksdb")
    parser.add_argument("--dev", action="store_true", help="carrega o frontend do Vite dev server")
    args = parser.parse_args()

    if args.dev:
        _wait_for(DEV_URL)
        url = DEV_URL
    else:
        url = _dist_index()

    webview.create_window(
        "sparksDB", url, js_api=Api(), width=1280, height=800, resizable=True, text_select=True
    )
    # http_server: os assets do Vite (caminhos absolutos) e o worker do Monaco nao carregam via file://.
    # O servidor so entrega o dist/ estatico; a API passa pela ponte JS.
    webview.start(
        gui="gtk", debug=args.dev, http_server=not args.dev, icon=str(PACKAGE_DIR / "icon.png")
    )
    pool_manager.close_all()


if __name__ == "__main__":
    main()
