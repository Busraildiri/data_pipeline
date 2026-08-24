import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

TABLES = ["orders", "transfer_events", "branch_events", "courier_events"]


def _get_connection():
    return psycopg2.connect(
        host=os.environ.get("PG_HOST"),
        port=os.environ.get("PG_PORT", "5432"),
        user=os.environ.get("PG_USER"),
        password=os.environ.get("PG_PASSWORD"),
        dbname=os.environ.get("PG_DBNAME"),
    )


def extract_table(table_name: str, conn=None) -> pd.DataFrame:
    if table_name not in TABLES:
        raise ValueError(f"Geçersiz tablo: {table_name}")

    own_connection = conn is None

    if own_connection:
        conn = _get_connection()

    try:
        return pd.read_sql(f"SELECT * FROM {table_name}", conn)
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