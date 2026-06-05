#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# deploy.py — Build the static Shinylive app locally (preview / manual build)
#
# Publishing is automated: .github/workflows/deploy.yml rebuilds and deploys to
# GitHub Pages on every push to main. You normally do NOT need to run this — use
# it only to preview the WebAssembly build locally before pushing.
#
# Run from the repository root (or anywhere — paths are resolved relative to
# this file):
#   python src/deploy.py
#
# What it does:
#   1. Exports the Shiny app in this folder to ../_site/ (WebAssembly build,
#      runs entirely in the browser — no server needed).
#   2. Adds .nojekyll so static hosts skip Jekyll processing.
#
# Preview the result with:
#   python -m http.server -d _site 8000   →  http://localhost:8000
#
# GitHub Pages setup (one-time, for the workflow):
#   - Settings → Pages → Build and deployment → Source: GitHub Actions
#   - The app goes live at https://<user>.github.io/<repo>/
# ─────────────────────────────────────────────────────────────────────────────

import subprocess
import sys
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DEST = APP_DIR.parent / "_site"


def main():
    print(f"Exporting Shinylive app to {DEST}/ ...")
    # shinylive ships a console-script entry point (shinylive._main:main) rather
    # than a runnable module, so invoke that entry point directly — this works
    # whether or not the `shinylive` script is on PATH.
    subprocess.run(
        [sys.executable, "-c", "from shinylive._main import main; main()",
         "export", str(APP_DIR), str(DEST)],
        check=True,
    )

    nojekyll = DEST / ".nojekyll"
    nojekyll.touch(exist_ok=True)

    print()
    print(f"Done — static build written to {DEST}/")
    print()
    print("Preview it locally with:")
    print(f"  python -m http.server -d {DEST} 8000   →  http://localhost:8000")
    print()
    print("To publish, just push to main — the GitHub Pages workflow rebuilds and")
    print("deploys automatically (.github/workflows/deploy.yml).")


if __name__ == "__main__":
    main()
