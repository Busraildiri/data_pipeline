# business_rule_validator.py
# Groupby ile çalışır: kargonun TÜM geçmişini (event sayıları, context) görmesi gerekir.

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from business_rules import MAX_TRANSFER_HOPS, MAX_DELIVERY_ATTEMPTS, can_cancel


def validate_transfer_hops(event_list: list[str]) -> list[str]:
    """TRANSFER_IN sayısı limiti aşıyor mu?"""
    transfer_in_count = event_list.count("TRANSFER_IN")
    if transfer_in_count > MAX_TRANSFER_HOPS:
        return [f"exceeds_max_transfer_hops: {transfer_in_count} > {MAX_TRANSFER_HOPS}"]
    return []


def validate_delivery_attempts(event_list: list[str]) -> list[str]:
    """OUT_FOR_DELIVERY sayısı limiti aşıyor mu?"""
    attempt_count = event_list.count("OUT_FOR_DELIVERY")
    if attempt_count > MAX_DELIVERY_ATTEMPTS:
        return [f"exceeds_max_delivery_attempts: {attempt_count} > {MAX_DELIVERY_ATTEMPTS}"]
    return []


def validate_cancellation(event_list: list[str]) -> list[str]:
    """CANCELLED, sadece CREATED'dan hemen sonra mı geldi?"""
    if "CANCELLED" in event_list:
        cancel_index = event_list.index("CANCELLED")
        if cancel_index != 1:  # index 0 = CREATED, index 1 = CANCELLED olmalı
            return ["invalid_cancellation: CANCELLED only allowed right after CREATED"]
    return []