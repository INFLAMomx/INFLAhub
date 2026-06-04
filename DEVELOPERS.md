# Developer guide

Technical reference for running, building, and deploying INFLAhub. For the
contribution workflow (branches, commits, PRs), see
[CONTRIBUTING.md](CONTRIBUTING.md).

## Repository layout

```
src/
  app.R              # the Shiny application (UI + server)
  deploy.R           # local Shinylive (WebAssembly) build script
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
`Spatial methods`, `Benchmarking`, `Evaluation metrics`). Columns are read **by
position** — see `METHOD_COLS` and the `skip =` offsets in `src/app.R` — so don't
reorder columns or header rows when editing.

## Running locally

You need R with the app's packages:

```r
install.packages(c(
  "shiny", "bslib", "DT", "plotly", "readxl",
  "dplyr", "tidyr", "stringr", "shinyWidgets"
))
```

Then, from the repository root:

```r
shiny::runApp("src")
```

The app reads `data/Method_hub_WG2.xlsx` relative to the app directory — run
`dvc pull` first if you don't have the spreadsheet locally.

## Building the static site

The published site is a [Shinylive](https://posit-dev.github.io/r-shinylive/)
build that runs entirely in the browser (WebAssembly via webR — **no server
required**). You don't normally need to build it by hand: the
[`deploy.yml`](.github/workflows/deploy.yml) workflow rebuilds and publishes to
GitHub Pages on every push to `main` that touches `src/**`.

To preview the Wasm build locally before pushing, run from `src/`:

```bash
Rscript deploy.R
```

Any new R package dependency must be available as a Wasm build for the Shinylive
deploy to succeed.
