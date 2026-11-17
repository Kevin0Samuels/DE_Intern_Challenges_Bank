"""Data Profiling Script for Stage 0 (Springer Capital Take-Home Test).

Profiles all 7 source tables:
- lead_log.csv
- paid_transactions.csv
- referral_rewards.csv
- user_logs.csv
- user_referral_logs.csv
- user_referral_statuses.csv
- user_referrals.csv

Generates both an Excel report (.xlsx) and a Markdown summary (.md).
"""

import os
import re
import argparse
import pandas as pd
import numpy as np
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

SOURCE_FILES = {
    "user_referrals": "user_referrals.csv",
    "user_referral_logs": "user_referral_logs.csv",
    "user_logs": "user_logs.csv",
    "user_referral_statuses": "user_referral_statuses.csv",
    "referral_rewards": "referral_rewards.csv",
    "paid_transactions": "paid_transactions.csv",
    "lead_log": "lead_log.csv",
}

# ERD Schema Metadata for Defined Length & Nulls Allowed
SCHEMA_METADATA = {
    "user_referrals": {
        "referral_id": {"type": "VARCHAR", "len": "32", "nullable": "No"},
        "referral_at": {"type": "TIMESTAMP", "len": "24", "nullable": "No"},
        "referrer_id": {"type": "VARCHAR", "len": "32", "nullable": "Yes"},
        "referee_id": {"type": "VARCHAR", "len": "32", "nullable": "Yes"},
        "referee_name": {"type": "VARCHAR", "len": "64", "nullable": "Yes"},
        "referee_phone": {"type": "VARCHAR", "len": "32", "nullable": "Yes"},
        "referral_source": {"type": "VARCHAR", "len": "32", "nullable": "No"},
        "referral_reward_id": {"type": "INTEGER", "len": "10", "nullable": "Yes"},
        "transaction_id": {"type": "VARCHAR", "len": "32", "nullable": "Yes"},
        "updated_at": {"type": "TIMESTAMP", "len": "24", "nullable": "No"},
        "user_referral_status_id": {"type": "INTEGER", "len": "10", "nullable": "No"},
    },
    "user_referral_logs": {
        "id": {"type": "INTEGER", "len": "10", "nullable": "No"},
        "user_referral_id": {"type": "VARCHAR", "len": "32", "nullable": "No"},
        "source_transaction_id": {"type": "VARCHAR", "len": "32", "nullable": "Yes"},
        "created_at": {"type": "TIMESTAMP", "len": "24", "nullable": "No"},
        "is_reward_granted": {"type": "BOOLEAN", "len": "1", "nullable": "No"},
    },
    "user_logs": {
        "id": {"type": "INTEGER", "len": "10", "nullable": "No"},
        "user_id": {"type": "VARCHAR", "len": "32", "nullable": "No"},
        "name": {"type": "VARCHAR", "len": "64", "nullable": "Yes"},
        "phone_number": {"type": "VARCHAR", "len": "32", "nullable": "Yes"},
        "homeclub": {"type": "VARCHAR", "len": "50", "nullable": "Yes"},
        "timezone_homeclub": {"type": "VARCHAR", "len": "30", "nullable": "Yes"},
        "membership_expired_date": {"type": "DATE", "len": "10", "nullable": "Yes"},
        "is_deleted": {"type": "BOOLEAN", "len": "1", "nullable": "No"},
    },
    "user_referral_statuses": {
        "id": {"type": "INTEGER", "len": "10", "nullable": "No"},
        "description": {"type": "VARCHAR", "len": "50", "nullable": "No"},
        "created_at": {"type": "TIMESTAMP", "len": "24", "nullable": "No"},
    },
    "referral_rewards": {
        "id": {"type": "INTEGER", "len": "10", "nullable": "No"},
        "reward_value": {"type": "VARCHAR", "len": "20", "nullable": "No"},
        "created_at": {"type": "TIMESTAMP", "len": "24", "nullable": "No"},
        "reward_type": {"type": "INTEGER", "len": "5", "nullable": "No"},
    },
    "paid_transactions": {
        "transaction_id": {"type": "VARCHAR", "len": "32", "nullable": "No"},
        "transaction_status": {"type": "VARCHAR", "len": "20", "nullable": "No"},
        "transaction_at": {"type": "TIMESTAMP", "len": "24", "nullable": "No"},
        "transaction_location": {"type": "VARCHAR", "len": "50", "nullable": "Yes"},
        "timezone_transaction": {"type": "VARCHAR", "len": "30", "nullable": "Yes"},
        "transaction_type": {"type": "VARCHAR", "len": "20", "nullable": "No"},
    },
    "lead_log": {
        "id": {"type": "INTEGER", "len": "10", "nullable": "No"},
        "lead_id": {"type": "VARCHAR", "len": "32", "nullable": "No"},
        "source_category": {"type": "VARCHAR", "len": "30", "nullable": "Yes"},
        "created_at": {"type": "TIMESTAMP", "len": "24", "nullable": "No"},
        "preferred_location": {"type": "VARCHAR", "len": "50", "nullable": "Yes"},
        "timezone_location": {"type": "VARCHAR", "len": "30", "nullable": "Yes"},
        "current_status": {"type": "VARCHAR", "len": "30", "nullable": "Yes"},
    },
}


def detect_pattern(series, col_name):
    """Detect textual format patterns (UUID/Hex, ISO Timestamp, Numeric, Category)."""
    valid_series = series.dropna().astype(str)
    if len(valid_series) == 0:
        return "Empty"
    sample = valid_series.iloc[0]
    if re.match(r"^[a-fA-F0-9]{32}$", sample):
        return "Hex32 (MD5/UUID Hash)"
    if re.match(r"^\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}", sample):
        return "ISO8601 Timestamp"
    if re.match(r"^\d{4}-\d{2}-\d{2}$", sample):
        return "YYYY-MM-DD Date"
    if valid_series.str.isdigit().all():
        return "Numeric Integer"
    if sample.lower() in ("true", "false"):
        return "Boolean Flag"
    return "Text / String"


def profile_table(df_raw, table_name):
    """Profile a single dataframe according to the required schema layout."""
    # Treat 'null' strings and empty strings as real NaNs
    df = df_raw.replace({"null": np.nan, "NULL": np.nan, "": np.nan})
    meta = SCHEMA_METADATA.get(table_name, {})
    total_rows = len(df)

    rows = []
    for col in df.columns:
        series = df[col]
        null_count = int(series.isna().sum())
        populated_pct = (
            ((total_rows - null_count) / total_rows * 100) if total_rows > 0 else 0.0
        )
        distinct_count = int(series.dropna().nunique())

        non_null_series = series.dropna()
        if len(non_null_series) > 0:
            min_val = str(non_null_series.min())
            max_val = str(non_null_series.max())
            is_str = non_null_series.apply(lambda x: isinstance(x, str)).all()
            if is_str:
                max_actual_len = str(non_null_series.astype(str).str.len().max())
            else:
                max_actual_len = "Not a string"
        else:
            min_val = "N/A"
            max_val = "N/A"
            max_actual_len = "N/A"

        col_meta = meta.get(col, {})
        data_type = col_meta.get("type", str(series.dtype))
        defined_len = col_meta.get("len", "N/A")
        nullable = col_meta.get("nullable", "Yes" if null_count > 0 else "No")

        # Frequencies
        top_freqs = series.dropna().value_counts().head(3).to_dict()
        freq_str = (
            ", ".join([f"'{k}': {v}" for k, v in top_freqs.items()])
            if top_freqs
            else "None"
        )
        pattern_str = detect_pattern(series, col)

        rows.append(
            {
                "Column Name": col,
                "Data Type": data_type,
                "Defined Length": defined_len,
                "Nulls Allowed": nullable,
                "Null Count": null_count,
                "% Populated": f"{populated_pct:.2f}%",
                "Distinct Value Count": distinct_count,
                "Minimum Value": min_val,
                "Maximum Value": max_val,
                "Max Actual Length": max_actual_len,
                "Top Frequencies": freq_str,
                "Detected Pattern": pattern_str,
            }
        )

    return pd.DataFrame(rows)


def df_to_markdown(df):
    headers = [str(c) for c in df.columns]
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        row_vals = [str(val).replace("\n", " ").replace("|", "\\|") for val in row]
        lines.append("| " + " | ".join(row_vals) + " |")
    return "\n".join(lines)


def run_profiling(data_dir: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    excel_path = os.path.join(output_dir, "data_profiling.xlsx")
    md_path = os.path.join(output_dir, "data_profiling.md")

    table_dfs = {}
    profiled_tables = {}
    overview_records = []

    for tbl_name, filename in SOURCE_FILES.items():
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            print(f"Warning: File {filepath} not found. Skipping.")
            continue
        df_raw = pd.read_csv(filepath, keep_default_na=False)
        table_dfs[tbl_name] = df_raw
        prof_df = profile_table(df_raw, tbl_name)
        profiled_tables[tbl_name] = prof_df

        overview_records.append(
            {
                "Table Name": tbl_name,
                "File Name": filename,
                "Total Rows": len(df_raw),
                "Total Columns": len(df_raw.columns),
                "Total Null Cells": int(prof_df["Null Count"].sum()),
            }
        )

    # 1. Export Excel Report with Professional Styling
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        # Overview Tab
        overview_df = pd.DataFrame(overview_records)
        overview_df.to_excel(writer, sheet_name="Overview", index=False)

        # Table Tabs
        for tbl_name, prof_df in profiled_tables.items():
            sheet_title = tbl_name[:31]  # Excel max sheet name limit
            prof_df.to_excel(writer, sheet_name=sheet_title, index=False)

        workbook = writer.book
        header_fill = PatternFill(
            start_color="1F497D", end_color="1F497D", fill_type="solid"
        )
        header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        thin_border = Border(
            left=Side(style="thin", color="D9D9D9"),
            right=Side(style="thin", color="D9D9D9"),
            top=Side(style="thin", color="D9D9D9"),
            bottom=Side(style="thin", color="D9D9D9"),
        )

        for sheet in workbook.worksheets:
            sheet.views.sheetView[0].showGridLines = True
            for col_idx, col in enumerate(sheet.columns, 1):
                col_letter = get_column_letter(col_idx)
                header_cell = col[0]
                header_cell.fill = header_fill
                header_cell.font = header_font
                header_cell.alignment = Alignment(
                    horizontal="center", vertical="center"
                )

                max_len = max(len(str(cell.value or "")) for cell in col)
                sheet.column_dimensions[col_letter].width = max(max_len + 3, 12)

                for row_idx, cell in enumerate(col[1:], 2):
                    cell.border = thin_border
                    cell.alignment = Alignment(vertical="center")
                    # Zebra striping
                    if row_idx % 2 == 0:
                        cell.fill = PatternFill(
                            start_color="F2F5F9", end_color="F2F5F9", fill_type="solid"
                        )

    print(f"Data profiling Excel saved to: {excel_path}")

    # 2. Export Markdown Summary
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Data Profiling Report: Springer Capital Referral System\n\n")
        f.write(
            "This report provides a systematic statistical and schema profiling of all 7 source tables.\n\n"
        )
        f.write("## 1. Tables Overview\n\n")
        f.write(df_to_markdown(overview_df))
        f.write("\n\n---\n\n")

        for tbl_name, prof_df in profiled_tables.items():
            f.write(f"## 2. Table: `{tbl_name}`\n\n")
            f.write(df_to_markdown(prof_df))
            f.write("\n\n")

    print(f"Data profiling Markdown saved to: {md_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Profile all source CSV tables.")
    parser.add_argument("--data-dir", default="data", help="Path to raw CSV directory.")
    parser.add_argument(
        "--output-dir", default="output", help="Path to output directory."
    )
    args = parser.parse_args()

    run_profiling(args.data_dir, args.output_dir)
