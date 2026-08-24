CREATE SCHEMA IF NOT EXISTS gold;

CREATE OR REPLACE VIEW gold.current_shipment_state AS
SELECT DISTINCT ON (order_key)
    order_key,
    source_owner,
    event_type AS current_state,
    event_time AS state_since
FROM silver.shipment_events
ORDER BY order_key, event_time DESC;

CREATE OR REPLACE VIEW gold.damage_rate_by_category AS
SELECT
    o.category,
    o.source_owner,
    COUNT(*) FILTER (WHERE e.event_type = 'DELIVERED') AS total_deliveries,
    COUNT(*) FILTER (WHERE e.event_type = 'DELIVERED' AND e.is_damaged = true) AS damaged_deliveries,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE e.event_type = 'DELIVERED' AND e.is_damaged = true)
        / NULLIF(COUNT(*) FILTER (WHERE e.event_type = 'DELIVERED'), 0), 2
    ) AS damage_rate_percent
FROM silver.orders o
JOIN silver.shipment_events e ON o.order_key = e.order_key
GROUP BY o.category, o.source_owner;

CREATE OR REPLACE VIEW gold.branch_performance AS
WITH delivery_times AS (
    SELECT
        o.order_key,
        o.source_owner,
        o.category,
        o.order_status,
        MIN(e.event_time) FILTER (WHERE e.event_type = 'CREATED') AS created_time,
        MIN(e.event_time) FILTER (WHERE e.event_type = 'DELIVERED') AS delivered_time
    FROM silver.orders o
    JOIN silver.shipment_events e ON o.order_key = e.order_key
    GROUP BY o.order_key, o.source_owner, o.category, o.order_status
)
SELECT
    source_owner,
    COUNT(*) AS total_orders,
    COUNT(*) FILTER (WHERE order_status = 'CANCELLED') AS cancelled_orders,
    ROUND(100.0 * COUNT(*) FILTER (WHERE order_status = 'CANCELLED') / COUNT(*), 2) AS cancellation_rate_percent,
    COUNT(delivered_time) AS delivered_orders,
    ROUND(AVG(EXTRACT(EPOCH FROM (delivered_time - created_time)) / 3600.0)
          FILTER (WHERE delivered_time IS NOT NULL), 1) AS avg_delivery_hours
FROM delivery_times
GROUP BY source_owner;