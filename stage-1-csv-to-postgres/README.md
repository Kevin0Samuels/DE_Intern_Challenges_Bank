# Stage 1: Local CSV → PostgreSQL via Dockerized Airflow

## Objective
Build an automated, containerized **Apache Airflow** pipeline that ingests a local CSV file, validates it against a strict **schema contract** (`schema.yaml`), transforms it, and loads it into a **PostgreSQL** table idempotently.

This stage uses the **`customer_care_emails`** dataset (Appendix Code `102` / `129`, Analysis Status: `Completed/Completed`).

---

## Architecture & Data Flow

```text
customer_care_emails/
  manifest.yaml ──┐
  schema.yaml   ──┼──► [ Airflow Orchestrator (Docker) ]
  customer_care ──┘       │               │              │
  _emails.csv        validate_schema -> transform -> load_to_postgres
                       (contract)       (clean)       (PostgresHook)
                                                             │
                                                             ▼
                                                    PostgreSQL Table
                                              (raw_customer_care_emails)
```

---

## Directory Layout
```text
stage-1-csv-to-postgres/
├── .env.example                                  # Template for environment secrets
├── .env                                          # Local environment configuration
├── docker-compose.yaml                           # Airflow + PostgreSQL stack definition
├── init-multiple-dbs.sh                          # Helper script initializing warehouse DB
├── customer_care_emails/
│   ├── manifest.yaml                             # Dataset metadata & Appendix status
│   ├── schema.yaml                               # Schema contract (columns, types, PK)
│   ├── ddl.sql                                   # Target table DDL
│   └── customer_care_emails.csv                  # Source CSV dataset (2,259 records)
├── dags/
│   └── load_customer_care_emails_to_postgres.py  # End-to-end Airflow DAG
└── README.md                                     # Runbook & verification guide
```

---

## Prerequisites
* **Docker & Docker Compose** installed and running.
* Modern web browser (to access Airflow UI on `:8080`).

---

## Getting Started (One-Command Setup)

1. **Configure Environment:**
   ```bash
   cp .env.example .env
   ```

2. **Start the Stack:**
   ```bash
   docker compose up -d
   ```

3. **Verify Containers are Healthy:**
   ```bash
   docker compose ps
   ```

4. **Access the Airflow UI:**
   * URL: `http://localhost:8080`
   * Username: `admin`
   * Password: `admin`

---

## Pipeline Operations

### Trigger Ingestion
1. In the Airflow UI, find `load_customer_care_emails_to_postgres`.
2. Toggle the switch to **Unpause**.
3. Click the **Play button (▶) → Trigger DAG**.

### Tasks Executed:
1. `check_manifest_status`: Confirms dataset status in `manifest.yaml` is approved (`Completed/Completed`).
2. `init_target_table`: Executes `ddl.sql` to ensure `raw_customer_care_emails` table exists in PostgreSQL.
3. `validate_schema_contract`: Validates CSV against `schema.yaml` contract (fails on column or constraint mismatch).
4. `transform_data`: Cleans whitespace, formats timestamps to ISO8601 UTC, and casts satisfaction scores.
5. `load_to_postgres`: Idempotently upserts records via `PostgresHook` using `ON CONFLICT (thread_id) DO UPDATE`.

---

## Verification & Queries

### 1. Check Loaded Records
```bash
docker exec -it stage1_postgres psql -U airflow -d warehouse -c \
  "SELECT count(*) AS total_rows, min(timestamp) AS earliest_email, max(timestamp) AS latest_email FROM raw_customer_care_emails;"
```

### 2. Sample Data
```bash
docker exec -it stage1_postgres psql -U airflow -d warehouse -c \
  "SELECT thread_id, sender, subject, customer_satisfaction, ingested_at FROM raw_customer_care_emails LIMIT 3;"
```

### 3. Verify Idempotency
Trigger the DAG a second time in Airflow. Query row count again: the count remains unchanged (671 unique threads), proving zero duplicate rows are created.

### 4. Verify Schema Contract Enforcement
Corrupt the header of the CSV:
```bash
python3 -c "p = 'customer_care_emails/customer_care_emails.csv'; open(p, 'w').write(open(p).read().replace('thread_id', 'bad_id', 1))"
```
Trigger the DAG in Airflow: `validate_schema_contract` will immediately fail, stopping downstream loading and preserving database integrity:
```text
ValueError: Schema Contract Violation: Missing expected columns: {'thread_id'}
```

Restore the clean CSV:
```bash
git checkout customer_care_emails/customer_care_emails.csv
```

---

## Teardown
To stop and remove containers:
```bash
docker compose down
```
To also delete the database volume:
```bash
docker compose down -v
```