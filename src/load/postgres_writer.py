# postgres_writer.py
# Mock generator ciktisini (orders, transfer_events, branch_events, courier_events)
# Aiven PostgreSQL'e yazan katman.
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd

load_dotenv()

DB_HOST = os.environ.get("PG_HOST")
DB_PORT = os.environ.get("PG_PORT", "5432")
DB_USER = os.environ.get("PG_USER")
DB_PASSWORD = os.environ.get("PG_PASSWORD")
DB_NAME = os.environ.get("PG_DBNAME", "defaultdb")


def get_engine():
    connection_string = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(connection_string, connect_args={"sslmode": "require"})


def write_tables_to_db(orders: list, transfer_events: list, branch_events: list, courier_events: list):
    engine = get_engine()

    if orders:
        pd.DataFrame(orders).to_sql("orders", engine, if_exists="append", index=False)
    if transfer_events:
        pd.DataFrame(transfer_events).to_sql("transfer_events", engine, if_exists="append", index=False)
    if branch_events:
        pd.DataFrame(branch_events).to_sql("branch_events", engine, if_exists="append", index=False)
    if courier_events:
        pd.DataFrame(courier_events).to_sql("courier_events", engine, if_exists="append", index=False)

    print(f"DB'ye yazildi: {len(orders)} orders, {len(transfer_events)} transfer_events, "
          f"{len(branch_events)} branch_events, {len(courier_events)} courier_events")


def create_tables():
    with open("sql/create_tables.sql", "r", encoding="utf-8-sig") as f:
        ddl_statements = f.read().split(";")

    engine = get_engine()
    with engine.connect() as conn:
        for statement in ddl_statements:
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
        conn.commit()
    print("Tablolar olusturuldu.")


if __name__ == "__main__":
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Baglanti basarili:", result.fetchone())

    create_tables()