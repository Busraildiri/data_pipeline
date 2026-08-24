# progression_engine.py
# Açık (terminal olmayan) kargoları olasılıksal şekilde bir sonraki lifecycle adımına ilerletir.

import random
import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "transform"))

from lifecycle import TRANSITIONS, TERMINAL_STATUSES
from business_rules import (
    can_add_transfer_hop,
    can_retry_delivery,
    resolve_delivery_failed_status,
)

PROGRESSION_PROBABILITY = 0.7
DELIVERY_FAILURE_PROBABILITY = 0.1
CANCELLATION_PROBABILITY = 0.03

DAMAGE_PROBABILITY = {
    "ELECTRONICS": 0.08,
    "COSMETICS": 0.02,
}


def get_last_event(shipment: dict) -> str:
    return shipment["events"][-1]["event_type"]


def get_event_count(shipment: dict, event_type: str) -> int:
    return sum(1 for e in shipment["events"] if e["event_type"] == event_type)


def is_terminal(shipment: dict, current_status: str) -> bool:
    return current_status in TERMINAL_STATUSES


def choose_next_event(shipment: dict, last_event: str) -> str | None:
    candidates = TRANSITIONS.get(last_event, [])

    valid_candidates = []
    for candidate in candidates:
        if candidate == "TRANSFER_IN":
            transfer_hop_count = get_event_count(shipment, "TRANSFER_IN")
            if not can_add_transfer_hop(transfer_hop_count):
                continue
        if candidate == "OUT_FOR_DELIVERY" and last_event == "DELIVERY_FAILED":
            attempt_count = get_event_count(shipment, "OUT_FOR_DELIVERY")
            if not can_retry_delivery(attempt_count):
                continue
        valid_candidates.append(candidate)

    if not valid_candidates:
        return None

    if last_event == "CREATED":
        if "CANCELLED" in valid_candidates and random.random() < CANCELLATION_PROBABILITY:
            return "CANCELLED"
        return "TRANSFER_IN"

    if last_event == "OUT_FOR_DELIVERY":
        if random.random() < DELIVERY_FAILURE_PROBABILITY:
            return "DELIVERY_FAILED"
        return "DELIVERED"

    if last_event == "TRANSFER_OUT" and "TRANSFER_IN" in valid_candidates:
        if random.random() < 0.2:
            return "TRANSFER_IN"
        return "BRANCH_IN"

    return random.choice(valid_candidates)


def progress_shipment(shipment: dict, event_time) -> dict | None:
    if random.random() > PROGRESSION_PROBABILITY:
        return None

    last_event = get_last_event(shipment)
    next_event = choose_next_event(shipment, last_event)

    if next_event is None:
        return None

    new_event = {"event_type": next_event, "event_time": event_time}

    if next_event == "DELIVERED":
        category = shipment["product_category"]
        new_event["is_damaged"] = random.random() < DAMAGE_PROBABILITY[category]

    return new_event


def progress_all_shipments(open_shipments: list[dict], event_time) -> list[dict]:
    for shipment in open_shipments:
        new_event = progress_shipment(shipment, event_time)
        if new_event:
            shipment["events"].append(new_event)
    return open_shipments