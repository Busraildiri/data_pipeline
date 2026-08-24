-- create_tables.sql
-- Misa subesi (PostgreSQL) icin ortak sema

CREATE TABLE IF NOT EXISTS orders (
    shipment_id VARCHAR(20) PRIMARY KEY,
    order_id VARCHAR(20),
    created_at TIMESTAMP,
    sender_city VARCHAR(50),
    receiver_city VARCHAR(50),
    customer_id VARCHAR(20),
    service_type VARCHAR(20),
    product_category VARCHAR(20),
    order_status VARCHAR(20),
    cancelled_at TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS transfer_events (
    id SERIAL PRIMARY KEY,
    shipment_id VARCHAR(20),
    center_id VARCHAR(20),
    event_type VARCHAR(30),
    event_time TIMESTAMP,
    FOREIGN KEY (shipment_id) REFERENCES orders(shipment_id)
);

CREATE TABLE IF NOT EXISTS branch_events (
    id SERIAL PRIMARY KEY,
    shipment_id VARCHAR(20),
    branch_id VARCHAR(20),
    event_type VARCHAR(30),
    event_time TIMESTAMP,
    FOREIGN KEY (shipment_id) REFERENCES orders(shipment_id)
);

CREATE TABLE IF NOT EXISTS courier_events (
    id SERIAL PRIMARY KEY,
    shipment_id VARCHAR(20),
    courier_id VARCHAR(20),
    event_type VARCHAR(30),
    event_time TIMESTAMP,
    delivery_result VARCHAR(50) NULL,
    is_damaged BOOLEAN NULL,
    FOREIGN KEY (shipment_id) REFERENCES orders(shipment_id)
);
