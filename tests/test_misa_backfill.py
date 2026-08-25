import os
import unittest
from datetime import date, datetime
from unittest.mock import patch

from src.mock_generator.misa_backfill import build_backfill_shipments
from src.mock_generator.progression_engine import resolve_event_time


class MisaBackfillTests(unittest.TestCase):
    def test_misa_event_time_has_minimum_delay(self):
        shipment = {
            "events": [{"event_type": "CREATED", "event_time": datetime(2026, 8, 20, 9)}]
        }
        with patch.dict(os.environ, {"BRANCH_NAME": "Misa"}):
            resolved = resolve_event_time(
                shipment,
                "TRANSFER_IN",
                datetime(2026, 8, 20, 9),
            )

        self.assertGreaterEqual(
            resolved,
            datetime(2026, 8, 20, 12),
        )

    def test_tayna_event_time_is_not_changed(self):
        requested = datetime(2026, 8, 20, 9)
        shipment = {
            "events": [{"event_type": "CREATED", "event_time": requested}]
        }
        with patch.dict(
            os.environ,
            {"BRANCH_NAME": "Tayna", "MOCK_TARGET": "mysql"},
        ):
            resolved = resolve_event_time(shipment, "TRANSFER_IN", requested)

        self.assertEqual(resolved, requested)

    def test_backfill_has_realistic_ordered_delivery_times(self):
        shipments = build_backfill_shipments(
            date(2026, 8, 20),
            10,
            {"COSMETICS": (85, 0), "ELECTRONICS": (91, 9)},
        )

        self.assertEqual(len(shipments), 10)
        for shipment in shipments:
            event_times = [event["event_time"] for event in shipment["events"]]
            self.assertEqual(event_times, sorted(event_times))
            delivery_hours = (
                event_times[-1] - event_times[0]
            ).total_seconds() / 3600
            self.assertGreaterEqual(delivery_hours, 42)
            self.assertLessEqual(delivery_hours, 72)

    def test_cosmetics_damage_moves_toward_four_percent(self):
        shipments = build_backfill_shipments(
            date(2026, 8, 20),
            40,
            {"COSMETICS": (85, 0), "ELECTRONICS": (91, 9)},
        )
        cosmetics = [
            shipment for shipment in shipments
            if shipment["product_category"] == "COSMETICS"
        ]
        damaged = sum(
            shipment["events"][-1]["is_damaged"] for shipment in cosmetics
        )

        self.assertEqual(damaged, 4)
        self.assertAlmostEqual(damaged / (85 + len(cosmetics)), 0.04, places=2)


if __name__ == "__main__":
    unittest.main()
