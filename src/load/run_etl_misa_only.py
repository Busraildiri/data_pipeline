import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.extract.postgres_extractor import extract_table
from src.transform.order_transformer import transform_orders
from src.transform.event_transformer import build_all_events
from src.load.silver_writer import write_orders, write_events

SOURCE_SYSTEM = "postgres"
SOURCE_OWNER = "Misa"


def run():
    orders_raw = extract_table("orders")
    transfer_raw = extract_table("transfer_events")
    branch_raw = extract_table("branch_events")
    courier_raw = extract_table("courier_events")

    orders_transformed = transform_orders(orders_raw, SOURCE_SYSTEM, SOURCE_OWNER)
    events = build_all_events(
        orders_raw, orders_transformed, transfer_raw, branch_raw, courier_raw,
        SOURCE_SYSTEM, SOURCE_OWNER
    )

    write_orders(orders_transformed)
    write_events(events)

    print("\nMişa/Postgres tarafı silver'a yazıldı.")


if __name__ == "__main__":
    run()