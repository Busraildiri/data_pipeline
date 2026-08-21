# lifecycle.py
# Tek source of truth: hem mock data generator hem de ETL validator bu dosyayı kullanır.

# Event -> Derived State eşlemesi
# NOT: DELIVERY_FAILED event'i attempt_count'a göre iki farklı state üretebilir,
# bu yüzden ayrı bir fonksiyonla ele alınacak (business_rules.py içinde).
EVENT_STATUS_MAP = {
    "CREATED": "CREATED",
    "TRANSFER_IN": "IN_TRANSFER_CENTER",
    "TRANSFER_OUT": "IN_TRANSIT",
    "BRANCH_IN": "AT_BRANCH",
    "COURIER_ASSIGNED": "ASSIGNED_TO_COURIER",
    "OUT_FOR_DELIVERY": "OUT_FOR_DELIVERY",
    "DELIVERED": "DELIVERED",
    "CANCELLED": "CANCELLED",
    # DELIVERY_FAILED kasıtlı olarak burada yok — business_rules.py'de ele alınacak
}

# Hangi event'ten sonra hangi event'ler sırayla geçerli (pure graph, limitleri bilmez)
TRANSITIONS = {
    "CREATED": ["TRANSFER_IN", "CANCELLED"],
    "TRANSFER_IN": ["TRANSFER_OUT"],
    "TRANSFER_OUT": ["TRANSFER_IN", "BRANCH_IN"],  # tekrar TRANSFER_IN = 2. hop ihtimali
    "BRANCH_IN": ["COURIER_ASSIGNED"],
    "COURIER_ASSIGNED": ["OUT_FOR_DELIVERY"],
    "OUT_FOR_DELIVERY": ["DELIVERED", "DELIVERY_FAILED"],
    "DELIVERY_FAILED": ["OUT_FOR_DELIVERY"],  # retry hakkı varsa
}

TERMINAL_STATUSES = {"DELIVERED", "DELIVERY_FAILED_FINAL", "CANCELLED"}