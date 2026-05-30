# SQLite & Python Surecleri Kararlilik Sertlestirme Plani

Denetim Zamani: [03:04 PM PT]

## 1. Giris
Bu plan, `<PROJECT_ROOT>` çalışma alanındaki tüm SQLite bağlantı noktalarının taranması, veritabanı kilitlenme (busy lock / deadlock) risklerinin tespit edilmesi ve sistem kararlılığını artırmak için uygulanacak sertleştirme adımlarını içerir. Bu rapor, sonradan çalıştırılacak ajanlar için kesin bir rehber (implementation guide) niteliğindedir.

---

## 2. Tespit Edilen SQLite Baglanti Noktalari ve Risk Analizi

### A. Dogrudan sqlite3.connect Kullanan Moduller (Eksik Timeout/WAL)
Aşağıdaki modüllerde yapılan bağlantılarda `timeout` parametresi eksiktir veya varsayılan düşük değere (5.0s) ayarlıdır. Ayrıca bağlantılarda `busy_timeout` veya `WAL` pragması çalıştırılmamaktadır:

1.  **[reflection_store.py](file:///cognition/mnemosyne/reflection_store.py#L83)**:
    *   *Mevcut Kod*: `return sqlite3.connect(self.db_path)`
    *   *Risk*: Yansıma ve entity güncellemelerinde anında kilitlenmeye düşer.
2.  **[context_cache.py](file:///src/architrave/context_cache.py#L63)**:
    *   *Mevcut Kod*: `sqlite3.connect(self.db_path)` (Ensure, get ve set metodlarının hepsinde)
    *   *Risk*: Ajan bağlam önbelleği okunurken en ufak bir veritabanı yazma kilidinde tüm seans kilitlenir.
3.  **[opencode_store.py](file:///src/architrave/opencode_store.py#L30)**:
    *   *Mevcut Kod*: `return sqlite3.connect(self.db_path)`
    *   *Risk*: OpenCode entegrasyonu seans sorgularken kilitlenir.
4.  **[snapshot_manager.py](file:///src/lachesis/snapshot_manager.py#L43)**:
    *   *Mevcut Kod*: `sqlite3.connect(self.db_path)`
    *   *Risk*: Dosya bütünlük baseline taraması esnasında veritabanı yazma kilidinde kalır.

### B. Zaman Asimi ve WAL Olan Ancak busy_timeout Olmayan Moduller
1.  **[temporal_store.py](file:///cognition/mnemosyne/temporal_store.py#L45)**:
    *   *Mevcut Kod*: `sqlite3.connect(self._db_path, timeout=30)` (WAL sadece tablo oluştururken set ediliyor, her açılışta set edilmeli)
    *   *Risk*: Metrik ve gecikme yazma sıklığı çok yüksek olduğu için bağlantı kuyruğa girmeden hata verebilir.
2.  **[orchestrator.py](file:///src/clotho/orchestrator.py#L328)**:
    *   *Mevcut Kod*: `sqlite3.connect(db_path, check_same_thread=False)` (WAL set ediliyor ama timeout parametresi yok)
    *   *Risk*: LangGraph durum kaydedicisi (checkpointer) yazma yaparken başka bir daimon yazma başlattığında checkpointer çöker.

### C. SQLAlchemy Kullanan Moduller (Eksik WAL/Pragma Yapılandırması)
*   **Modüller**: `goal_store.py`, `meta_cognition.py`, `operational_store.py`, `procedural_store.py`, `rational_store.py`, `spatial_store.py`, `tone_store.py`, `visual_store.py`.
*   *Mevcut Durum*: Sadece `episodic_store.py` ve `hypergraph_store.py` modülleri connect event listener ile `WAL` modu set etmektedir. Diğer modüller veritabanı dosyasının o anki WAL durumuna güvenirler; ancak kendi bağlantı havuzlarında (pool) `busy_timeout` veya senkron pragma tanımları eksiktir.

---

## 3. Adim Adim Sertlestirme (Hardening) Aksiyon Plani

Ajanların altyapıyı onarmak için yapması gereken kod değişiklikleri şunlardır:

### 1. Adım: Tüm Doğrudan sqlite3 Bağlantılarına Ortak Yardımcı Eklenmesi
`sqlite3.connect` yapan tüm modüllerde bağlantı oluşturma fonksiyonu şu şekilde güncellenmelidir:
```python
def _get_secure_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    return conn
```
Bu yardımcı fonksiyon; `reflection_store.py`, `context_cache.py`, `opencode_store.py` ve `snapshot_manager.py` modüllerine entegre edilmelidir.

### 2. Adım: orchestrator.py Checkpointer Bağlantısının Hardening'i
`src/clotho/orchestrator.py` dosyasındaki bağlantı kurma satırı (Satır 328) şu şekilde güncellenmelidir:
```python
conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL;")
conn.execute("PRAGMA busy_timeout = 30000;")
conn.execute("PRAGMA synchronous=NORMAL;")
```

### 3. Adım: SQLAlchemy Bağlantı Havuzlarının Standartlaştırılması
`cognition/mnemosyne/` altındaki tüm SQLAlchemy tabanlı store sınıflarının `__init__` fonksiyonlarındaki `create_engine` çağrıları, `connect_args` içine `timeout=30` alacak şekilde güncellenmeli ve hepsine `episodic_store.py` içindeki `_set_wal_pragma` event dinleyicisi eklenmelidir:
```python
@event.listens_for(self.engine, "connect")
def _set_wal_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA busy_timeout = 30000;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.close()
```
