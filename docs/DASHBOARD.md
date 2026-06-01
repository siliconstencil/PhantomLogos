# Phantom Logos Web Operator Dashboard (DASHBOARD.md)

Bu doküman, Phantom Logos Sovereign OS (v1.2.1) ile entegre gelen premium web tabanlı Operatör Konsolu (Dashboard) hakkında teknik detayları ve kullanım kılavuzunu içerir.

---

## 1. Genel Bakış

Web Operator Dashboard, Phantom Logos sistem mimarisinin (Sovereign Gateway ve Local Muscle) çalışma durumunu, 14-Eksen Mnemosyne bellek durumlarını ve sistem güvenilirlik skorlarını (reliability) izlemek için tasarlanmış modern, premium ve responsive bir arayüzdür.

### Ana Özellikler:
- **Genel Bakış:** Sophia, Clotho, Lachesis ajanlarının anlık güvenilirlik seviyeleri, VRAM kullanımı ve aktif veritabanlarının (mnemosyne, reliability, spatial) durumları.
- **14-Eksen Sağlık Matrisi:** 14 bellek ekseninin (Episodic, Procedural, Goals vb.) satır/bütünlük durumları, warn ve broken uyarıları.
- **Terminal ve Loglar:** `logs/system.json` log dosyasının gerçek zamanlı (JSON tabanlı) takibi.
- **Operatör Konsolu (Aksiyonlar):** Arayüz üzerinden canlı sağlık denetimi tetikleme ve sistem çöp toplayıcısını (garbage collector) çalıştırma.

---

## 2. Kurulum ve Başlatma

Dashboard ek bir bağımlılığa gerek duymadan sanal ortam (.venv) içindeki `aiohttp` kütüphanesini kullanır. Başlatmak için aşağıdaki komutu çalıştırmanız yeterlidir:

```bash
python scripts/dashboard.py
```

Sistem varsayılan olarak `8080` portunda çalışacaktır. Tarayıcınızdan aşağıdaki adrese giderek konsolu açabilirsiniz:
**URL:** [http://localhost:8080](http://localhost:8080)

Portu özelleştirmek için ortam değişkenini (env) kullanabilirsiniz:
```bash
set PORT=9000
python scripts/dashboard.py
```

---

## 3. API Uç Noktaları (REST Endpoints)

Dashboard backend servisi (`src/dashboard/api_server.py`) aşağıdaki REST API endpoints'leri sunar:

- **`GET /`**: HTML Operator Console arayüzünü sunar.
- **`GET /api/metrics`**: Sophia/System güvenilirlik skorlarını, VRAM bellek durumunu ve 14-Eksen SQLite bütünlük özetini JSON biçiminde döner.
- **`GET /api/logs`**: `logs/system.json` dosyasındaki son 150 log satırını okur ve JSON olarak parse edip döner.
- **`POST /api/trigger-health`**: Canlı eksen sağlık testini (`scripts/health_check_14_axes.py`) arka planda çalıştırır ve çıktısını döndürür.

---

## 4. Testler

Dashboard API ve web sunucusu entegrasyon testleri `tests/test_dashboard_api.py` altında otomatikleştirilmiştir:

```bash
pytest tests/test_dashboard_api.py -v
```
