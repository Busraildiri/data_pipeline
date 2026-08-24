CREATE SCHEMA IF NOT EXISTS silver;

CREATE TABLE IF NOT EXISTS silver.orders (
    order_key       VARCHAR(50) PRIMARY KEY,
    source_order_id VARCHAR(50) NOT NULL,
    source_system   VARCHAR(20) NOT NULL,
    source_owner    VARCHAR(20) NOT NULL,
    category        VARCHAR(30),
    sender_city     VARCHAR(50),
    receiver_city   VARCHAR(50),
    order_status    VARCHAR(20),
    created_at      TIMESTAMP NOT NULL,
    cancelled_at    TIMESTAMP,
    loaded_at       TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS silver.shipment_events (
    event_id                 SERIAL PRIMARY KEY,
    order_key                VARCHAR(50) NOT NULL REFERENCES silver.orders(order_key),
    source_system            VARCHAR(20) NOT NULL,
    source_owner             VARCHAR(20) NOT NULL,
    event_type               VARCHAR(30) NOT NULL,
    event_time                TIMESTAMP NOT NULL,
    hop_number                INT,
    delivery_attempt_number   INT,
    is_damaged                BOOLEAN,
    loaded_at                 TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_shipment_events_order_key ON silver.shipment_events(order_key);
CREATE INDEX IF NOT EXISTS idx_shipment_events_event_type ON silver.shipment_events(event_type);
CREATE INDEX IF NOT EXISTS idx_shipment_events_event_time ON silver.shipment_events(event_time);

-- Idempotent ETL için: aynı event'in tekrar eklenmesini engeller
ALTER TABLE silver.shipment_events
ADD CONSTRAINT uq_shipment_events_natural_key
UNIQUE (order_key, event_type, event_time, hop_number, delivery_attempt_number);