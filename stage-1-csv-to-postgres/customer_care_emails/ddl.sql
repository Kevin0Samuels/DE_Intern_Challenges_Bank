CREATE TABLE IF NOT EXISTS raw_customer_care_emails (
    thread_id VARCHAR(64) PRIMARY KEY,
    subject VARCHAR(255),
    sender VARCHAR(255) NOT NULL,
    receiver VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    message_body TEXT,
    email_types VARCHAR(100),
    email_status VARCHAR(50),
    email_criticality VARCHAR(50),
    product_types VARCHAR(100),
    agent_effectivity VARCHAR(50),
    agent_efficiency VARCHAR(50),
    customer_satisfaction NUMERIC(4, 2),
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);