"""Generates the Business Data Dictionary in Excel format (.xlsx).

Targeted at non-technical business users (e.g. Marketing Manager, Operations Lead).
Covers all 22 output columns of the referral report with descriptions,
data types, sample values, and business rules.
"""

import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter


DATA_DICTIONARY_ROWS = [
    {
        "Column Name": "referral_details_id",
        "Business Label": "Referral Detail / Log ID",
        "Category": "Identification",
        "Data Type": "INTEGER",
        "Nullable": "Yes",
        "Sample Value": "30",
        "Description": "Unique identifier of the referral event log entry in the audit tracking system. Left empty if no audit log exists.",
        "Business Rules & Constraints": "Originates from user_referral_logs.id. Populated when an event or reward milestone is recorded."
    },
    {
        "Column Name": "referral_id",
        "Business Label": "Referral Code / ID",
        "Category": "Identification",
        "Data Type": "STRING",
        "Nullable": "No",
        "Sample Value": "9e9324e6fde29bb0d230654b38ccfdd4",
        "Description": "Unique identifier for each referral transaction created when a new user signs up or is registered using a referral link/code.",
        "Business Rules & Constraints": "Primary key of the referral event; exactly 46 unique referral records exist in this report."
    },
    {
        "Column Name": "referral_source",
        "Business Label": "Referral Channel Source",
        "Category": "Referral Context",
        "Data Type": "STRING",
        "Nullable": "No",
        "Sample Value": "Draft Transaction",
        "Description": "The entry touchpoint where the referral was initiated (e.g., 'Draft Transaction', 'User Sign Up', 'Lead').",
        "Business Rules & Constraints": "Normalized with Title Casing. Mapped to broad marketing channel categories."
    },
    {
        "Column Name": "referral_source_category",
        "Business Label": "Marketing Channel Category",
        "Category": "Referral Context",
        "Data Type": "STRING",
        "Nullable": "No",
        "Sample Value": "Offline",
        "Description": "High-level classification of marketing origin: 'Online' for digital user signups, 'Offline' for in-club draft transactions, or lead-specific channel.",
        "Business Rules & Constraints": "User Sign Up -> Online; Draft Transaction -> Offline; Lead -> Inherited from lead source category."
    },
    {
        "Column Name": "referral_at",
        "Business Label": "Referral Submission Timestamp",
        "Category": "Referral Context",
        "Data Type": "DATETIME",
        "Nullable": "No",
        "Sample Value": "2024-05-14 13:17:03",
        "Description": "Local date and time when the referral record was formally registered into the system.",
        "Business Rules & Constraints": "Converted from original UTC timestamp to the user/club local timezone (WIB/WITA) in 'YYYY-MM-DD HH:MM:SS' format."
    },
    {
        "Column Name": "referrer_id",
        "Business Label": "Referring Member ID",
        "Category": "Referrer Profile",
        "Data Type": "STRING",
        "Nullable": "Yes",
        "Sample Value": "f2de40c8394f4ea9a6aa49965380dd8f",
        "Description": "Unique account ID of the existing club member who shared their referral invitation.",
        "Business Rules & Constraints": "Foreign key joining to user_logs.user_id. Must belong to an active, non-expired member to earn rewards."
    },
    {
        "Column Name": "referrer_name",
        "Business Label": "Referring Member Name",
        "Category": "Referrer Profile",
        "Data Type": "STRING",
        "Nullable": "Yes",
        "Sample Value": "2Eb4B6E1Ee9574C9E4A5F7E7E9B09280",
        "Description": "Name of the referring member (anonymized in data extract for privacy compliance).",
        "Business Rules & Constraints": "Applied Initcap formatting per challenge specification."
    },
    {
        "Column Name": "referrer_phone_number",
        "Business Label": "Referring Member Contact",
        "Category": "Referrer Profile",
        "Data Type": "STRING",
        "Nullable": "Yes",
        "Sample Value": "d02b067e0f767dbb4564526385f49d84",
        "Description": "Contact phone number of the referring member (anonymized/hashed for security).",
        "Business Rules & Constraints": "Used for communication, notifications, and cross-account duplication prevention."
    },
    {
        "Column Name": "referrer_homeclub",
        "Business Label": "Referrer Home Club Location",
        "Category": "Referrer Profile",
        "Data Type": "STRING",
        "Nullable": "Yes",
        "Sample Value": "PLUIT",
        "Description": "Primary fitness club location where the referring member holds their active membership.",
        "Business Rules & Constraints": "Preserved strictly in UPPERCASE as required (club names are exempt from title casing)."
    },
    {
        "Column Name": "referee_id",
        "Business Label": "Referred User / Lead ID",
        "Category": "Referee Profile",
        "Data Type": "STRING",
        "Nullable": "Yes",
        "Sample Value": "d1b90f8e27b5ec0d37f180aed67d76b4",
        "Description": "Unique identifier of the invited new user. Links to lead records if acquired through marketing lead campaigns.",
        "Business Rules & Constraints": "Nullable for certain self-service signup channels where only name/phone was supplied."
    },
    {
        "Column Name": "referee_name",
        "Business Label": "Referred User Name",
        "Category": "Referee Profile",
        "Data Type": "STRING",
        "Nullable": "Yes",
        "Sample Value": "2E68F7F5C8854Bd2Cf2B5Ff55Bc7E780",
        "Description": "Name of the prospective or new customer being referred (anonymized in source).",
        "Business Rules & Constraints": "Applied Initcap formatting."
    },
    {
        "Column Name": "referee_phone",
        "Business Label": "Referred User Contact",
        "Category": "Referee Profile",
        "Data Type": "STRING",
        "Nullable": "No",
        "Sample Value": "321b0102e766ef73b63d1bd797203c02",
        "Description": "Contact telephone number of the referred new customer (anonymized hash in test dataset).",
        "Business Rules & Constraints": "Mandatory contact identifier used for referee validation and verification."
    },
    {
        "Column Name": "referral_status",
        "Business Label": "Referral Status",
        "Category": "Program Lifecycle",
        "Data Type": "STRING",
        "Nullable": "No",
        "Sample Value": "Berhasil",
        "Description": "Current business standing of the referral: 'Berhasil' (Successful), 'Menunggu' (Pending), or 'Tidak Berhasil' (Failed).",
        "Business Rules & Constraints": "Derived from user_referral_statuses.description. Only 'Berhasil' can qualify for positive reward days."
    },
    {
        "Column Name": "num_reward_days",
        "Business Label": "Granted Free Membership Days",
        "Category": "Reward Management",
        "Data Type": "INTEGER",
        "Nullable": "No",
        "Sample Value": "20",
        "Description": "The duration of complimentary gym membership granted as an incentive (e.g., 10, 15, or 20 days). 0 if no reward assigned.",
        "Business Rules & Constraints": "Parsed from referral_rewards.reward_value. Must be > 0 for a valid successful referral."
    },
    {
        "Column Name": "transaction_id",
        "Business Label": "Qualifying Transaction ID",
        "Category": "Transaction Verification",
        "Data Type": "STRING",
        "Nullable": "Yes",
        "Sample Value": "e05121ea99fed4f4c5224a4667bb3dad",
        "Description": "Unique identifier of the payment transaction tied to the referee's membership purchase.",
        "Business Rules & Constraints": "Foreign key joining to paid_transactions.transaction_id. Required for successful status."
    },
    {
        "Column Name": "transaction_status",
        "Business Label": "Payment Status",
        "Category": "Transaction Verification",
        "Data Type": "STRING",
        "Nullable": "Yes",
        "Sample Value": "Paid",
        "Description": "Financial state of the linked purchase (e.g. 'Paid'). Empty if no payment is linked.",
        "Business Rules & Constraints": "Title Cased ('Paid'). Must be confirmed 'Paid' for reward qualification."
    },
    {
        "Column Name": "transaction_at",
        "Business Label": "Transaction Timestamp",
        "Category": "Transaction Verification",
        "Data Type": "DATETIME",
        "Nullable": "Yes",
        "Sample Value": "2024-05-14 13:17:03",
        "Description": "Local date and time when the payment transaction was settled at the club.",
        "Business Rules & Constraints": "Converted to local timezone. Must occur after referral_at and within the same calendar month."
    },
    {
        "Column Name": "transaction_location",
        "Business Label": "Transaction Club Location",
        "Category": "Transaction Verification",
        "Data Type": "STRING",
        "Nullable": "Yes",
        "Sample Value": "ADITYAWARMAN",
        "Description": "Physical fitness center where the referee completed their membership purchase.",
        "Business Rules & Constraints": "Club name preserved in UPPERCASE format."
    },
    {
        "Column Name": "transaction_type",
        "Business Label": "Purchase Category",
        "Category": "Transaction Verification",
        "Data Type": "STRING",
        "Nullable": "Yes",
        "Sample Value": "New",
        "Description": "Classification of membership purchase: 'New' for brand new joiners, 'Rejoin' for returning former members.",
        "Business Rules & Constraints": "Title Cased. Program policy dictates referral rewards only trigger on 'New' membership purchases."
    },
    {
        "Column Name": "updated_at",
        "Business Label": "Record Last Updated",
        "Category": "Audit Tracking",
        "Data Type": "DATETIME",
        "Nullable": "No",
        "Sample Value": "2024-05-14 13:17:34",
        "Description": "Local date and time when the referral record was last modified by system automations or staff.",
        "Business Rules & Constraints": "Converted to local timezone in 'YYYY-MM-DD HH:MM:SS' format."
    },
    {
        "Column Name": "reward_granted_at",
        "Business Label": "Reward Fulfillment Timestamp",
        "Category": "Reward Management",
        "Data Type": "DATETIME",
        "Nullable": "Yes",
        "Sample Value": "2024-05-14 13:17:36",
        "Description": "Local date and time when the referral reward days were formally provisioned onto the member's account.",
        "Business Rules & Constraints": "Converted to local time. Null if reward has not yet been processed or granted."
    },
    {
        "Column Name": "is_business_logic_valid",
        "Business Label": "Compliance & Anti-Fraud Flag",
        "Category": "Compliance & Fraud",
        "Data Type": "BOOLEAN",
        "Nullable": "No",
        "Sample Value": "True",
        "Description": "Master integrity indicator: TRUE if the referral complies fully with program rules; FALSE if flagged as suspicious or violating policy.",
        "Business Rules & Constraints": "Calculated by evaluating 2 valid conditions against 5 invalid fraud conditions."
    }
]

BUSINESS_RULES_SUMMARY = [
    {
        "Rule Category": "Valid Condition 1",
        "Rule Name": "Legitimate Successful Referral",
        "Detailed Logic": "All 10 conditions must simultaneously pass: (1) Reward days > 0; (2) Status is 'Berhasil'; (3) Has transaction ID; (4) Transaction status is 'PAID'; (5) Transaction type is 'NEW'; (6) Transaction timestamp is after referral timestamp; (7) Occurs within same calendar month; (8) Referrer membership has not expired; (9) Referrer account is not deleted; (10) Reward granted flag is true.",
        "Expected Verdict": "TRUE"
    },
    {
        "Rule Category": "Valid Condition 2",
        "Rule Name": "Legitimate Incomplete / Pending Referral",
        "Detailed Logic": "Referral status is either 'Menunggu' (Pending) or 'Tidak Berhasil' (Failed) AND no reward value (0 days) is assigned.",
        "Expected Verdict": "TRUE"
    },
    {
        "Rule Category": "Invalid Condition 1",
        "Rule Name": "Reward Granted on Incomplete Status",
        "Detailed Logic": "Reward days > 0 but referral status is NOT 'Berhasil'. (Prevents unearned rewards on pending/failed leads).",
        "Expected Verdict": "FALSE"
    },
    {
        "Rule Category": "Invalid Condition 2",
        "Rule Name": "Ghost Reward Without Transaction",
        "Detailed Logic": "Reward days > 0 but no transaction ID is linked to the referral.",
        "Expected Verdict": "FALSE"
    },
    {
        "Rule Category": "Invalid Condition 3",
        "Rule Name": "Unrewarded Paid Conversion (Potential Fraud/Leakage)",
        "Detailed Logic": "No reward assigned (0 days), yet referral has a valid PAID transaction that occurred after referral creation.",
        "Expected Verdict": "FALSE"
    },
    {
        "Rule Category": "Invalid Condition 4",
        "Rule Name": "Successful Referral With Missing Reward",
        "Detailed Logic": "Referral status is marked 'Berhasil' but reward days is null or 0.",
        "Expected Verdict": "FALSE"
    },
    {
        "Rule Category": "Invalid Condition 5",
        "Rule Name": "Anomalous Pre-Referral Transaction",
        "Detailed Logic": "The transaction timestamp occurred BEFORE the referral was created (backdated transaction fraud).",
        "Expected Verdict": "FALSE"
    }
]


def create_data_dictionary(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "data_dictionary.xlsx")
    
    wb = Workbook()
    
    # -------------------------------------------------------------
    # Styling Definitions
    # -------------------------------------------------------------
    primary_color = "1F497D"      # Navy Blue
    secondary_color = "2E75B6"    # Medium Blue
    zebra_color = "F2F5F9"        # Soft Ice Blue
    
    title_font = Font(name="Calibri", size=16, bold=True, color="1F497D")
    subtitle_font = Font(name="Calibri", size=11, italic=True, color="595959")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    bold_cell_font = Font(name="Calibri", size=10, bold=True, color="1A1A1A")
    body_font = Font(name="Calibri", size=10, color="262626")
    code_font = Font(name="Consolas", size=9, color="1F497D")
    
    header_fill = PatternFill(start_color=primary_color, end_color=primary_color, fill_type="solid")
    sec_header_fill = PatternFill(start_color=secondary_color, end_color=secondary_color, fill_type="solid")
    zebra_fill = PatternFill(start_color=zebra_color, end_color=zebra_color, fill_type="solid")
    
    thin_border = Border(
        left=Side(style='thin', color='D9D9D9'),
        right=Side(style='thin', color='D9D9D9'),
        top=Side(style='thin', color='D9D9D9'),
        bottom=Side(style='thin', color='D9D9D9')
    )
    
    # -------------------------------------------------------------
    # 1. Sheet 1: Data Dictionary
    # -------------------------------------------------------------
    ws_dict = wb.active
    ws_dict.title = "Data Dictionary"
    ws_dict.views.sheetView[0].showGridLines = True
    
    # Title Block
    ws_dict["A1"] = "Referral Program Data Dictionary"
    ws_dict["A1"].font = title_font
    ws_dict["A2"] = "Reference guide for business stakeholders and marketing managers evaluating referral fraud detection reports."
    ws_dict["A2"].font = subtitle_font
    
    headers = [
        "Column Name", "Business Label", "Category", "Data Type",
        "Nullable", "Sample Value", "Description", "Business Rules & Constraints"
    ]
    
    start_row = 4
    for col_idx, h in enumerate(headers, 1):
        cell = ws_dict.cell(row=start_row, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    ws_dict.row_dimensions[start_row].height = 28
    
    for row_idx, data in enumerate(DATA_DICTIONARY_ROWS, start_row + 1):
        ws_dict.row_dimensions[row_idx].height = 24
        fill = zebra_fill if (row_idx % 2 == 0) else None
        
        for col_idx, key in enumerate(headers, 1):
            val = data[key]
            cell = ws_dict.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            if fill:
                cell.fill = fill
                
            if key == "Column Name":
                cell.font = code_font
                cell.alignment = Alignment(vertical="center")
            elif key in ("Data Type", "Nullable", "Category"):
                cell.font = body_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif key == "Sample Value":
                cell.font = code_font
                cell.alignment = Alignment(horizontal="left", vertical="center")
            else:
                cell.font = body_font
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                
    # Column Widths
    col_widths = {
        'A': 25, 'B': 26, 'C': 20, 'D': 14,
        'E': 10, 'F': 25, 'G': 48, 'H': 50
    }
    for col_letter, width in col_widths.items():
        ws_dict.column_dimensions[col_letter].width = width
        
    # -------------------------------------------------------------
    # 2. Sheet 2: Business & Anti-Fraud Rules
    # -------------------------------------------------------------
    ws_rules = wb.create_sheet(title="Business Rules & Anti-Fraud")
    ws_rules.views.sheetView[0].showGridLines = True
    
    ws_rules["A1"] = "Referral Fraud Detection Rules Engine"
    ws_rules["A1"].font = title_font
    ws_rules["A2"] = "Technical specifications for evaluating 'is_business_logic_valid' across 46 program referrals."
    ws_rules["A2"].font = subtitle_font
    
    rule_headers = ["Rule Category", "Rule Name", "Detailed Logic", "Expected Verdict"]
    start_row = 4
    for col_idx, h in enumerate(rule_headers, 1):
        cell = ws_rules.cell(row=start_row, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = sec_header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
    
    ws_rules.row_dimensions[start_row].height = 26
    
    for row_idx, r in enumerate(BUSINESS_RULES_SUMMARY, start_row + 1):
        ws_rules.row_dimensions[row_idx].height = 36
        fill = zebra_fill if (row_idx % 2 == 0) else None
        
        for col_idx, key in enumerate(rule_headers, 1):
            val = r[key]
            cell = ws_rules.cell(row=row_idx, column=col_idx, value=val)
            cell.border = thin_border
            if fill:
                cell.fill = fill
                
            if key == "Expected Verdict":
                cell.font = bold_cell_font
                cell.alignment = Alignment(horizontal="center", vertical="center")
            elif key in ("Rule Category", "Rule Name"):
                cell.font = bold_cell_font
                cell.alignment = Alignment(vertical="center")
            else:
                cell.font = body_font
                cell.alignment = Alignment(vertical="center", wrap_text=True)
                
    ws_rules.column_dimensions['A'].width = 22
    ws_rules.column_dimensions['B'].width = 32
    ws_rules.column_dimensions['C'].width = 75
    ws_rules.column_dimensions['D'].width = 18
    
    wb.save(file_path)
    print(f"Data dictionary Excel workbook generated at: {file_path}")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description="Generate Business Data Dictionary")
    parser.add_argument('--output-dir', default='stage-0-referral-program/output', help="Directory to save data_dictionary.xlsx")
    args = parser.parse_args()
    create_data_dictionary(args.output_dir)
