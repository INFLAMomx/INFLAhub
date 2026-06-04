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
src/
  app.py             # the Shiny application (UI + server)
  deploy.py          # local Shinylive (WebAssembly) build script
  requirements.txt   # extra Wasm packages (only those not bundled by Shinylive)
  www/custom.css     # styling
  data/              # working copy of the catalogue spreadsheet
data/
  *.xlsx.dvc         # DVC pointers to the source spreadsheets (data tracked via DVC)
.github/workflows/
  deploy.yml         # CI: builds & publishes to GitHub Pages on push to main
```

## The data

The catalogue lives in `Method_hub_WG2.xlsx`. The actual `.xlsx` files are **not**
committed to git — they are tracked with [DVC](https://dvc.org/); only the small
`.dvc` pointer files are versioned. Run `dvc pull` to fetch the spreadsheet before
running the app.

The app reads several sheets (`Bulk methods`, `Single-cell methods`,
`Spatial methods`, `Benchmarking`, `Evaluation metrics`). Method columns are read
**by position** — see `METHOD_COLS` and the `skiprows=` offsets in `src/app.py` —
so don't reorder columns or header rows when editing.

## Running locally

You need Python 3.9+ with the app's packages:

```bash
pip install shiny shinywidgets shinyswatch plotly pandas openpyxl faicons
```

Then, from the repository root:

```bash
shiny run --reload src/app.py
```

…and open the URL it prints (default <http://127.0.0.1:8000>). The app reads
`data/Method_hub_WG2.xlsx` relative to the app file — run `dvc pull` first if you
don't have the spreadsheet locally.

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
most dependencies need no extra configuration. Only packages that are **not**
provided by Shinylive/Pyodide go in `src/requirements.txt` (currently just
`openpyxl`, pandas' `.xlsx` engine), where they are installed at app-load time via
micropip. A new dependency must be a pure-Python wheel or have a Pyodide build for
the deploy to work.
