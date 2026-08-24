# daily_runner.py
# Artımlı (incremental) günlük çalışma: DB'den açık kargoları okur,
# onları ilerletir, o günün yeni siparişlerini ekler, SADECE yeni event'leri DB'ye yazar.

from datetime import datetime, timedelta
from sqlalchemy import text

from shipment_factory import generate_daily_orders
from progression_engine import progress_all_shipments, is_terminal
from lifecycle import EVENT_STATUS_MAP, TERMINAL_STATUSES
from table_mapper import split_shipment_to_tables
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "transform"))
from business_rules import resolve_delivery_failed_status

sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), "load"))
from mysql_writer import get_engine, write_tables_to_db


def derive_current_status(shipment: dict) -> str:
    last_event = shipment["events"][-1]["event_type"]
    if last_event == "DELIVERY_FAILED":
        attempt_count = sum(1 for e in shipment["events"] if e["event_type"] == "OUT_FOR_DELIVERY")
        return resolve_delivery_failed_status(attempt_count)
    return EVENT_STATUS_MAP.get(last_event, "UNKNOWN")


def load_open_shipments_from_db(engine) -> list[dict]:
    """
    DB'den order_status='ACTIVE' olan siparişleri ve event geçmişlerini okur,
    son event'i terminal (DELIVERED/DELIVERY_FAILED_FINAL) olmayanları döner.
    """
    open_shipments = []

    with engine.connect() as conn:
        orders = conn.execute(text("SELECT * FROM orders WHERE order_status = 'ACTIVE'")).mappings().all()

        for order in orders:
            shipment_id = order["shipment_id"]
            events = [{"event_type": "CREATED", "event_time": order["created_at"]}]

            for table in ["transfer_events", "branch_events", "courier_events"]:
                rows = conn.execute(
                    text(f"SELECT event_type, event_time, delivery_result, is_damaged FROM {table} "
                         f"WHERE shipment_id = :sid" if table == "courier_events"
                         else f"SELECT event_type, event_time, NULL as delivery_result, NULL as is_damaged FROM {table} WHERE shipment_id = :sid"),
                    {"sid": shipment_id}
                ).mappings().all()
                for row in rows:
                    events.append({
                        "event_type": row["event_type"],
                        "event_time": row["event_time"],
                        "delivery_result": row.get("delivery_result"),
                        "is_damaged": row.get("is_damaged"),
                    })

            events.sort(key=lambda e: e["event_time"])
            shipment = {
                "shipment_id": shipment_id,
                "product_category": order["product_category"],
                "order_record": dict(order),
                "events": events,
            }
            if is_terminal(shipment, derive_current_status(shipment)):
                continue

            open_shipments.append(shipment)

    return open_shipments


def run_daily_update():
    engine = get_engine()
    event_time = datetime.now() - timedelta(days=1)  # sysdate-1

    with engine.connect() as conn:
        already_ran = conn.execute(
            text("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = :run_date"),
            {"run_date": event_time.date()},
        ).scalar_one()
        if already_ran:
            print(
                f"{event_time.date()} iş günü daha önce üretildi "
                f"({already_ran} sipariş); çalışma atlandı."
            )
            return

        day_count = conn.execute(
            text("SELECT COUNT(DISTINCT DATE(created_at)) FROM orders")
        ).scalar_one()

    day_number = (day_count or 0) + 1

    open_shipments = load_open_shipments_from_db(engine)
    print(f"DB'den okunan açık kargo sayısı: {len(open_shipments)}")

    # O günün yeni siparişleri
    new_orders = generate_daily_orders(event_time, day_number)
    new_shipments = [
        {
            "shipment_id": o["shipment_id"],
            "product_category": o["product_category"],
            "order_record": o,
            "events": [{"event_type": "CREATED", "event_time": o["created_at"]}],
        }
        for o in new_orders
    ]

    previous_event_counts = {s["shipment_id"]: len(s["events"]) for s in open_shipments}

    all_shipments = open_shipments + new_shipments
    all_shipments = progress_all_shipments(all_shipments, event_time)

    new_order_rows = []
    new_transfer_events = []
    new_branch_events = []
    new_courier_events = []
    order_updates = []

    for shipment in all_shipments:
        shipment_id = shipment["shipment_id"]
        is_new = shipment_id not in previous_event_counts

        if is_new:
            # Tamamen yeni kargo: tüm event geçmişini (henüz sadece CREATED + belki 1 ilerleme) işle
            tables = split_shipment_to_tables(shipment, shipment["order_record"])
            new_order_rows.append(tables["orders"])
            new_transfer_events.extend(tables["transfer_events"])
            new_branch_events.extend(tables["branch_events"])
            new_courier_events.extend(tables["courier_events"])
        else:
            # Zaten açık olan kargo: SADECE bu run'da eklenen yeni event'i yaz
            prev_count = previous_event_counts[shipment_id]
            if len(shipment["events"]) > prev_count:
                new_event = shipment["events"][-1]
                event_type = new_event["event_type"]
                event_time_val = new_event["event_time"]
                suffix = shipment_id[-4:]

                if event_type in ("TRANSFER_IN", "TRANSFER_OUT"):
                    new_transfer_events.append({
                        "shipment_id": shipment_id, "center_id": f"TC{suffix}",
                        "event_type": event_type, "event_time": event_time_val,
                    })
                elif event_type in ("BRANCH_IN", "COURIER_ASSIGNED"):
                    new_branch_events.append({
                        "shipment_id": shipment_id, "branch_id": f"BR{suffix}",
                        "event_type": event_type, "event_time": event_time_val,
                    })
                elif event_type in ("OUT_FOR_DELIVERY", "DELIVERED", "DELIVERY_FAILED"):
                    new_courier_events.append({
                        "shipment_id": shipment_id, "courier_id": f"CR{suffix}",
                        "event_type": event_type, "event_time": event_time_val,
                        "delivery_result": new_event.get("delivery_result"),
                        "is_damaged": new_event.get("is_damaged"),
                    })

                new_status = derive_current_status(shipment)
                if new_status in TERMINAL_STATUSES:
                    order_updates.append({
                        "shipment_id": shipment_id,
                        "order_status": new_status,
                        "cancelled_at": event_time_val if new_status == "CANCELLED" else None,
                    })

    write_tables_to_db(
        new_order_rows,
        new_transfer_events,
        new_branch_events,
        new_courier_events,
        order_updates,
    )

    print(f"Gün {day_number} ({event_time.date()}): {len(new_orders)} yeni sipariş, "
          f"{len(all_shipments)} kargo işlendi, "
          f"{len(new_order_rows)} yeni orders satırı yazıldı")


if __name__ == "__main__":
    run_daily_update()
