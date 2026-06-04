# ─────────────────────────────────────────────────────────────────────────────
# INFLAMomx · WG2 Method Hub
# COST Action CA24166 — Multi-omics Integration Methods
# Deliverable D2.1 (month 18)
# ─────────────────────────────────────────────────────────────────────────────

suppressPackageStartupMessages({
  library(shiny)
  library(bslib)
  library(DT)
  library(plotly)
  library(readxl)
  library(dplyr)
  library(tidyr)
  library(stringr)
  library(shinyWidgets)
})

# ─── Helpers ──────────────────────────────────────────────────────────────────

# Return first non-empty value or a dash placeholder
val <- function(x) {
  x <- x[[1]]
  if (length(x) == 0 || is.na(x) || x == "") "—" else as.character(x)
}

star_rating <- function(n, max_n = 5) {
  n <- suppressWarnings(as.integer(n[[1]]))
  if (is.na(n) || n < 1 || n > max_n) return("—")
  paste0(strrep("★", n), strrep("☆", max_n - n))
}

yn_badge <- function(x) {
  switch(as.character(x),
    "Y" = tags$span(class = "badge bg-success",             "Yes"),
    "N" = tags$span(class = "badge bg-danger",              "No"),
          tags$span(class = "badge bg-secondary opacity-75", "—")
  )
}

status_badge <- function(x) {
  switch(as.character(x),
    "PASS"   = tags$span(class = "badge bg-success",              "PASS"),
    "REVIEW" = tags$span(class = "badge bg-warning text-dark",    "REVIEW"),
               tags$span(class = "badge bg-secondary opacity-75", "—")
  )
}

link_btn <- function(href, label, icon_name, class = "btn-outline-primary") {
  if (is.na(href) || href == "") return(NULL)
  tags$a(
    class = paste("btn btn-sm", class),
    href = href, target = "_blank", rel = "noopener noreferrer",
    icon(icon_name), " ", label
  )
}

# ─── Data loading ──────────────────────────────────────────────────────────────

XLSX <- "data/Method_hub_WG2.xlsx"

METHOD_COLS <- c(
  "Assigned_to", "Tool", "Integration_category", "Link",
  "Use_case", "Integration_type", "Omics_layers",
  "Strengths", "Limitations", "Best_for", "Study_examples",
  "Paper_DOI", "Citation_count", "Benchmarked_in",
  "Installation_source", "Doc_quality", "Usability",
  "Maintenance_status", "Language", "Input_formats",
  "Input_details", "Output_formats", "Underlying_method",
  "Actively_maintained", "Published", "Code_available",
  "Parameters_documented", "Include_raw"
)

read_methods <- function(sheet, type_label) {
  tryCatch({
    df <- read_excel(XLSX, sheet = sheet, skip = 3,
                     col_names = METHOD_COLS, col_types = "text")
    df %>%
      filter(!is.na(Tool), nchar(trimws(Tool)) > 0) %>%
      mutate(
        Data_type      = type_label,
        Doc_quality    = suppressWarnings(as.numeric(Doc_quality)),
        Usability      = suppressWarnings(as.numeric(Usability)),
        Citation_count = suppressWarnings(as.numeric(Citation_count)),
        # Recompute inclusion from Y/N criteria (more reliable than cached formula)
        Include = case_when(
          coalesce(Actively_maintained, "") == "Y" &
            coalesce(Published, "")            == "Y" &
            coalesce(Code_available, "")       == "Y" &
            coalesce(Parameters_documented, "") == "Y" ~ "PASS",
          !is.na(Actively_maintained) | !is.na(Published) |
            !is.na(Code_available) | !is.na(Parameters_documented) ~ "REVIEW",
          TRUE ~ NA_character_
        )
      )
  }, error = function(e) {
    warning("Could not load sheet '", sheet, "': ", conditionMessage(e))
    tibble()
  })
}

methods_all <- bind_rows(
  read_methods("Bulk methods",        "Bulk"),
  read_methods("Single-cell methods", "Single-cell"),
  read_methods("Spatial methods",     "Spatial")
)

bench <- tryCatch({
  df <- read_excel(XLSX, sheet = "Benchmarking", skip = 1, col_types = "text")
  df %>% filter(!is.na(df[[2]]))
}, error = function(e) tibble())

metrics <- tryCatch({
  df <- read_excel(XLSX, sheet = "Evaluation metrics", skip = 1, col_types = "text")
  df <- df %>% filter(!is.na(Metric))
  names(df)[1] <- "ID"
  df
}, error = function(e) tibble(ID = character(), Metric = character()))

# ─── Palettes & constants ─────────────────────────────────────────────────────

PAL_TYPE <- c(
  "Bulk"        = "#264653",
  "Single-cell" = "#E9A825",
  "Spatial"     = "#3a7ca5"
)
PAL_TYPE_TEXT <- c(
  "Bulk"        = "#ffffff",
  "Single-cell" = "#1a1a1a",
  "Spatial"     = "#ffffff"
)

PAL_CAT <- c(
  "Joint dimension reduction" = "#4EBFD4",
  "Network/knowledge-based"   = "#F4A261",
  "Deep learning/AI"          = "#E76F51",
  "Concatenation-based"       = "#2A9D8F"
)

cat_color <- function(cat) {
  unname(ifelse(cat %in% names(PAL_CAT), PAL_CAT[cat], "#888888"))
}

# Filter options derived from data
OPT_TYPES <- c("Bulk", "Single-cell", "Spatial")
OPT_CATS  <- sort(unique(na.omit(methods_all$Integration_category)))
OPT_LANGS <- sort(setdiff(
  unique(na.omit(trimws(unlist(str_split(methods_all$Language, "[;,/\\s]+"))))),
  c("", "+", "NA")
))
OPT_LANGS <- OPT_LANGS[nchar(OPT_LANGS) >= 1]

# ─── Theme ────────────────────────────────────────────────────────────────────

APP_THEME <- bs_theme(
  preset      = "flatly",
  primary     = "#264653",
  secondary   = "#4EBFD4",
  success     = "#2A9D8F",
  warning     = "#E9C46A",
  danger      = "#E76F51",
  info        = "#3a7ca5",
  font_scale  = 0.94,
  `navbar-bg` = "#264653",
  `navbar-fg` = "#ffffff"
)

# ─── UI ───────────────────────────────────────────────────────────────────────

ui <- page_navbar(
  title        = tags$span(
    tags$img(src = "logo.svg", height = "24px", style = "margin-right:8px; vertical-align:middle;",
             onerror = "this.style.display='none'"),
    "INFLAMomx · WG2 Method Hub"
  ),
  theme        = APP_THEME,
  window_title = "WG2 Method Hub | INFLAMomx CA24166",
  header       = tags$head(tags$link(rel = "stylesheet", href = "custom.css")),

  # ────────────────────────────────────────────────────────────────────────────
  # Tab 1 – Method Explorer
  # ────────────────────────────────────────────────────────────────────────────
  nav_panel("Method Explorer", icon = icon("table"),

    layout_sidebar(
      sidebar = sidebar(
        width = 268, open = "open",
        bg    = "#f8f9fa",

        pickerInput("f_type", "Data type",
          choices  = OPT_TYPES,
          selected = OPT_TYPES,
          multiple = TRUE,
          options  = pickerOptions(
            actionsBox          = TRUE,
            selectedTextFormat  = "count > 1",
            countSelectedText   = "{0} of {1} selected",
            style               = "btn-sm btn-outline-secondary"
          )
        ),

        pickerInput("f_cat", "Integration category",
          choices  = OPT_CATS,
          selected = OPT_CATS,
          multiple = TRUE,
          options  = pickerOptions(
            actionsBox          = TRUE,
            liveSearch          = TRUE,
            selectedTextFormat  = "count > 1",
            countSelectedText   = "{0} of {1} selected",
            style               = "btn-sm btn-outline-secondary"
          )
        ),

        pickerInput("f_lang", "Language",
          choices  = OPT_LANGS,
          selected = OPT_LANGS,
          multiple = TRUE,
          options  = pickerOptions(
            actionsBox          = TRUE,
            selectedTextFormat  = "count > 1",
            style               = "btn-sm btn-outline-secondary"
          )
        ),

        div(class = "d-flex align-items-center gap-2 mt-1",
          switchInput("f_pass", label = NULL, value = FALSE,
            onLabel = "Yes", offLabel = "No",
            onStatus = "success", size = "small"),
          span("PASS inclusion only", class = "small")
        ),

        hr(class = "my-3"),

        p(class = "small text-muted mb-0",
          icon("circle-info"), " Click any row to view full details.")
      ),

      card(
        full_screen = TRUE,
        card_header(
          class = "d-flex align-items-center gap-2",
          "Tools",
          span(textOutput("n_tools_label", inline = TRUE),
               class = "badge bg-secondary")
        ),
        DTOutput("tbl_methods")
      )
    )
  ),

  # ────────────────────────────────────────────────────────────────────────────
  # Tab 2 – Visual Overview
  # ────────────────────────────────────────────────────────────────────────────
  nav_panel("Visual Overview", icon = icon("chart-bar"),

    layout_columns(
      col_widths = c(6, 6),

      card(
        card_header("Quality landscape"),
        card_body(class = "p-1",
          plotlyOutput("plt_scatter", height = "360px"),
          p(class = "text-muted small text-center mt-1 mb-0",
            "x = documentation quality · y = usability (1–5 scale)")
        )
      ),

      card(
        card_header("Tools by integration category"),
        card_body(class = "p-1",
          plotlyOutput("plt_bar", height = "360px")
        )
      )
    ),

    card(
      card_header("Omics layer coverage per tool"),
      card_body(class = "p-1",
        plotlyOutput("plt_heatmap", height = "400px")
      )
    )
  ),

  # ────────────────────────────────────────────────────────────────────────────
  # Tab 3 – Benchmarking & Metrics
  # ────────────────────────────────────────────────────────────────────────────
  nav_panel("Benchmarking & Metrics", icon = icon("flask"),

    navset_card_underline(
      nav_panel("Benchmark studies",  DTOutput("tbl_bench")),
      nav_panel("Evaluation metrics", DTOutput("tbl_metrics"))
    )
  ),

  # ────────────────────────────────────────────────────────────────────────────
  # Tab 4 – About
  # ────────────────────────────────────────────────────────────────────────────
  nav_panel("About", icon = icon("circle-info"),

    layout_columns(
      col_widths = c(8, 4),

      card(
        card_header("About this hub"),
        card_body(
          tags$p(class = "lead mb-1",
            tags$strong("COST Action CA24166"), " — INFLAMomx"),
          tags$p(class = "text-muted",
            tags$em("Pan-European Network for Inflammaging: A Multi-omics Integration Approach")),
          hr(),
          tags$p(
            "This Method Hub is a living catalogue of multi-omics integration tools, benchmarking studies,",
            "and evaluation metrics curated by Working Group 2 members. It supports ",
            tags$b("Deliverable D2.1"), " (month 18): publication on the state of the art and",
            "knowledge gaps in multi-omics data integration."
          ),
          tags$h6("WG2 — Integrative Framework of Data Management & Reproducibility Enhancement"),
          tags$p("Main objective: identify best practices for multi-omics data integration,",
                 "ensuring standardization and reproducibility."),
          tags$h6("Specific objectives addressed"),
          tags$ul(
            tags$li(tags$b("RCO4:"), " Optimize and standardize protocols and pipelines for multi-omics integration"),
            tags$li(tags$b("RCO5:"), " Define knowledge gaps and priority areas for implementation into clinical settings")
          ),
          tags$h6("Inclusion criteria (T2.1)"),
          tags$ol(
            tags$li("Actively maintained"),
            tags$li("Published in peer-reviewed literature"),
            tags$li("Source code publicly available"),
            tags$li("Parameters and usage documented")
          ),
          tags$p(class = "small text-muted mb-0",
            tags$span(class = "badge bg-success", "PASS"), " — all four criteria met   ",
            tags$span(class = "badge bg-warning text-dark", "REVIEW"), " — one or more criteria missing or not yet assessed"
          )
        )
      ),

      tagList(
        card(
          card_header("Catalogue stats"),
          card_body(uiOutput("about_stats"))
        ),
        card(
          class = "mt-3",
          card_header("Data types"),
          card_body(
            p(class = "small",
              tags$span(class = "badge me-1",
                style = sprintf("background:%s;color:%s",
                                PAL_TYPE["Bulk"], PAL_TYPE_TEXT["Bulk"]), "Bulk"),
              "Bulk tissue / population-level multi-omics"),
            p(class = "small",
              tags$span(class = "badge me-1",
                style = sprintf("background:%s;color:%s",
                                PAL_TYPE["Single-cell"], PAL_TYPE_TEXT["Single-cell"]), "Single-cell"),
              "Single-cell or single-nucleus resolution"),
            p(class = "small mb-0",
              tags$span(class = "badge me-1",
                style = sprintf("background:%s;color:%s",
                                PAL_TYPE["Spatial"], PAL_TYPE_TEXT["Spatial"]), "Spatial"),
              "Spatially resolved omics + imaging")
          )
        )
      )
    )
  ),

  nav_spacer(),

  nav_item(
    tags$a(icon("github"), " GitHub",
           href = "https://github.com/INFLAMomx/INFLAhub", target = "_blank",
           class = "nav-link px-2")
  )
)

# ─── Server ───────────────────────────────────────────────────────────────────

server <- function(input, output, session) {

  # ── Reactive: filtered data ──────────────────────────────────────────────────
  filt <- reactive({
    df <- methods_all
    if (length(input$f_type))
      df <- df %>% filter(Data_type %in% input$f_type)
    if (length(input$f_cat))
      df <- df %>% filter(Integration_category %in% input$f_cat)
    if (length(input$f_lang))
      df <- df %>% filter(
        str_detect(coalesce(Language, ""),
                   paste(input$f_lang, collapse = "|")))
    if (isTRUE(input$f_pass))
      df <- df %>% filter(coalesce(Include, "") == "PASS")
    df
  })

  output$n_tools_label <- renderText(
    paste0(nrow(filt()), " tool", if (nrow(filt()) != 1) "s")
  )

  # ── Methods table ────────────────────────────────────────────────────────────
  output$tbl_methods <- renderDT({
    df <- filt() %>%
      mutate(
        Type_html = sprintf(
          '<span class="badge" style="background:%s;color:%s">%s</span>',
          PAL_TYPE[Data_type], PAL_TYPE_TEXT[Data_type], Data_type),
        Tool_html = ifelse(
          !is.na(Link) & Link != "",
          sprintf('<a href="%s" target="_blank" rel="noopener">%s <span class="ext-link">&#8599;</span></a>',
                  Link, Tool),
          Tool),
        Doc_stars  = sapply(Doc_quality, star_rating),
        UX_stars   = sapply(Usability,   star_rating),
        Status_html = case_when(
          coalesce(Include, "") == "PASS"   ~
            '<span class="badge bg-success">PASS</span>',
          coalesce(Include, "") == "REVIEW" ~
            '<span class="badge bg-warning text-dark">REVIEW</span>',
          TRUE ~
            '<span class="badge bg-secondary opacity-75">—</span>'
        )
      ) %>%
      select(Type_html, Tool_html, Integration_category, Integration_type,
             Omics_layers, Language, Doc_stars, UX_stars, Status_html)

    names(df) <- c("Type", "Tool", "Category", "Supervised?",
                   "Omics layers", "Language", "Doc ★", "UX ★", "Status")

    datatable(
      df,
      escape    = FALSE,
      rownames  = FALSE,
      selection = "single",
      class     = "stripe hover compact nowrap",
      options   = list(
        pageLength = 25,
        dom        = "frtip",
        scrollX    = TRUE,
        autoWidth  = FALSE,
        columnDefs = list(
          list(width = "94px",  targets = 0),
          list(width = "180px", targets = 1),
          list(width = "220px", targets = 2),
          list(width = "120px", targets = 3),
          list(width = "60px",  targets = c(6, 7, 8), className = "text-center"),
          list(orderable = FALSE, targets = c(6, 7))
        ),
        language = list(
          search = "Search tools:",
          zeroRecords = "No tools match the current filters."
        )
      )
    )
  }, server = FALSE)

  # ── Row click → detail modal ─────────────────────────────────────────────────
  observeEvent(input$tbl_methods_rows_selected, {
    idx <- input$tbl_methods_rows_selected
    req(length(idx) > 0)
    r <- filt()[idx, ]

    showModal(modalDialog(
      title = tagList(
        tags$span(
          class = "badge me-2 align-middle",
          style = sprintf("background:%s;color:%s;font-size:0.75rem",
                          PAL_TYPE[r$Data_type[[1]]], PAL_TYPE_TEXT[r$Data_type[[1]]]),
          r$Data_type[[1]]
        ),
        r$Tool[[1]]
      ),
      size       = "xl",
      easyClose  = TRUE,
      footer     = modalButton("Close"),

      fluidRow(
        # Left column: taxonomy & evidence
        column(6,
          tags$h6(class = "text-muted text-uppercase small fw-bold mb-2", "Classification"),
          tags$dl(class = "row small mb-3",
            tags$dt(class = "col-5 text-muted", "Category"),
            tags$dd(class = "col-7", val(r$Integration_category)),
            tags$dt(class = "col-5 text-muted", "Integration type"),
            tags$dd(class = "col-7", val(r$Integration_type)),
            tags$dt(class = "col-5 text-muted", "Omics layers"),
            tags$dd(class = "col-7", val(r$Omics_layers)),
            tags$dt(class = "col-5 text-muted", "Underlying method"),
            tags$dd(class = "col-7", val(r$Underlying_method)),
            tags$dt(class = "col-5 text-muted", "Language"),
            tags$dd(class = "col-7", val(r$Language)),
            tags$dt(class = "col-5 text-muted", "Install via"),
            tags$dd(class = "col-7", val(r$Installation_source)),
            tags$dt(class = "col-5 text-muted", "Maintenance"),
            tags$dd(class = "col-7", val(r$Maintenance_status)),
            tags$dt(class = "col-5 text-muted", "Citations"),
            tags$dd(class = "col-7", val(r$Citation_count)),
            tags$dt(class = "col-5 text-muted", "Benchmarked in"),
            tags$dd(class = "col-7", val(r$Benchmarked_in))
          )
        ),
        # Right column: quality & inclusion
        column(6,
          tags$h6(class = "text-muted text-uppercase small fw-bold mb-2", "Quality & Inclusion"),
          tags$dl(class = "row small mb-3",
            tags$dt(class = "col-6 text-muted", "Documentation (1–5)"),
            tags$dd(class = "col-6", star_rating(r$Doc_quality)),
            tags$dt(class = "col-6 text-muted", "Usability (1–5)"),
            tags$dd(class = "col-6", star_rating(r$Usability)),
            tags$dt(class = "col-6 text-muted", "Actively maintained"),
            tags$dd(class = "col-6", yn_badge(val(r$Actively_maintained))),
            tags$dt(class = "col-6 text-muted", "Published"),
            tags$dd(class = "col-6", yn_badge(val(r$Published))),
            tags$dt(class = "col-6 text-muted", "Code available"),
            tags$dd(class = "col-6", yn_badge(val(r$Code_available))),
            tags$dt(class = "col-6 text-muted", "Params documented"),
            tags$dd(class = "col-6", yn_badge(val(r$Parameters_documented))),
            tags$dt(class = "col-6 text-muted", "Inclusion status"),
            tags$dd(class = "col-6", status_badge(val(r$Include)))
          )
        )
      ),

      # Narrative fields (only shown when not empty)
      if (!is.na(r$Use_case[[1]]) && r$Use_case[[1]] != "") tagList(
        hr(class = "my-2"),
        tags$h6("Use case"), tags$p(class = "small", r$Use_case[[1]])
      ),
      if (!is.na(r$Strengths[[1]]) && r$Strengths[[1]] != "") tagList(
        if (is.na(r$Use_case[[1]]) || r$Use_case[[1]] == "") hr(class = "my-2"),
        tags$h6("Strengths"), tags$p(class = "small", r$Strengths[[1]])
      ),
      if (!is.na(r$Limitations[[1]]) && r$Limitations[[1]] != "") tagList(
        tags$h6("Limitations"), tags$p(class = "small", r$Limitations[[1]])
      ),
      if (!is.na(r$Best_for[[1]]) && r$Best_for[[1]] != "") tagList(
        tags$h6("Best for"), tags$p(class = "small text-muted", r$Best_for[[1]])
      ),

      hr(class = "my-2"),
      div(class = "d-flex flex-wrap gap-2",
        link_btn(val(r$Link),      "Homepage / repo", "arrow-up-right-from-square", "btn-outline-primary"),
        link_btn(val(r$Paper_DOI), "Paper / DOI",     "file-lines",                 "btn-outline-secondary")
      )
    ))
  })

  # ── Scatter: quality landscape ───────────────────────────────────────────────
  output$plt_scatter <- renderPlotly({
    df <- methods_all %>%
      filter(!is.na(Doc_quality) | !is.na(Usability)) %>%
      mutate(
        doc_jit = Doc_quality + runif(n(), -0.12, 0.12),
        ux_jit  = Usability   + runif(n(), -0.12, 0.12),
        color   = sapply(Integration_category, cat_color),
        label   = paste0(
          "<b>", Tool, "</b><br>",
          "Category: ",  coalesce(Integration_category, "—"), "<br>",
          "Type: ",      Data_type, "<br>",
          "Language: ",  coalesce(Language, "—"), "<br>",
          "Doc: ",       coalesce(as.character(Doc_quality), "—"),
          " | UX: ",     coalesce(as.character(Usability), "—")
        )
      )

    if (nrow(df) == 0) {
      return(
        plotly_empty(type = "scatter", mode = "markers") %>%
          layout(
            annotations = list(list(
              text = "<b>No quality scores yet</b><br><span style='font-size:12px'>Add Doc quality & Usability columns to see tools plotted here.</span>",
              xref = "paper", yref = "paper", x = 0.5, y = 0.5,
              showarrow = FALSE, font = list(size = 13, color = "#6c757d")
            )),
            paper_bgcolor = "rgba(0,0,0,0)",
            plot_bgcolor  = "#f8f9fa"
          )
      )
    }

    plot_ly(df,
      x = ~doc_jit, y = ~ux_jit,
      color  = ~Integration_category,
      symbol = ~Data_type,
      text   = ~label,
      hovertemplate = "%{text}<extra></extra>",
      type   = "scatter",
      mode   = "markers",
      marker = list(size = 14, opacity = 0.85,
                    line = list(color = "white", width = 1.5))
    ) %>%
      layout(
        xaxis  = list(title = "Documentation quality",
                      range = c(0.5, 5.5), tickvals = 1:5, zeroline = FALSE,
                      gridcolor = "#dee2e6"),
        yaxis  = list(title = "Usability",
                      range = c(0.5, 5.5), tickvals = 1:5, zeroline = FALSE,
                      gridcolor = "#dee2e6"),
        legend = list(orientation = "h", y = -0.35, font = list(size = 10)),
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "#f8f9fa",
        margin = list(t = 10, b = 10, l = 50, r = 10)
      )
  })

  # ── Bar: tools by category ───────────────────────────────────────────────────
  output$plt_bar <- renderPlotly({
    df <- methods_all %>%
      count(Data_type, Integration_category) %>%
      mutate(cat_wrap = str_wrap(Integration_category, 26))

    plot_ly(df,
      x     = ~n,
      y     = ~reorder(cat_wrap, n),
      color = ~Data_type,
      colors = PAL_TYPE,
      text  = ~n,
      textposition = "inside",
      insidetextanchor = "middle",
      hovertemplate = "<b>%{y}</b><br>%{fullData.name}: %{x}<extra></extra>",
      type  = "bar",
      orientation = "h"
    ) %>%
      layout(
        barmode = "stack",
        xaxis   = list(title = "Number of tools", dtick = 1,
                       zeroline = FALSE, gridcolor = "#dee2e6"),
        yaxis   = list(title = "", automargin = TRUE),
        legend  = list(orientation = "h", y = -0.18, font = list(size = 10)),
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "#f8f9fa",
        margin  = list(t = 10, b = 10, l = 10, r = 10)
      )
  })

  # ── Heatmap: omics coverage ──────────────────────────────────────────────────
  output$plt_heatmap <- renderPlotly({

    # Canonical layer names mapped from raw text
    LAYER_MAP <- list(
      "Transcriptomics"      = "RNA|rna|transcript|mRNA|snRNA|scRNA",
      "Chromatin access."    = "ATAC|chromatin|access",
      "Methylation"          = "methylat|epigenom|snmC|DNA.methyl",
      "Proteomics"           = "protein|proteom",
      "Metabolomics"         = "metabol",
      "Spatial"              = "spatial|Visium|[Ss][Tt](?!AL|AI)",
      "Metagenomics"         = "microbiom|metagenom",
      "Imaging/Histology"    = "imaging|histol|H.?E|morphology|MSI|MALDI|DESI",
      "CNV"                  = "CNV|copy.?number",
      "miRNA"                = "miRNA",
      "Mutation/Variant"     = "mutation|variant",
      "CITE-seq"             = "CITE|cite.seq"
    )

    norm_layer <- function(x) {
      for (nm in names(LAYER_MAP)) {
        if (grepl(LAYER_MAP[[nm]], x, perl = TRUE, ignore.case = TRUE))
          return(nm)
      }
      trimws(x)
    }

    expanded <- methods_all %>%
      filter(!is.na(Omics_layers)) %>%
      mutate(parts = str_split(Omics_layers, "[;,+]+")) %>%
      unnest(parts) %>%
      mutate(
        parts = trimws(parts),
        Layer = sapply(parts, norm_layer)
      ) %>%
      filter(nchar(Layer) >= 2) %>%
      distinct(Tool, Layer)

    mat <- expanded %>%
      mutate(present = 1L) %>%
      pivot_wider(names_from = Layer, values_from = present, values_fill = 0L) %>%
      arrange(Tool)

    if (nrow(mat) == 0) {
      return(plotly_empty() %>%
               layout(title = "No omics layer data",
                      paper_bgcolor = "rgba(0,0,0,0)"))
    }

    tools_vec  <- mat$Tool
    layers_vec <- colnames(mat)[-1]

    # Sort layers by frequency
    layer_freq  <- colSums(mat[, -1])
    layers_vec  <- names(sort(layer_freq, decreasing = TRUE))
    z_mat       <- as.matrix(mat[, layers_vec, drop = FALSE])

    plot_ly(
      x = layers_vec,
      y = tools_vec,
      z = z_mat,
      type = "heatmap",
      colorscale = list(
        list(0, "#f1f3f5"),
        list(1, "#264653")
      ),
      showscale = FALSE,
      xgap = 2, ygap = 2,
      hovertemplate = "<b>%{y}</b><br>%{x}: %{z}<extra></extra>"
    ) %>%
      layout(
        xaxis = list(
          tickangle  = -35,
          automargin = TRUE,
          title      = "",
          tickfont   = list(size = 11)
        ),
        yaxis = list(
          automargin = TRUE,
          title      = "",
          tickfont   = list(size = 11)
        ),
        margin = list(l = 20, r = 20, t = 10, b = 20),
        paper_bgcolor = "rgba(0,0,0,0)"
      )
  })

  # ── Benchmarking table ───────────────────────────────────────────────────────
  output$tbl_bench <- renderDT({
    df <- bench
    if (nrow(df) == 0) {
      return(datatable(
        data.frame(Message = "No benchmarking data loaded."),
        options = list(dom = "t"), rownames = FALSE
      ))
    }

    # Clickable link columns
    if ("Link" %in% names(df))
      df$Link <- ifelse(!is.na(df$Link),
        sprintf('<a href="%s" target="_blank" rel="noopener">↗</a>', df$Link), "—")
    if ("Paper link / DOI" %in% names(df))
      df[["Paper link / DOI"]] <- ifelse(!is.na(df[["Paper link / DOI"]]),
        sprintf('<a href="%s" target="_blank" rel="noopener">paper ↗</a>',
                df[["Paper link / DOI"]]), "—")

    show_cols <- intersect(
      c("Benchmark / framework", "Type", "Data modality",
        "Tissue / disease compared", "Language", "Maintenance status",
        "Link", "Paper link / DOI"),
      names(df)
    )

    datatable(
      df[, show_cols, drop = FALSE],
      escape    = FALSE,
      rownames  = FALSE,
      class     = "stripe hover compact",
      options   = list(
        pageLength = 10, dom = "frtip", scrollX = TRUE,
        columnDefs = list(
          list(width = "50px",  targets = which(show_cols == "Link") - 1),
          list(width = "80px",  targets = which(show_cols == "Paper link / DOI") - 1)
        )
      )
    )
  })

  # ── Evaluation metrics table ─────────────────────────────────────────────────
  output$tbl_metrics <- renderDT({
    df <- metrics
    if (nrow(df) == 0) {
      return(datatable(
        data.frame(Message = "No metrics data loaded."),
        options = list(dom = "t"), rownames = FALSE
      ))
    }

    show_cols <- intersect(
      c("ID", "Metric", "Category / applies to", "What it measures",
        "Objective / Subjective", "Tools / packages (Python | R)",
        "Reference (definition paper / DOI)"),
      names(df)
    )

    datatable(
      df[, show_cols, drop = FALSE],
      escape   = FALSE,
      rownames = FALSE,
      class    = "stripe hover compact",
      options  = list(
        pageLength = 15, dom = "frtip", scrollX = TRUE,
        columnDefs = list(
          list(width = "36px",  targets = 0),
          list(width = "170px", targets = 1),
          list(width = "160px", targets = 2)
        )
      )
    )
  })

  # ── About stats ──────────────────────────────────────────────────────────────
  output$about_stats <- renderUI({
    n_all    <- nrow(methods_all)
    n_pass   <- sum(coalesce(methods_all$Include, "") == "PASS")
    n_review <- sum(coalesce(methods_all$Include, "") == "REVIEW")
    n_bench  <- nrow(bench)
    n_met    <- nrow(metrics)
    n_bulk   <- sum(methods_all$Data_type == "Bulk")
    n_sc     <- sum(methods_all$Data_type == "Single-cell")
    n_spa    <- sum(methods_all$Data_type == "Spatial")

    stat <- function(n, label, color) {
      div(
        class = "stat-card d-flex align-items-center gap-3 p-2 mb-2 rounded",
        style = sprintf("border-left:4px solid %s; background:#f8f9fa", color),
        div(class = "fw-bold fs-4", style = sprintf("color:%s; min-width:2rem; text-align:right", color), n),
        div(class = "small text-muted lh-sm", label)
      )
    }

    tagList(
      stat(n_all,    "tools catalogued",             "#264653"),
      stat(n_pass,   "meet all inclusion criteria",  "#2A9D8F"),
      stat(n_review, "under review / incomplete",    "#E9A825"),
      stat(n_bench,  "benchmark studies",            "#F4A261"),
      stat(n_met,    "evaluation metrics",           "#4EBFD4"),
      hr(class = "my-2"),
      div(class = "d-flex justify-content-between small text-muted px-1",
        span(tags$b(n_bulk), " Bulk"),
        span(tags$b(n_sc),   " Single-cell"),
        span(tags$b(n_spa),  " Spatial")
      )
    )
  })
}

shinyApp(ui, server)
