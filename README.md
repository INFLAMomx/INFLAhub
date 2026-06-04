# INFLAhub: a knowledge hub for multiomics tools and datasets

A living catalogue of multi-omics datasets, integration tools, benchmarking studies, and
evaluation metrics, curated by Working Groups 1 and 2 of [COST Action CA24166 — INFLAMomx](https://www.cost.eu/)
(*Pan-European Network for Inflammaging: A Multi-omics Integration Approach*).

**Live app:** https://inflamomx.github.io/INFLAhub/

## What's inside

The hub is a [Shiny for Python](https://shiny.posit.co/py/) app for browsing the catalogue:

- **Method Explorer** — filterable, searchable table of tools, with a detail panel per tool.
- **Visual Overview** — quality landscape, tools-by-category chart, and omics-layer coverage.
- **Benchmarking & Metrics** — benchmark studies and evaluation metrics tables.
- **About** — scope, inclusion criteria, and catalogue stats.

Tools are tagged **PASS** when they meet all four inclusion criteria (actively
maintained · published · code available · parameters documented) and **REVIEW**
otherwise.

## Documentation

- [Developer guide](DEVELOPERS.md) — running locally, the data/DVC workflow, and building the site.
- [Contributing](CONTRIBUTING.md) — branch, commit, and pull-request guidelines.
- [Code of Conduct](code_of_conduct.md).

## License

This repository is dual-licensed:

- **Application code** — [MIT](LICENSE) © 2026 INFLAMomx COST Action (CA24166).
- **Catalogue data** (the curated spreadsheets) — [CC BY 4.0](LICENSE-data); reuse
  freely with attribution to the INFLAMomx COST Action (CA24166).
