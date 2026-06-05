# ─────────────────────────────────────────────────────────────────────────────
# INFLAMomx · WG2 Method Hub
# COST Action CA24166 — Multi-omics Integration Methods
# Deliverable D2.1 (month 18)
#
# Shiny for Python port of the original R/Shiny app (app.R).
# ─────────────────────────────────────────────────────────────────────────────

import re
import textwrap
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

import faicons
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_widget

APP_DIR = Path(__file__).parent
DASH = "—"

# ─── Helpers ──────────────────────────────────────────────────────────────────


def val(x):
    """First non-empty value or a dash placeholder."""
    if pd.isna(x):
        return DASH
    if isinstance(x, float) and float(x).is_integer():
        return str(int(x))
    s = str(x).strip()
    return DASH if s == "" else s


def star_rating(n, max_n=5):
    try:
        n = int(float(n))
    except (TypeError, ValueError):
        return DASH
    if n < 1 or n > max_n:
        return DASH
    return "★" * n + "☆" * (max_n - n)


def yn_badge(x):
    x = str(x)
    if x == "Y":
        return ui.span("Yes", class_="badge bg-success")
    if x == "N":
        return ui.span("No", class_="badge bg-danger")
    return ui.span(DASH, class_="badge bg-secondary opacity-75")


def status_badge(x):
    x = str(x)
    if x == "PASS":
        return ui.span("PASS", class_="badge bg-success")
    if x == "REVIEW":
        return ui.span("REVIEW", class_="badge bg-warning text-dark")
    return ui.span(DASH, class_="badge bg-secondary opacity-75")


def link_btn(href, label, icon_name, btn_class="btn-outline-primary"):
    if href is None or pd.isna(href) or str(href).strip() in ("", DASH):
        return None
    return ui.tags.a(
        faicons.icon_svg(icon_name),
        " " + label,
        class_=f"btn btn-sm {btn_class}",
        href=str(href),
        target="_blank",
        rel="noopener noreferrer",
    )


# ─── Data loading ──────────────────────────────────────────────────────────────
# The catalogue lives in per-table CSV files under src/data/ (git-tracked, so
# edits show up as diffs on GitHub). Regenerate them from the master Excel
# workbook with `python build_csvs.py`.

DATA_DIR = APP_DIR / "data"

# Expected method-sheet columns. The CSVs carry these as their header, so they
# are read by name; this list is kept for the empty/missing-file fallback and to
# document the schema. KEEP IN SYNC with build_csvs.py.
METHOD_COLS = [
    "Assigned_to", "Tool", "Integration_category", "Link",
    "Use_case", "Integration_type", "Omics_layers", "Technologies",
    "Strengths", "Limitations", "Best_for", "Study_examples",
    "Paper_DOI", "Citation_count", "Benchmarked_in",
    "Installation_source", "Doc_quality", "Usability",
    "Maintenance_status", "Language", "Preprocessing_steps",
    "Input_formats", "Input_details", "Output_formats", "Underlying_method",
    "Actively_maintained", "Published", "Code_available",
    "Parameters_documented", "Include_raw",
]


def read_methods(csv_name, type_label):
    try:
        df = pd.read_csv(DATA_DIR / csv_name, dtype=str)
    except Exception as e:  # noqa: BLE001
        print(f"Could not load '{csv_name}': {e}")
        return pd.DataFrame(columns=METHOD_COLS + ["Data_type", "Include"])

    for col in METHOD_COLS:  # tolerate a CSV missing an optional column
        if col not in df.columns:
            df[col] = pd.NA

    df = df[df["Tool"].notna() & (df["Tool"].astype(str).str.strip() != "")].copy()
    df["Data_type"] = type_label
    df["Doc_quality"] = pd.to_numeric(df["Doc_quality"], errors="coerce")
    df["Usability"] = pd.to_numeric(df["Usability"], errors="coerce")
    df["Citation_count"] = pd.to_numeric(df["Citation_count"], errors="coerce")

    # Recompute inclusion from Y/N criteria (more reliable than cached formula)
    crit = ["Actively_maintained", "Published", "Code_available", "Parameters_documented"]
    pass_mask = np.logical_and.reduce([df[c].fillna("") == "Y" for c in crit])
    review_mask = df[crit].notna().any(axis=1)
    df["Include"] = np.where(pass_mask, "PASS", np.where(review_mask, "REVIEW", None))
    return df


methods_all = pd.concat(
    [
        read_methods("methods_bulk.csv", "Bulk"),
        read_methods("methods_single_cell.csv", "Single-cell"),
        read_methods("methods_spatial.csv", "Spatial"),
    ],
    ignore_index=True,
)

try:
    bench = pd.read_csv(DATA_DIR / "benchmarking.csv", dtype=str)
except Exception as e:  # noqa: BLE001
    print(f"Could not load benchmarking.csv: {e}")
    bench = pd.DataFrame()

try:
    metrics = pd.read_csv(DATA_DIR / "evaluation_metrics.csv", dtype=str)
    metrics = metrics[metrics["Metric"].notna()].copy()
except Exception as e:  # noqa: BLE001
    print(f"Could not load evaluation_metrics.csv: {e}")
    metrics = pd.DataFrame({"ID": [], "Metric": []})

# ─── Palettes & constants ─────────────────────────────────────────────────────

PAL_TYPE = {"Bulk": "#264653", "Single-cell": "#E9A825", "Spatial": "#3a7ca5"}
PAL_TYPE_TEXT = {"Bulk": "#ffffff", "Single-cell": "#1a1a1a", "Spatial": "#ffffff"}

PAL_CAT = {
    "Joint dimension reduction": "#4EBFD4",
    "Network/knowledge-based": "#F4A261",
    "Deep learning/AI": "#E76F51",
    "Concatenation-based": "#2A9D8F",
}


def cat_color(cat):
    return PAL_CAT.get(cat, "#888888")


# Plotly's default qualitative palette + symbol sequence, used to colour the
# scatter by integration category and shape it by data type (mirrors the R
# plot_ly(color=, symbol=) encoding).
QUAL_COLORS = [
    "#636EFA", "#EF553B", "#00CC96", "#AB63FA", "#FFA15A",
    "#19D3F3", "#FF6692", "#B6E880", "#FF97FF", "#FECB52",
]
TYPE_SYMBOL = {"Bulk": "circle", "Single-cell": "square", "Spatial": "diamond"}


# Filter options derived from data
OPT_TYPES = ["Bulk", "Single-cell", "Spatial"]
OPT_CATS = sorted(methods_all["Integration_category"].dropna().unique().tolist())

_lang_tokens = set()
for _v in methods_all["Language"].dropna():
    for _tok in re.split(r"[;,/\s]+", str(_v)):
        _tok = _tok.strip()
        if _tok:
            _lang_tokens.add(_tok)
OPT_LANGS = sorted(t for t in _lang_tokens if t not in {"", "+", "NA"} and len(t) >= 1)

# ─── Theme ────────────────────────────────────────────────────────────────────
# We deliberately do NOT set a custom bslib/shinyswatch theme: those compile Sass
# at runtime via libsass, which is unavailable in the browser (Pyodide/Shinylive)
# and crashes the app on load. Instead we use the default (precompiled) Bootstrap
# and apply the flatly-inspired brand palette + accents entirely in
# www/custom.css (Bootstrap CSS variables), which needs no compilation.


# ─── UI builders ──────────────────────────────────────────────────────────────


def dl_rows(pairs, dt_class, dd_class):
    items = []
    for label, value in pairs:
        items.append(ui.tags.dt(label, class_=dt_class))
        items.append(ui.tags.dd(value, class_=dd_class))
    return ui.tags.dl(*items, class_="row small mb-3")


def about_left():
    return ui.card_body(
        ui.p(ui.tags.strong("COST Action CA24166"), " — INFLAMomx", class_="lead mb-1"),
        ui.p(
            ui.tags.em(
                "Pan-European Network for Inflammaging: A Multi-omics Integration Approach"
            ),
            class_="text-muted",
        ),
        ui.tags.hr(),
        ui.p(
            "This Method Hub is a living catalogue of multi-omics integration tools, ",
            "benchmarking studies, and evaluation metrics curated by Working Group 2 ",
            "members. It supports ",
            ui.tags.b("Deliverable D2.1"),
            " (month 18): publication on the state of the art and knowledge gaps in ",
            "multi-omics data integration.",
        ),
        ui.h6(
            "WG2 — Integrative Framework of Data Management & Reproducibility Enhancement"
        ),
        ui.p(
            "Main objective: identify best practices for multi-omics data integration, ",
            "ensuring standardization and reproducibility.",
        ),
        ui.h6("Specific objectives addressed"),
        ui.tags.ul(
            ui.tags.li(
                ui.tags.b("RCO4:"),
                " Optimize and standardize protocols and pipelines for multi-omics integration",
            ),
            ui.tags.li(
                ui.tags.b("RCO5:"),
                " Define knowledge gaps and priority areas for implementation into clinical settings",
            ),
        ),
        ui.h6("Inclusion criteria (T2.1)"),
        ui.tags.ol(
            ui.tags.li("Actively maintained"),
            ui.tags.li("Published in peer-reviewed literature"),
            ui.tags.li("Source code publicly available"),
            ui.tags.li("Parameters and usage documented"),
        ),
        ui.p(
            ui.span("PASS", class_="badge bg-success"),
            " — all four criteria met   ",
            ui.span("REVIEW", class_="badge bg-warning text-dark"),
            " — one or more criteria missing or not yet assessed",
            class_="small text-muted mb-0",
        ),
    )


def data_type_card():
    def row(name, desc):
        return ui.p(
            ui.span(
                name,
                class_="badge me-1",
                style=f"background:{PAL_TYPE[name]};color:{PAL_TYPE_TEXT[name]}",
            ),
            desc,
            class_="small mb-0" if name == "Spatial" else "small",
        )

    return ui.card_body(
        row("Bulk", "Bulk tissue / population-level multi-omics"),
        row("Single-cell", "Single-cell or single-nucleus resolution"),
        row("Spatial", "Spatially resolved omics + imaging"),
    )


# ─── UI ───────────────────────────────────────────────────────────────────────

# ─── Methods table: column registry ───────────────────────────────────────────
# One source of truth for the methods table AND its export. Each column has:
#   display(row) -> str       text shown in the grid cell
#   export(row)  -> scalar    clean value for downloads (numbers stay numeric)
#   style(row)   -> dict|None  optional per-cell CSS (badges)


def _num_or_blank(v):
    if pd.isna(v):
        return ""
    if isinstance(v, float) and float(v).is_integer():
        return int(v)
    return v


def _text(field):
    return lambda r: "" if pd.isna(r[field]) else str(r[field])


def _status_text(r):
    return r["Include"] if r["Include"] in ("PASS", "REVIEW") else DASH


def _style_type(r):
    t = r["Data_type"]
    return {
        "background-color": PAL_TYPE.get(t, "#888888"),
        "color": PAL_TYPE_TEXT.get(t, "#ffffff"),
        "font-weight": "500",
        "text-align": "center",
    }


def _style_status(r):
    s = r["Include"]
    if s == "PASS":
        bg, fg = "#2A9D8F", "#ffffff"
    elif s == "REVIEW":
        bg, fg = "#E9C46A", "#1a1a1a"
    else:
        return None
    return {"background-color": bg, "color": fg, "font-weight": "500",
            "text-align": "center"}


# Ordered registry. The first 9 are the default view; the rest are opt-in.
COLUMN_DEFS = [
    {"label": "Type", "display": lambda r: str(r["Data_type"]),
     "export": lambda r: str(r["Data_type"]), "style": _style_type},
    {"label": "Tool", "display": _text("Tool"), "export": _text("Tool")},
    {"label": "Category", "display": _text("Integration_category"),
     "export": _text("Integration_category")},
    {"label": "Supervised?", "display": _text("Integration_type"),
     "export": _text("Integration_type")},
    {"label": "Omics layers", "display": _text("Omics_layers"),
     "export": _text("Omics_layers")},
    {"label": "Language", "display": _text("Language"), "export": _text("Language")},
    {"label": "Doc ★", "display": lambda r: star_rating(r["Doc_quality"]),
     "export": lambda r: _num_or_blank(r["Doc_quality"])},
    {"label": "UX ★", "display": lambda r: star_rating(r["Usability"]),
     "export": lambda r: _num_or_blank(r["Usability"])},
    {"label": "Status", "display": _status_text,
     "export": lambda r: (r["Include"] if r["Include"] in ("PASS", "REVIEW") else ""),
     "style": _style_status},
    {"label": "Technologies", "display": _text("Technologies"),
     "export": _text("Technologies")},
    {"label": "Underlying method", "display": _text("Underlying_method"),
     "export": _text("Underlying_method")},
    {"label": "Install via", "display": _text("Installation_source"),
     "export": _text("Installation_source")},
    {"label": "Maintenance", "display": _text("Maintenance_status"),
     "export": _text("Maintenance_status")},
    {"label": "Citations", "display": lambda r: str(_num_or_blank(r["Citation_count"])),
     "export": lambda r: _num_or_blank(r["Citation_count"])},
    {"label": "Benchmarked in", "display": _text("Benchmarked_in"),
     "export": _text("Benchmarked_in")},
    {"label": "Preprocessing", "display": _text("Preprocessing_steps"),
     "export": _text("Preprocessing_steps")},
    {"label": "Input formats", "display": _text("Input_formats"),
     "export": _text("Input_formats")},
    {"label": "Output formats", "display": _text("Output_formats"),
     "export": _text("Output_formats")},
    {"label": "Best for", "display": _text("Best_for"), "export": _text("Best_for")},
    {"label": "Paper / DOI", "display": _text("Paper_DOI"),
     "export": _text("Paper_DOI")},
    {"label": "Link", "display": _text("Link"), "export": _text("Link")},
    {"label": "Actively maintained", "display": _text("Actively_maintained"),
     "export": _text("Actively_maintained")},
    {"label": "Published", "display": _text("Published"),
     "export": _text("Published")},
    {"label": "Code available", "display": _text("Code_available"),
     "export": _text("Code_available")},
    {"label": "Params documented", "display": _text("Parameters_documented"),
     "export": _text("Parameters_documented")},
]

COLUMNS = {c["label"]: c for c in COLUMN_DEFS}
ALL_COLS = [c["label"] for c in COLUMN_DEFS]
DEFAULT_COLS = [
    "Type", "Tool", "Category", "Supervised?", "Omics layers",
    "Language", "Doc ★", "UX ★", "Status",
]


def _resolve_columns(columns):
    """Selected labels reordered to canonical order; fall back to defaults."""
    if not columns:
        return DEFAULT_COLS
    chosen = set(columns)
    ordered = [c for c in ALL_COLS if c in chosen]
    return ordered or DEFAULT_COLS


def build_methods_grid(df, columns=None):
    labels = _resolve_columns(columns)

    if df.shape[0] == 0:
        disp = pd.DataFrame({lab: pd.Series(dtype="object") for lab in labels})
        return render.DataGrid(disp, selection_mode="row", filters=True,
                               height="640px", width="100%")

    disp = pd.DataFrame(
        {lab: df.apply(COLUMNS[lab]["display"], axis=1) for lab in labels}
    )

    styles = []
    for ci, lab in enumerate(labels):
        style_fn = COLUMNS[lab].get("style")
        if style_fn is None:
            continue
        for ri in range(df.shape[0]):
            st = style_fn(df.iloc[ri])
            if st:
                styles.append({"rows": [ri], "cols": [ci], "style": st})

    return render.DataGrid(
        disp,
        selection_mode="row",
        filters=True,
        styles=styles,
        height="640px",
        width="100%",
    )


def methods_export_df(df, columns=None):
    """Clean-value DataFrame for download: selected columns over the given rows."""
    labels = _resolve_columns(columns)
    if df.shape[0] == 0:
        return pd.DataFrame({lab: pd.Series(dtype="object") for lab in labels})
    return pd.DataFrame(
        {lab: df.apply(COLUMNS[lab]["export"], axis=1) for lab in labels}
    )


# ─── Export helpers (CSV / TSV / JSON — no extra dependencies) ─────────────────

EXPORT_FORMATS = ["CSV", "TSV", "JSON"]
_EXPORT_EXT = {"CSV": "csv", "TSV": "tsv", "JSON": "json"}

# Columns shown (and exported) for the Benchmarking and Evaluation-metrics tables.
BENCH_COLS = [
    "Benchmark / framework", "Type", "Data modality",
    "Tissue / disease compared", "Language", "Maintenance status",
    "Link", "Paper link / DOI",
]
METRIC_COLS = [
    "ID", "Metric", "Category / applies to", "What it measures",
    "Objective / Subjective", "Tools / packages (Python | R)",
    "Reference (definition paper / DOI)",
]


def table_to_text(df, fmt):
    if fmt == "TSV":
        return df.to_csv(index=False, sep="\t")
    if fmt == "JSON":
        return df.to_json(orient="records", indent=2, force_ascii=False)
    return df.to_csv(index=False)  # CSV (default)


def export_filename(stem, fmt):
    return f"inflahub_{stem}_{date.today().isoformat()}.{_EXPORT_EXT.get(fmt, 'csv')}"


def export_toolbar(select_id, button_id, extra_class=""):
    """Compact format-select + download button used above each table."""
    return ui.div(
        ui.input_select(select_id, None, choices=EXPORT_FORMATS, width="86px"),
        ui.download_button(button_id, "Export",
                           class_="btn btn-sm btn-outline-primary"),
        class_=f"d-flex align-items-center gap-2 {extra_class}".strip(),
    )


app_ui = ui.page_navbar(
    # ── Tab 1 – Method Explorer ──────────────────────────────────────────────
    ui.nav_panel(
        "Method Explorer",
        ui.layout_sidebar(
            ui.sidebar(
                ui.input_selectize(
                    "f_type", "Data type", choices=OPT_TYPES, selected=OPT_TYPES,
                    multiple=True, options={"plugins": ["remove_button"]},
                ),
                ui.input_selectize(
                    "f_cat", "Integration category", choices=OPT_CATS, selected=OPT_CATS,
                    multiple=True, options={"plugins": ["remove_button"]},
                ),
                ui.input_selectize(
                    "f_lang", "Language", choices=OPT_LANGS, selected=OPT_LANGS,
                    multiple=True, options={"plugins": ["remove_button"]},
                ),
                ui.input_switch("f_pass", "PASS inclusion only", value=False),
                ui.tags.hr(class_="my-3"),
                ui.input_selectize(
                    "f_cols", "Columns", choices=ALL_COLS, selected=DEFAULT_COLS,
                    multiple=True, options={"plugins": ["remove_button"]},
                ),
                ui.tags.hr(class_="my-3"),
                ui.p(
                    faicons.icon_svg("circle-info"),
                    " Click any row to view full details.",
                    class_="small text-muted mb-0",
                ),
                width="268px",
                bg="#f8f9fa",
            ),
            ui.card(
                ui.card_header(
                    "Tools",
                    ui.span(
                        ui.output_text("n_tools_label", inline=True),
                        class_="badge bg-secondary",
                    ),
                    export_toolbar("methods_fmt", "dl_methods", extra_class="ms-auto"),
                    class_="d-flex align-items-center gap-2",
                ),
                ui.output_data_frame("tbl_methods"),
                full_screen=True,
            ),
        ),
        icon=faicons.icon_svg("table"),
    ),
    # ── Tab 2 – Visual Overview ──────────────────────────────────────────────
    ui.nav_panel(
        "Visual Overview",
        ui.layout_columns(
            ui.card(
                ui.card_header("Quality landscape"),
                ui.card_body(
                    output_widget("plt_scatter", height="360px"),
                    ui.p(
                        "x = documentation quality · y = usability (1–5 scale)",
                        class_="text-muted small text-center mt-1 mb-0",
                    ),
                    class_="p-1",
                ),
            ),
            ui.card(
                ui.card_header("Tools by integration category"),
                ui.card_body(output_widget("plt_bar", height="360px"), class_="p-1"),
            ),
            col_widths=[6, 6],
        ),
        ui.card(
            ui.card_header("Omics layer coverage per tool"),
            ui.card_body(output_widget("plt_heatmap", height="400px"), class_="p-1"),
        ),
        icon=faicons.icon_svg("chart-bar"),
    ),
    # ── Tab 3 – Benchmarking & Metrics ───────────────────────────────────────
    ui.nav_panel(
        "Benchmarking & Metrics",
        ui.navset_card_underline(
            ui.nav_panel(
                "Benchmark studies",
                export_toolbar("bench_fmt", "dl_bench",
                               extra_class="justify-content-end mb-2"),
                ui.output_data_frame("tbl_bench"),
            ),
            ui.nav_panel(
                "Evaluation metrics",
                export_toolbar("metrics_fmt", "dl_metrics",
                               extra_class="justify-content-end mb-2"),
                ui.output_data_frame("tbl_metrics"),
            ),
        ),
        icon=faicons.icon_svg("flask"),
    ),
    # ── Tab 4 – About ────────────────────────────────────────────────────────
    ui.nav_panel(
        "About",
        ui.layout_columns(
            ui.card(ui.card_header("About this hub"), about_left()),
            ui.div(
                ui.card(
                    ui.card_header("Catalogue stats"),
                    ui.card_body(ui.output_ui("about_stats")),
                ),
                ui.card(
                    ui.card_header("Data types"),
                    data_type_card(),
                    class_="mt-3",
                ),
            ),
            col_widths=[8, 4],
        ),
        icon=faicons.icon_svg("circle-info"),
    ),
    ui.nav_spacer(),
    ui.nav_control(
        ui.tags.a(
            faicons.icon_svg("github"),
            " GitHub",
            href="https://github.com/INFLAMomx/INFLAhub",
            target="_blank",
            class_="nav-link px-2",
        )
    ),
    title=ui.span(
        ui.tags.img(
            src="logo.svg",
            height="24px",
            style="margin-right:8px; vertical-align:middle;",
            onerror="this.style.display='none'",
        ),
        "INFLAMomx · WG2 Method Hub",
    ),
    window_title="WG2 Method Hub | INFLAMomx CA24166",
    header=ui.head_content(ui.tags.link(rel="stylesheet", href="custom.css")),
    id="page",
)


# ─── Figure / table / modal builders ──────────────────────────────────────────
# Pure functions (no reactivity) so they can be unit-tested directly; the server
# render functions are thin wrappers around these.


def build_modal(r):
    dtype = r["Data_type"]

    left = ui.column(
        6,
        ui.h6("Classification", class_="text-muted text-uppercase small fw-bold mb-2"),
        dl_rows(
            [
                ("Category", val(r["Integration_category"])),
                ("Integration type", val(r["Integration_type"])),
                ("Omics layers", val(r["Omics_layers"])),
                ("Technologies", val(r["Technologies"])),
                ("Underlying method", val(r["Underlying_method"])),
                ("Language", val(r["Language"])),
                ("Install via", val(r["Installation_source"])),
                ("Maintenance", val(r["Maintenance_status"])),
                ("Citations", val(r["Citation_count"])),
                ("Benchmarked in", val(r["Benchmarked_in"])),
            ],
            "col-5 text-muted",
            "col-7",
        ),
    )

    right = ui.column(
        6,
        ui.h6("Quality & Inclusion", class_="text-muted text-uppercase small fw-bold mb-2"),
        dl_rows(
            [
                ("Documentation (1–5)", star_rating(r["Doc_quality"])),
                ("Usability (1–5)", star_rating(r["Usability"])),
                ("Actively maintained", yn_badge(val(r["Actively_maintained"]))),
                ("Published", yn_badge(val(r["Published"]))),
                ("Code available", yn_badge(val(r["Code_available"]))),
                ("Params documented", yn_badge(val(r["Parameters_documented"]))),
                ("Inclusion status", status_badge(val(r["Include"]))),
            ],
            "col-6 text-muted",
            "col-6",
        ),
    )

    def nonempty(x):
        return (not pd.isna(x)) and str(x).strip() != ""

    narrative = []
    if nonempty(r["Use_case"]):
        narrative += [
            ui.tags.hr(class_="my-2"),
            ui.h6("Use case"),
            ui.p(str(r["Use_case"]), class_="small"),
        ]
    if nonempty(r["Strengths"]):
        if not nonempty(r["Use_case"]):
            narrative.append(ui.tags.hr(class_="my-2"))
        narrative += [ui.h6("Strengths"), ui.p(str(r["Strengths"]), class_="small")]
    if nonempty(r["Limitations"]):
        narrative += [ui.h6("Limitations"), ui.p(str(r["Limitations"]), class_="small")]
    if nonempty(r["Best_for"]):
        narrative += [
            ui.h6("Best for"),
            ui.p(str(r["Best_for"]), class_="small text-muted"),
        ]
    if nonempty(r["Preprocessing_steps"]):
        narrative += [
            ui.h6("Preprocessing steps"),
            ui.p(str(r["Preprocessing_steps"]), class_="small text-muted"),
        ]

    buttons = [
        b
        for b in (
            link_btn(val(r["Link"]), "Homepage / repo",
                     "arrow-up-right-from-square", "btn-outline-primary"),
            link_btn(val(r["Paper_DOI"]), "Paper / DOI",
                     "file-lines", "btn-outline-secondary"),
        )
        if b is not None
    ]

    return ui.modal(
        ui.row(left, right),
        *narrative,
        ui.tags.hr(class_="my-2"),
        ui.div(*buttons, class_="d-flex flex-wrap gap-2"),
        title=ui.TagList(
            ui.span(
                dtype,
                class_="badge me-2 align-middle",
                style=(
                    f"background:{PAL_TYPE.get(dtype, '#888888')};"
                    f"color:{PAL_TYPE_TEXT.get(dtype, '#ffffff')};font-size:0.75rem"
                ),
            ),
            str(r["Tool"]),
        ),
        size="xl",
        easy_close=True,
        footer=ui.modal_button("Close"),
    )


def scatter_fig():
    df = methods_all[
        methods_all["Doc_quality"].notna() | methods_all["Usability"].notna()
    ].copy()

    if df.shape[0] == 0:
        fig = go.Figure()
        fig.add_annotation(
            text=(
                "<b>No quality scores yet</b><br>"
                "<span style='font-size:12px'>Add Doc quality & Usability "
                "columns to see tools plotted here.</span>"
            ),
            xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            font=dict(size=13, color="#6c757d"),
        )
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#f8f9fa")
        return fig

    rng = np.random.default_rng(42)
    df["doc_jit"] = df["Doc_quality"] + rng.uniform(-0.12, 0.12, len(df))
    df["ux_jit"] = df["Usability"] + rng.uniform(-0.12, 0.12, len(df))
    df["cat"] = df["Integration_category"].fillna(DASH)

    def mk_label(row):
        num = lambda v: str(int(v)) if not pd.isna(v) else DASH  # noqa: E731
        txt = lambda v: str(v) if not pd.isna(v) else DASH  # noqa: E731
        return (
            f"<b>{row['Tool']}</b><br>"
            f"Category: {txt(row['Integration_category'])}<br>"
            f"Type: {row['Data_type']}<br>"
            f"Language: {txt(row['Language'])}<br>"
            f"Doc: {num(row['Doc_quality'])} | UX: {num(row['Usability'])}"
        )

    df["label"] = df.apply(mk_label, axis=1)

    cats = sorted(df["cat"].unique())
    color_map = {c: QUAL_COLORS[i % len(QUAL_COLORS)] for i, c in enumerate(cats)}

    fig = go.Figure()
    for (cat, dtype), g in df.groupby(["cat", "Data_type"]):
        fig.add_trace(
            go.Scatter(
                x=g["doc_jit"], y=g["ux_jit"], mode="markers",
                name=f"{cat} · {dtype}", legendgroup=cat,
                marker=dict(
                    size=14, opacity=0.85, color=color_map[cat],
                    symbol=TYPE_SYMBOL.get(dtype, "circle"),
                    line=dict(color="white", width=1.5),
                ),
                customdata=g[["label"]].to_numpy(),
                hovertemplate="%{customdata[0]}<extra></extra>",
            )
        )
    fig.update_layout(
        xaxis=dict(title="Documentation quality", range=[0.5, 5.5],
                   tickvals=[1, 2, 3, 4, 5], zeroline=False, gridcolor="#dee2e6"),
        yaxis=dict(title="Usability", range=[0.5, 5.5],
                   tickvals=[1, 2, 3, 4, 5], zeroline=False, gridcolor="#dee2e6"),
        legend=dict(orientation="h", y=-0.35, font=dict(size=10), title_text=""),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#f8f9fa",
        margin=dict(t=10, b=10, l=50, r=10),
    )
    return fig


def bar_fig():
    d = (
        methods_all.groupby(["Data_type", "Integration_category"], dropna=False)
        .size()
        .reset_index(name="n")
    )
    d["cat_wrap"] = d["Integration_category"].map(lambda s: _wrap(s, 26))

    fig = go.Figure()
    for dtype in OPT_TYPES:
        sub = d[d["Data_type"] == dtype]
        fig.add_trace(
            go.Bar(
                x=sub["n"], y=sub["cat_wrap"], orientation="h", name=dtype,
                marker_color=PAL_TYPE[dtype],
                text=sub["n"], textposition="inside", insidetextanchor="middle",
                hovertemplate="<b>%{y}</b><br>" + dtype + ": %{x}<extra></extra>",
            )
        )
    fig.update_yaxes(categoryorder="total ascending")
    fig.update_layout(
        barmode="stack",
        xaxis=dict(title="Number of tools", dtick=1, zeroline=False,
                   gridcolor="#dee2e6"),
        yaxis=dict(title="", automargin=True),
        legend=dict(orientation="h", y=-0.18, font=dict(size=10), title_text=""),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#f8f9fa",
        margin=dict(t=10, b=10, l=10, r=10),
    )
    return fig


def heatmap_fig():
    expanded = _omics_matrix()
    if expanded.empty:
        fig = go.Figure()
        fig.update_layout(title="No omics layer data", paper_bgcolor="rgba(0,0,0,0)")
        return fig

    mat = (
        expanded.assign(present=1)
        .pivot_table(index="Tool", columns="Layer", values="present",
                     aggfunc="max", fill_value=0)
        .sort_index()
    )
    layer_freq = mat.sum(axis=0).sort_values(ascending=False)
    layers_vec = list(layer_freq.index)
    z = mat[layers_vec].values

    fig = go.Figure(
        go.Heatmap(
            z=z, x=layers_vec, y=list(mat.index),
            colorscale=[[0, "#f1f3f5"], [1, "#264653"]],
            showscale=False, xgap=2, ygap=2,
            hovertemplate="<b>%{y}</b><br>%{x}: %{z}<extra></extra>",
        )
    )
    fig.update_layout(
        xaxis=dict(tickangle=-35, automargin=True, title="", tickfont=dict(size=11)),
        yaxis=dict(automargin=True, title="", tickfont=dict(size=11)),
        margin=dict(l=20, r=20, t=10, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ─── Server ───────────────────────────────────────────────────────────────────


def server(input, output, session):

    # ── Reactive: filtered data ──────────────────────────────────────────────
    @reactive.calc
    def filt():
        df = methods_all
        if input.f_type():
            df = df[df["Data_type"].isin(input.f_type())]
        if input.f_cat():
            df = df[df["Integration_category"].isin(input.f_cat())]
        if input.f_lang():
            pattern = "|".join(re.escape(t) for t in input.f_lang())
            df = df[df["Language"].fillna("").str.contains(pattern, regex=True)]
        if input.f_pass():
            df = df[df["Include"].fillna("") == "PASS"]
        return df.reset_index(drop=True)

    @render.text
    def n_tools_label():
        n = filt().shape[0]
        return f"{n} tool" + ("s" if n != 1 else "")

    # ── Methods table ────────────────────────────────────────────────────────
    @reactive.calc
    def selected_columns():
        return _resolve_columns(list(input.f_cols() or []))

    @render.data_frame
    def tbl_methods():
        return build_methods_grid(filt(), selected_columns())

    @render.download(
        filename=lambda: export_filename("methods", input.methods_fmt())
    )
    def dl_methods():
        df = methods_export_df(filt(), selected_columns())
        yield table_to_text(df, input.methods_fmt())

    # ── Row click → detail modal ─────────────────────────────────────────────
    @reactive.effect
    @reactive.event(input.tbl_methods_cell_selection)
    def _show_detail():
        sel = input.tbl_methods_cell_selection()
        rows = sel.get("rows", ()) if sel else ()
        if not rows:
            return
        with reactive.isolate():
            df = filt()
        idx = list(rows)[0]
        if idx >= df.shape[0]:
            return
        r = df.iloc[idx]
        ui.modal_show(build_modal(r))

    # ── Visual Overview plots ────────────────────────────────────────────────
    @render_widget
    def plt_scatter():
        return scatter_fig()

    @render_widget
    def plt_bar():
        return bar_fig()

    @render_widget
    def plt_heatmap():
        return heatmap_fig()

    # ── Benchmarking table ───────────────────────────────────────────────────
    def _bench_view():
        return bench[[c for c in BENCH_COLS if c in bench.columns]]

    @render.data_frame
    def tbl_bench():
        if bench.shape[0] == 0:
            return render.DataGrid(
                pd.DataFrame({"Message": ["No benchmarking data loaded."]})
            )
        return render.DataGrid(_bench_view(), width="100%", height="560px")

    @render.download(
        filename=lambda: export_filename("benchmarking", input.bench_fmt())
    )
    def dl_bench():
        df = _bench_view() if bench.shape[0] else bench
        yield table_to_text(df, input.bench_fmt())

    # ── Evaluation metrics table ─────────────────────────────────────────────
    def _metrics_view():
        return metrics[[c for c in METRIC_COLS if c in metrics.columns]]

    @render.data_frame
    def tbl_metrics():
        if metrics.shape[0] == 0:
            return render.DataGrid(
                pd.DataFrame({"Message": ["No metrics data loaded."]})
            )
        return render.DataGrid(_metrics_view(), width="100%", height="560px")

    @render.download(
        filename=lambda: export_filename("evaluation_metrics", input.metrics_fmt())
    )
    def dl_metrics():
        df = _metrics_view() if metrics.shape[0] else metrics
        yield table_to_text(df, input.metrics_fmt())

    # ── About stats ──────────────────────────────────────────────────────────
    @render.ui
    def about_stats():
        inc = methods_all["Include"].fillna("")
        n_all = int(methods_all.shape[0])
        n_pass = int((inc == "PASS").sum())
        n_review = int((inc == "REVIEW").sum())
        n_bench = int(bench.shape[0])
        n_met = int(metrics.shape[0])
        n_bulk = int((methods_all["Data_type"] == "Bulk").sum())
        n_sc = int((methods_all["Data_type"] == "Single-cell").sum())
        n_spa = int((methods_all["Data_type"] == "Spatial").sum())

        def stat(n, label, color):
            return ui.div(
                ui.div(
                    str(n),
                    class_="fw-bold fs-4",
                    style=f"color:{color}; min-width:2rem; text-align:right",
                ),
                ui.div(label, class_="small text-muted lh-sm"),
                class_="stat-card d-flex align-items-center gap-3 p-2 mb-2 rounded",
                style=f"border-left:4px solid {color}; background:#f8f9fa",
            )

        return ui.TagList(
            stat(n_all, "tools catalogued", "#264653"),
            stat(n_pass, "meet all inclusion criteria", "#2A9D8F"),
            stat(n_review, "under review / incomplete", "#E9A825"),
            stat(n_bench, "benchmark studies", "#F4A261"),
            stat(n_met, "evaluation metrics", "#4EBFD4"),
            ui.tags.hr(class_="my-2"),
            ui.div(
                ui.span(ui.tags.b(str(n_bulk)), " Bulk"),
                ui.span(ui.tags.b(str(n_sc)), " Single-cell"),
                ui.span(ui.tags.b(str(n_spa)), " Spatial"),
                class_="d-flex justify-content-between small text-muted px-1",
            ),
        )


# ─── Module-level data transforms (shared by plots) ───────────────────────────

# Canonical layer names mapped from raw text (insertion order matters)
LAYER_MAP = {
    "Transcriptomics": r"RNA|rna|transcript|mRNA|snRNA|scRNA",
    "Chromatin access.": r"ATAC|chromatin|access",
    "Methylation": r"methylat|epigenom|snmC|DNA.methyl",
    "Proteomics": r"protein|proteom",
    "Metabolomics": r"metabol",
    "Spatial": r"spatial|Visium|[Ss][Tt](?!AL|AI)",
    "Metagenomics": r"microbiom|metagenom",
    "Imaging/Histology": r"imaging|histol|H.?E|morphology|MSI|MALDI|DESI",
    "CNV": r"CNV|copy.?number",
    "miRNA": r"miRNA",
    "Mutation/Variant": r"mutation|variant",
    "CITE-seq": r"CITE|cite.seq",
}


def _norm_layer(x):
    for nm, pat in LAYER_MAP.items():
        if re.search(pat, x, flags=re.IGNORECASE):
            return nm
    return x.strip()


def _omics_matrix():
    records = []
    for _, row in methods_all.iterrows():
        layers = row["Omics_layers"]
        if pd.isna(layers):
            continue
        for part in re.split(r"[;,+]+", str(layers)):
            part = part.strip()
            if not part:
                continue
            layer = _norm_layer(part)
            if len(layer) >= 2:
                records.append((row["Tool"], layer))
    return pd.DataFrame(records, columns=["Tool", "Layer"]).drop_duplicates()


def _wrap(s, width):
    if pd.isna(s):
        s = DASH
    wrapped = "<br>".join(textwrap.wrap(str(s), width=width))
    return wrapped if wrapped else str(s)


app = App(app_ui, server, static_assets=APP_DIR / "www")
