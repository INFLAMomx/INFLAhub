#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────────────────────
# build_csvs.py — regenerate the catalogue CSVs from the master Excel workbook.
#
# The master workbook (Method_hub_WG2.xlsx) and this script live at the repo root
# on purpose: they are authoring tools, NOT part of the deployable app, so they
# stay out of the Shinylive bundle (which only ships src/). The app reads the
# generated CSVs in src/data/ — and because CSVs are plain text, GitHub shows a
# real diff for every edit.
#
# Workflow: edit Method_hub_WG2.xlsx, then run this and commit the changed CSVs:
#   python build_csvs.py
#
# Requires pandas + openpyxl locally (dev only; the deployed app needs neither
# openpyxl nor the xlsx).
# ─────────────────────────────────────────────────────────────────────────────

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent
XLSX = ROOT / "Method_hub_WG2.xlsx"
OUT = ROOT / "src" / "data"

# Method-sheet column names, in spreadsheet order. KEEP IN SYNC with app.py's
# METHOD_COLS. The method sheets have 3 header rows (title / group / names), so
# we skip them and supply clean names; data starts on row 4.
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

METHOD_SHEETS = {
    "Bulk methods": "methods_bulk.csv",
    "Single-cell methods": "methods_single_cell.csv",
    "Spatial methods": "methods_spatial.csv",
}


def export_methods():
    for sheet, out in METHOD_SHEETS.items():
        df = pd.read_excel(
            XLSX, sheet_name=sheet, skiprows=3, header=None,
            names=METHOD_COLS, dtype=str,
        )
        df = df[df["Tool"].notna() & (df["Tool"].astype(str).str.strip() != "")]
        df.to_csv(OUT / out, index=False)
        print(f"  {sheet:<22} -> src/data/{out:<24} ({len(df)} rows)")


def export_table(sheet, out, key_col=1, rename_first=None):
    # These sheets have one title row above a normal header row (skiprows=1).
    df = pd.read_excel(XLSX, sheet_name=sheet, skiprows=1, dtype=str)
    if rename_first:
        df = df.rename(columns={df.columns[0]: rename_first})
    df = df[df.iloc[:, key_col].notna()]
    df.to_csv(OUT / out, index=False)
    print(f"  {sheet:<22} -> src/data/{out:<24} ({len(df)} rows)")


def main():
    if not XLSX.exists():
        raise SystemExit(f"Master workbook not found: {XLSX}")
    print(f"Reading {XLSX.name} ...")
    export_methods()
    export_table("Benchmarking", "benchmarking.csv", key_col=1)
    export_table("Evaluation metrics", "evaluation_metrics.csv",
                 key_col=1, rename_first="ID")
    print("Done. Commit the updated src/data/*.csv files.")


if __name__ == "__main__":
    main()
