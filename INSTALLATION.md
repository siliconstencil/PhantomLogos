# Phantom Logos v1.2.1 Kurulum Rehberi (INSTALLATION.md)

Bu doküman, Phantom Logos sistemini sıfırdan kurup çalıştırmak isteyen geliştiriciler ve operatörler için eksiksiz adımları içerir.

---

## 1. Sistem Gereksinimleri

Sisteminizin stabil ve performanslı çalışabilmesi için aşağıdaki asgari donanım ve yazılım gereksinimleri karşılanmalıdır:

* **İşletim Sistemi**: Windows 10/11, Ubuntu 22.04 LTS veya daha günceli, macOS 14 (Sonoma) veya daha günceli.
* **Bellek (RAM)**: En az 16 GB DDR4/DDR5 RAM.
* **Ekran Kartı (VRAM)**: En az 7.0 GB kullanılabilir VRAM'e sahip NVIDIA GPU (yerel çıkarım kararlılığı için).
* **Python Sürümü**: Python >= 3.12 (asgari gereksinim).

---

## 2. Ollama Kurulumu

Sistem yerel LLM ve gömme (embedding) modellerini çalıştırmak için **Ollama** motorunu kullanır. İşletim sisteminize uygun Ollama sürümünü indirip kurun:

* **Windows**: [Ollama for Windows](https://ollama.com/download/windows)
* **macOS**: [Ollama for macOS](https://ollama.com/download/mac)
* **Linux**: [Ollama for Linux](https://ollama.com/download/linux)

Kurulum bittikten sonra Ollama servisinin arka planda çalıştığından emin olun (Görev çubuğunda veya systemd üzerinde aktif olmalıdır).

---

## 3. Depoyu Klonlama ve Bootstrap Kurulumu

Projeyi klonlayın ve kök dizine geçiş yapın:

```bash
git clone <repo-adresi> phantom-logos
cd phantom-logos
```

Ardından, sanal ortam kurulumunu, bağımlılıkları, veritabanı şemasını ve modelleri tek bir adımda yapılandırmak için **Bootstrap** kurulum scriptini çalıştırın:

```bash
python scripts/bootstrap.py
```

### Bootstrap Parametreleri (Opsiyonel):
* `--skip-models`: Ollama modellerini indirme adımını atlar (Modelleri daha önce indirdiyseniz veya manuel yönetmek istiyorsanız kullanın).
* `--skip-seeds`: Veritabanı ön-seed (tohumlama) adımlarını atlar.
* `--check-only`: Kurulum yapmadan yalnızca mevcut durumu ve bütünlüğü doğrular.
* `--verbose`: Detaylı kurulum günlüklerini ekrana yansıtır.

Örnek (Model indirmeyi atlayarak hızlı kurulum):
```bash
python scripts/bootstrap.py --skip-models
```

---

## 4. Ortam Değişkenleri (.env) Rehberi

Bootstrap işlemi otomatik olarak `.env.example` dosyasını `.env` olarak kopyalar. Sisteminizin çalışabilmesi için `.env` dosyasındaki ayarları kendi ortamınıza göre düzenleyin:

```env
# GGUF ve Ollama modellerinin bulunduğu dizin (Mutlak veya göreceli yol)
LLM_MODEL_DIR=./models

# Ollama Servis Bağlantı Bilgileri
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_HOST=localhost:11434

# GPU üzerinde ayrılacak maksimum VRAM miktarı (Varsayılan: 7.0 GB)
GPU_TOTAL_VRAM_GB=7.0

# Güvenlik ve Ajanlar Arası İletişim (A2A) Şifreleme Anahtarı (En az 32 karakter olmalıdır)
A2A_SECRET_KEY=your-super-secret-key-min-32-chars

# L0 Yönetici Yetkilendirme Token Ömrü (Varsayılan: 60 saniye)
L0_AUTH_TOKEN_TTL=60

# Loglama Düzeyi (DEBUG, INFO, WARNING, ERROR)
LOG_LEVEL=INFO
```

---

## 5. İlk Doğrulama ve Test Adımları

Sistemin kurulumunu ve bileşen kararlılığını doğrulamak için aşağıdaki komutları çalıştırın:

### 1. 14-Axis Bellek Durum Doğrulaması:
```bash
python scripts/health_check_14_axes.py
```
Tüm 14 eksenin durumunu ve veri bütünlüğünü ekrana yansıtır.

### 2. Pytest Duman (Smoke) Testleri:
```bash
pytest tests/ -m smoke -v
```
5 temel duman testinin başarıyla geçmesi (`PASSED`) kurulumun tamamen doğru yapıldığını gösterir.

---

## 6. Sıkça Sorulan Sorular (SSS)

### S: "Ollama Port Conflict" (Port Çakışması) hatası alıyorum, ne yapmalıyım?
Arka planda başka bir servis 11434 portunu bloke ediyor olabilir. `.env` dosyasında `OLLAMA_BASE_URL` ve `OLLAMA_HOST` adreslerini boşta olan başka bir porta yönlendirip Ollama servisini o port üzerinden ayağa kaldırabilirsiniz.

### S: Ekran kartımın VRAM'i 6 GB, sistem çalışır mı?
Evet, çalışır. Ancak `.env` dosyasındaki `GPU_TOTAL_VRAM_GB` değerini ekran kartınıza göre ayarlayın (Örn: `5.0`). Bellek yetersizliği durumunda sistem otomatik olarak bazı model katmanlarını CPU üzerine kaydıracaktır (offloading).

### S: MCP sunucuları başlamıyor veya yetki hatası alıyorum.
Proje kök dizinindeki `.mcp.json` dosyasındaki yolların doğruluğunu teyit edin. Ayrıca, `python scripts/create_l0_token.py` çalıştırarak L0 yönetici yetkisini tazeleyin.

---

## 7. Sorun Giderme (Troubleshooting)

* **Sistem Günlükleri**: Sistemdeki tüm eylemler ve detaylı hata kayıtları `logs/system.json` (JSON formatlı yapısal loglar) ve `logs/system.log` (düz metin formatlı) dosyalarına kaydedilir. Hata anında ilk olarak bu dosyaları inceleyin.
* **Acil Durum Sıfırlaması**: Veritabanlarında veya MCP oturumlarında kilitlenme ya da tutarsızlık meydana gelirse acil durum sıfırlamasını çalıştırabilirsiniz:
  ```bash
  python scripts/emergency_reset.py
  ```
  Bu işlem, geçici kilit dosyalarını temizleyecek ve servisleri güvenli varsayılan değerlerle yeniden başlatacaktır.
