# Cargo Data Pipeline

Tayna/MySQL ve Misa/PostgreSQL kaynaklarındaki kargo verilerini ortak bir
PostgreSQL analitik modelinde birleştiren Python ETL projesidir. Proje ayrıca
günlük sentetik sipariş ve kargo eventi üretir.

## Mimari

```text
Sentetik üretici --> Tayna / MySQL -----+
                                        +--> Extract --> Transform --> Silver --> Gold
                   Misa / PostgreSQL ---+
```

- Kaynak tablolar: `orders`, `transfer_events`, `branch_events`, `courier_events`
- Silver: `silver.orders`, `silver.shipment_events`
- Gold: güncel durum, kategori bazında hasar oranı ve şube performansı

## Dizinler

```text
src/extract/                Kaynak veritabanı okuyucuları
src/transform/              Dönüşüm, yaşam döngüsü ve iş kuralları
src/transform/validation/   Veri kalite kontrolleri
src/load/                   Veritabanı yazıcıları ve ETL giriş noktaları
src/mock_generator/         Sentetik günlük veri üretimi
sql/                        Kaynak, Silver ve Gold DDL dosyaları
tests/                      Otomatik testler
```

## Yaşam döngüsü

```text
CREATED --> TRANSFER_IN --> TRANSFER_OUT --> BRANCH_IN
   |                                            |
   +--> CANCELLED                               v
                                      COURIER_ASSIGNED
                                               |
                                               v
                                      OUT_FOR_DELIVERY
                                        |             |
                                   DELIVERED   DELIVERY_FAILED --> retry
```

- En fazla iki transfer hop'u
- En fazla iki teslimat denemesi
- Yalnızca `CREATED` sonrasında iptal
- Kategoriye bağlı teslimat hasarı olasılığı

## Kurulum

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Proje kökünde, Git tarafından takip edilmeyen `.env` dosyası oluşturun:

```dotenv
TAYNA_DB_HOST=mysql.example.com
TAYNA_DB_PORT=3306
TAYNA_DB_USER=app_user
TAYNA_DB_PASSWORD=change-me
TAYNA_DB_NAME=defaultdb

MISA_PG_HOST=misa-postgres.example.com
MISA_PG_PORT=5432
MISA_PG_USER=app_user
MISA_PG_PASSWORD=change-me
MISA_PG_DBNAME=defaultdb

SILVER_PG_HOST=warehouse-postgres.example.com
SILVER_PG_PORT=5432
SILVER_PG_USER=etl_user
SILVER_PG_PASSWORD=change-me
SILVER_PG_DBNAME=defaultdb

BRANCH_NAME=Tayna
BRANCH_CITY=Istanbul
```

Eski `PG_*` değişkenleri geriye dönük uyumluluk için desteklenir; yeni kurulumlarda
Misa kaynağı için `MISA_PG_*`, merkezi hedef için `SILVER_PG_*` kullanın. Örnek
yapılandırmayı `.env.example` dosyasından kopyalayabilirsiniz.

## Veritabanı kurulumu

- MySQL kaynak tabloları: `sql/create_tables.sql`
- PostgreSQL kaynak tabloları: `sql/create_tables_postgres.sql`
- Merkezi Silver şeması: `sql/create_silver_schema.sql`
- Gold görünümleri: `sql/create_gold_views.sql`

Merkezi PostgreSQL üzerinde önce Silver, sonra Gold SQL dosyasını çalıştırın.
Mevcut bir kurulumda nullable event tekrarlarını temizleyip idempotent indeksi
oluşturmak için bir kez `sql/migrations/001_fix_event_idempotency.sql` çalıştırın.

## Çalıştırma

Komutlar proje kökünden çalıştırılmalıdır.

```powershell
# Sentetik günlük Tayna verisi üret
python src/mock_generator/daily_runner.py

# Tayna/MySQL verisini Silver'a taşı
python src/load/run_etl_tayna.py

# Misa/PostgreSQL verisini Silver'a taşı
python src/load/run_etl_misa_only.py

# Testleri çalıştır
python -m unittest discover -s tests -v
```

ETL çalışmaları yüklemeden önce eksik alan, tekrar, bilinmeyen shipment,
yaşam döngüsü sırası ve iş kuralı kontrollerini uygular. Hatalı kaynak veri
Silver'a yazılmadan işlem durur. Sipariş ve event yükleri tek transaction içinde
gerçekleşir; yüklerden biri başarısız olursa ikisi de geri alınır.

## Gold görünümleri

- `gold.current_shipment_state`: Siparişin en son eventi
- `gold.damage_rate_by_category`: Kaynak ve kategori bazında hasar oranı
- `gold.branch_performance`: Sipariş, iptal, teslimat ve ortalama süre metrikleri

```sql
SELECT * FROM gold.branch_performance ORDER BY source_owner;
```

## Otomasyon ve güvenlik

Kökteki `.bat` dosyaları Windows Task Scheduler örnekleridir. Kullanımdan önce
proje ve sanal ortam yollarını bilgisayarınıza göre düzenleyin. `.env`, parolalar
ve operasyonel loglar repoya eklenmemelidir.
