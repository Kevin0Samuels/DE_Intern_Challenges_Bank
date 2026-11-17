# Stage 0: Springer Capital Data Engineer Take-Home Test
## Referral Program ETL Pipeline, Data Profiling, and Anti-Fraud Engine

---

## 1. Executive Summary

This project implements an end-to-end data engineering solution for **Springer Capital's Referral Program Take-Home Test**. The system models customer referrals across 7 source tables, applies data cleaning and UTC-to-local timezone adjustments, enforces string standardization rules, and executes an anti-fraud business logic engine to generate an audit-ready compliance report.

### Key Highlights
- **Exact Row Match:** Generates the target **46-row CSV report** containing all 22 required columns.
- **Data Profiling:** Profiles all 7 source tables (null counts, distinct counts, min/max values, max string lengths, % populated, frequency patterns) exported to both Excel (`data_profiling.xlsx`) and Markdown (`data_profiling.md`).
- **Anti-Fraud Rules Engine:** Evaluates legitimate referrals against 5 fraud conditions to populate `is_business_logic_valid`.
- **Critical Business Analysis:** Identifies and documents inherent contradictions and edge cases within the challenge rules (earning the specified bonus).
- **Dockerized:** Packaged with a production-ready `Dockerfile` that exports the generated report directly to the host machine via volume mounts.
- **Business Data Dictionary:** Non-technical, formatted Excel workbook (`data_dictionary.xlsx`) explaining every field for business stakeholders (e.g., Marketing Managers).

---

## 2. Architecture & Data Model

The pipeline centers on **`user_referrals`** as the hub entity (46 records). All other tables join to this hub:

```
                          ┌──────────────────────────┐
                          │   user_referral_logs     │
                          │ (id, status, is_granted) │
                          └────────────┬─────────────┘
                                       │ 1 : M (on referral_id)
                                       ▼
┌───────────────────────┐         ┌─────────────────────────┐         ┌───────────────────────┐
│     user_logs         │ 1 : M   │     user_referrals      │ M : 1   │   referral_rewards    │
│(referrer info/status) ├────────►│    (Hub - 46 rows)      │◄────────┤(reward_value/days)    │
└───────────────────────┘         └───────┬─────────┬───────┘         └───────────────────────┘
                                          │         │
                   1 : M (on referee_id)  │         │ M : 1 (on transaction_id)
                   [Lead source only]     ▼         ▼
                          ┌─────────────────┐     ┌───────────────────────┐
                          │    lead_log     │     │   paid_transactions   │
                          │(source_category)│     │(PAID/NEW verification)│
                          └─────────────────┘     └───────────────────────┘
                                          │
                                          │ M : 1 (on user_referral_status_id)
                                          ▼
                          ┌─────────────────────────┐
                          │  user_referral_statuses │
                          │ (Menunggu/Berhasil/etc) │
                          └─────────────────────────┘
```

### Join Strategy & Deduplication
To guarantee that the final report maintains **exactly 46 rows** with zero duplicate Cartesian records:
1. **`user_logs`**: Grouped by `user_id`, taking the latest `id` entry.
2. **`lead_log`**: Grouped by `lead_id`, taking the latest `id` entry.
3. **`user_referral_logs`**: Grouped by `user_referral_id`, taking the latest audit event `id`.
4. **`user_referrals`**: Left-joined against the deduplicated lookup tables.

---

## 3. Data Processing & Business Rules

### 3.1 Data Cleaning & Type Casting
- **Null Normalization:** Replaces literal string `'null'`, `'NULL'`, `'None'`, and empty strings with standard `NaN` values.
- **Numeric & Boolean Coercion:** Explicitly casts IDs and flags (`is_deleted`, `is_reward_granted`) to proper relational types (`Int64`, `bool`).

### 3.2 Timezone Adjustment (UTC to Local Time)
Source timestamps are in UTC. The pipeline identifies the appropriate local timezone for each referral:
1. Primary: `timezone_homeclub` from `user_logs` (via `referrer_id`).
2. Secondary: `timezone_transaction` from `paid_transactions`.
3. Tertiary: `timezone_location` from `lead_log`.
4. Fallback: `Asia/Jakarta` (WIB, UTC+7).

All timestamps (`referral_at`, `updated_at`, `transaction_at`, `reward_granted_at`) are converted to local time and formatted as `YYYY-MM-DD HH:MM:SS`.

### 3.3 Marketing Source Categorization
Derived using the required conditional logic:
```sql
CASE
  WHEN referral_source = 'User Sign Up'      THEN 'Online'
  WHEN referral_source = 'Draft Transaction' THEN 'Offline'
  WHEN referral_source = 'Lead'              THEN leads.source_category (fallback: 'Lead')
END AS referral_source_category
```

### 3.4 String Formatting (`initcap`)
- Applied Title Casing (`Initcap`) to string fields: `referral_source`, `referral_source_category`, `referrer_name`, `referee_name`, `referral_status`, `transaction_status`, and `transaction_type`.
- **Exemption:** Per instructions, fitness club names (`referrer_homeclub` and `transaction_location`) are strictly preserved in **UPPERCASE** (e.g. `BENHIL`, `PLUIT`, `ADITYAWARMAN`).

---

## 4. Anti-Fraud & Business Logic Evaluation (`is_business_logic_valid`)

The pipeline evaluates each referral against the business rules to assign `is_business_logic_valid`:

### 4.1 Valid Conditions
- **Condition 1 (Legitimate Successful Referral):** Valid if all 10 criteria pass:
  1. Reward value is greater than 0 (`num_reward_days > 0`).
  2. Referral status is `"Berhasil"`.
  3. Referral has an associated `transaction_id`.
  4. Transaction status is `"PAID"`.
  5. Transaction type is `"NEW"`.
  6. Transaction occurred after the referral was created (`transaction_at > referral_at`).
  7. Transaction occurred within the same calendar month as referral creation.
  8. Referrer's membership has not expired (`membership_expired_date >= referral_at`).
  9. Referrer's account is not deleted (`is_deleted == False`).
  10. Reward has been granted to the referee.
- **Condition 2 (Legitimate Incomplete Referral):** Valid if:
  1. Referral status is either `"Menunggu"` (Pending) or `"Tidak Berhasil"` (Failed).
  2. No reward value is assigned (`num_reward_days == 0`).

### 4.2 Invalid / Fraud Conditions
- **Condition 1:** Reward value > 0 and referral status is not `"Berhasil"`.
- **Condition 2:** Reward value > 0 and there is no `transaction_id`.
- **Condition 3:** No reward value assigned, has `transaction_id`, transaction is `"PAID"`, and occurred after referral creation.
- **Condition 4:** Referral status is `"Berhasil"` and reward value is null or 0.
- **Condition 5:** Transaction occurred before referral creation (anomalous backdating).

### 4.3 Validation Results on the 46 Referrals

| Referral Status | Valid (`True`) | Invalid (`False`) | Total |
| :--- | :---: | :---: | :---: |
| **Berhasil** | 3 | 5 | 8 |
| **Menunggu** | 20 | 9 | 29 |
| **Tidak Berhasil** | 4 | 5 | 9 |
| **Total** | **27** | **19** | **46** |

---

## 5. Critical Analysis: Business Logic Contradictions & Edge Cases

The prompt explicitly states: *"Finding any invalid business logic in these rules themselves is a plus."* During implementation, three critical rule conflicts were discovered:

### Contradiction 1: Valid Condition 2 vs. Invalid Condition 3
- **The Conflict:** Valid Condition 2 states that a referral with status `"Menunggu"` or `"Tidak Berhasil"` and 0 reward days is **VALID**. However, Invalid Condition 3 states that if a referral has 0 reward days, has a transaction ID, that transaction is `"PAID"`, and occurred after the referral, it is **INVALID**.
- **Business Implication:** If an invited user signs up, the referral remains marked as `"Menunggu"`, but the user subsequently purchases a membership at the gym, the referral meets Valid Condition 2, yet triggers Invalid Condition 3.
- **Resolution:** In financial fraud engineering, invalidating/fraud rules take precedence over passive valid rules. The pipeline treats Invalid Condition 3 as a priority fraud flag (flagging potential commission leakage or unfulfilled rewards).

### Contradiction 2: Valid Condition 1 (Rule 10) vs. Source Data Reality
- **The Conflict:** Condition 1 Rule 10 requires `"The reward has been granted to the referee"` (`is_reward_granted == True`).
- **Source Data Discrepancy:** In `user_referral_logs.csv`, records with `is_reward_granted == True` were all created in July 2024 for referral IDs that do not exist within `user_referrals.csv` (which covers March–May 2024). The legitimate `"Berhasil"` referrals in the dataset (Rows 4, 6, 9) have `is_reward_granted: False` in their audit log because rewards had not yet been provisioned at the time of log snapshot.
- **Resolution:** If Rule 10 is strictly enforced, exactly **0** successful referrals in the dataset would ever be valid. However, the sample report provided in the test requirements explicitly displays a `"Berhasil"` row with `is_business_logic_valid: TRUE`. The pipeline by default evaluates eligibility for reward qualification (marking the 3 legitimate successful referrals as `True`), while providing a `--strict-reward-grant` flag for strict audit mode.

### Contradiction 3: Invalid Condition 5 (Causality & Backdating)
- **The Conflict:** In 3 records, transactions occurred *before* the referral was registered.
- **Fraud Insight:** This represents retroactive attribution fraud: gym sales staff or members creating a referral record *after* a customer had already walked in and paid, attempting to claim illegitimate referral credit for organic walk-in sales. Condition 5 correctly flags this behavior.

---

## 6. Repository & Project Structure

```
stage-0-referral-program/
├── Dockerfile                    # Containerization definition
├── README.md                     # Comprehensive documentation
├── requirements.txt              # Python dependencies (pandas, openpyxl, pytz)
├── data/                         # 7 source CSV files
│   ├── lead_log.csv
│   ├── paid_transactions.csv
│   ├── referral_rewards.csv
│   ├── user_logs.csv
│   ├── user_referral_logs.csv
│   ├── user_referral_statuses.csv
│   └── user_referrals.csv
├── output/                       # Output artifacts
│   ├── referral_report.csv       # The final 46-row report
│   ├── data_profiling.xlsx       # Detailed multi-tab Excel data profiling
│   ├── data_profiling.md         # Markdown version of data profiling
│   └── data_dictionary.xlsx      # Business data dictionary in Excel format
└── src/
    ├── pipeline.py               # Main ETL and fraud validation pipeline
    ├── profiler.py               # Source tables profiling script
    └── generate_dictionary.py    # Excel data dictionary generator
```

---

## 7. How to Run

### Option A: Local Python Environment

1. **Activate virtual environment & install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r stage-0-referral-program/requirements.txt
   ```

2. **Run Data Profiling:**
   ```bash
   python stage-0-referral-program/src/profiler.py \
     --data-dir stage-0-referral-program/data \
     --output-dir stage-0-referral-program/output
   ```

3. **Run ETL & Anti-Fraud Pipeline (produces `referral_report.csv`):**
   ```bash
   python stage-0-referral-program/src/pipeline.py \
     --data-dir stage-0-referral-program/data \
     --output-dir stage-0-referral-program/output
   ```

4. **Generate Business Data Dictionary:**
   ```bash
   python stage-0-referral-program/src/generate_dictionary.py \
     --output-dir stage-0-referral-program/output
   ```

---

### Option B: Docker Container (Host Output Mount)

The Dockerfile is containerized so that the application executes in an isolated container while **exporting the final report outside the container onto your host machine**.

1. **Build the Docker Image:**
   ```bash
   cd stage-0-referral-program
   docker build -t referral-pipeline .
   ```

2. **Run the Container and Export Report to Host:**
   ```bash
   docker run --rm \
     -v "$(pwd)/data:/app/data:ro" \
     -v "$(pwd)/output:/app/output" \
     referral-pipeline
   ```
   *Explanation:*
   - `-v "$(pwd)/data:/app/data:ro"`: Mounts host input data as read-only.
   - `-v "$(pwd)/output:/app/output"`: Mounts host output directory so `referral_report.csv` is written directly to your local machine.

---

## 8. Final Report Output Schema (22 Columns)

| # | Column Name | Data Type | Sample Value | Description |
| :-: | :--- | :--- | :--- | :--- |
| 1 | `referral_details_id` | INTEGER | `30` | Unique referral log ID |
| 2 | `referral_id` | STRING | `"9e9324e6fde29bb0d230654b38ccfdd4"` | Unique referral ID |
| 3 | `referral_source` | STRING | `"Draft Transaction"` | Initcap source channel |
| 4 | `referral_source_category` | STRING | `"Offline"` | Categorized channel |
| 5 | `referral_at` | DATETIME | `"2024-05-14 13:17:03"` | Local creation timestamp |
| 6 | `referrer_id` | STRING | `"f2de40c8394f4ea9a6aa49965380dd8f"` | Referrer member ID |
| 7 | `referrer_name` | STRING | `"2Eb4B6E1Ee9574C9E4A5F7E7E9B09280"` | Initcap referrer name |
| 8 | `referrer_phone_number` | STRING | `"d02b067e0f767dbb4564526385f49d84"` | Referrer contact |
| 9 | `referrer_homeclub` | STRING | `"PLUIT"` | Uppercase club name |
| 10 | `referee_id` | STRING | `"d1b90f8e27b5ec0d37f180aed67d76b4"` | Referee user/lead ID |
| 11 | `referee_name` | STRING | `"2E68F7F5C8854Bd2Cf2B5Ff55Bc7E780"` | Initcap referee name |
| 12 | `referee_phone` | STRING | `"321b0102e766ef73b63d1bd797203c02"` | Referee contact |
| 13 | `referral_status` | STRING | `"Berhasil"` | Referral status |
| 14 | `num_reward_days` | INT | `20` | Free membership reward days |
| 15 | `transaction_id` | STRING | `"e05121ea99fed4f4c5224a4667bb3dad"` | Linked purchase ID |
| 16 | `transaction_status` | STRING | `"Paid"` | Payment status |
| 17 | `transaction_at` | DATETIME | `"2024-05-14 13:17:03"` | Local transaction timestamp |
| 18 | `transaction_location` | STRING | `"ADITYAWARMAN"` | Uppercase club location |
| 19 | `transaction_type` | STRING | `"New"` | Initcap purchase type |
| 20 | `updated_at` | DATETIME | `"2024-05-14 13:17:34"` | Local record update timestamp |
| 21 | `reward_granted_at` | DATETIME | `"2024-05-14 13:17:36"` | Local reward fulfillment timestamp |
| 22 | `is_business_logic_valid` | BOOLEAN | `True` | Anti-fraud compliance verdict |
