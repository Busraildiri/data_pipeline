# schema_validator.py
# Klasik data quality kontrolleri: eksik alan, format hatası, duplicate kayıt.

import pandas as pd

REQUIRED_COLUMNS = ["shipment_id", "event_type", "event_time"]


def validate_missing_fields(df: pd.DataFrame) -> pd.DataFrame:
    """Zorunlu kolonlarda eksik (null) değer olan satırları işaretler."""
    missing_mask = df[REQUIRED_COLUMNS].isnull().any(axis=1)
    return df[missing_mask]


def validate_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Aynı shipment_id + event_type + event_time'a sahip duplicate satırları bulur."""
    duplicate_mask = df.duplicated(subset=["shipment_id", "event_type", "event_time"], keep="first")
    return df[duplicate_mask]


def validate_known_shipment_id(df: pd.DataFrame, valid_shipment_ids: set) -> pd.DataFrame:
    """orders tablosunda olmayan shipment_id'leri (bilinmeyen kargo) bulur."""
    unknown_mask = ~df["shipment_id"].isin(valid_shipment_ids)
    return df[unknown_mask]