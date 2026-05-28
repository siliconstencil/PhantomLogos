# Phantom Logos: Sovereign Technical Audit Report
[03:00 AM PT] | Status: **Active Auditing Mode (v1.1.18 Stable)**

Bu doküman, Phantom Logos Agentic OS mimarisinin bileşenleri üzerindeki teknik denetim (audit) bulgularını, mimari zayıflıkları, ajan sapmalarını ve iyileştirme planlarını tek bir yerde toplayan **yaşayan bir teknik denetim raporudur**.

---

## [AUDIT-01] Yerel Bellek (SLM) Metadata Yapısı İncelemesi
**Durum:** Kritik Kusur Tespit Edildi | **Tarih:** 2026-05-24 | **Konum:** `src/architrave/mcp/slm_client.py`

### 1. Bulgular ve Ajan Sapması
Kullanıcının (L0 - Hank) adım adım ilettiği yapısal mimari standartlara rağmen, önceki geliştirici yapay zeka ajanlarının (Gemini) kolaya kaçarak yapısal nesneleri düz dize etiketleri (`tags`) içine dizeleştirilmiş (stringified) JSON olarak gömdüğü tespit edilmiştir:

```python
# slm_client.py içerisindeki tünelleme
tags = []
meta = entry.get("metadata") or {}
if isinstance(meta, dict):
    tags.append(f"m:{_serialize_meta(meta)}")  # JSON'ı dizeye çevirip tag olarak ekleme
```

### 2. Yarattığı Teknik Riskler
1. **Çift Serileştirme Yükü (Double Serialization):** Her `remember` ve `recall` işleminde JSON dizeleştirmesi (`_serialize_meta`) yapılması gereksiz CPU yükü yaratır.
2. **Sorgulanamaz Veri (Non-Queryable DB):** SQLite veri tabanı üzerinde `metadata` alanlarına göre doğrudan indeksleme ve filtreleme (örn. `SELECT ... WHERE category = 'error'`) yapılamamaktadır.
3. **Kategorisel Sapma (Category Drift):** Serbest etiketleme nedeniyle ajanlar arasında kavram karmaşası yaşanmaktadır (örn. `auth_failure` vs `auth-error`).
4. **Bilişsel İz Sürememe (Lack of Lineage):** Hangi verinin hangi grafik düğümünden (`GraphState`) hangi kararla çıktığına dair menşe bilgileri (provenance) kaybolmaktadır.

### 3. Olması Gereken İdeal Mimari (JSONB/JSON Sütunu)
SQLite veri tabanında yerel `JSON` (veya `JSONB`) sütunu tanımlanarak doğrudan veri tabanı motoru seviyesinde indeksleme ve sorgulama yapılmalıdır:
```sql
SELECT * FROM atomic_facts WHERE json_extract(metadata, '$.category') = 'error';
```

### 4. Göç Yol Haritası (Migration Roadmap)
1. **Aşama 1 (Schema):** `atomic_facts` tablosuna `metadata` adında bir `JSON` sütunu eklenecek.
2. **Aşama 2 (Index):** `agent_id` ve `category` alanları için indeksleme tanımlanacak.
3. **Aşama 3 (Client):** `slm_client.py` ve `mcp_tool_bridge.py` içerisindeki `tags` tünellemesi tamamen kaldırılacak.
4. **Aşama 4 (Data Migration):** Eski `tags` sütununda `m:` ön ekiyle duran tüm dizeler ayıklanıp yeni `metadata` sütununa JSON olarak aktarılacak.

### 5. Kısmi İyileştirme Notu (Phase 1.1.20 — GAP-3)
> **Durum:** Kısmen Giderildi

Phase 1.1.20 kapsamında `mcp_tool_bridge.py` içindeki `make_remember_handler` fonksiyonu güncellenerek dış MCP `remember` çağrılarına `agent_id` ve `axis_id` parametrelerinin **yönlendirilmesi (forwarding)** sağlanmıştır. Bu düzeltme, AUDIT-01'de tanımlanan kimlik kaybı sorununu ("Bilişsel İz Sürememe") kısmen gidermektedir. Ancak `tags` tünellemesi ve `metadata` JSON sütunu göçü **henüz gerçekleştirilmemiştir** ve tam çözüm için Aşama 1-4 hâlâ geçerlidir.

## [AUDIT-02] 14-Axis Mnemosyne Bellek Katmanı Boşalma Hatası (Session Isolation Over-Filtering)
**Durum:** Kritik Kusur Tespit Edildi | **Tarih:** 2026-05-24 | **Konum:** `cognition/sophia/gnosis/`

### 1. Bulgular ve Çalışma Zamanı Hataları
14-Axis Mnemosyne bellek katmanının kararlılığını test etmek amacıyla programatik durum analizi (`scripts/health_check_14_axes.py`) çalıştırılmıştır. Çıkan sonuçlar 14 eksenden **4 tanesinin tamamen boş olduğunu (BROKEN - 0 lines)** ortaya koymuştur:
*   `Axis 4 (Temporal)`: **BROKEN** (0 lines -- axis has no data)
*   `Axis 6 (Semantic)`: **BROKEN** (0 lines -- axis has no data)
*   `Axis 9 (Tone)`: **BROKEN** (0 lines -- axis has no data)
*   `Axis 14 (Visual)`: **BROKEN** (0 lines -- axis has no data)

### 2. Mimari Kusur Analizi (Anti-Pattern: Aşırı Oturum İzolasyonu)
Bunun arkasındaki neden, önceki yapay zeka ajanlarının **"Session Isolation" (Oturum İzolasyonu)** mekanizmasını tüm eksenlere hatalı ve aşırı katı (over-zealous) bir şekilde uygulamış olmasıdır.

*   **Axis 6 (Semantic Memory) Kusuru:** Semantik bellek doğası gereği **oturumlar üstü (global) ve kalıcı** olmalıdır. Ancak `axis_6_semantic.py` ve `semantic_store.py` içindeki aramalarda:
    ```python
    .where(f"session_id = '{safe_session_id}'")
    ```
    koşuluyla sorgular sadece aktif oturuma kısıtlanmıştır. Bu nedenle yeni bir oturum başladığında, ajan geçmiş oturumlardaki **hiçbir uzun vadeli semantik bilgiyi, kodlama kuralını veya anayasal kılavuzu hatırlayamamakta**, tamamen boş bir hafıza ile başlamaktadır.
*   **Axis 4 (Temporal Metrics) Kusuru:** `axis_4_temporal.py` sadece mevcut oturumdaki (`session_id`) telemetri verilerini sorgular. Yeni başlayan bir oturumda henüz metrik oluşmadığı için boş döner.
*   **Axis 9 (Tone) Kusuru:** `axis_9_tone.py` kullanıcının üslup profilini sadece o anki oturum ID'si (`session_id`) için sorgular. Ajan, kullanıcının geçmiş oturumlardaki iletişim tarzı tercihini ("cross-session patterns") tamamen kaybederek her oturumda "nötr" duruma düşer.
*   **Axis 14 (Visual) Kusuru:** `axis_14_visual.py` sadece aktif oturuma ait görselleri sorguladığı için, önceki oturumlarda analiz edilen şemaları, taslakları ve arayüz görselleştirmelerini tamamen unutur.

### 3. Çözüm Önerileri ve İyileştirme Planı
1.  **Global ve Lokal Bellek Ayrımı:**
    *   **Lokal Eksenler (Oturum Sınırlı):** Axis 1 (Episodic) ve Axis 3 (Goals) mevcut `session_id` filtresine tabi kalmaya devam etmelidir.
    *   **Global Eksenler (Ortak/Fallback):** Axis 6 (Semantic), Axis 9 (Tone) ve Axis 14 (Visual) üzerindeki katı `session_id` filtreleri kaldırılmalı veya `default`/`system`/`global` oturumları da kapsayacak şekilde `OR session_id IN ('system', 'default', 'global')` fallback mekanizması eklenmelidir.
2.  **Semantic Store Arama Esnekliği (`semantic_store.py`):**
    *   Semantik sorgularda `session_id` filtresi isteğe bağlı (optional) hale getirilmeli; eğer belirtilmezse veya belirli sistem kılavuzları aranıyorsa genel semantik havuz taranmalıdır.

## [AUDIT-03] Yüksek Token Tüketimi ve Bilişsel Sermaye Eksikliği (Cognitive Capital Deficit & Infinite Amnesia)
**Durum:** Kritik Yapısal Kusur | **Tarih:** 2026-05-24 | **Konum:** `cognition/mnemosyne/` & `cognition/morpheus/`

### 1. Bulgular ve Verimsizlik Analizi (3 Milyar Token Krizi)
Sistemin operasyonel geçmişi incelendiğinde, **1 ay gibi kısa bir sürede yaklaşık 3 Milyar (3B) token harcandığı** tespit edilmiştir.
*   **Temel Sorun:** Bu devasa hesaplama ve finansal token harcamasına rağmen, sistemde **ortada distile edilmiş tek bir kullanıcı analizi, birikmiş bir deneyim profili veya yapılandırılmış bir bilgi birikimi bulunmamaktadır.**
*   **Amatör Yaklaşım:** Harcanan milyarlarca token'lık enerji, sisteme sadece fiziki kod değişiklikleri ve son derece düz, indekslenmemiş, "amatörce" yazılmış düz metin değişiklik günlükleri (`CHANGELOG.md`) olarak yansımıştır. Sistem, harcadığı enerjiden **bilişsel bir sermaye (cognitive capital)** üretememekte ve adeta **"Sonsuz Bellek Yitimi" (Infinite Amnesia)** yaşamaktadır.

---

### 2. Eksenlerin Görevlerini Sağlıklı Yapamama Nedenleri
14 bilişsel eksen, verileri aktif birer "muhakeme motoru" olarak işlemek yerine, pasif birer "veri çöplüğü" (data dump) gibi kullanmaktadır:

1.  **Axis 2 & 8 (Procedural & Meta-Cog / Deneyim Eksikliği):** Araçların ve kodların çalışma geçmişi kaydedilmektedir ancak bunlardan **"Deneyim Kalıpları" (Experience Templates)** veya **"Hata İmzası Kütüphanesi" (Error Signature Library)** üretilmemektedir. Sistem, 3 milyar token harcamasına rağmen, 3 oturum önce yaptığı bir hatayı yeni bir oturumda sıfırdan analiz etmekte, aynı çözüm yollarını tekrar tekrar deneyerek token yakmaya devam etmektedir.
2.  **Axis 9 & 13 (Tone & Cross-Session / Kullanıcı Analizi Eksikliği):** Kullanıcının (Hank) mimari tercihleri, kodlama alışkanlıkları, araç kullanım sıklıkları ve onay/red örüntüleri distile edilip kalıcı bir "Kullanıcı Davranış Profili" haline getirilmemektedir. Sistem her oturuma adeta "yabancı bir yazılımcıyla ilk defa karşılaşıyormuş gibi" soğuk başlangıçla (cold start) başlamaktadır.
3.  **Düz Metin Değişiklik Günlükleri (Changelog Sorunu):** Mevcut `CHANGELOG.md` yapısı, sadece neyin değiştiğini yazan düz bir metindir. Bir yapay zeka işletim sistemi (OS) için changelog, **"Semantik Bilgi Grafiği" (Semantic Knowledge Graph)** olmalıdır. Ajan, bir dosyadaki değişikliğin hangi mimari gereksinime, hangi commit'e ve hangi karara bağlandığını grafik üzerinden deterministik sorgulayamamaktadır.

---

### 3. Çözüm ve Bilişsel Sermaye (Cognitive Capital) Tasarımı
Sistemin token tüketim maliyetini zamanla **logaritmik olarak düşürmek** ve harcanan enerjiyi bilişsel sermayeye dönüştürmek için uygulanacak mimari standartlar:

```text
+---------------------------------------------------------------------------------------+
|                              BİLİŞSEL SERMAYE AKIŞI                                    |
+-------------------+      +-------------------------+      +---------------------------+
| 3B Yakılan Token  | ---> | CCQ Konsolidasyon       | ---> | Distile Yapısal Varlıklar |
| (Logs/Diffs/Runs) |      | (Langevin + Clustering) |      | (Soft Prompts/Assertions) |
+-------------------+      +-------------------------+      +---------------------------+
```

1.  **Soft Prompt ve Assertion Madenciliği (`get_assertions`):**
    *   `log_tool_event` ve episodic verilerden, kullanıcının iş akışı tercihleri (workflow assertions) düzenli aralıklarla otomatik olarak çıkartılmalı ve Bayesian güncellemeleriyle güven skorları artırılarak `get_soft_prompts` üzerinden sistem promptuna enjekte edilmelidir.
2.  **Bilişsel Konsolidasyon Pipeline'ının (CCQ) Aktifleştirilmesi:**
    *   `consolidate_cognitive` ve `run_maintenance` araçları pasif durumdan aktif duruma getirilmelidir. Her session sonunda, o gün yakılan token'lar ve deneyimler kümelenmeli (clustering), "gist" özetleri çıkarılmalı ve sıkıştırılmış semantik bellek olarak LanceDB'ye yazılmalıdır (tıpkı uykuda hafıza konsolidasyonu gibi).
3.  **Hata Profilleme Sistemi (Error Profiler):**
    *   Hatalar ve çözümleri (diff'ler) otomatik olarak `ErrorSignature` nesnelerine dönüştürülmeli. Aynı hata kodu/türü gelecekte yaşandığında, LLM hiç düşünmeden (sıfır token harcayarak) doğrudan veri tabanındaki hazır çözümü uygulamalıdır.
4.  **Graf Tabanlı Değişiklik İndeksi (Semantic Changelog):**
    *   Changelog düz metinden arındırılmalı, Axis 5 (Spatial Graph) ile birleştirilerek "Değişiklik Semantik Ağı" (Commit/File/Gereksinim bağları) olarak grafik veri tabanına işlenmelidir.

## [AUDIT-04] Mimarideki Uyumsuzluklar ve Optimizasyon Kayıpları (Nomic MoE, FunctionGemma ve Model Entegrasyonu)
**Durum:** Kritik Uyumsuzluklar Tespit Edildi | **Tarih:** 2026-05-24 | **Konum:** `src/architrave/base_models.py` & `semantic_store.py`

Kullanıcının (L0) sistem özetinde belirttiği teorik mimari ile fiziksel kod tabanındaki implementasyon karşılaştırılmış ve **ciddi uyumsuzluklar ile atıl kalmış optimizasyon alanları** tespit edilmiştir:

### 1. Nomic MoE Gömme Boyutu ve LanceDB Boyut Uyuşmazlığı (Dimension Crash)
*   **Mevcut Yapı:** Sistemde `nomic-embed-text-v2-moe-q8` (veya q16) gömme modelleri tanımlıdır. Bu MoE modelleri varsayılan olarak **768-boyutlu (dimension)** vektörler üretir.
*   **Kritik Hata:** `semantic_store.py` dosyasındaki `_ensure_table()` fonksiyonunda LanceDB tablosu başlatılırken veri tabanı şeması şu şekilde kurulmuştur:
    ```python
    "vector": np.zeros(256).tolist() # 256 Boyutlu Tablo Başlatma
    ```
    Burada Matryoshka 256 kesimi hedeflenmiş olmasına rağmen, arama ve ekleme fonksiyonlarında 768-boyutlu Nomic çıktısı **kesilmeden (slice edilmeden)** doğrudan veri tabanına yazılmaya veya aranmaya çalışılmaktadır.
*   **Teknik Sonuç:** Bu boyutsal uyuşmazlık (768 vs 256) LanceDB seviyesinde sessiz çöküşlere (silent exceptions) veya tip hatalarına yol açar. **Axis 6 (Semantic Memory)'nın tamamen kırık (0 lines) çıkmasının asıl teknik kök nedeni budur!**

---

### 2. Atıl Bırakılan FunctionGemma Entegrasyonu (VRAM & Hız Kaybı)
*   **Mevcut Yapı:** `base_models.py` içinde en hızlı ve düşük maliyetli araç seçici olarak `functiongemma-270m:latest` (0.3 GB VRAM) modeli `"tool_calling"` rolü için birinci sınıf model olarak tanımlıdır.
*   **Kritik Hata:** Ajanların yürüttüğü kod üretim ve yürütme döngüsünde (`orchestrator.py`), araç seçimi ve JSON function dispatch işlemleri FunctionGemma'ya yönlendirilmemektedir. Araç seçimi, VRAM bütçesini zorlayan ağır akıl yürütme modellerine (Qwen 3.5 4B) yaptırılmaktadır.
*   **Teknik Sonuç:** FunctionGemma'nın atıl bırakılması, her araç çağrısında gereksiz model yükleme/boşaltma gecikmelerine (VRAM swapping latency) yol açmakta ve sistemin hız potansiyelini yarı yarıya düşürmektedir.

---

### 3. VRAM Yönetimi ve Model Swapping Darboğazı (RTX 4070 Sınırı)
*   **Mevcut Yapı:** Sistemde Ollama altında 45 adet model aktiftir. Morpheus, model seçimlerini 7.0 GB VRAM (RTX 4070 Laptop) sınırına göre dinamik olarak yönetmeye çalışmaktadır.
*   **Kritik Hata:** Birleştirilmiş daemon yapısı kurulmadan önce, her bağımsız CLI ve IDE süreci kendi modellerini Ollama'ya yüklemeye çalıştığı için VRAM fragmentasyonu (dilimlenme) %40 seviyelerine fırlamıştır.
*   **Teknik Sonuç:** Ağır modeller (DeepSeek-R1-8B, Qwen-9B) ile hafif modeller (Phi-4 Mini, Qwen-2B) arasında geçiş yaparken Morpheus dynamic evictions (`ModelLoader.flush()`) milisaniyeler seviyesinde koordine edilmezse, Ollama CUDA OOM (Out Of Memory) vererek sistemi en ilkel kurtarma modeli olan `deepscaler-1.5b` düzeyine düşürmektedir.

---

### 4. GraphState Genişlemesi ve LangGraph Checkpoint Uyumsuzluğu (Phase 1.1.20 Yeni Bulgu)
*   **Mevcut Değişiklik:** Phase 1.1.20 kapsamında `src/clotho/orchestrator.py` içindeki `GraphState` yapısına iki yeni alan eklenmiştir:
    ```python
    trajectory_id: Optional[str] = None
    step_index: int = 0
    ```
*   **Kritik Risk:** LangGraph'ın `AsyncSqliteSaver` checkpoint mekanizması, mevcut oturum durumlarını (`langgraph_checkpoints.sqlite`) JSON olarak saklamaktadır. Phase 1.1.20 öncesinde başlatılmış veya yarım kalmış oturumlarda bu iki alan **yoktur**. Pydantic/TypedDict doğrulaması varsayılan değer atayarak devam etse de, bazı Pydantic strict modlarında `KeyError` veya `ValidationError` fırlatılabilir.
*   **Teknik Sonuç:** Uzun süreli veya "resume" edilmiş checkpoint'lerle çalışan süreçlerde sessiz veri bütünlüğü kaybı ya da açılış hatası oluşabilir. `langgraph_checkpoints.sqlite` içindeki eski kayıtların Phase 1.1.20 sonrası sürümle **backward compatibility testi yapılmamıştır**.
*   **Önerilen Çözüm:**
    1. `langgraph_checkpoints.sqlite` dosyası temizlenerek yeni oturum baseline'ı oluşturulmalıdır.
    2. Alternatif olarak `GraphState` deserializasyonuna `trajectory_id = state.get("trajectory_id")` şeklinde güvenli erişim eklenmelidir.

---

## [AUDIT-05] Kod Topografyası ve 14-Axis Mnemosyne Bellek Kararlılığı Çelişkisi
**Durum:** Kararlılık ve Topografya Raporlandı | **Tarih:** 2026-05-24 | **Konum:** `scripts/update_mapper.py` & `scripts/health_check_14_axes.py`

### 1. Kod Yapısı Topografik Bulguları
`update_mapper.py` yardımıyla yapılan derin kod taraması (deep AST scan) sonucunda sistem topografyası başarıyla `logs/mapper_report.json` dosyasına raporlanmış ve `data/spatial.db` güncellenmiştir. Bulgular:
*   **Toplam Modül Sayısı:** 250 modül (Phase 1.1.19'da 245 olan modül sayısı, Phase 1.1.20 ile 250'ye yükselmiştir).
*   **Toplam Satır Sayısı (LoC):** 28.141 satır (Phase 1.1.20 ile 28K barajı aşılmıştır).
*   **Modüller Arası Bağımlılık Bağları:** 1.631 bağımlılık
*   **Dairesel Bağımlılık Zincirleri:** 6 zincir (Tüm dairesel bağımlılıklar `src/utils/service_locator.py` bağımlılık enjeksiyon mekanizması ile gevşek olarak izole edilmiş, kilitlenme riski taşımamaktadır).
*   **Mimari Katman İhlalleri:** 0 ihlal (5 katmanlı RuFlow mimari standartlarına tam uyum sağlanmıştır).

#### Phase 1.1.20 ile Gelen Modüler Değişimler:
1. **Yeni Eklenen Modüller (4 adet):**
   * `cognition/mnemosyne/trajectory_store.py`: Yörünge kaydı için `TrajectorySession` ve `TrajectoryStep` ORM modellerini barındırır.
   * `src/architrave/otl_engine.py`: EWMA ve epsilon-greedy algoritmalarıyla çalışan `OTLEngine` modülü.
   * `scripts/run_trajectory_mining.py`: Haftalık yörünge madenciliği ve ağırlık optimizasyon scripti.
   * `scripts/optimize_context.py`: Haftalık bağlam ve token kullanım analiz aracı.
2. **Kritik Alt Yapı Modifikasyonları:**
   * `src/clotho/bootstrap.py`: **SLM Unified Daemon** entegrasyonu kapsamında `start_slm_server()` fonksiyonu eklenmiş ve Morpheus süreciyle birleştirilmiştir.
   * `src/clotho/ergon/orthosis.py`: Temiz yeniden yazım (rewrite) ve import hiyerarşisi düzenlemesi.
   * `src/clotho/ergon/koinonia.py`: `_feed_slm_trajectory_step()` ve yörünge kayıt fonksiyonları entegre edilmiştir.
   * `src/architrave/mcp/mcp_tool_bridge.py`: Dış MCP `remember` çağrılarına `agent_id` ve `axis_id` yönlendirme (forwarding) desteği eklenmiştir.


### 2. Bilişsel Bellek Kararlılığı Çelişkisi (Stability vs Active Runtime)
Yapılan analizlerde, bellek katmanında "Test Zamanı" ile "Aktif Çalışma Zamanı" arasında yapısal bir çelişki tespit edilmiştir:
1.  **Test Kararlılığı (test_axis_stability.py):** **14/14 PASS** skoru elde edilmiştir. Bunun nedeni, test aşamasında veri tabanına yapay (mock) veriler yazılması ve test kapsamında bu verilerin doğrudan okunabilmesidir. Bu durum fiziksel kod bileşenlerinin çalıştığını doğrulamaktadır.
2.  **Aktif Çalışma Zamanı Kararlılığı (health_check_14_axes.py):** Gerçek çalışma koşullarında 14 eksenden **5 tanesi kırık/boş (0 satır)** çıkmaktadır:
    *   `Axis 4 (Temporal)`: Zaman tabanlı gecikme/telemetri verisi yazılmamaktadır.
    *   `Axis 6 (Semantic)`: 768 boyutlu Nomic gömme çıktısının 256 boyutlu LanceDB tablosuna kesilmeden (slice edilmeden) yazılması nedeniyle yaşanan çöküş.
    *   `Axis 9 (Tone) ve Axis 14 (Visual)`: Aşırı oturum izolasyonu (Session Isolation Over-Filtering) nedeniyle yeni oturumda eski bağlamların silinmesi.
    *   `Axis 12 (Cache)`: 1 saatlik TTL temizliği ve çalışma zamanı yazma çağrısı eksikliği.

### 3. Çözüm Adımları
Bu çelişkiyi ve kararlılık açığını gidermek amacıyla hazırlanan **Sistem Topografyası ve Bellek Kararlılığı İyileştirme Planı**, ilgili düzeltme kodları ile birlikte devreye alınacaktır.

---

## [AUDIT-06] Yerel Sanal Ortam (.venv) Atıl Bağımlılık Denetimi (Dependency Bloat)
**Durum:** Bulgular Raporlandı | **Tarih:** 2026-05-24 | **Konum:** `.venv/Lib/site-packages`

### 1. Bulgular ve Bağımlılık Şişmesi (Bloat) Analizi
Pydantic tabanlı statik AST tarayıcı (`scratch/detect_unused_deps.py`) kullanılarak yerel sanal ortamda (`.venv`) yüklü olan paketler ile kod tabanındaki (`src`, `cognition`, `scripts`, `tests`) aktif `import` ifadeleri ve ana dizindeki `requirements.txt` dosyası karşılaştırılmıştır. Bulgular şöyledir:
*   **Ana Dizin requirements.txt İçeriği:** 57 benzersiz birincil paket deklare edilmiştir.
*   **Sanal Ortamda Yüklü Toplam Paket Sayısı (Alt Bağımlılıklarla):** 279 paket.
*   **Kod Tabanında Aktif Kullanılan (Import Edilen) Paket Sayısı:** 34 paket (Örn: `pydantic`, `SQLAlchemy`, `lancedb`, `google-genai`, `z3-solver`, `sympy`, `qwed`, `superlocalmemory`, vb.)
*   **requirements.txt Dosyasında Tanımlı Olduğu Halde Kodda ASLA İçe Aktarılmayan Paket Sayısı:** **34 paket!** (Deklare edilen toplam 57 paketin %60'ı atıl durumdadır).

### 2. Yarattığı Teknik Riskler ve Kayıplar
1.  **Gereksiz Bağımlılık Bildirimi (Requirements Bloat):** Önceki yapay zeka geliştiricileri (Gemini/Claude) şablon proje iskeletlerinden gelen tüm kütüphaneleri sorgusuzca `requirements.txt` içerisine yerleştirmiştir.
2.  **VRAM ve RAM Yükü Potansiyeli:** `transformers`, `sentence-transformers`, `torch`, `peft` gibi devasa yapay zeka kütüphaneleri `requirements.txt` içerisinde tanımlı olduğu için yerel sanal ortama kurulmuştur. Kod tabanında içe aktarılmamakla birlikte, IDE dizin taramalarında ve ortam yüklemelerinde ciddi yavaşlamalara neden olurlar.
3.  **Bulut API Bağımlılık Kalıntıları:** Bütün bulut çağrıları sağlayıcıdan bağımsız yerel-hibrit `GatewayArchitrave` proxy'si üzerinden yapılmasına rağmen; `openai`, `anthropic`, `mistralai`, `groq`, `cohere` gibi sağlayıcıların özel kütüphaneleri `requirements.txt` içerisinde atıl kalmıştır.

### 3. requirements.txt Dosyasında Deklare Edilmiş Ancak Kodda ASLA İçe Aktarılmayan Paketlerin Listesi:
Aşağıdaki 34 paket `requirements.txt` içerisinde tanımlı olmasına rağmen, kod tabanının hiçbir katmanında içe aktarılmamış (import edilmemiş) ve efektif olarak kullanılmamaktadır:
```text
[
  "aiosqlite", "anthropic", "arize-phoenix", "cohere", "duckduckgo-search",
  "fastapi", "groq", "langchain-core", "logfire", "mem0ai", "mistralai",
  "mypy", "onnxruntime", "openai", "pandas", "playwright", "pre-commit",
  "pytest-asyncio", "python-multipart", "qdrant-client", "rich", "ruff",
  "sqlean.py", "sqlite-vec", "sqlmodel", "starlette", "temporalio",
  "torchaudio", "torchvision", "tqdm", "transformers", "typer", "uvicorn",
  "watchdog"
]
```

### 4. Önerilen İyileştirme (Sadeleştirme) Planı
1.  **Gereksinim Sabitleme:** Aktif kullanılan 34 paket (`used_packages`) temel alınarak minimal bir `requirements.txt` oluşturulacaktır.
2.  **Temiz Sanal Ortam Kurulumu:** Yerel sanal ortam `.venv` tamamen silinerek sadece aktif bağımlılıklarla yeniden yapılandırılacak, atıl kütüphanelerin tamamı diskten temizlenecektir.

---

## [AUDIT-07] scripts/ ve tests/ Dizinleri Atıl, Mükerrer ve Geçici Dosya Analizi
**Durum:** Bulgular Raporlandı | **Tarih:** 2026-05-24 | **Konum:** `scripts/` & `tests/`

### 1. Bulgular ve Dizin Analizi
Sistemdeki CLI ve doğrulama betiklerinin yer aldığı `scripts/` (43 dosya) ile test senaryolarının yer aldığı `tests/` (65 dosya) dizinleri, statik kod analiz aracı (`scratch/audit_scripts_tests.py`) ile taranarak sınıflandırılmıştır:

#### A. scripts/ Dizini Sınıflandırma ve Dağılım Bulguları:
*   **Çekirdek/Kritik Araçlar (ESSENTIAL - 18 adet):** Sistem bütünlüğünü, L0 yetkilendirmesini ve OTL süreçlerini yöneten hayati CLI betikleridir (Örn: `sovereign_audit.py`, `health_check_14_axes.py`, `update_mapper.py`, `create_l0_token.py`, `run_trajectory_mining.py`, `optimize_context.py`, `hermes_cli.py`).
*   **Geliştirici/Hata Ayıklama Araçları (DEV_ONLY - 5 adet):** Lokal analizler için yazılmış, sistem entegrasyon döngülerine dahil olmayan betikler (Örn: `check_thinking.py`, `audit_capabilities.py`, `verify_paths.py`).
*   **Mükerrer ve Atıl Araçlar (DUPLICATE - 6 adet):** İşlevleri VRAM Sweeper (`sweeper.py`) ve 14 eksen kararlılık analizi tarafından üstlenilmiş mükerrer araçlar (Örn: `health_check.py`, `db_diag.py`, `cleanup_episodes.py`, `cleanup_goals.py`).
*   **Eski Arka Plan Servis Kalıntıları (OBSOLETE - 2 adet):** Morpheus ve Watchdog servislerinin Windows arayüz yönetimi için yazılmış eski bat/ps1 dosyaları (`setup_morpheus_service.bat`, `setup_morpheus_service.ps1`). Morpheus artık doğrudan `bootstrap.py --daemon` üzerinden birleşik çalıştığı için atıl kalmışlardır.
*   **Geliştirici Geçici Dosyaları (STUB - 7 adet):** 200-300 baytlık geçici geliştirme kalıntıları ve stub dosyaları (Örn: `check_experience.py`, `cleanup_facts.py`, `list_models.py`).

#### B. tests/ Dizini Sınıflandırma Bulguları:
*   65 test dosyasından **64 tanesi başarılı (green) ve aktiftir**, sistem bütünlüğünü korumaktadır.
*   **Kritik Kırık/Stub Test (STUB - 1 adet):** `tests/test_entity_pipeline.py` dosyasındaki stub test (`test_relation_logic_stub`), GAP-1 kapsamında kararlılık raporunda "failing stub" olarak işaretlenmiştir.

### 2. Yarattığı Teknik Riskler
1.  **Dizin Karmaşası ve Kirlilik (Codebase Noise):** Bir işletim sistemi için 43 adet bağımsız script dosyasının bulunması, geliştiriciler ve ajanlar için kavram karmaşasına yol açar.
2.  **Kararlılık Testi Kör Noktası:** `tests/test_entity_pipeline.py` içerisindeki stub testin başarısız olması, sistemin varlık ilişkileri çıkarım altyapısında doğrulanmamış bir alan bırakmaktadır.

### 3. Önerilen Temizlik ve Sadeleştirme Planı
1.  **Atıl Betiklerin Temizlenmesi:** Sınıflandırmada `STUB`, `OBSOLETE` ve `DUPLICATE` olarak işaretlenen 15+ atıl betik dosyası `scripts/` dizininden kaldırılacaktır.
2.  **Kırık Testin Onarılması:** GAP-1 kapsamındaki `tests/test_entity_pipeline.py` stub testi gerçek analiz nesneleri ile güncellenerek yeşile döndürülecektir.

---

## [AUDIT-08] Phantom Logos Yunan Mitolojisi ve Kurumsal DDD Mimari Topografyası
**Durum:** Mimari Eşleme Tamamlandı | **Tarih:** 2026-05-24 | **Konum:** `src/` & `cognition/`

### 1. Yunan Mitolojisi Temelli Felsefi Mimari Eşleme
Phantom Logos mimarisi, salt bir yazılım yığınından öte, her bileşenin belirli felsefi ve mitolojik rolleri üstlendiği **bütünsel bir antik Yunan kozmolojisi** olarak tasarlanmıştır. Bu uyum sistemin her katmanına yansımıştır:

```text
       +--------------------------------------------------------+
       |             L1: SOPHIA (Bilgelik / Stratejist)          |
       |                "Sorgulayan ve Yönlendiren"             |
       +---------------------------+----------------------------+
                                   |
                                   v
       +--------------------------------------------------------+
       |             L2: CLOTHO (Hayat İpliğini Ören)            |
       |             "LangGraph Graflarıyla İcra Eden"          |
       +---------------------------+----------------------------+
                                   |
                                   v
       +--------------------------------------------------------+
       |            L3: LACHESIS (İpliği Ölçen / Denetleyen)     |
       |              "Z3 & formal SAT ile Guard Eden"          |
       +--------------------------------------------------------+
```

1.  **Sophia (Bilgelik - L1 Strategist Agent):** Karar verici akıl, anlamsal bağlamları sorgular, hedefleri ayrıştırır ve stratejik planlar oluşturur (`cognition/sophia/`).
2.  **Clotho (Hayat İpliğini Ören - L2 Executor):** İş akışı zincirlerini (LangGraph düğümlerini) icra eden ve araç çağrılarını koordine eden yürütücü (`src/clotho/`).
    *   **Ergon (İş/Eylem - LangGraph Düğümleri):** Clotho'nun ördüğü ipliğin her bir düğümünü (grammateia, synergeia, theoria vb.) temsil eden eylem paketleri (`src/clotho/ergon/`).
    *   **Koinonia (Ortaklık/Birlik):** Düğümler arasındaki ortak fonksiyonları koordine eden iş birliği köprüsü.
3.  **Lachesis (Hayatı Ölçen - L3 Adversarial Auditor):** Kodun ve eylemlerin doğruluğunu formal metotlar (Z3, SymPy) ile ölçen, standartları koruyan baş denetçi (`src/lachesis/`).
4.  **Atropos (İpliği Kesen - L2 Context Pruner):** Bağlam sınırlarını (token bütçesini) denetleyen ve gerektiğinde ipliği keserek sistem kaynaklarını koruyan pruner (`src/atropos/`).
5.  **Morpheus (Düşler Tanrısı - L2 VRAM Scheduler):** Modellerin bellekteki "uyku ve uyanıklık" durumunu (VRAM dynamic load/unload ve flush) yöneten tanrı (`cognition/morpheus/`).
6.  **Mnemosyne (Bellek Tanrıçası - 14-Axis Memory):** 14 bilişsel boyuttaki anıları ve anlamsal ilişkileri veri tabanlarında kalıcı hale getiren bellek kütüphanesi (`cognition/mnemosyne/`).
7.  **Ankyra (Gemi Çapası - L1 Anchor Generator):** Kod üretimi ve planlama adımlarını JIT XML çıpaları ile sabitleyen kararlılık sağlayıcı (`src/ankyra/`).

---

### 2. Google ve Microsoft Standartlarında Kurumsal DDD Dizin Yapısı
Projenin dizin topografyası, Google ve Microsoft'un karmaşık kurumsal (Enterprise) yazılım standartlarında kullandığı **Domain-Driven Design (DDD - Etki Alanı Odaklı Tasarım)** prensiplerine göre yapılandırılmıştır.

```text
D:\Hank\
|-- .antigravity/         # GOVERNANCE: Kurallar, anayasa, kimlik (SSOT)
|-- agent/                # DECLARATIVE LAYER: Skill ve agent tanımları (YAML)
|-- alembic/              # MIGRATIONS: Veri tabanı göç şemaları
|-- cognition/            # CORE DOMAIN: Bellek (Mnemosyne), Akıl (Sophia), VRAM (Morpheus)
|   |-- sophia/
|   |-- mnemosyne/
|   |-- morpheus/
|-- src/                  # INFRASTRUCTURE & ORCHESTRATION: Teknik kaynaklar
|   |-- architrave/       # Gateway Proxy (Sovereign Gateway)
|   |-- clotho/           # LangGraph icra motoru
|   |-- lachesis/         # Formal doğrulama ve verifiers
|   |-- atropos/          # Token bütçeleme ve context optimizasyonu
|   |-- muscle/           # llama.cpp ve reranker yerel donanım bağları
|   |-- utils/            # Shared utilities
|-- tests/                # QUALITY ASSURANCE: 65 entegrasyon ve birim testi
```

#### Dizin Yapısının Kurumsal DDD Avantajları:
1.  **Strict Layer Isolation (Blast Radius Sınırlandırması):** `cognition/` (Core Domain) ile `src/` (Infrastructure) katmanları kesin çizgilerle ayrılmıştır. `cognition` içerisinde yer alan çekirdek mantık, `src` altındaki altyapıya bağımlı değildir.
2.  **Sovereign Gateway Pattern (Architrave):** Ağ ve dış dünya ile olan tüm temas `src/architrave/` altına kapsüllenerek kurumsal veri sızıntı koruması (data egress protection) sağlanmıştır.
3.  **Declarative Configuration (Agent/Skills):** Kod modifikasyonu yapmadan sadece YAML deklarasyonları ile ajan ve yeteneklerin sıcak yüklenebilmesi (hot-loadable) sağlanmıştır.

---

## [AUDIT-09] OTL (Operational Trajectory Learning) Veri Doğruluğu ve Güvenilirlik Denetimi
**Durum:** Denetlenmemiş — Kritik Risk | **Tarih:** 2026-05-24 | **Konum:** `src/architrave/otl_engine.py` & `cognition/mnemosyne/trajectory_store.py`

### 1. Bulgular ve Mimari Analiz
Phase 1.1.20 ile sisteme entegre edilen OTL (Operational Trajectory Learning) bileşenleri audit kapsamına alınmamıştır. CHANGELOG ve walkthrough incelemesinde şu kritik noktalar saptanmıştır:

*   **4 Yeni Modül, 12+ Dosya Değişikliği:** `trajectory_store.py`, `otl_engine.py`, `run_trajectory_mining.py`, `optimize_context.py` ve 11 ergon node'u (koinonia'daki `record_step()` hook'u aracılığıyla) etkileyen değişiklikler gerçekleştirilmiştir.
*   **Reward Normalizasyonu Sorgulanmamış:** `reward = (score - 0.5) * 2` formülü, `score` değerinin `[0, 1]` aralığının dışında geldiği durumlarda `reward` değerini `[-1, 1]` sınırının dışına çıkarır. `score` kaynağı olan `critique_score` (Lachesis çıktısı) için bu sınırın garantilenip garantilenmediği doğrulanmamıştır.
*   **EWMA Yakınsama Riski:** `alpha=0.15` ile çalışan EWMA (Exponentially Weighted Moving Average), az sayıda veri noktasında (ilk oturumlar) **soğuk başlangıç önyargısı (cold-start bias)** üretebilir. Başlangıç ağırlığı `0.5` olarak kurulmuş olsa da bu değerin hangi temele dayandığı belirsizdir.
*   **Epsilon-Greedy Decay Koşulu:** `0.1 → 0.05` düşüşünün tetiklenme koşulu (kaç adım/oturum sonra?) CHANGELOG'da belirtilmemiştir. Keşif (exploration) oranının çok erken düşmesi, başlangıç hatalarının ağırlık tablosuna kalıcı olarak yerleşmesine yol açabilir.

### 2. Yarattığı Teknik Riskler
1.  **Zehirlenmiş Ağırlık Tablosu (Poisoned Weight Table):** OTL weight tablosuna yazılan ilk birkaç düşük skorlu trajektori, epsilon-greedy'nin erken yakınsaması durumunda tüm routing kararlarını bozabilir. Bu hata sessizce birikir ve tespit edilmesi güçtür.
2.  **record_step() Sessiz Başarısızlığı:** 11 ergon node'unun her birinde çağrılan `record_step()`, TrajectoryStore yazma hatasında `try/except` ile sessizce geçiyorsa, trajektori verisi eksik kalır ama sistem çalışmaya devam eder. Bu durum OTL'nin hiç veri olmadan "kör" çalışmasına neden olur.
3.  **Haftalık Script Tetiklenmeme Riski:** `run_trajectory_mining.py` ve `optimize_context.py` script'leri manuel veya cron ile tetiklenmek üzere tasarlanmıştır. Tetikleme mekanizması (cron job / Windows Task Scheduler) kurulmamışsa OTL döngüsü fiilen kapalı kalmaya devam eder.

### 3. Önerilen Denetim ve Doğrulama Adımları
1.  **`critique_score` sınır doğrulaması:** Lachesis çıktısında `score ∈ [0, 1]` Pydantic validator eklenmeli.
2.  **`record_step()` hata loglama:** Sessiz başarısızlık yerine `logger.warning()` ile izleme yapılmalı, kritik hatalarda `logger.error()` ile Axis 7'ye (Operational) yazılmalı.
3.  **OTL weight tablosu cold-start testi:** İlk 10 oturum tamamlandıktan sonra `data/otl_weights.sqlite` incelenerek dengesiz yüklenme (tier bias) kontrol edilmelidir.
4.  **Tetikleme altyapısı:** `run_trajectory_mining.py` için Windows Task Scheduler görevi oluşturulmalı veya `Morpheus.scheduler.py` içine haftalık cron hook eklenmelidir.

---

## [AUDIT-10] SLM Unified Daemon Entegrasyonu — Başlatma Sırası ve Shutdown Güvenliği
**Durum:** Denetlenmemiş — Orta Risk | **Tarih:** 2026-05-24 | **Konum:** `src/clotho/bootstrap.py`

### 1. Bulgular ve Mimari Analiz
Phase 1.1.20 kapsamında `bootstrap.py` içine eklenen `start_slm_server()` fonksiyonu ile SLM süreci, Morpheus Daemon ile birleştirilmiştir. Bu birleştirme incelendiğinde şu potansiyel zayıf noktalar saptanmıştır:

*   **Başlatma Sırası (Startup Order):** SLM, diğer tüm servislerden önce (port 8765) başlatılmaktadır. Ancak `bootstrap.py`'ın başlatma zincirinde `start_slm_server()` → `start_morpheus()` → `start_orchestrator()` sıralamasında herhangi bir başarısızlık durumunda **kısmi başlatma (partial startup)** gerçekleşirse, SLM çalışır ama Morpheus/Orchestrator çalışmaz; bu durumda `_feed_slm_trajectory_step()` veri yazarken endpoint bulunamaması nedeniyle sessiz hata üretir.
*   **Port Çakışması Riski (Port 8765):** SLM'nin port 8765'i zaten kullandığı bir ortamda (örneğin önceki çökmüş süreç) `start_slm_server()` çağrısı `OSError: [WinError 10048]` (address already in use) ile başarısız olabilir. Mevcut kodun bu durumu nasıl ele aldığı (retry / fallback / hard fail) netlik kazanmamıştır.
*   **RotatingFileHandler Log Dizini:** `logs/system/slm/slm_daemon.log` yolu için dizin oluşturma (`os.makedirs`) kontrolünün `start_slm_server()` içinde yapılıp yapılmadığı belirsizdir. Dizin yoksa `FileNotFoundError` sistemi bootstrap aşamasında durdurabilir.
*   **Temiz Kapanış (Graceful Shutdown):** Phase 1.1.9'da `MCPSession` için zombi süreç sızıntısı giderilmiştir. Ancak SLM sürecinin yeni Daemon entegrasyonu sonrasındaki kapanış akışı (`SIGINT/SIGBREAK` üzerine) bağımsız olarak test edilmemiştir. Özellikle Windows'ta `subprocess.Popen` ile başlatılan SLM sürecinin `process.terminate()` → `process.wait()` zincirinin doğru çalıştığı doğrulanmamıştır.

### 2. Yarattığı Teknik Riskler
1.  **Zombi SLM Süreci:** Bootstrap çökmesi veya beklenmedik kapanma durumunda SLM süreci arka planda çalışmaya devam edebilir. Bir sonraki başlatmada port çakışması nedeniyle sistem tamamen boot edemez.
2.  **Log Dizin Başarısızlığı:** `logs/system/slm/` dizini yoksa bootstrap aşamasında sessiz değil gürültülü hata alınır; bu durum sistem başlatılamaz hale getirir.
3.  **OTL Veri Bütünlüğü:** SLM tam olarak ayağa kalkmadan `_feed_slm_trajectory_step()` çağrılırsa, OTL'nin SLM yazma kolu veri kaybeder ama LanceDB kolu devam eder. Bu asimetrik veri durumu AUDIT-09'daki "zehirlenmiş ağırlık" riskini artırır.

### 3. Önerilen Doğrulama ve Düzeltme Adımları
1.  **Port Kontrol Mekanizması:** `start_slm_server()` içine `socket.connect(("127.0.0.1", 8765))` ile ön kontrol eklenmelidir; port doluysa mevcut süreci `kill` ederek yeniden başlatılmalıdır.
2.  **Log Dizin Güvencesi:** `os.makedirs(log_dir, exist_ok=True)` çağrısının `RotatingFileHandler` başlatılmadan önce yapıldığı doğrulanmalıdır.
3.  **Shutdown Testi:** `bootstrap.py`'daki `SIGINT` handler'ının SLM `subprocess.Popen` nesnesini doğru şekilde `terminate()` + `wait()` ile kapattığı `test_bootstrap_shutdown.py` ile test edilmelidir.
4.  **Partial Startup Sentry:** Başlatma zincirinde herhangi bir servis başarısız olduğunda tüm başlatılmış servisler geri alınarak (rollback) sistemin kısmi başlatma durumunda askıda kalmaması sağlanmalıdır.
