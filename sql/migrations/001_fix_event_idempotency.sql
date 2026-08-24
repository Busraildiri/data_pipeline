BEGIN;

-- Eski nullable UNIQUE constraint NULL değerli eventleri tekrar kabul ediyordu.
ALTER TABLE silver.shipment_events
DROP CONSTRAINT IF EXISTS uq_shipment_events_natural_key;

-- Aynı doğal anahtara sahip mevcut kayıtların en eski event_id'sini koru.
WITH ranked_events AS (
    SELECT
        event_id,
        ROW_NUMBER() OVER (
            PARTITION BY
                order_key,
                event_type,
                event_time,
                COALESCE(hop_number, 0),
                COALESCE(delivery_attempt_number, 0)
            ORDER BY event_id
        ) AS row_number
    FROM silver.shipment_events
)
DELETE FROM silver.shipment_events AS event
USING ranked_events AS ranked
WHERE event.event_id = ranked.event_id
  AND ranked.row_number > 1;

CREATE UNIQUE INDEX IF NOT EXISTS uq_shipment_events_natural_key
ON silver.shipment_events (
    order_key,
    event_type,
    event_time,
    COALESCE(hop_number, 0),
    COALESCE(delivery_attempt_number, 0)
);

COMMIT;
