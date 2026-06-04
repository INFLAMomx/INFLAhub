<!--
Thanks for contributing to INFLAhub! Please fill in the sections below.
See CONTRIBUTING.md for the full guidelines.
-->

## What & why

<!-- Summarize the change and the motivation. Link any related issue: Closes #123 -->

## Type of change

- [ ] Catalogue data (tools / benchmarks / metrics)
- [ ] App code (`src/app.R`, styling)
- [ ] CI / build / docs
- [ ] Other:

## How I verified it

<!-- How did you check this works? -->

- [ ] Ran `shiny::runApp("src")` and clicked through all four tabs without errors
- [ ] (Data) Ran `dvc add` + `dvc push`; committed the updated `.dvc` pointer
- [ ] (Build-affecting) Verified the Shinylive build with `Rscript deploy.R`
- [ ] Any new R package dependencies are available as Wasm builds

## Notes for reviewers

<!-- Anything specific you'd like feedback on, screenshots, caveats, follow-ups. -->
