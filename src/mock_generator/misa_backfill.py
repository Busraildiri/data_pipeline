"""Misa için güvenli, idempotent geçmiş demo batch üretimi."""

import os
import random
from datetime import date, datetime, time, timedelta

try:
    from .progression_engine import DAMAGE_PROBABILITY
    from .table_mapper import split_shipment_to_tables
except ImportError:  # daily_runner.py doğrudan çalıştırıldığında
    from progression_engine import DAMAGE_PROBABILITY
    from table_mapper import split_shipment_to_tables


BACKFILL_DURATION_HOURS = (42, 72)
TURKISH_CITIES = [
    "Istanbul", "Ankara", "Izmir", "Antalya", "Bursa", "Adana", "Konya",
    "Gaziantep", "Kayseri", "Trabzon", "Samsun", "Eskisehir", "Mersin",
]


def _batch_prefix(target_date: date) -> str:
    return f"BF{target_date:%y%m%d}"


def _existing_delivery_stats(engine) -> dict[str, tuple[int, int]]:
    from sqlalchemy import text

    query = text(
        """
        SELECT
            o.product_category,
            COUNT(DISTINCT o.shipment_id) AS delivered_count,
            COUNT(DISTINCT o.shipment_id) FILTER (
                WHERE e.is_damaged IS TRUE
            ) AS damaged_count
        FROM orders o
        JOIN courier_events e ON e.shipment_id = o.shipment_id
        WHERE e.event_type = 'DELIVERED'
        GROUP BY o.product_category
        """
    )
    with engine.connect() as conn:
        rows = conn.execute(query).mappings().all()
    return {
        row["product_category"]: (
            int(row["delivered_count"]), int(row["damaged_count"])
        )
        for row in rows
    }


def _existing_branch_city(engine) -> str:
    from sqlalchemy import text

    with engine.connect() as conn:
        city = conn.execute(
            text(
                """
                SELECT sender_city
                FROM orders
                WHERE sender_city IS NOT NULL
                GROUP BY sender_city
                ORDER BY COUNT(*) DESC
                LIMIT 1
                """
            )
        ).scalar_one_or_none()
    return city or os.environ.get("BRANCH_CITY", "Istanbul")


def _damage_flags(
    category: str,
    new_count: int,
    existing_stats: dict[str, tuple[int, int]],
    rng: random.Random,
) -> list[bool]:
    existing_delivered, existing_damaged = existing_stats.get(category, (0, 0))
    target_probability = DAMAGE_PROBABILITY[category]
    desired_total_damaged = int(
        (existing_delivered + new_count) * target_probability + 0.5
    )
    required_new_damaged = min(
        new_count,
        max(0, desired_total_damaged - existing_damaged),
    )
    flags = [True] * required_new_damaged + [False] * (
        new_count - required_new_damaged
    )
    rng.shuffle(flags)
    return flags


def build_backfill_shipments(
    target_date: date,
    count: int,
    existing_stats: dict[str, tuple[int, int]],
    branch_city: str | None = None,
) -> list[dict]:
    """Tamamı geçmişte kalan, 42–72 saatlik teslimatlar üretir."""
    if count < 2:
        raise ValueError("Backfill sipariş sayısı en az 2 olmalıdır.")

    rng = random.Random(int(target_date.strftime("%Y%m%d")))
    categories = [
        "COSMETICS" if index % 2 == 0 else "ELECTRONICS"
        for index in range(count)
    ]
    category_flags = {
        category: iter(
            _damage_flags(
                category,
                categories.count(category),
                existing_stats,
                rng,
            )
        )
        for category in set(categories)
    }

    prefix = _batch_prefix(target_date)
    shipments = []
    for index, category in enumerate(categories, start=1):
        created_at = datetime.combine(target_date, time(8, 0)) + timedelta(
            minutes=rng.randint(0, 8 * 60)
        )
        duration_hours = rng.uniform(*BACKFILL_DURATION_HOURS)
        delivered_at = created_at + timedelta(hours=duration_hours)
        offsets = (0.10, 0.25, 0.50, 0.70, 0.82, 1.00)
        event_types = (
            "TRANSFER_IN",
            "TRANSFER_OUT",
            "BRANCH_IN",
            "COURIER_ASSIGNED",
            "OUT_FOR_DELIVERY",
            "DELIVERED",
        )

        resolved_branch_city = branch_city or os.environ.get(
            "BRANCH_CITY", "Istanbul"
        )
        receiver_cities = [
            city for city in TURKISH_CITIES if city != resolved_branch_city
        ]
        order = {
            "shipment_id": f"{prefix}{index:04d}",
            "order_id": f"BFORD{target_date:%y%m%d}{index:04d}",
            "created_at": created_at,
            "sender_city": resolved_branch_city,
            "receiver_city": rng.choice(receiver_cities),
            "customer_id": f"BFCUS{index:06d}",
            "service_type": rng.choice(["standard", "express"]),
            "product_category": category,
        }

        events = [{"event_type": "CREATED", "event_time": created_at}]
        for event_type, fraction in zip(event_types, offsets):
            event = {
                "event_type": event_type,
                "event_time": created_at + timedelta(
                    hours=duration_hours * fraction
                ),
            }
            if event_type == "DELIVERED":
                event["event_time"] = delivered_at
                event["is_damaged"] = next(category_flags[category])
            events.append(event)

        shipments.append(
            {
                "shipment_id": order["shipment_id"],
                "product_category": category,
                "order_record": order,
                "events": events,
            }
        )

    return shipments


def run_misa_backfill(engine, writer, target_date: date, count: int = 40):
    from sqlalchemy import text

    prefix = _batch_prefix(target_date)
    with engine.connect() as conn:
        existing_batch_count = conn.execute(
            text("SELECT COUNT(*) FROM orders WHERE shipment_id LIKE :prefix"),
            {"prefix": f"{prefix}%"},
        ).scalar_one()

    if existing_batch_count:
        print(
            f"{target_date} Misa backfill batch'i zaten var "
            f"({existing_batch_count} sipariş); yeni veri üretilmedi."
        )
        return

    existing_stats = _existing_delivery_stats(engine)
    shipments = build_backfill_shipments(
        target_date,
        count,
        existing_stats,
        _existing_branch_city(engine),
    )

    orders = []
    transfer_events = []
    branch_events = []
    courier_events = []
    for shipment in shipments:
        tables = split_shipment_to_tables(shipment, shipment["order_record"])
        tables["orders"]["order_status"] = "DELIVERED"
        orders.append(tables["orders"])
        transfer_events.extend(tables["transfer_events"])
        branch_events.extend(tables["branch_events"])
        courier_events.extend(tables["courier_events"])

    writer(
        orders,
        transfer_events,
        branch_events,
        courier_events,
        [],
    )
    damaged_count = sum(
        1
        for shipment in shipments
        if shipment["events"][-1].get("is_damaged")
    )
    print(
        f"Misa backfill tamamlandı: tarih={target_date}, sipariş={count}, "
        f"hasarlı={damaged_count}, teslimat süresi=42–72 saat."
    )
