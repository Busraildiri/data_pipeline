import pandas as pd


def transform_orders(orders_df: pd.DataFrame, source_system: str, source_owner: str) -> pd.DataFrame:
    """
    Ham (bronze) orders DataFrame'ini silver.orders şemasına uygun hale getirir.
    order_key üretimi burada yapılır: source_owner + source_order_id.
    """
    df = orders_df.copy()

    # Kaynak sistem bilgisi ekle
    df["source_order_id"] = df["order_id"]
    df["source_system"] = source_system
    df["source_owner"] = source_owner

    # Kolon adı standardizasyonu: product_category -> category
    df["category"] = df["product_category"]

    # order_key üret: örn. "misa_ORDE4BB00EE"
    df["order_key"] = (
        source_owner.lower() + "_" + df["source_order_id"].astype(str)
    )

    # silver.orders şemasındaki kolon sırasına göre seç
    result = df[[
        "order_key",
        "source_order_id",
        "source_system",
        "source_owner",
        "category",
        "sender_city",
        "receiver_city",
        "order_status",
        "created_at",
        "cancelled_at",
    ]].copy()

    return result


if __name__ == "__main__":
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).resolve().parents[2]))

    from src.extract.postgres_extractor import extract_table

    raw_orders = extract_table("orders")
    transformed = transform_orders(raw_orders, source_system="postgres", source_owner="Misa")

    print(transformed.head())
    print(f"\nToplam {len(transformed)} satır dönüştürüldü.")