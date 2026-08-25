# shipment_factory.py
# Yeni CREATED kargo (shipment) üretimi.

import os
import random
import uuid
from datetime import datetime, timedelta
from faker import Faker
from dotenv import load_dotenv

load_dotenv()

fake = Faker("tr_TR")

BRANCH_NAME = os.environ.get("BRANCH_NAME")
BRANCH_CITY = os.environ.get("BRANCH_CITY")

PRODUCT_CATEGORIES = ["COSMETICS", "ELECTRONICS"]
SERVICE_TYPES = ["standard", "express"]
DAILY_ORDER_RANGE = (20, 35)

# Ortak, sabit şehir listesi — hangi şube olursa olsun aynı liste kullanılır
TURKISH_CITIES = [
    "Istanbul", "Ankara", "Izmir", "Antalya", "Bursa", "Adana", "Konya",
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
    # Kendi şubenin şehrine kargo göndermeyi engelle
    possible_cities = [c for c in TURKISH_CITIES if c != BRANCH_CITY]

    return {
        "shipment_id": generate_shipment_id(),
        "order_id": generate_order_id(),
        "created_at": created_at,
        "sender_city": BRANCH_CITY,
        "receiver_city": random.choice(possible_cities),
        "customer_id": generate_customer_id(),
        "service_type": random.choice(SERVICE_TYPES),
        "product_category": random.choice(PRODUCT_CATEGORIES),
    }


def generate_daily_orders(created_at: datetime, day_number: int) -> list[dict]:
    """
    Bir günlük yeni sipariş listesini üretir.
    Hacim, dashboard'da anlamlı günlük değişim oluşturacak sabit bantta tutulur.
    day_number geriye dönük çağrı uyumluluğu için korunur.
    """
    del day_number
    daily_count = random.randint(*DAILY_ORDER_RANGE)

    return [create_new_shipment(created_at) for _ in range(daily_count)]


if __name__ == "__main__":
    # Hızlı test: 5. gün için örnek üretim
    today = datetime.now() - timedelta(days=1)  # sysdate-1
    orders = generate_daily_orders(today, day_number=5)
    print(f"Şube: {BRANCH_NAME} ({BRANCH_CITY})")
    print(f"{len(orders)} yeni sipariş üretildi:\n")
    for order in orders:
        print(order)
