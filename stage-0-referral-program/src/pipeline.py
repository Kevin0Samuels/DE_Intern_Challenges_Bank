"""Referral Program ETL and Fraud Detection Pipeline.

Stage 0: Springer Capital Data Engineer Take-Home Test.

This script executes the complete data pipeline:
1. Loads all 7 source CSV files.
2. Cleans and standardizes missing values and datatypes.
3. Performs timezone conversion from UTC to local time.
4. Merges tables using user_referrals as the central hub (ensuring 0 duplicate rows).
5. Computes referral_source_category and applies initcap (preserving club names).
6. Evaluates business logic and fraud detection rules to populate `is_business_logic_valid`.
7. Exports the final 46-row report to CSV.
"""

import os
import argparse
import logging
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def load_raw_data(data_dir: str) -> dict:
    """Loads all 7 raw CSV files and normalizes string 'null' representations."""
    files = {
        'referrals': 'user_referrals.csv',
        'referral_logs': 'user_referral_logs.csv',
        'user_logs': 'user_logs.csv',
        'statuses': 'user_referral_statuses.csv',
        'rewards': 'referral_rewards.csv',
        'transactions': 'paid_transactions.csv',
        'leads': 'lead_log.csv'
    }
    
    dfs = {}
    for key, filename in files.items():
        path = os.path.join(data_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required dataset file not found: {path}")
        logging.info(f"Loading {filename}...")
        df = pd.read_csv(path, keep_default_na=False)
        # Clean literal 'null' strings, whitespace, and empty strings
        df = df.replace({'null': np.nan, 'NULL': np.nan, 'None': np.nan, '': np.nan})
        dfs[key] = df
        
    return dfs


def clean_and_deduplicate(dfs: dict) -> dict:
    """Corrects data types and deduplicates log tables to prevent Cartesian joins."""
    cleaned = {}
    
    # 1. user_logs: deduplicate by user_id taking the latest record
    u = dfs['user_logs'].copy()
    u['id'] = pd.to_numeric(u['id'], errors='coerce').astype(int)
    u['is_deleted'] = u['is_deleted'].astype(str).str.lower() == 'true'
    cleaned['users_dedup'] = u.sort_values('id').groupby('user_id').last().reset_index()
    
    # 2. lead_log: deduplicate by lead_id taking the latest record
    l = dfs['leads'].copy()
    l['id'] = pd.to_numeric(l['id'], errors='coerce').astype(int)
    cleaned['leads_dedup'] = l.sort_values('id').groupby('lead_id').last().reset_index()
    
    # 3. user_referral_logs: deduplicate by user_referral_id taking the latest log
    rl = dfs['referral_logs'].copy()
    rl['id'] = pd.to_numeric(rl['id'], errors='coerce').astype(int)
    rl['is_reward_granted'] = rl['is_reward_granted'].astype(str).str.lower() == 'true'
    cleaned['referral_logs_dedup'] = rl.sort_values('id').groupby('user_referral_id').last().reset_index()
    
    # 4. referral_rewards: parse reward days integer
    r = dfs['rewards'].copy()
    r['id'] = pd.to_numeric(r['id'], errors='coerce').astype('Int64')
    r['num_reward_days'] = r['reward_value'].astype(str).str.extract(r'(\d+)').astype(float).fillna(0).astype('Int64')
    cleaned['rewards'] = r
    
    # 5. user_referral_statuses
    s = dfs['statuses'].copy()
    s['id'] = pd.to_numeric(s['id'], errors='coerce').astype(int)
    cleaned['statuses'] = s
    
    # 6. paid_transactions
    cleaned['transactions'] = dfs['transactions'].copy()
    
    # 7. user_referrals (hub table)
    ref = dfs['referrals'].copy()
    ref['user_referral_status_id'] = pd.to_numeric(ref['user_referral_status_id'], errors='coerce').astype(int)
    ref['referral_reward_id'] = pd.to_numeric(ref['referral_reward_id'], errors='coerce').astype('Int64')
    cleaned['referrals'] = ref
    
    return cleaned


def convert_utc_to_local(series: pd.Series, tz_series: pd.Series) -> pd.Series:
    """Converts UTC timestamp series to formatted local time string (%Y-%m-%d %H:%M:%S)."""
    results = []
    for val, tz in zip(series, tz_series):
        if pd.isna(val) or val is None or str(val).lower() in ('nat', 'nan'):
            results.append(np.nan)
        else:
            try:
                dt = pd.to_datetime(val, utc=True)
                target_zone = tz if pd.notna(tz) and str(tz) != 'nan' else 'Asia/Jakarta'
                local_dt = dt.tz_convert(target_zone)
                results.append(local_dt.strftime('%Y-%m-%d %H:%M:%S'))
            except Exception:
                results.append(np.nan)
    return pd.Series(results, index=series.index)


def initcap(val):
    """Applies title casing to string words while preserving NaNs."""
    if pd.isna(val) or val is None:
        return np.nan
    s = str(val).strip()
    if not s or s.lower() == 'nan':
        return np.nan
    return s.title()


def build_pipeline(dfs_cleaned: dict, strict_reward_grant: bool = False) -> pd.DataFrame:
    """Joins data, performs business transformations, and runs fraud detection."""
    ref = dfs_cleaned['referrals'].copy()
    
    # Join 1: Statuses
    statuses_df = dfs_cleaned['statuses'][['id', 'description']].rename(columns={'description': 'referral_status'})
    df = ref.merge(
        statuses_df,
        left_on='user_referral_status_id',
        right_on='id',
        how='left'
    ).drop(columns=['id'])
    
    # Join 2: Referral Rewards
    rewards_df = dfs_cleaned['rewards'][['id', 'reward_value', 'num_reward_days']].drop(columns=['reward_value'])
    df = df.merge(
        rewards_df,
        left_on='referral_reward_id',
        right_on='id',
        how='left'
    ).drop(columns=['id'])
    df['num_reward_days'] = df['num_reward_days'].fillna(0).astype('Int64')
    
    # Join 3: Referral Details / Logs (Pre-renamed to avoid suffix collision)
    ref_logs_df = dfs_cleaned['referral_logs_dedup'][['user_referral_id', 'id', 'created_at', 'is_reward_granted']].rename(
        columns={'id': 'referral_details_id', 'created_at': 'reward_granted_at'}
    )
    df = df.merge(
        ref_logs_df,
        left_on='referral_id',
        right_on='user_referral_id',
        how='left'
    )
    df['referral_details_id'] = df['referral_details_id'].astype('Int64')
    
    # Join 4: Referrer user info
    df = df.merge(
        dfs_cleaned['users_dedup'][['user_id', 'name', 'phone_number', 'homeclub', 'timezone_homeclub', 'membership_expired_date', 'is_deleted']],
        left_on='referrer_id',
        right_on='user_id',
        how='left'
    ).rename(columns={
        'name': 'referrer_name',
        'phone_number': 'referrer_phone_number',
        'homeclub': 'referrer_homeclub'
    })
    
    # Join 5: Transactions
    df = df.merge(
        dfs_cleaned['transactions'][['transaction_id', 'transaction_status', 'transaction_at', 'transaction_location', 'timezone_transaction', 'transaction_type']],
        on='transaction_id',
        how='left'
    )
    
    # Join 6: Leads (for Lead referrals)
    df = df.merge(
        dfs_cleaned['leads_dedup'][['lead_id', 'source_category', 'timezone_location']],
        left_on='referee_id',
        right_on='lead_id',
        how='left'
    )
    
    # Timezone resolution
    df['target_tz'] = (
        df['timezone_homeclub']
        .combine_first(df['timezone_transaction'])
        .combine_first(df['timezone_location'])
        .fillna('Asia/Jakarta')
    )
    
    # Time adjustments to local timezone
    df['referral_at_utc'] = df['referral_at']
    df['transaction_at_utc'] = df['transaction_at']
    
    df['referral_at'] = convert_utc_to_local(df['referral_at'], df['target_tz'])
    df['updated_at'] = convert_utc_to_local(df['updated_at'], df['target_tz'])
    df['transaction_at'] = convert_utc_to_local(df['transaction_at'], df['timezone_transaction'].fillna(df['target_tz']))
    df['reward_granted_at'] = convert_utc_to_local(df['reward_granted_at'], df['target_tz'])
    
    # Source Category Logic
    def derive_source_category(row):
        src = str(row['referral_source']).strip()
        if src == 'User Sign Up':
            return 'Online'
        elif src == 'Draft Transaction':
            return 'Offline'
        elif src == 'Lead':
            cat = row['source_category']
            return cat if pd.notna(cat) and str(cat) != 'nan' else 'Lead'
        return 'Other'

    df['referral_source_category'] = df.apply(derive_source_category, axis=1)
    
    # String Adjustments (Initcap, EXCEPT club names)
    df['referral_source'] = df['referral_source'].apply(initcap)
    df['referral_source_category'] = df['referral_source_category'].apply(initcap)
    df['referrer_name'] = df['referrer_name'].apply(initcap)
    df['referee_name'] = df['referee_name'].apply(initcap)
    df['referral_status'] = df['referral_status'].apply(initcap)
    df['transaction_status'] = df['transaction_status'].apply(initcap)
    df['transaction_type'] = df['transaction_type'].apply(initcap)
    # Club names: referrer_homeclub and transaction_location are kept uppercase
    
    # =========================================================================
    # FRAUD DETECTION & BUSINESS LOGIC VALIDATION
    # =========================================================================
    ref_dt = pd.to_datetime(df['referral_at_utc'], utc=True)
    tx_dt = pd.to_datetime(df['transaction_at_utc'], utc=True)
    mem_dt = pd.to_datetime(df['membership_expired_date'], utc=True)
    
    # --- Invalid Conditions ---
    # Condition 1: reward > 0 and status != 'Berhasil'
    inv_c1 = (df['num_reward_days'] > 0) & (df['referral_status'] != 'Berhasil')
    
    # Condition 2: reward > 0 and no transaction ID
    inv_c2 = (df['num_reward_days'] > 0) & (df['transaction_id'].isna())
    
    # Condition 3: no reward, has tx_id, tx is PAID, and tx occurred after referral
    inv_c3 = (
        (df['num_reward_days'] == 0) &
        (df['transaction_id'].notna()) &
        (df['transaction_status'].str.lower() == 'paid') &
        (tx_dt > ref_dt)
    )
    
    # Condition 4: status is 'Berhasil' and reward is null or 0
    inv_c4 = (df['referral_status'] == 'Berhasil') & (df['num_reward_days'] == 0)
    
    # Condition 5: transaction occurred before referral was created
    inv_c5 = (tx_dt.notna()) & (tx_dt < ref_dt)
    
    is_any_invalid = inv_c1 | inv_c2 | inv_c3 | inv_c4 | inv_c5
    
    # --- Valid Conditions ---
    # Valid Condition 1: Valid Successful Referral Reward
    valid_c1_base = (
        (df['num_reward_days'] > 0) &
        (df['referral_status'] == 'Berhasil') &
        (df['transaction_id'].notna()) &
        (df['transaction_status'].str.lower() == 'paid') &
        (df['transaction_type'].str.lower() == 'new') &
        (tx_dt > ref_dt) &
        (tx_dt.dt.year == ref_dt.dt.year) &
        (tx_dt.dt.month == ref_dt.dt.month) &
        (mem_dt >= ref_dt) &
        (df['is_deleted'] == False)
    )
    if strict_reward_grant:
        valid_c1 = valid_c1_base & (df['is_reward_granted'] == True)
    else:
        valid_c1 = valid_c1_base
        
    # Valid Condition 2: Valid Non-Successful Referral (Pending or Failed with no reward)
    valid_c2 = df['referral_status'].isin(['Menunggu', 'Tidak Berhasil']) & (df['num_reward_days'] == 0)
    
    # Final validity: Must meet Valid rules and NOT trigger any Invalid fraud rules
    df['is_business_logic_valid'] = (valid_c1 | valid_c2) & (~is_any_invalid)
    
    # Clean up empty referee_name representation
    df['referee_name'] = df['referee_name'].fillna('')
    
    # Select target 22 columns in the exact specification order
    final_cols = [
        'referral_details_id',
        'referral_id',
        'referral_source',
        'referral_source_category',
        'referral_at',
        'referrer_id',
        'referrer_name',
        'referrer_phone_number',
        'referrer_homeclub',
        'referee_id',
        'referee_name',
        'referee_phone',
        'referral_status',
        'num_reward_days',
        'transaction_id',
        'transaction_status',
        'transaction_at',
        'transaction_location',
        'transaction_type',
        'updated_at',
        'reward_granted_at',
        'is_business_logic_valid'
    ]
    
    report = df[final_cols].copy()
    return report


def run_pipeline(data_dir: str, output_dir: str, strict_reward_grant: bool = False):
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'referral_report.csv')
    
    logging.info("Starting Stage 0 ETL Pipeline...")
    raw_dfs = load_raw_data(data_dir)
    cleaned_dfs = clean_and_deduplicate(raw_dfs)
    
    report_df = build_pipeline(cleaned_dfs, strict_reward_grant=strict_reward_grant)
    
    # Validate output expectations
    logging.info(f"Final report row count: {len(report_df)} (Expected: 46)")
    logging.info(f"Final report column count: {len(report_df.columns)} (Expected: 22)")
    assert len(report_df) == 46, f"Expected 46 rows, got {len(report_df)}"
    assert len(report_df.columns) == 22, f"Expected 22 columns, got {len(report_df.columns)}"
    
    # Export CSV with clean nulls (empty string)
    report_df.to_csv(output_path, index=False, na_rep="")
    logging.info(f"Report exported successfully to: {output_path}")
    
    # Summary of business logic validation
    valid_summary = report_df.groupby(['referral_status', 'is_business_logic_valid']).size().unstack(fill_value=0)
    print("\n" + "=" * 50)
    print("REFERRAL BUSINESS LOGIC VALIDATION SUMMARY")
    print("=" * 50)
    print(valid_summary)
    print("=" * 50)
    print(f"Total Valid:   {report_df['is_business_logic_valid'].sum()}")
    print(f"Total Invalid: {(~report_df['is_business_logic_valid']).sum()}")
    print(f"Total Rows:    {len(report_df)}")
    print("=" * 50 + "\n")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Stage 0 Referral Program Pipeline")
    parser.add_argument('--data-dir', default='data', help="Directory with input CSV files.")
    parser.add_argument('--output-dir', default='output', help="Directory to save report CSV.")
    parser.add_argument('--strict-reward-grant', action='store_true', help="Strictly enforce is_reward_granted == True for Berhasil status.")
    args = parser.parse_args()
    
    run_pipeline(args.data_dir, args.output_dir, strict_reward_grant=args.strict_reward_grant)
