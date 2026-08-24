# table_mapper.py
# Bir shipment'ın events listesini, ortak şemadaki 4 tabloya (orders, transfer_events,
# branch_events, courier_events) ayrıştırır.

import uuid


def generate_center_id() -> str:
    return f"TC{uuid.uuid4().hex[:4].upper()}"


def generate_branch_id() -> str:
    return f"BR{uuid.uuid4().hex[:4].upper()}"


def generate_courier_id() -> str:
    return f"CR{uuid.uuid4().hex[:4].upper()}"


def split_shipment_to_tables(shipment: dict, order_record: dict) -> dict:
    """
    Bir shipment'ın event geçmişini ortak şemadaki tablolara ayırır.
    order_record: shipment_factory.create_new_shipment()'ın döndürdüğü orijinal sipariş kaydı.
    Döner: {"orders": dict, "transfer_events": list, "branch_events": list, "courier_events": list}
    """
    order_row = dict(order_record)
    order_row["order_status"] = "ACTIVE"
    order_row["cancelled_at"] = None

    transfer_events = []
    branch_events = []
    courier_events = []

    # Bu shipment için sabit ID'ler (aynı şube/kurye tekrar kullanılabilir varsayımıyla)
    branch_id = generate_branch_id()
    courier_id = generate_courier_id()
    transfer_hop_centers = []  # her yeni TRANSFER_IN'de yeni bir center_id atanır

    for event in shipment["events"]:
        event_type = event["event_type"]
        event_time = event["event_time"]

        if event_type == "CREATED":
            continue  # zaten orders tablosunda

        elif event_type == "CANCELLED":
            order_row["order_status"] = "CANCELLED"
            order_row["cancelled_at"] = event_time

        elif event_type in ("TRANSFER_IN", "TRANSFER_OUT"):
            if event_type == "TRANSFER_IN":
                transfer_hop_centers.append(generate_center_id())
            center_id = transfer_hop_centers[-1] if transfer_hop_centers else generate_center_id()
            transfer_events.append({
                "shipment_id": shipment["shipment_id"],
                "center_id": center_id,
                "event_type": event_type,
                "event_time": event_time,
            })

        elif event_type in ("BRANCH_IN", "COURIER_ASSIGNED"):
            branch_events.append({
                "shipment_id": shipment["shipment_id"],
                "branch_id": branch_id,
                "event_type": event_type,
                "event_time": event_time,
            })

        elif event_type in ("OUT_FOR_DELIVERY", "DELIVERED", "DELIVERY_FAILED"):
            courier_events.append({
                "shipment_id": shipment["shipment_id"],
                "courier_id": courier_id,
                "event_type": event_type,
                "event_time": event_time,
                "delivery_result": event.get("delivery_result"),
                "is_damaged": event.get("is_damaged"),
            })

    return {
        "orders": order_row,
        "transfer_events": transfer_events,
        "branch_events": branch_events,
        "courier_events": courier_events,
    }