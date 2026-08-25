import pandas as pd

from src.transform.validation.business_rule_validator import (
    validate_cancellation, validate_delivery_attempts, validate_transfer_hops,
)
from src.transform.validation.lifecycle_validator import validate_shipment_sequence
from src.transform.validation.schema_validator import (
    validate_duplicates, validate_known_shipment_id, validate_missing_fields,
)


class DataQualityError(ValueError):
    """Kaynak veri Silver katmanına yüklenmeye uygun olmadığında fırlatılır."""


def _event_frame(orders_df, transfer_df, branch_df, courier_df):
    created = orders_df[["shipment_id", "created_at"]].rename(columns={"created_at": "event_time"})
    created = created.assign(event_type="CREATED")
    cancelled = orders_df.dropna(subset=["cancelled_at"])[["shipment_id", "cancelled_at"]]
    cancelled = cancelled.rename(columns={"cancelled_at": "event_time"}).assign(event_type="CANCELLED")
    frames = [created, cancelled]
    frames.extend(
        frame[["shipment_id", "event_type", "event_time"]].copy()
        for frame in (transfer_df, branch_df, courier_df)
    )
    return pd.concat(frames, ignore_index=True)


def validate_source_data(orders_df, transfer_df, branch_df, courier_df):
    errors = []
    valid_ids = set(orders_df["shipment_id"].dropna())

    for table_name, frame in (
        ("transfer_events", transfer_df), ("branch_events", branch_df),
        ("courier_events", courier_df),
    ):
        checks = (
            (validate_missing_fields(frame), "eksik zorunlu alan"),
            (validate_duplicates(frame), "tekrarlı event"),
            (validate_known_shipment_id(frame, valid_ids), "bilinmeyen shipment_id"),
        )
        errors.extend(
            f"{table_name}: {len(rows)} {message}"
            for rows, message in checks if not rows.empty
        )

    all_events = _event_frame(orders_df, transfer_df, branch_df, courier_df)
    # Eşit timestamp'te event_type'a göre alfabetik sıralamak CANCELLED'ı
    # CREATED'dan önceye taşıyordu. _event_frame CREATED satırlarını önce kurduğu
    # için stable sıralama bu gerçek lifecycle sırasını korur.
    all_events = all_events.sort_values(
        ["shipment_id", "event_time"],
        kind="stable",
    )
    for shipment_id, shipment_events in all_events.groupby("shipment_id", sort=False):
        event_list = shipment_events["event_type"].tolist()
        shipment_errors = (
            validate_shipment_sequence(event_list)
            + validate_transfer_hops(event_list)
            + validate_delivery_attempts(event_list)
            + validate_cancellation(event_list)
        )
        errors.extend(f"shipment_id={shipment_id}: {error}" for error in shipment_errors)

    if errors:
        preview = "\n".join(f"- {error}" for error in errors[:20])
        remaining = len(errors) - 20
        suffix = f"\n- ... ve {remaining} hata daha" if remaining > 0 else ""
        raise DataQualityError(f"Kaynak veri kalite kontrolünden geçemedi:\n{preview}{suffix}")
