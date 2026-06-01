# Phantom Logos Geliştirici Katkı Rehberi (CONTRIBUTING.md)

Phantom Logos otonom işletim sistemi projesine katkıda bulunmak istediğiniz için teşekkür ederiz. Bu doküman, geliştirme standartlarımızı, kurallarımızı ve katkı süreçlerini açıklar.

---

## 1. Git Dal (Branch) Stratejisi

Geliştirme süreçlerinin kararlılığını korumak için git dalları aşağıdaki standartlara göre yönetilir:

* **master**: Üretim (production) ve kararlı yayın dalıdır. Doğrudan bu dala push yapılması (L0 yetkili acil durum yamaları hariç) yasaktır.
* **feature/<özellik-adı>**: Yeni özellikler, geliştirmeler veya refaktör çalışmaları bu dallarda geliştirilir ve testleri tamamlandıktan sonra master dalına Pull Request (PR) açılır.
* **hotfix/<hata-adı>**: master dalındaki acil giderilmesi gereken kritik hatalar için oluşturulur.

---

## 2. BA-01 Dil ve Emoji Yönetişim Protokolü

Projeye katkı sağlarken **BA-01** kurallarına kesinlikle uyulmalıdır:

1. **L0 Kullanıcı Etkileşimi (Chat & Arayüz)**: L0 (Hank/Yönetici) ile olan tüm sohbetler, terminal raporları ve `.md` formatlı dokümantasyonlar tamamen **Türkçe** olmalıdır.
2. **Çekirdek Kod Tabanı (Code, Logs, DB, Config)**: Python kodları, yorum satırları, değişken isimleri, veri tabanı şemaları ve log kayıtları tamamen **İngilizce (ASCII-only)** olmalıdır. Kod veya yorumlarda Türkçe karakter (ç, ğ, ı, ö, ş, ü, vb.) kullanımı yasaktır.
3. **EMOJI_BAN (Emoji Yasağı)**: Tüm kod tabanında, loglarda, commmit mesajlarında ve dokümanlarda emoji veya süsleyici özel karakterlerin kullanımı **kesinlikle yasaktır**.

---

## 3. Pre-commit ve Kod Kalitesi standartları

Değişikliklerinizi commit etmeden önce kod kalitesi araçlarını çalıştırmanız önerilir. Projede biçimlendirme ve statik analiz için **Ruff** kullanılmaktadır:

```bash
# Kod biçimlendirme (Formatting)
ruff format src/ cognition/ scripts/ tests/

# Statik analiz ve kuralların kontrolü (Linting)
ruff check src/ cognition/ scripts/ tests/ --fix
```

Ayrıca, `pyright` ile statik tip denetimini doğrulayabilirsiniz:
```bash
pyright src/
```

---

## 4. L0_AUTH_TOKEN Protokolü

Sistemde güvenlik ve otonom bütünlük koruması (Watchdog/Guardian) aktiftir. Codebase üzerinde dosya yazma, silme veya yapılandırma değiştirme eylemleri gerçekleştirmeden önce L0 onay tokenı oluşturulmalıdır:

```bash
python scripts/create_l0_token.py
```
Bu komut `data/snapshots/L0_AUTH_TOKEN` yolunda 60 saniye geçerli bir yetkilendirme penceresi açar. Yetkisiz veya süresi geçmiş yazma operasyonları Guardian tarafından otomatik olarak geri alınacaktır (Rollback).

---

## 5. Test Ekleme Standartları

Yazdığınız her yeni özellik veya hata düzeltmesi için ilgili testleri eklemelisiniz. Testler `tests/` dizininde konumlandırılmalı ve aşağıdaki kategorilere göre etiketlenmelidir:

* **smoke**: Temel derleme ve kararlılığı doğrulayan hızlı testler.
* **integration**: Gerçek Ollama servisi, veritabanları veya MCP sunucu bağlantılarına ihtiyaç duyan testler.
* **slow**: Çalışması 30 saniyeden uzun süren ağır entegrasyon testleri.

Test marker etiketleme örneği:
```python
import pytest

@pytest.mark.smoke
def test_my_feature():
    assert True
```

---

## 6. Pull Request (PR) Süreci

1. Değişikliklerinizi içeren dalınızı (branch) oluşturun.
2. Ruff, Pyright ve pytest testlerinin yerelde başarıyla geçtiğinden emin olun.
3. Dalınızı uzak sunucuya push edin ve master dalına karşı bir Pull Request açın.
4. PR açıklamasına yapılan değişikliklerin özetini, hangi testlerle doğrulandığını ve BA-01 uyumluluk onayını ekleyin.
