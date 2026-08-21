# business_rules.py
# TRANSITIONS (lifecycle.py) sadece sıralamayı bilir; bu dosya ise limitleri kontrol eder.
# Guard fonksiyonları, kargonun TÜM event geçmişine (context) bakarak karar verir.

MAX_TRANSFER_HOPS = 2
MAX_DELIVERY_ATTEMPTS = 2
CANCELLATION_ALLOWED_AFTER = ["CREATED"]  # başka hiçbir state'ten sonra değil


def can_add_transfer_hop(transfer_hop_count: int) -> bool:
    """
    Kargo kaçıncı kez transfer merkezine giriyor?
    transfer_hop_count: bu ana kadar kaç kez TRANSFER_IN yaşandığı (yeni event dahil değil)
    """
    return transfer_hop_count < MAX_TRANSFER_HOPS


def can_retry_delivery(delivery_attempt_count: int) -> bool:
    """
    Kargo kaçıncı teslimat denemesinde?
    delivery_attempt_count: bu ana kadar kaç kez OUT_FOR_DELIVERY yaşandığı
    """
    return delivery_attempt_count < MAX_DELIVERY_ATTEMPTS


def resolve_delivery_failed_status(delivery_attempt_count: int) -> str:
    """
    DELIVERY_FAILED event'i geldiğinde, EVENT_STATUS_MAP'te karşılığı yok
    (çünkü context'e göre iki farklı sonuca gidebiliyor). Bu fonksiyon o kararı verir.
    """
    if can_retry_delivery(delivery_attempt_count):
        return "DELIVERY_RETRY_PENDING"
    return "DELIVERY_FAILED_FINAL"


def can_cancel(current_status: str) -> bool:
    """
    Kargo iptal edilebilir mi? Sadece CREATED durumundaysa.
    """
    return current_status in CANCELLATION_ALLOWED_AFTER