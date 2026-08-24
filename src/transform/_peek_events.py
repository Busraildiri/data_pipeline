import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.extract.mysql_extractor import extract_table

for table in ["orders", "transfer_events", "branch_events", "courier_events"]:
    df = extract_table(table)
    print(f"\n--- {table} ---")
    print(df.columns.tolist())
    print(df.head(2))