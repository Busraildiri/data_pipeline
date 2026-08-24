# lifecycle_validator.py
# Satır/event bazlı çalışır: tek bir event'in, kargonun bir önceki event'inden sonra
# gelip gelemeyeceğini kontrol eder. Limitleri bilmez — sadece SIRA'yı bilir.

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from lifecycle import TRANSITIONS, TERMINAL_STATUSES


def is_valid_transition(previous_event: str, new_event: str) -> bool:
    """
    previous_event'ten sonra new_event gelebilir mi?
    previous_event None ise (kargonun ilk event'i), sadece CREATED geçerlidir.
    """
    if previous_event is None:
        return new_event == "CREATED"

    allowed_next_events = TRANSITIONS.get(previous_event, [])
    return new_event in allowed_next_events


def validate_shipment_sequence(event_list: list[str]) -> list[str]:
    """
    Bir kargonun TÜM event sırasını baştan sona kontrol eder.
    Geçersiz geçişleri (hata mesajı olarak) bir listede döner. Boş liste = her şey geçerli.
    """
    errors = []
    previous_event = None
    for event in event_list:
        if not is_valid_transition(previous_event, event):
            errors.append(f"Invalid sequence: {previous_event} -> {event}")
        previous_event = event
    return errors