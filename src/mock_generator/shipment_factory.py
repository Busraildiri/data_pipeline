# shipment_factory.py
# Yeni CREATED kargo (shipment) üretimi.

import random
import uuid
from datetime import datetime, timedelta
from faker import Faker

fake = Faker("tr_TR")

BRANCH_NAME = "Tayna"
BRANCH_CITY = "Antalya"

PRODUCT_CATEGORIES = ["COSMETICS", "ELECTRONICS"]
SERVICE_TYPES = ["standard", "express"]

TURKISH_CITIES = [
    "Istanbul", "Ankara", "Izmir", "Bursa", "Adana", "Konya",
    "Gaziantep", "Kayseri", "Trabzon", "Samsun", "Eskisehir", "Mersin"
]


def generate_shipment_id() -> str:
    return f"SHP{uuid.uuid4().hex[:8].upper()}"


def generate_order_id() -> str:
    return f"ORD{uuid.uuid4().hex[:8].upper()}"


def generate_customer_id() -> str:
    return f"CUS{uuid.uuid4().hex[:6].upper()}"


def create_new_shipment(created_at: datetime) -> dict:
    """
    Tek bir yeni CREATED kargo kaydı üretir.
    created_at: bu kargonun oluşturulma zamanı (sysdate-1 mantığı runner'da hesaplanır)
    """
    return {
        "shipment_id": generate_shipment_id(),
        "order_id": generate_order_id(),
        "created_at": created_at,
        "sender_city": BRANCH_CITY,
        "receiver_city": random.choice(TURKISH_CITIES),
        "customer_id": generate_customer_id(),
        "service_type": random.choice(SERVICE_TYPES),
        "product_category": random.choice(PRODUCT_CATEGORIES),
    }


def generate_daily_orders(created_at: datetime, day_number: int) -> list[dict]:
    """
    Bir günlük yeni sipariş listesini üretir.
    day_number: kaçıncı gün (büyüme eğrisi için) — 1'den başlar.
    """
    base_orders = 5
    growth_per_day = 0.8
    target_mean = base_orders + growth_per_day * day_number

    # Poisson dağılımı: ortalama etrafında gerçekçi rastgelelik üretir
    daily_count = max(1, int(random.gauss(target_mean, target_mean * 0.2)))

    return [create_new_shipment(created_at) for _ in range(daily_count)]


if __name__ == "__main__":
    # Hızlı test: 5. gün için örnek üretim
    today = datetime.now() - timedelta(days=1)  # sysdate-1
    orders = generate_daily_orders(today, day_number=5)
    print(f"{len(orders)} yeni sipariş üretildi:\n")
    for order in orders:
        print(order)