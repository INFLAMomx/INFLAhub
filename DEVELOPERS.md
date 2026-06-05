# Developer guide

Technical reference for running, building, and deploying INFLAhub. For the
contribution workflow (branches, commits, PRs), see
[CONTRIBUTING.md](CONTRIBUTING.md).

The app is built with [Shiny for Python](https://shiny.posit.co/py/), with
[plotly](https://plotly.com/python/) charts (rendered via
[shinywidgets](https://github.com/posit-dev/py-shinywidgets)) and
[pandas](https://pandas.pydata.org/) for the data wrangling.

## Repository layout

```
Method_hub_WG2.xlsx  # master workbook (edit here) — kept out of src/ so it isn't
build_csvs.py        #   bundled into the deploy; regenerates the CSVs from it
src/
  app.py             # the Shiny application (UI + server)
  deploy.py          # local Shinylive (WebAssembly) build script
  www/custom.css     # styling
  data/
    methods_bulk.csv          # catalogue tables the app reads
    methods_single_cell.csv   #   (git-tracked → diffs on GitHub)
    methods_spatial.csv
    benchmarking.csv
    evaluation_metrics.csv
.github/workflows/
  deploy.yml         # CI: builds & publishes to GitHub Pages on push to main
```

## The data

The catalogue is stored as **CSV files** in `src/data/` (one per table), committed
to git so every edit shows up as a readable diff:

- `methods_bulk.csv`, `methods_single_cell.csv`, `methods_spatial.csv`
- `benchmarking.csv`
- `evaluation_metrics.csv`

The app reads these CSVs directly. They are generated from the master workbook
`Method_hub_WG2.xlsx` (at the repo root, deliberately outside `src/` so it isn't
bundled into the deploy) by `build_csvs.py`. The method CSVs use the `METHOD_COLS`
names as their header (kept in sync between `app.py` and `build_csvs.py`);
`Data_type` and inclusion status (`PASS`/`REVIEW`) are derived in the app, not
stored.

To update the catalogue: edit the workbook, run `python build_csvs.py` (needs
`pandas` + `openpyxl` locally), and commit the changed `src/data/*.csv` files (and
the workbook). You can also edit the CSVs directly if you prefer — just keep their
headers intact.

## Running locally

You need Python 3.9+ with the app's packages:

```bash
pip install shiny shinywidgets plotly pandas faicons
```

Then, from the repository root:

```bash
shiny run --reload src/app.py
```

…and open the URL it prints (default <http://127.0.0.1:8000>). The app reads the
CSVs in `src/data/`, which are committed to the repo — no extra data fetch needed.

## Building the static site

The published site is a [Shinylive](https://shiny.posit.co/py/docs/shinylive.html)
build that runs entirely in the browser (WebAssembly via Pyodide — **no server
required**). You don't normally need to build it by hand: the
[`deploy.yml`](.github/workflows/deploy.yml) workflow rebuilds and publishes to
GitHub Pages on every push to `main` that touches `src/**`.

To preview the Wasm build locally before pushing:

```bash
pip install shinylive
python src/deploy.py                       # exports to ./_site/
python -m http.server -d _site 8000        # http://localhost:8000
```

(Equivalently: `shinylive export src _site`.)

### Dependencies in the browser build

Shinylive detects the app's imports and bundles matching wheels automatically, so
the app currently needs **no** extra configuration (it reads CSVs, so there is no
`openpyxl`/`requirements.txt` and nothing is fetched at load time). If you add a
dependency that Shinylive/Pyodide doesn't already provide, create
`src/requirements.txt` listing it — it must be a pure-Python wheel or have a
Pyodide build, and it is installed at app-load time via micropip.

> Note: the static bundle only ships what's under `src/`, so the deploy contains
> just the app and the CSVs — the master `.xlsx` and `build_csvs.py` live at the
> repo root and are never sent to the browser.
