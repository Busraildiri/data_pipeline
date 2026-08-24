import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.extract.mysql_extractor import extract_table
from src.transform.order_transformer import transform_orders
from src.transform.event_transformer import build_all_events
from src.transform.validation.pipeline_validator import validate_source_data
from src.load.silver_writer import write_to_silver

SOURCE_SYSTEM = "mysql"
SOURCE_OWNER = "Tayna"


def run():
    orders_raw = extract_table("orders")
    transfer_raw = extract_table("transfer_events")
    branch_raw = extract_table("branch_events")
    courier_raw = extract_table("courier_events")

    validate_source_data(orders_raw, transfer_raw, branch_raw, courier_raw)

    orders_transformed = transform_orders(orders_raw, SOURCE_SYSTEM, SOURCE_OWNER)
    events = build_all_events(
        orders_raw, orders_transformed, transfer_raw, branch_raw, courier_raw,
        SOURCE_SYSTEM, SOURCE_OWNER
    )

    write_to_silver(orders_transformed, events)

    print("\nTayna/MySQL tarafı silver'a yazıldı.")


if __name__ == "__main__":
    run()
