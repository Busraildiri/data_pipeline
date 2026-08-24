import unittest

import pandas as pd

from src.transform.event_transformer import transform_courier_events, transform_transfer_events
from src.transform.order_transformer import transform_orders


class TransformerTests(unittest.TestCase):
    def test_order_key_is_namespaced(self):
        raw = pd.DataFrame([{
            "order_id": "ORD1", "product_category": "ELECTRONICS",
            "sender_city": "Istanbul", "receiver_city": "Ankara",
            "order_status": "ACTIVE", "created_at": pd.Timestamp("2026-01-01"),
            "cancelled_at": None,
        }])
        result = transform_orders(raw, "mysql", "Tayna")
        self.assertEqual(result.loc[0, "order_key"], "tayna_ORD1")

    def test_transfer_hops_use_chronological_order(self):
        raw = pd.DataFrame([
            {"id": 4, "shipment_id": "S1", "event_type": "TRANSFER_OUT", "event_time": pd.Timestamp("2026-01-04")},
            {"id": 1, "shipment_id": "S1", "event_type": "TRANSFER_IN", "event_time": pd.Timestamp("2026-01-01")},
            {"id": 3, "shipment_id": "S1", "event_type": "TRANSFER_IN", "event_time": pd.Timestamp("2026-01-03")},
            {"id": 2, "shipment_id": "S1", "event_type": "TRANSFER_OUT", "event_time": pd.Timestamp("2026-01-02")},
        ])
        result = transform_transfer_events(raw, {"S1": "tayna_ORD1"}, "mysql", "Tayna")
        self.assertEqual(result["hop_number"].tolist(), [1, 1, 2, 2])
        self.assertEqual(result["event_type"].tolist(), [
            "TRANSFER_IN", "TRANSFER_OUT", "TRANSFER_IN", "TRANSFER_OUT"
        ])

    def test_delivery_attempts_use_chronological_order(self):
        raw = pd.DataFrame([
            {"id": 2, "shipment_id": "S1", "event_type": "DELIVERY_FAILED", "event_time": pd.Timestamp("2026-01-02"), "is_damaged": None},
            {"id": 1, "shipment_id": "S1", "event_type": "OUT_FOR_DELIVERY", "event_time": pd.Timestamp("2026-01-01"), "is_damaged": None},
            {"id": 3, "shipment_id": "S1", "event_type": "OUT_FOR_DELIVERY", "event_time": pd.Timestamp("2026-01-03"), "is_damaged": None},
        ])
        result = transform_courier_events(raw, {"S1": "tayna_ORD1"}, "mysql", "Tayna")
        self.assertEqual(result["delivery_attempt_number"].tolist(), [1, 1, 2])


if __name__ == "__main__":
    unittest.main()
