# Contributing to INFLAhub

Thanks for helping build the WG2 Method Hub! This guide covers how we work and
what we expect in a pull request. By contributing you agree to follow our
[Code of Conduct](code_of_conduct.md).

There are two kinds of contributions:

- **Catalogue data** — adding or correcting tools, benchmarks, or metrics in the
  spreadsheet.
- **App code** — changes to the Shiny app (`src/app.py`), styling, or CI.

## Before you start

- For anything beyond a small fix, **open an issue first** to align on scope and
  avoid duplicate work.
- Keep pull requests **focused** — one logical change per PR. Don't mix a data
  update with a code refactor.

## Branching & commits

- Branch off `main`. Use a short, descriptive branch name, e.g.
  `add-mofa-tool`, `fix-heatmap-layers`, `data/update-benchmarks`.
- Write clear commit messages. We loosely follow
  [Conventional Commits](https://www.conventionalcommits.org/):
  - `feat: add language filter to Method Explorer`
  - `fix: handle empty Omics_layers in heatmap`
  - `data: add 3 spatial integration tools`
  - `docs: clarify local build steps`
  - `ci: cache Shinylive assets in deploy workflow`
- Keep commits logically grouped; rebase/squash noisy WIP commits before opening
  the PR.

## Editing the catalogue data

The catalogue lives in `Method_hub_WG2.xlsx`, which is tracked with
[DVC](https://dvc.org/) — **not** committed directly to git.

1. `dvc pull` to fetch the current spreadsheet.
2. Edit the relevant sheet (`Bulk methods`, `Single-cell methods`,
   `Spatial methods`, `Benchmarking`, or `Evaluation metrics`).
   - **Don't change the column order or header rows** — `app.py` reads method
     columns by position (see `METHOD_COLS` and the `skiprows=` offsets in
     `src/app.py`).
   - Use `Y` / `N` for the inclusion-criteria columns (actively maintained,
     published, code available, parameters documented). Inclusion status is
     **recomputed** from these in the app, so you don't need to fill it in.
   - Leave unknown cells blank rather than inventing values.
3. `dvc add data/Method_hub_WG2.xlsx` and commit the updated `.dvc` pointer file.
4. `dvc push` so others (and CI) can fetch your data.

## Changing the app

- Match the existing code style in `src/app.py` (pandas, the section banners, the
  module-level builder functions and helpers like `val()`, `star_rating()`,
  `yn_badge()`).
- Guard against missing/empty data — sheets and columns may be incomplete. Follow
  the existing `try`/`except`, `fillna`, and empty-state patterns.
- **Test locally before pushing:** `shiny run --reload src/app.py` and click
  through all four tabs. There is no automated test suite, so manual verification
  is the bar.
- If you change anything that affects the Wasm build, sanity-check it with
  `python src/deploy.py` and preview `_site/` before pushing.

## Opening the pull request

- Target `main`.
- Fill in the PR template: **what** changed, **why**, and **how you verified it**.
- Confirm the app still loads and all four tabs render without errors.
- Note any new Python dependencies — they must be pure-Python wheels or have a
  Pyodide build, and non-bundled ones belong in `src/requirements.txt`, for the
  Shinylive deploy to succeed.
- A maintainer will review. Deployment to GitHub Pages happens automatically once
  the PR is merged to `main` (when `src/**` changes).

## License of contributions

This repository is dual-licensed. By submitting a contribution you agree it is
licensed accordingly:

- **App code** under the [MIT License](LICENSE).
- **Catalogue data** (the curated spreadsheets) under
  [CC BY 4.0](LICENSE-data).

Only contribute data you have the right to share, and prefer linking to original
sources over copying substantial third-party content.

## Reporting bugs & ideas

Open a [GitHub issue](https://github.com/INFLAMomx/INFLAhub/issues) describing the
problem or suggestion. For data issues, point to the specific tool/row and sheet.
