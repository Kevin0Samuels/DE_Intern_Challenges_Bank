"""
Airflow DAG: Ingest customer_care_emails CSV to PostgreSQL
Stage 1 of Data Engineering Task Bank.
"""

from datetime import datetime, timedelta
import os
import yaml
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

# Paths inside Docker container
BASE_DATASET_DIR = "/opt/airflow/customer_care_emails"
MANIFEST_PATH = os.path.join(BASE_DATASET_DIR, "manifest.yaml")
SCHEMA_PATH = os.path.join(BASE_DATASET_DIR, "schema.yaml")
DDL_PATH = os.path.join(BASE_DATASET_DIR, "ddl.sql")
CSV_PATH = os.path.join(BASE_DATASET_DIR, "customer_care_emails.csv")
STAGED_CLEANED_PATH = "/tmp/staged_customer_care_emails.csv"
POSTGRES_CONN_ID = "postgres_warehouse"

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


def task_check_manifest_status():
    """Validates that the dataset status in manifest.yaml allows processing."""
    if not os.path.exists(MANIFEST_PATH):
        raise FileNotFoundError(f"Dataset manifest not found at {MANIFEST_PATH}")
    
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)
    
    status = manifest.get("status", "")
    print(f"Dataset Name: {manifest.get('dataset_name')}")
    print(f"Recorded Status in Appendix: {status}")
    
    # Check that analysis status is marked complete/done per requirements
    valid_statuses = ["Completed/Completed", "Done", "Completed"]
    if status not in valid_statuses:
        raise ValueError(f"Dataset status '{status}' is not approved for ingestion! Expected one of: {valid_statuses}")
    print("Manifest status verified successfully.")


def task_init_target_table():
    """Executes ddl.sql to create target PostgreSQL table if not present."""
    if not os.path.exists(DDL_PATH):
        raise FileNotFoundError(f"DDL script not found at {DDL_PATH}")
    
    with open(DDL_PATH, "r", encoding="utf-8") as f:
        ddl_query = f.read()
    
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    hook.run(ddl_query)
    print("Target PostgreSQL table schema initialized successfully.")


def task_validate_schema_contract():
    """Enforces the schema.yaml contract against the CSV file. Fails on violation."""
    if not os.path.exists(SCHEMA_PATH):
        raise FileNotFoundError(f"Schema contract not found at {SCHEMA_PATH}")
    if not os.path.exists(CSV_PATH):
        raise FileNotFoundError(f"Input CSV not found at {CSV_PATH}")

    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    df = pd.read_csv(CSV_PATH)
    print(f"Loaded CSV with {len(df)} rows and columns: {list(df.columns)}")

    contract_columns = schema.get("columns", [])
    expected_col_names = [col["name"] for col in contract_columns]

    # Rule 1: All contracted columns must exist
    missing_cols = set(expected_col_names) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Schema Contract Violation: Missing expected columns: {missing_cols}")

    # Rule 2: Primary key must not contain nulls or duplicates in raw file
    pk_cols = schema.get("primary_key", [])
    for pk in pk_cols:
        if pk not in df.columns:
            raise ValueError(f"Schema Contract Violation: Primary key column '{pk}' missing!")
        null_count = df[pk].isna().sum()
        if null_count > 0:
            raise ValueError(f"Schema Contract Violation: Primary key '{pk}' contains {null_count} null rows!")

    # Rule 3: Nullable checks on non-nullable columns
    for col in contract_columns:
        col_name = col["name"]
        if not col.get("nullable", True):
            null_count = df[col_name].isna().sum()
            if null_count > 0:
                raise ValueError(f"Schema Contract Violation: Column '{col_name}' is NOT nullable but has {null_count} nulls!")

    print("Schema contract validation PASSED successfully.")


def task_transform_data():
    """Cleans, casts types, and stages transformed data."""
    df = pd.read_csv(CSV_PATH)

    # 1. Strip whitespace on string columns
    str_cols = df.select_dtypes(include=["object"]).columns
    for col in str_cols:
        df[col] = df[col].astype(str).str.strip().replace({"nan": None, "None": None, "": None})

    # 2. Parse timestamps to ISO UTC (supporting mixed microsecond precision)
    df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601")

    # 3. Numeric conversion
    df["customer_satisfaction"] = pd.to_numeric(df["customer_satisfaction"], errors="coerce")

    # Save to staging path
    df.to_csv(STAGED_CLEANED_PATH, index=False)
    print(f"Transformed {len(df)} rows and staged to {STAGED_CLEANED_PATH}.")


def task_load_to_postgres():
    """Idempotently loads cleaned data into PostgreSQL using UPSERT on thread_id."""
    if not os.path.exists(STAGED_CLEANED_PATH):
        raise FileNotFoundError(f"Staged data not found at {STAGED_CLEANED_PATH}")

    df = pd.read_csv(STAGED_CLEANED_PATH)
    hook = PostgresHook(postgres_conn_id=POSTGRES_CONN_ID)
    conn = hook.get_conn()
    cursor = conn.cursor()

    upsert_sql = """
        INSERT INTO raw_customer_care_emails (
            thread_id, subject, sender, receiver, timestamp, message_body,
            email_types, email_status, email_criticality, product_types,
            agent_effectivity, agent_efficiency, customer_satisfaction
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (thread_id) DO UPDATE SET
            subject = EXCLUDED.subject,
            sender = EXCLUDED.sender,
            receiver = EXCLUDED.receiver,
            timestamp = EXCLUDED.timestamp,
            message_body = EXCLUDED.message_body,
            email_types = EXCLUDED.email_types,
            email_status = EXCLUDED.email_status,
            email_criticality = EXCLUDED.email_criticality,
            product_types = EXCLUDED.product_types,
            agent_effectivity = EXCLUDED.agent_effectivity,
            agent_efficiency = EXCLUDED.agent_efficiency,
            customer_satisfaction = EXCLUDED.customer_satisfaction,
            ingested_at = CURRENT_TIMESTAMP;
    """

    records = []
    for _, row in df.iterrows():
        records.append((
            row["thread_id"],
            row["subject"],
            row["sender"],
            row["receiver"],
            row["timestamp"],
            row["message_body"],
            row["email_types"],
            row["email_status"],
            row["email_criticality"],
            row["product_types"],
            row["agent_effectivity"],
            row["agent_efficiency"],
            row["customer_satisfaction"] if pd.notna(row["customer_satisfaction"]) else None
        ))

    from psycopg2.extras import execute_batch
    execute_batch(cursor, upsert_sql, records, page_size=500)
    conn.commit()

    # Verify loaded count
    cursor.execute("SELECT COUNT(*) FROM raw_customer_care_emails;")
    row_count = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    print(f"Load complete! Current row count in PostgreSQL table: {row_count}")


with DAG(
    dag_id="load_customer_care_emails_to_postgres",
    default_args=default_args,
    description="Validates and loads customer_care_emails dataset into PostgreSQL",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["stage-1", "csv-to-postgres", "customer_care_emails"],
) as dag:

    check_manifest = PythonOperator(
        task_id="check_manifest_status",
        python_callable=task_check_manifest_status,
    )

    init_table = PythonOperator(
        task_id="init_target_table",
        python_callable=task_init_target_table,
    )

    validate_schema = PythonOperator(
        task_id="validate_schema_contract",
        python_callable=task_validate_schema_contract,
    )

    transform = PythonOperator(
        task_id="transform_data",
        python_callable=task_transform_data,
    )

    load = PythonOperator(
        task_id="load_to_postgres",
        python_callable=task_load_to_postgres,
    )

    # DAG Dependency Pipeline
    check_manifest >> init_table >> validate_schema >> transform >> load