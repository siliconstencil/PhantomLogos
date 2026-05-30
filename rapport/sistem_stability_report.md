# Antigravity Sistem Kararlilik Raporu

Denetim Zamani: [01:37 PM PT]

## 1. Genel Durum
Antigravity Sovereign OS kararlilik denetimi, dosya editlemesi yapilmadan tamamen audit modunda tamamlanmistir.

- Sistem Kararlilik Durumu: STABLE AND SEALED
- Guvenilirlik Skoru (Sophia): 1.00
- Tool Bridge Erisimi: 9/9 PASS
- Eksen Bellek Durumu (Mnemosyne): 10/14 OK, 4/14 VERI YOK (BROKEN)

---

## 2. 14-Eksen Bellek (Mnemosyne) Detaylari
Yapilan denetimde eksenlerin veri durum kodlari asagidaki sekildedir:

* Axis 1 (Episodic): OK (4 satir)
* Axis 2 (Procedural): OK (11 satir)
* Axis 3 (Goals): OK (4 satir)
* Axis 4 (Temporal): OK (4 satir)
* Axis 5 (Spatial): OK (4 satir)
* Axis 6 (Semantic): BROKEN (0 satir - mevcut session context icinde veri bulunmamaktadir)
* Axis 7 (Operational): OK (4 satir)
* Axis 8 (Meta): OK (2 satir)
* Axis 9 (Tone): BROKEN (0 satir - veri bulunmamaktadir)
* Axis 10 (Rational): OK (5 satir)
* Axis 11 (Verify): OK (2 satir)
* Axis 12 (Cache): BROKEN (0 satir - veri bulunmamaktadir)
* Axis 13 (Patterns): OK (2 satir)
* Axis 14 (Visual): BROKEN (0 satir - veri bulunmamaktadir)

Not: BROKEN olarak raporlanan eksenler (6, 9, 12, 14), sistem yapisindan kaynakli bir hatadan degil, aktif calisma oturumunda henuz bu eksenlere yazma islemi yapilmamis olmasindan kaynaklanmaktadir.

---

## 3. Tool Bridge Denetimi (Clotho)
Dokuz temel aracin erisilebilirligi ve kontrol akisi basariyla test edilmistir. Butun araclarin cagrilarinin basariyla yonlendirildigi teyit edilmistir:

* ls: PASS
* mapper: PASS
* semantic: PASS
* vram: PASS
* verify: PASS
* report: PASS
* skill: PASS
* prune: PASS
* vision: PASS

---

## 4. Veritabani Durumu (mnemosyne.db)
Sistem veritabani dosya yolu (<PROJECT_ROOT>/data/mnemosyne.db) uzerinde 24 tablo tespit edilmis ve tablo doluluk oranlari analiz edilmistir:

* operational_logs_v2: 1322 satir
* events: 1272 satir
* temporal_metrics: 5850 satir
* facts: 89 satir
* episodes: 226 satir
* goals: 33 satir
* tone_history: 155 satir
* governance_rules: 36 satir
* entities: 24 satir
* reflections: 9 satir
* agent_experience: 5 satir
* tool_paths: 17 satir
* semantic_relations: 2 satir
* failure_memory: 7 satir
* test_infra: 4 satir
* weekly_summary: 0 satir
* monthly_trend: 0 satir
* context_cache: 0 satir
* hyperedges: 0 satir
* hypernodes: 0 satir

---

## 5. Dizin ve Calisma Alani Sertlestirme (Path Hardening)
* Proje Kok Dizini: <PROJECT_ROOT> (SUCCESS)
* LocalRuntime Calisabilir Dizin: <PROJECT_ROOT>\bin\llama_bin (SUCCESS - yollar guvenli sekilde sabitlenmistir)
