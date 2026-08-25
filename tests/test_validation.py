import unittest
import pandas as pd

from src.transform.validation.lifecycle_validator import validate_shipment_sequence
from src.transform.validation.pipeline_validator import DataQualityError, validate_source_data
from src.transform.validation.schema_validator import validate_duplicates


class ValidationTests(unittest.TestCase):
    def test_valid_lifecycle(self):
        events = ["CREATED", "TRANSFER_IN", "TRANSFER_OUT", "BRANCH_IN",
                  "COURIER_ASSIGNED", "OUT_FOR_DELIVERY", "DELIVERED"]
        self.assertEqual(validate_shipment_sequence(events), [])

    def test_invalid_transition(self):
        self.assertTrue(validate_shipment_sequence(["CREATED", "DELIVERED"]))

    def test_duplicate_detection(self):
        frame = pd.DataFrame([
            {"shipment_id": "S1", "event_type": "CREATED", "event_time": "2026-01-01"},
            {"shipment_id": "S1", "event_type": "CREATED", "event_time": "2026-01-01"},
        ])
        self.assertEqual(len(validate_duplicates(frame)), 1)

    def test_pipeline_rejects_unknown_shipment(self):
        orders = pd.DataFrame([{"shipment_id": "S1", "created_at": pd.Timestamp("2026-01-01"), "cancelled_at": None}])
        transfer = pd.DataFrame([{"shipment_id": "UNKNOWN", "event_type": "TRANSFER_IN", "event_time": pd.Timestamp("2026-01-02")}])
        empty = pd.DataFrame(columns=["shipment_id", "event_type", "event_time"])
        with self.assertRaises(DataQualityError):
            validate_source_data(orders, transfer, empty, empty)

    def test_same_timestamp_created_then_cancelled_is_valid(self):
        timestamp = pd.Timestamp("2026-01-01 09:00:00")
        orders = pd.DataFrame([{
            "shipment_id": "S1",
            "created_at": timestamp,
            "cancelled_at": timestamp,
        }])
        empty = pd.DataFrame(
            columns=["shipment_id", "event_type", "event_time"]
        )

        validate_source_data(orders, empty, empty, empty)
