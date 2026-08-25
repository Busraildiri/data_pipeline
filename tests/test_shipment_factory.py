import os
import sys
import types
import unittest
from datetime import datetime
from unittest.mock import patch

_faker_module = types.ModuleType("faker")
_faker_module.Faker = lambda *_args, **_kwargs: object()
_dotenv_module = types.ModuleType("dotenv")
_dotenv_module.load_dotenv = lambda: None

with patch.dict(
    sys.modules,
    {"faker": _faker_module, "dotenv": _dotenv_module},
):
    from src.mock_generator.shipment_factory import (
        DAILY_ORDER_RANGE,
        generate_daily_orders,
    )


class ShipmentFactoryTests(unittest.TestCase):
    def test_daily_order_count_stays_in_configured_range(self):
        for day_number in (1, 10, 100):
            orders = generate_daily_orders(datetime(2026, 8, 25, 9), day_number)
            self.assertGreaterEqual(len(orders), DAILY_ORDER_RANGE[0])
            self.assertLessEqual(len(orders), DAILY_ORDER_RANGE[1])


if __name__ == "__main__":
    unittest.main()
