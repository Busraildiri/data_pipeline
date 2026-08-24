import os
import pandas as pd
import pymysql
from dotenv import load_dotenv

load_dotenv()

TABLES = ["orders", "transfer_events", "branch_events", "courier_events"]
ORDER_BY = {
    "orders": "created_at, shipment_id",
    "transfer_events": "shipment_id, event_time, id",
    "branch_events": "shipment_id, event_time, id",
    "courier_events": "shipment_id, event_time, id",
}


def _get_connection():
    return pymysql.connect(
        host=os.environ.get("TAYNA_DB_HOST"),
        port=int(os.environ.get("TAYNA_DB_PORT", 3306)),
        user=os.environ.get("TAYNA_DB_USER"),
        password=os.environ.get("TAYNA_DB_PASSWORD"),
        database=os.environ.get("TAYNA_DB_NAME"),
    )


def extract_table(table_name: str, conn=None) -> pd.DataFrame:
    if table_name not in TABLES:
        raise ValueError(f"Geçersiz tablo: {table_name}")

    own_connection = conn is None

    if own_connection:
        conn = _get_connection()

    try:
        return pd.read_sql(f"SELECT * FROM {table_name} ORDER BY {ORDER_BY[table_name]}", conn)
    finally:
        if own_connection:
            conn.close()


def extract_all() -> dict[str, pd.DataFrame]:
    conn = _get_connection()

    try:
        return {
            table: extract_table(table, conn)
            for table in TABLES
        }
    finally:
        conn.close()


if __name__ == "__main__":
    data = extract_all()

    for name, df in data.items():
        print(f"{name}: {len(df)} satır")
