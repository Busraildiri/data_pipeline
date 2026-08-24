# postgres_writer.py
# Mock generator ciktisini (orders, transfer_events, branch_events, courier_events)
# Aiven PostgreSQL'e yazan katman.
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import pandas as pd

load_dotenv()

DB_HOST = os.environ.get("MISA_PG_HOST", os.environ.get("PG_HOST"))
DB_PORT = os.environ.get("MISA_PG_PORT", os.environ.get("PG_PORT", "5432"))
DB_USER = os.environ.get("MISA_PG_USER", os.environ.get("PG_USER"))
DB_PASSWORD = os.environ.get("MISA_PG_PASSWORD", os.environ.get("PG_PASSWORD"))
DB_NAME = os.environ.get("MISA_PG_DBNAME", os.environ.get("PG_DBNAME", "defaultdb"))


def get_engine():
    missing = [name for name, value in {
        "MISA_PG_HOST": DB_HOST,
        "MISA_PG_USER": DB_USER,
        "MISA_PG_PASSWORD": DB_PASSWORD,
    }.items() if not value]
    if missing:
        raise ValueError(f"Eksik PostgreSQL ortam değişkenleri: {', '.join(missing)}")
    connection_url = URL.create(
        "postgresql+psycopg2", username=DB_USER, password=DB_PASSWORD,
        host=DB_HOST, port=int(DB_PORT), database=DB_NAME,
    )
    return create_engine(
        connection_url, connect_args={"sslmode": "require"}, pool_pre_ping=True
    )


def write_tables_to_db(
    orders: list,
    transfer_events: list,
    branch_events: list,
    courier_events: list,
    order_updates: list | None = None,
):
    engine = get_engine()
    order_updates = order_updates or []

    with engine.begin() as conn:
        if orders:
            pd.DataFrame(orders).to_sql("orders", conn, if_exists="append", index=False)
        if transfer_events:
            pd.DataFrame(transfer_events).to_sql("transfer_events", conn, if_exists="append", index=False)
        if branch_events:
            pd.DataFrame(branch_events).to_sql("branch_events", conn, if_exists="append", index=False)
        if courier_events:
            pd.DataFrame(courier_events).to_sql("courier_events", conn, if_exists="append", index=False)
        for update in order_updates:
            conn.execute(
                text(
                    "UPDATE orders SET order_status = :order_status, "
                    "cancelled_at = :cancelled_at WHERE shipment_id = :shipment_id"
                ),
                update,
            )

    print(f"DB'ye yazildi: {len(orders)} orders, {len(transfer_events)} transfer_events, "
          f"{len(branch_events)} branch_events, {len(courier_events)} courier_events, "
          f"{len(order_updates)} order güncellemesi")


def create_tables():
    with open("sql/create_tables_postgres.sql", "r", encoding="utf-8-sig") as f:
        ddl_statements = f.read().split(";")

    engine = get_engine()
    with engine.begin() as conn:
        for statement in ddl_statements:
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
    print("Tablolar olusturuldu.")


if __name__ == "__main__":
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Baglanti basarili:", result.fetchone())

    create_tables()
