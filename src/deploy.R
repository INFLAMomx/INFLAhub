# ─────────────────────────────────────────────────────────────────────────────
# deploy.R — Build the static Shinylive app locally (preview / manual build)
#
# Publishing is automated: .github/workflows/deploy.yml rebuilds and deploys to
# GitHub Pages on every push to main. You normally do NOT need to run this — use
# it only to preview the Wasm build locally before pushing.
#
# Run this script from the src/ directory (the folder that contains app.R):
#   Rscript deploy.R
#
# What it does:
#   1. Installs shinylive if missing
#   2. Exports the Shiny app to ../docs/ (WebAssembly build, no server needed)
#   3. Adds .nojekyll so static hosts skip Jekyll processing
#
# GitHub Pages setup (one-time, for the workflow):
#   - Settings → Pages → Build and deployment → Source: GitHub Actions
#   - The app goes live at https://<user>.github.io/<repo>/
# ─────────────────────────────────────────────────────────────────────────────

# Ensure we're in the app directory (the one holding app.R)
if (!file.exists("app.R")) {
  stop("Run this script from the src/ directory (where app.R lives): Rscript deploy.R")
}

# Set CRAN mirror if not already configured
cran_mirror <- unname(getOption("repos")["CRAN"])
if (is.null(cran_mirror) || identical(cran_mirror, "@CRAN@")) {
  options(repos = c(CRAN = "https://cloud.r-project.org"))
}

# Install / update shinylive — older versions crash on packages absent from the
# Wasm repo (desc$Repository bug); always pull the latest to get the fix.
message("Installing/updating shinylive and its dependencies...")
install.packages(c("shinylive", "S7", "httpuv"), quiet = TRUE)

dest <- "../docs"

message("Exporting Shinylive app to ", dest, "/ ...")

shinylive::export(
  appdir    = ".",
  destdir   = dest,
  overwrite = TRUE
)

# Skip Jekyll processing on static hosts (required for Shinylive's asset layout)
nojekyll <- file.path(dest, ".nojekyll")
if (!file.exists(nojekyll)) file.create(nojekyll)

message("")
message("Done — static build written to ", normalizePath(dest), "/")
message("")
message("Preview it locally with:")
message("  shinylive::preview('", dest, "')")
message("")
message("To publish, just push to main — the GitHub Pages workflow rebuilds and")
message("deploys automatically (.github/workflows/deploy.yml).")
