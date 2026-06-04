# ─────────────────────────────────────────────────────────────────────────────
# deploy.R — Build static Shinylive app and prepare for GitHub Pages
#
# Run this script from the app/ directory:
#   Rscript deploy.R
#
# What it does:
#   1. Installs shinylive if missing
#   2. Exports the Shiny app to ../docs/ (WebAssembly build, no server needed)
#   3. Adds .nojekyll so GitHub Pages skips Jekyll processing
#
# GitHub Pages setup (one-time):
#   - Push the repo to GitHub
#   - Settings → Pages → Source: Deploy from branch
#   - Branch: main  |  Folder: /docs
#   - Your app will be live at https://<user>.github.io/<repo>/
# ─────────────────────────────────────────────────────────────────────────────

# Ensure we're in the app/ directory
if (!file.exists("app.R")) {
  stop("Run this script from the app/ directory: Rscript deploy.R")
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

# Prevent GitHub Pages from running Jekyll (required for Shinylive)
nojekyll <- file.path(dest, ".nojekyll")
if (!file.exists(nojekyll)) file.create(nojekyll)

message("")
message("Done! Next steps:")
message("  1. git add docs/ && git commit -m 'deploy: rebuild Shinylive app'")
message("  2. git push")
message("  3. Enable GitHub Pages in repo Settings → Pages → /docs on main")
message("")
message("To preview locally before pushing:")
message("  shinylive::preview('", dest, "')")
