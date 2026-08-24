import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import pandas as pd

load_dotenv()


def _get_connection():
    return psycopg2.connect(
        host=os.environ.get("SILVER_PG_HOST", os.environ.get("PG_HOST")),
        port=os.environ.get("SILVER_PG_PORT", os.environ.get("PG_PORT", "5432")),
        user=os.environ.get("SILVER_PG_USER", os.environ.get("PG_USER")),
        password=os.environ.get("SILVER_PG_PASSWORD", os.environ.get("PG_PASSWORD")),
        dbname=os.environ.get("SILVER_PG_DBNAME", os.environ.get("PG_DBNAME")),
    )


def _clean_for_insert(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """NaN/NaT değerlerini psycopg2'nin anlayacağı None'a çevirir (datetime kolonlar dahil)."""
    return df[columns].astype(object).where(pd.notnull(df[columns]), None)


def write_orders(orders_df: pd.DataFrame, conn=None, commit=True):
    """silver.orders tablosuna upsert eder (order_key çakışırsa günceller)."""
    own_connection = conn is None
    if own_connection:
        conn = _get_connection()

    columns = [
        "order_key", "source_order_id", "source_system", "source_owner",
        "category", "sender_city", "receiver_city", "order_status",
        "created_at", "cancelled_at",
    ]
    df = _clean_for_insert(orders_df, columns)
    records = list(df.itertuples(index=False, name=None))
    if not records:
        return

    insert_sql = f"""
        INSERT INTO silver.orders ({", ".join(columns)})
        VALUES %s
        ON CONFLICT (order_key) DO UPDATE SET
            order_status = EXCLUDED.order_status,
            cancelled_at = EXCLUDED.cancelled_at,
            loaded_at = now()
    """

    try:
        with conn.cursor() as cur:
            execute_values(cur, insert_sql, records)
        if commit:
            conn.commit()
        print(f"silver.orders: {len(records)} satır yazıldı/güncellendi.")
    finally:
        if own_connection:
            conn.close()


def write_events(events_df: pd.DataFrame, conn=None, commit=True):
    """silver.shipment_events tablosuna insert eder. Zaten var olan event'ler (aynı doğal key) atlanır."""
    own_connection = conn is None
    if own_connection:
        conn = _get_connection()

    columns = [
        "order_key", "source_system", "source_owner", "event_type",
        "event_time", "hop_number", "delivery_attempt_number", "is_damaged",
    ]
    df = _clean_for_insert(events_df, columns)
    records = list(df.itertuples(index=False, name=None))
    if not records:
        return

    insert_sql = f"""
        INSERT INTO silver.shipment_events ({", ".join(columns)})
        VALUES %s
        ON CONFLICT DO NOTHING
    """

    try:
        with conn.cursor() as cur:
            execute_values(cur, insert_sql, records)
        if commit:
            conn.commit()
        print(f"silver.shipment_events: {len(records)} satır denendi (yeni olanlar eklendi, mevcut olanlar atlandı).")
    finally:
        if own_connection:
            conn.close()


def write_to_silver(orders_df: pd.DataFrame, events_df: pd.DataFrame):
    """Sipariş ve event yüklerini tek transaction içinde atomik olarak yazar."""
    conn = _get_connection()
    try:
        write_orders(orders_df, conn=conn, commit=False)
        write_events(events_df, conn=conn, commit=False)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
