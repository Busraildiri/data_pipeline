import pandas as pd


def _shipment_to_order_key(orders_raw_df: pd.DataFrame, source_owner: str) -> dict:
    """shipment_id -> order_key eşleşmesi (orders bronze tablosundan)."""
    return {
        row["shipment_id"]: f"{source_owner.lower()}_{row['order_id']}"
        for _, row in orders_raw_df.iterrows()
    }


def transform_transfer_events(df, shipment_map, source_system, source_owner):
    df = df.sort_values(["shipment_id", "event_time", "id"], kind="stable").copy()
    df["order_key"] = df["shipment_id"].map(shipment_map)
    # Aynı shipment içinde kaçıncı hop (TRANSFER_IN+TRANSFER_OUT bir çift = 1 hop)
    df["hop_number"] = df.groupby("shipment_id").cumcount() // 2 + 1
    df["source_system"] = source_system
    df["source_owner"] = source_owner
    df["delivery_attempt_number"] = None
    df["is_damaged"] = None
    return df[["order_key", "source_system", "source_owner", "event_type",
               "event_time", "hop_number", "delivery_attempt_number", "is_damaged"]]


def transform_branch_events(df, shipment_map, source_system, source_owner):
    df = df.sort_values(["shipment_id", "event_time", "id"], kind="stable").copy()
    df["order_key"] = df["shipment_id"].map(shipment_map)
    df["source_system"] = source_system
    df["source_owner"] = source_owner
    df["hop_number"] = None
    df["delivery_attempt_number"] = None
    df["is_damaged"] = None
    return df[["order_key", "source_system", "source_owner", "event_type",
               "event_time", "hop_number", "delivery_attempt_number", "is_damaged"]]


def transform_courier_events(df, shipment_map, source_system, source_owner):
    df = df.sort_values(["shipment_id", "event_time", "id"], kind="stable").copy()
    df["order_key"] = df["shipment_id"].map(shipment_map)
    # Her shipment için kaçıncı teslimat denemesi (OUT_FOR_DELIVERY ile başlayan grup)
    df["delivery_attempt_number"] = (
        df.groupby("shipment_id")["event_type"]
        .transform(lambda s: (s == "OUT_FOR_DELIVERY").cumsum())
    )
    df["source_system"] = source_system
    df["source_owner"] = source_owner
    df["hop_number"] = None
    # is_damaged: MySQL'den float (1.0/NaN), Postgres'ten bool/None gelebilir - normalize et
    df["is_damaged"] = df["is_damaged"].map(lambda x: bool(x) if pd.notnull(x) else None)
    return df[["order_key", "source_system", "source_owner", "event_type",
               "event_time", "hop_number", "delivery_attempt_number", "is_damaged"]]


def derive_created_cancelled_events(orders_transformed_df, source_system, source_owner):
    """orders.created_at / cancelled_at değerlerinden CREATED ve CANCELLED event satırları üretir."""
    created = orders_transformed_df[["order_key", "created_at"]].copy()
    created["event_type"] = "CREATED"
    created = created.rename(columns={"created_at": "event_time"})

    cancelled = orders_transformed_df.dropna(subset=["cancelled_at"])[["order_key", "cancelled_at"]].copy()
    cancelled["event_type"] = "CANCELLED"
    cancelled = cancelled.rename(columns={"cancelled_at": "event_time"})

    combined = pd.concat([created, cancelled], ignore_index=True)
    combined["source_system"] = source_system
    combined["source_owner"] = source_owner
    combined["hop_number"] = None
    combined["delivery_attempt_number"] = None
    combined["is_damaged"] = None

    return combined[["order_key", "source_system", "source_owner", "event_type",
                      "event_time", "hop_number", "delivery_attempt_number", "is_damaged"]]


def build_all_events(orders_raw_df, orders_transformed_df, transfer_df, branch_df, courier_df,
                      source_system, source_owner):
    shipment_map = _shipment_to_order_key(orders_raw_df, source_owner)

    transfer = transform_transfer_events(transfer_df, shipment_map, source_system, source_owner)
    branch = transform_branch_events(branch_df, shipment_map, source_system, source_owner)
    courier = transform_courier_events(courier_df, shipment_map, source_system, source_owner)
    created_cancelled = derive_created_cancelled_events(orders_transformed_df, source_system, source_owner)

    all_events = pd.concat([created_cancelled, transfer, branch, courier], ignore_index=True)
    all_events = all_events.sort_values(["order_key", "event_time"]).reset_index(drop=True)
    return all_events


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

    from src.extract.postgres_extractor import extract_table
    from src.transform.order_transformer import transform_orders

    orders_raw = extract_table("orders")
    orders_transformed = transform_orders(orders_raw, source_system="postgres", source_owner="Misa")

    transfer_raw = extract_table("transfer_events")
    branch_raw = extract_table("branch_events")
    courier_raw = extract_table("courier_events")

    events = build_all_events(
        orders_raw, orders_transformed, transfer_raw, branch_raw, courier_raw,
        source_system="postgres", source_owner="Misa"
    )

    print(events.head(15))
    print(f"\nToplam {len(events)} event satırı üretildi.")
    print("\nevent_type dağılımı:")
    print(events["event_type"].value_counts())
