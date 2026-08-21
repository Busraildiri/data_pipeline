# mysql_writer.py
# Mock generator çıktısını (orders, transfer_events, branch_events, courier_events)
# Aiven MySQL'e yazan katman.
import os
from sqlalchemy import create_engine, text
import pandas as pd

DB_HOST = "tayna-busraildiri1-1dc9.i.aivencloud.com"
DB_PORT = 21631
DB_USER = "avnadmin"
DB_PASSWORD = os.environ.get("***")
DB_NAME = "defaultdb"



def get_engine():
    connection_string = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(connection_string, connect_args={"ssl": {}})


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

    print(f"DB'ye yazıldı: {len(orders)} orders, {len(transfer_events)} transfer_events, "
          f"{len(branch_events)} branch_events, {len(courier_events)} courier_events")


def create_tables():
    with open("sql/create_tables.sql", "r") as f:
        ddl_statements = f.read().split(";")

    engine = get_engine()
    with engine.connect() as conn:
        for statement in ddl_statements:
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
        conn.commit()
    print("Tablolar oluşturuldu.")


if __name__ == "__main__":
    # 1. Bağlantı testi
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Bağlantı başarılı:", result.fetchone())

    # 2. Tabloları oluştur
    create_tables()