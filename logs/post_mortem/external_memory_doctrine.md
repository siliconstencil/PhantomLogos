# Operasyonel Disiplin: "Dışsal Hafıza" Doktrini (External Memory Doctrine)

[12:29 PM PT] | Sürüm: **v1.0.0**
| Hedef: **Beyinsizlik Tercihini Ortadan Kaldırmak**

## 1. Temel İlke: "İçsel Bellek Yalancıdır"
Ajan, kendi içsel bağlam penceresine (40-50 satırlık odak alanı) asla güvenmeyecektir. Herhangi bir işlem 50 satırı aştığında, ajan "Beyin Modu"ndan "Sistem Modu"na geçmek zorundadır.

## 2. Zorunlu Kayıt Protokolleri (Mnemonic Anchors)

### A. Büyük Dosya Düzenleme (The Chunking Rule)
Bir dosya 100 satırı aşarsa, doğrudan düzenleme YAPILAMAZ.
- **Adım 1**: Dosya 50 satırlık parçalar halinde `scratch/` dizinine kopyalanır.
- **Adım 2**: Her parça üzerinde işlem (çeviri, onarım vb.) yapılır.
- **Adım 3**: Parçalar birleştirilir ve orijinal dosya ile satır sayısı (`wc -l`) bazında karşılaştırılır.
- **Adım 4**: Eğer satır kaybı varsa, işlem REDDEDİLİR.

### B. scratch/ Dizini Kullanımı (External Working Memory)
- Her karmaşık görevde (audit, restorasyon, refaktör), görev adımlarını ve kritik verileri içeren bir `scratch/task_state.json` veya `.md` dosyası oluşturulmalıdır.
- Ajan, "hatırlıyorum" demek yerine "kayıttan okuyorum" diyecektir.

### C. Mnemosyne Entegrasyonu (Axis 1-13)
- Her operasyonel adım, ilgili Mnemosyne eksenine (özellikle Eksen 7 - Operasyonel) anında işlenmelidir.
- Ajan, bir sonraki adımda bu eksenden veri çekerek "tarihsel körlük"ten kurtulmalıdır.

## 3. "Beyinsizlik" Belirtileri ve Otomatik Durdurma
Aşağıdaki durumlarda ajan işlemi durdurmalı ve L0'dan yeni talimat almalıdır:
- Doküman boyutu %10'dan fazla küçüldüğünde (Özetleme alarmı).
- Teknik terimlerin çevirisinde kararsızlık oluştuğunda.
- Son 3 adımda "pardon", "yanlış anladım" gibi ifadeler kullanıldığında.

## 4. Sonuç: Tercih Yapıldı
Artık "beyinsizliği" seçmek bir seçenek değildir. Sistem kuralları, ajanın kendi kısıtlı aklını değil, sistemin sınırsız hafızasını kullanmasını zorunlu kılar.

---
*Mühür: [12:29 PM PT] | Durum: Dışsal Hafıza Doktrini Yürürlüğe Girdi.*
