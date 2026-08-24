import unittest

from src.transform.business_rules import (
    can_add_transfer_hop, can_cancel, can_retry_delivery,
    resolve_delivery_failed_status,
)


class BusinessRuleTests(unittest.TestCase):
    def test_transfer_hop_limit_is_two(self):
        self.assertTrue(can_add_transfer_hop(1))
        self.assertFalse(can_add_transfer_hop(2))

    def test_delivery_attempt_limit_is_two(self):
        self.assertTrue(can_retry_delivery(1))
        self.assertFalse(can_retry_delivery(2))

    def test_final_failure_status(self):
        self.assertEqual(resolve_delivery_failed_status(1), "DELIVERY_RETRY_PENDING")
        self.assertEqual(resolve_delivery_failed_status(2), "DELIVERY_FAILED_FINAL")

    def test_cancellation_only_after_created(self):
        self.assertTrue(can_cancel("CREATED"))
        self.assertFalse(can_cancel("IN_TRANSIT"))
