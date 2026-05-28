# Phantom Logos: Sistem Raporu & Kullanim Kilavuzu
# v1.1.27 | Durum: STABLE | [Oluturma: 2026-05-27 PT]

---

## 1. Sistem Nedir?

Phantom Logos, yerel donanim uzerinde calistrilan, bulut destekli hibrit bir **Agentic OS** (Otonom Ajan Isletim Sistemi) dir.

Temel vizyon: **Bulut = Beyin, Yerel = Kas ve Hafiza.**

- Internet olsa da olmasa da calisir.
- Bulut modeline erisim varsa derin strateji uretir; yoksa yerel LLM'ler devralir.
- 14 eksenli kalici hafizasi (Mnemosyne), 46 yerel model, 6 MCP sunucusu ve 103+ aracla donanmistir.
- Vibe coding, kod uretimi, dogrulama, gorsel analiz ve sistem otomasyonu icin tasarlanmistir.
- Token tasarrufunu merkeze alir: Matryoshka 256-boyut kesimi, FunctionGemma 270M ile sifir maliyetli arac secimi, adaptif draft atlama ile gereksiz LLM cagrisi yapilmaz.

---

## 2. Mimari Genel Bakis

```
[L0 — Hank (Insan Otorite)]
    |
    |-- Antigravity IDE (Web/Desktop) :32553
    |       |
    |       +-- Sovereign Gateway (GatewayArchitrave)
    |               |-- Cloud Provider (derin strateji)
    |               |-- Circuit Breaker (60s cooldown)
    |               +-- Yerel Fallback (Ollama :11434)
    |
    |-- OpenCode CLI (Capraz-Oturum Koprusu)
            |
            +-- Hermes CLI -> Mnemosyne Axis 13
```

### Ajan Katmanlari (RuFlow 3-Tier)

| Katman | Ajan | Rol | Model |
|--------|------|-----|-------|
| **L0** | Hank | Insan otoritesi. Tum yazma/silme islemleri L0 onayi gerektirir | — |
| **L1** | Sophia | Stratejist. 14 eksen baginlamini okur, plan uretir, taslak yazar | Sovereign Gateway (Cloud) / Qwen 3.5 9B UD (yerel) |
| **L2** | Clotho | Yurutucü. Arac cagrilarini, kod uretimini, LangGraph akisini yonetir | Qwen 3.5 4B UD (birincil) |
| **L2** | Atropos | Baglam Muhendisi. Token butcesini ve Matryoshka kesimini yonetir | Deterministik |
| **L2** | Morpheus | VRAM Yoneticisi. 7 GB VRAM hijyenini korur, modelleri yukler/bosaltir | Deterministik (nvidia-smi) |
| **L3** | Lachesis | Denetci. 4 motorlu formal dogrulama (SymPy, Z3, QWED, LLM) | Phi-4 Mini UD |
| **L3** | Hermes | Kopru Denetcisi. CLI araciligi ile capraz-oturum kaliciligi | CLI / Axis 13 |
| **L0 Router** | FunctionGemma | Arac Secici. 270 MB ile aninda JSON yapilandirilmis arac secimi yapar | FunctionGemma 270M |

---

## 3. 14 Eksenli Mnemosyne Hafizasi

Sistemin en kritik bileseni. Her oturum, her karar ve her arac cagrisi bu 14 eksende kalici olarak depolanir. SQLite (WAL) + LanceDB + SLM uzerinde calisir.

| Eksen | Ad | Teknoloji | Ne Depolar |
|-------|----|-----------|-----------|
| **1** | Episodik | SQLite WAL | Oturum olaylari, ajan adim gecmisi |
| **2** | Prosedural | SQLite | Arac kullanim kaliplari, basarili yollar |
| **3** | Hedef | SQLite | Aktif gorevler, fase durumu |
| **4** | Zamansal | SQLite | Zaman serisi metrikleri, gecikme verileri |
| **5** | Uzamsal | SQLite + AST | Codebase haritasi: 266 modul, 10 dairesel bagimlilik, AST analizi |
| **6** | Semantik | LanceDB + FTS | Vektor + tam metin arama (RRF birlestirme), Nomic MoE embeddingler |
| **7** | Operasyonel | SQLite + Sweeper | VRAM metrikleri, DB bakimi, saglik telemetrisi |
| **8** | Meta-Bilis | SQLite | Guvenilirlik skorlari, hata belleginin onleyici kurallar |
| **9** | Ton | ToneStore | Kisilik, iletisim stili, Turkce anahtar kelimeler |
| **10** | Rasyonel | SQLite | Yonetisim kurallari (rules.json), karar agaclari |
| **11** | Dogrulama | SymPy + Z3 + QWED | Matematiksel/mantiksal iddialarin resmi dogrulamasi |
| **12** | Verimlilik | SQLite + Axis12 Cache | Gemini baglam oncelleme metrikleri, token hit/miss dagilimi |
| **13** | Capraz-Oturum | SQLite (Dis) | OpenCode CLI ile oturumlararasi kalibi tanima |
| **14** | Gorsel | SQLite + VisualStore | VLM ciktilarinin Nomic metin embeddingleriyle depolanmasi |

### Baglam Montaji (gnosis.py)

Sophia bir gorev aldiginda `get_dynamic_context()` calisir: 14 eksenin tamamindan veri cekilir, token butcesi uygulanir ve `### MNEMOSYNE AXIS N` etiketleriyle yapilandirilmis tek bir baglam blogu Sophia'ya sunulur. Her iddia `[SRC:axis_N]` ile kaynak gostermek zorundadir.

---

## 4. Hafiza Katmani: SLM (SuperLocalMemory)

Mnemosyne'ye paralel calishan ek hafiza sistemi. SLM MCP sunucusu (slm.exe), yerel olarak Ollama uzerinde calisir ve 34 arac saglar.

### SLM'nin Mnemosyne'den Farki

| Ozellik | Mnemosyne (14 Eksen) | SLM |
|---------|---------------------|-----|
| Amac | Ajan bilissel hafizasi | Yukusk hafizasi (assertion, soft prompt, skill) |
| Depolama | SQLite + LanceDB | SQLite (yerel, izole) |
| Yazma yolu | Ajan pipeline | mcp_slm_* araclari |
| Saglik yedegi | LanceDB+Nomic+Jina | Nomic+Jina cascade |
| Agik P2P | Hayir | Mesh (mesh_send/peers/inbox) |
| Skill evrimi | Hayir | evolve_skill / skill_health |

### SLM Arac Kategorileri (34 arac)

- **Bellek CRUD**: `mcp_slm_remember`, `mcp_slm_observe`, `mcp_slm_update_memory`, `mcp_slm_delete_memory`, `mcp_slm_fetch`
- **Geri Cagirma**: `mcp_slm_recall` (4-kanal), `mcp_slm_search` (BM25 FTS5), `mcp_slm_rerank`, `mcp_slm_list_recent`
- **Oturum**: `mcp_slm_session_init`, `mcp_slm_close_session`, `mcp_slm_report_feedback`, `mcp_slm_report_outcome`
- **Davranissal**: `mcp_slm_get_assertions`, `mcp_slm_reinforce_assertion`, `mcp_slm_contradict_assertion`, `mcp_slm_get_soft_prompts`
- **Mesh P2P**: `mcp_slm_mesh_peers/send/inbox/state/lock/summary/events/status`
- **Skill Evrimi**: `mcp_slm_evolve_skill`, `mcp_slm_skill_health`, `mcp_slm_skill_lineage`
- **Bakim**: `mcp_slm_run_maintenance`, `mcp_slm_forget`, `mcp_slm_consolidate_cognitive`, `mcp_slm_set_mode`, `mcp_slm_log_tool_event`

---

## 5. Yerel Model Ekosistemi (46 Model)

Tum modeller GGUF formatinda D:\Google\AntiGravity\General Tools\ konumunda saklanir. Hicbir model HuggingFace'ten indirilmez.

### 5.1 Katman Yonlendirme (RuFlow Tier Secimi)

| Tier | Karmasiklik | Model | VRAM | Kullanim |
|------|------------|-------|------|---------|
| **0** | < 0.3 | DeepScaler 1.5B | 1.1 GB | Hizli Q&A, arac yok, dogrulama yok |
| **1** | 0.3-0.5 | Ministral 3B UD | 2.2 GB | Hafif, dusuk gecikme, araclar aktif |
| **2** | 0.5-0.8 | Qwen 3.5 4B UD | 2.9 GB | Tam agentic dongu, dogrulama aktif |
| **3** | > 0.8 | Sovereign Gateway (Cloud) | — | Derin strateji, bulut; yerel yedek: Qwen 3.5 9B |

### 5.2 Gercek Zamanli Model Performansi

| Gorev | Model | Gecikme |
|-------|-------|---------|
| Basit Q&A | DeepScaler 1.5B | < 800ms ilk token |
| Kod uretimi | Qwen 3.5 4B UD | ~1.5s ilk token |
| Mantik denetimi | Phi-4 Mini UD | ~1.5s ilk token |
| Matematik (SymPy) | Deterministik | < 10ms |
| Semantik arama | Nomic MoE + Jina v3 | ~2.1s toplam |
| Sahne analizi | MiMo-VL-7B-RL | ~3s ilk token |
| Dokusan OCR | Qwen2-VL OCR 2B | ~1.5s |
| Arac secimi | FunctionGemma 270M | < 500ms |
| Yonlendirme | Granite 3-2B | < 400ms |

### 5.3 Embedding ve Yeniden Siralama

| Model | VRAM | Rol |
|-------|------|-----|
| **Nomic Embed v2 MoE Q8** | 0.5 GB | Axis 6 — Semantik bellek embeddingsi |
| **Nomic Embed v2 MoE Q16** | 1.0 GB | Yuksek kalite embedding (hassas mod) |
| **Jina Reranker v3** | 0.6 GB | Aramanin 2. asama iyilestirmesi |

**Matryoshka Kesimi**: Nomic MoE Q8/Q16 modelleri Matryoshka tanimli; 256 boyut kesimi ile tam vektore gerek kalmadan hizli benzerlik hesaplamasi yapilir.

### 5.4 Gorsel Pipeline

| Mod | Model | VRAM | Kullanim |
|-----|-------|------|---------|
| Varsayilan | Qwen2.5-VL 3B | 2.5 GB | Genel gorsel analiz |
| OCR | Qwen2-VL OCR 2B | 1.1 GB | Dokusan metin cikartma |
| Amiral | MiMo-VL-7B-RL | 5.7 GB | Derin sahne analizi, kod diyagrami, math |

---

## 6. VRAM Butce Yonetimi

### Donanim

| Bilesim | Ozellikleri |
|---------|------------|
| GPU | NVIDIA RTX 4070 Laptop 8 GB GDDR6 |
| CPU | Intel i7-13620H (6P + 4E cekirdek) |
| RAM | 32 GB DDR4 |
| Depolama | 2 TB Samsung Pro NVMe |

### VRAM Dagilimi

| Kullanim | GB |
|----------|----|
| Toplam GPU VRAM | 8.0 |
| Windows OS rezervasyonu | 1.0 |
| Her zaman yuklü (Nomic + Jina) | 1.1 |
| **LLM'ler icin kullanilabilir** | **5.9** |

### Calisma Modlari

| Mod | Aktif Modeller | VRAM | Kullanim |
|-----|--------------|------|---------|
| **Standart** | Qwen 3.5 4B UD + Phi-4 Mini (denetimde) | 2.9-5.7 GB | Normal agentic dongu |
| **Gorsel** | Qwen2.5-VL 3B veya MiMo-VL-7B | 2.5-5.7 GB | Gorsel analiz |
| **Hizli** | DeepScaler + Ministral + Granite | 5.0 GB | Hizli yanit |
| **Dogrulama** | Qwen 3.5 4B + Qwen 2.5 Coder 3B | 5.4 GB | Agir mantik/kod denetimi |
| **Bosta** | Nomic + Jina | 1.1 GB | Yalnizca arka plan aramalari |

### Morpheus VRAM Kurallari

- Esik altinda (< 2 GB): Zorla Tier 0
- Agir model gecisi (> 3 GB): `Morpheus.flush()` zorunlu
- OOM kurtarma: Otomatik TinyLlama 1.1B (0.7 GB) devralir
- Arka plan gorevleri: E-cekirdeklere (12-15) bagli (psutil)
- TTL: 120 saniye kullanilmayan modeller otomatik bosaltilir

---

## 7. LangGraph Islem Pipeline'i (11 Node)

`src/clotho/orchestrator.py` tarafindan yonetilen LangGraph durum makinesi:

```
[negotiate_node]          -> Hedef muzakeresi (DOD: Definition of Done)
    |
[vision_node]             -> VLM on-isleme (gorsel varsa)
    |
[anchor_inject_node]      -> Spatial codebase baglami enjeksiyonu (Axis 5)
    |
[draft_node / expert_draft_node] -> L1 Sophia taslak uretimi
    |
[verify_node]             -> GLiNER2 varlik kontrolu, Z3 mantik dogrulama
    |
[tool_exec_node]          -> Paralel arac yurumu (ToolBridge)
    |
[critique_node]           -> L3 Lachesis 8-sutunlu adverseryal degerlendirme
    |
    |-- confidence > 0.9  -> refine_node ATLANIYOR (token tasarrufu)
    |-- confidence <= 0.9 -> [refine_node] -> Hassas duzeltme
    |
[reflection_node]         -> Meta-analiz (Axis 8 yazma)
    |
    |-- 3+ basarisiz denetim -> [deadlock_resolver_node] -> Kisit gevsetme (Axis 10)
    |
[END]
```

### Esik Degerleri

| Kural | Deger |
|-------|-------|
| Maksimum arac yinelemesi | 2 |
| Maksimum dogrulama yeniden denemesi | 3 |
| Kirmizi Zon guvenilirlik esigi | < 0.4 |
| Hard sonlandirma esigi | < 0.2 |
| L0 yetki penceresi | 60 saniye |
| Adaptif taslak atlama esigi | confidence > 0.9 |
| Deadlock tetikleyici | > 80% kod benzerligi ile 3+ basarisiz denetim |

---

## 8. Arac Ekosistemi (103+ Arac, 6 MCP Sunucusu)

### 8.1 Dahili Araclar (ToolBridge)

| Kategori | Araclar |
|----------|---------|
| Dosya sistemi | `ls`, `write_file`, `replace_content` |
| Semantik | `semantic` (LanceDB hibrit arama) |
| Gorsel | `vision` (VLM dispatch) |
| Dogrulama | `verify` (4-motor zinciri) |
| Rapor | `report` (Axis 7 telemetri) |
| VRAM | `vram` (Morpheus flush/durum) |
| Kod calistirma | `run_code` (LightSandbox) |

### 8.2 MCP Sunuculari

| Sunucu | Arac Sayisi | Kullanim |
|--------|------------|---------|
| **SLM** | 34 | SuperLocalMemory: semantik bellek, skill, mesh |
| **Sequential Thinking** | 1 | Yapili cok adimli zincir dusunce |
| **Fetch** | 1 | Statik web sayfasi getirme (markdown) |
| **KG-Mem** | 9 | Kaliici varlik-iliski grafigi |
| **GitHub** | 26 | GitHub API (depo, PR, issue, arama) |
| **Playwright** | 33 | Tarayici otomasyonu (gezinme, etkilesim, kodgen) |

### 8.3 Arac Secim Onceligi

| Amac | Oncelik Sirasi |
|------|----------------|
| Web icerik | webfetch (statik) > fetch MCP (okunabilirlik) > playwright (SPA/dinamik) |
| Mantik zinciri | Dahili CoT (basit) < sequentialthinking MCP (karmasik/dallanan) |
| Varlik grafigi | mcp_slm_recall (semantik) > kg-mem (yapisal) > semantic_store |
| Surum kontrolu | Yerel git > GitHub MCP (uzak depo) |
| Tarayici testi | Playwright MCP (E2E) |

---

## 9. Sovereign Gateway Mimarisi

Tum bulut trafigi tek bir egemen proxy katmanindan gec,er — veri sizintisi ve cok-istemci uyumsuzlugu engellenir.

```
Sophia / Pydantic AI
    |
    v
GatewayArchitrave (gateway_client.py)
    |-- SovereignProvider -> genai.Client -> localhost:32553
    |       |
    |       +-- Circuit Breaker (60s cooldown, jitter: 0.5-2.0s)
    |               |-- Acik -> Antigravity IDE Proxy -> Cloud
    |               +-- Kapali -> Yerel Fallback (Ollama :11434)
    |
    +-- generate_async() -> AriadneAsyncGateway (ariadne.py)
    +-- generate() -> NomosSyncGateway (nomos.py)
    +-- Circuit Breaker -> CircuitBreaker (kratos.py)
```

**Temel Tasarim Kararlari:**
- Pydantic AI, standart bir Google modeli kullandigini zanneder; tum trafik localhost:32553'ten gec,er.
- Hem sync hem async yollar ayni `genai.Client` ornegini kullanir (20-30 yinelemeden sonra baglam uyumsuzlugunu onler).
- `GEMINI_API_KEY` -> `GATEWAY_API_KEY` olarak geriye donuk eslestirilir.
- `api_key = "antigravity-native"` — IDE yonlendirmesi icin sahte anahtar.

---

## 10. Sovereign Shield (Butunluk Katmani)

| Bilesim | Dosya | Islevselligi |
|---------|-------|-------------|
| Snapshot Guardian | `src/lachesis/snapshot_manager.py` | 120 kritik dosyanin 30s'de bir SHA-256 anlık goruntusü |
| File Watchdog | `src/lachesis/file_watchdog.py` | OS-seviyesinde dosya butunluk izleme, atomik geri alma |
| L0 Auth Token | `scripts/create_l0_token.py` | 60 saniye TTL yetki penceresi, yazma islemlerini kilitler |
| L3 OutputGuard | `src/lachesis/verifiers/output_guard.py` | Tum ciktilar uzerinde kural uygulama |

### L0 Yetki Protokolu

Her yazma veya sistem degisikligi oncesinde:
```
python scripts/create_l0_token.py
```
Token uretilir -> 60 saniyelik pencere baslar -> islem yapilir -> pencere kapanir.

### Egemen Silme Kapisi (SOVEREIGN_DELETION_GATE)

Hicbir dosya silinmeden once:
1. `.antigravity/backup/` dizininde dogrulanmis kopya olmali
2. Bagimlilik analizi tamamlanmali
3. Kurtarma plani hazirlanmali
4. Yapisal etki raporu L0'a sunulmali

---

## 11. Resmi Dogrulama Pipeline'i (4 Motor)

`src/lachesis/verifiers/` ile her mantik-kritik veya matematiksel degisiklik icin tetiklenir:

```
[1] AST Analizi     -> Sozdizimi ve kapsam dogrulama
    |
[2] QWED           -> Kod-mantik tutarliligi (Qwen 2.5 Coder 3B)
    |
[3] SymPy          -> Sembolik matematik dogrulama
    |
[4] Z3 SAT         -> Formel mantik ve kisit cozumu (5000ms timeout)
```

Ek dogrulama: `python scripts/sovereign_audit.py` ile tam 4-asama zincir tetiklenir.

---

## 12. Codebase Haritasi (Axis 5 — Uzamsal Hafiza)

`src/lachesis/mapper/` — AST tabanlı bagimlilik grafigi yoneticisi:

- **266 modul** taranmis ve indekslenmis
- **10 dairesel bagimlilik** tespit edilmis (mevcut, izleniyor)
- **0 katman ihlali** (L1->L2->L3 mimarisi saglam)
- `scripts/update_mapper.py` ile artimli yeniden haritalama
- `spatial.db` uzerinde SQL LIKE ile anahtar kelime sorgusu
- Debounced async yeniden haritalama: 3 yazma -> 1 yeniden haritalama (iptal mekanizmasi)

---

## 13. CLI ve IDE Entegrasyonu

### Antigravity IDE
- Port: `localhost:32553`
- Sistem buradan baslatilir; tum Sovereign Gateway trafigi bu uzerinden akar.

### OpenCode CLI
```bash
python scripts/hermes_cli.py
```
- Capraz-oturum koprusu (Axis 13)
- Claude ve DeepSeek API uzerinden entegre CLI
- `opencode.db` araciligi ile Mnemosyne'ye yazar

### Diger Kritik Scriptler

| Script | Amac |
|--------|------|
| `scripts/create_l0_token.py` | L0 yetki tokeni olustur (yazma oncesi zorunlu) |
| `scripts/health_check_14_axes.py` | 14 eksen butunluk kontrolu |
| `scripts/morpheus_flush.py` | VRAM bosaltma (agir model gecisi oncesi) |
| `scripts/seed_14_axes.py` | Temiz kurulumda 14-eksen tohumlamasi |
| `scripts/seed_semantic.py` | Semantik bellek tohumlamasi |
| `scripts/sovereign_audit.py` | 4-asama formel dogrulama zinciri |
| `run_morpheus.bat` | Morpheus daemon baslatma (PowerShell, PID yakalama) |

---

## 14. Veri Depolama

| Depo | Yol | Icerik |
|------|-----|--------|
| `mnemosyne.db` | `data/mnemosyne.db` | 14 eksen SQLite (Axis 1-5, 7-11, 13-14) |
| `spatial.db` | `data/spatial.db` | Codebase bagimlilik grafigi (Axis 5) |
| `reliability.db` | `data/reliability.db` | Ajan guvenilirlik metrikleri |
| `opencode.db` | `data/opencode.db` | OpenCode CLI capraz-oturum |
| `lancedb/` | `data/lancedb/` | Vektör ve zamansal depolar (Axis 6) |
| `langgraph_checkpoints.sqlite` | `data/` | LangGraph AsyncSqliteSaver kontrol noktalari |
| `snapshots.db` | `data/snapshots.db` | Sovereign Shield SHA-256 anlık goruntuleri |

**Notlar:**
- Tum `data/` dizini `.gitignore`'da; yerel sifirdan tohumlanmali.
- Alembic migrasyonu aktif: `alembic upgrade head` ile schema guncellenir.
- WAL modu: SQLite esles,meli okuma/yazma destekler.
- Periyodik yedekleme (12 saatte bir): `cognition/morpheus/sweeper.py` — son 5 dongu saklanir.

---

## 15. Skill Ekosistemi (51 Skill)

`agent/skills/` altinda YAML frontmatter ile taninmis: her skill bir `model_role` alani icerir, `skill_loader.match_for_task()` ile gorev eslestirilir.

### Onemli Skill Kategorileri

| Kategori | Ornekler |
|----------|---------|
| Orkestrasyon | agent-orchestrator, sprint-contract, autoplan |
| Kod Uretimi | code-generation, local-runtime |
| Guvenlik | security-audit, security-first-guardian, sovereign-gateway, sovereign-shield |
| Hafiza | mnemosyne-high-fidelity-query, mnemosyne-write-path, 14-axis-memory |
| MCP/Arac | mcp-orchestration, hermes-bridge, discovery-mcp-scanner |
| Gorsel | (visual pipeline entegrasyonu) |
| Kullanici Analizi | socratic-analyst, persona-auditor, persona-runner |
| Optimizasyon | resource-scheduling, ruflow-tier-routing, model-lifecycle, prompt-compression |
| Kalite | autonomous-qa-evals, context-slicing, error-self-recovery |

---

## 16. Yonetisim Kurallari (Ozet)

Tam liste: `.antigravity/rules.json` ve `.antigravity/CONSTITUTION.md`

| Kural | Onem | Icerik |
|-------|------|--------|
| **BA-01** | YUKSEK | Dil: Kod/log = Ingilizce (ASCII). Chat/plan/dokuman = Turkce |
| **EMOJI_BAN** | KRITIK | Emoji yasak, tum ciktilarda |
| **L0_AUTH_PROTOCOL** | KRITIK | Her yazma oncesi `create_l0_token.py` (60s) |
| **BACKUP_BEFORE_DELETE** | KRITIK | `.antigravity/backup/` zorunlu |
| **BACKUP_BEFORE_WRITE** | YUKSEK | Atomik oncesi yedekleme |
| **SOVEREIGN_DELETION_GATE** | KRITIK | Silme icin Silme Justifikasyon Raporu |
| **VENV_ISOLATION** | KRITIK | Tum islemler `.venv` icerisinde |
| **PRIME_DIRECTIVE** | KRITIK | Sistem butunlugu ve hafiza kaliciligi her seyden once |
| **LACONISM_MANDATE** | YUKSEK | Gereksiz cikti yok; < 4 satir (teknik gereksinim olmadikca) |
| **3-STRIKE** | KRITIK | Hata > 80% kod benzerligiyle 3. kez tekrararsa dur, post-mortem yaz |

---

## 17. Baslatma Sirasi

```bash
# 1. Bagimliliklari yukle
pip install -r requirements.txt
pip install -e ".[dev]"

# 2. Veritabanlarini baslat
alembic upgrade head
python scripts/seed_14_axes.py
python scripts/seed_semantic.py

# 3. Saglik kontrolu
python scripts/health_check_14_axes.py

# 4. Morpheus daemon baslatma
run_morpheus.bat

# 5. L0 yetki tokeni (yazma oncesi)
python scripts/create_l0_token.py

# 6. Sistem giris noktasi
python scripts/hermes_cli.py

# Veya dogrudan kontrol devri
python src/clotho/control_handoff.py
```

---

## 18. Test ve Dogrulama

```bash
# Tum testler
PYTHONPATH=. pytest tests/ -v

# Smoke testleri
PYTHONPATH=. pytest tests/ -m smoke -v

# 14 eksen butunluk
python scripts/health_check_14_axes.py

# Formel dogrulama
python scripts/sovereign_audit.py

# Lint
ruff check .
ruff format .

# Tip kontrolu (pyright — mypy degil)
pyright src/
```

**Mevcut Durum (v1.1.27):**
- 26/28 test gecti (2 onceden beri atlanan)
- 266 modul, 0 katman ihlali
- SLM MCP: 33 arac + 5 sunucu = 104 toplam MCP araci aktif
- Dil ihlali: 0 (BA-01 uyumlu)

---

## 19. Bilinen Kisitlamalar

| Kisit | Ayrintilar |
|-------|-----------|
| VRAM | Max 7.0 GB kullanilabilir; ayni anda 2 agir model (> 3 GB) yukleme yasak |
| CUDA MPS | Windows'ta sinirli destek; 2 modelin ayni anda GPU'da calistirilan arastirmasi K5.1'de |
| MiMo-VL-7B-RL | VRAM yuksekliginden dolayi standby'da; yalnizca talep uzerine |
| semantic_relations | gliner2 bagimliliginin eksikligi nedeniyle 0 satir (K0.1 onarim bekliyor) |
| Test kapsamasi | Mevcut ~ %10-15 (hedef: v1.1.0'da %65) |
| Alembic | Kuruldu ve aktif; ilk migrasyonlar test edilmis |

---

## 20. Baglanti Haritasi

```
[L0 Kullanicisi]
    |
    +-- Antigravity IDE  ->  http://localhost:32553 (Sovereign Gateway)
    |                                |
    |                                +-> Cloud Provider (deep reasoning)
    |                                +-> http://localhost:11434 (Ollama)
    |                                        |
    |                                        +-> RTX 4070 8GB VRAM
    |                                        +-> D:\Google\AntiGravity\... (GGUF)
    |
    +-- OpenCode CLI  ->  Hermes CLI  ->  data/opencode.db  (Axis 13)
    |
    +-- MCP Sunuculari (6 adet):
            slm.exe MCP (SLM)
            npx sequential-thinking MCP
            python fetch MCP
            npm kg-mem MCP
            npm github MCP
            npm playwright MCP
```

---

*Son Guncelleme: 2026-05-27 | Sistem Surumu: v1.1.27*
*Durum: STABLE | 104 MCP araci | 46 model | 266 modul | 0 katman ihlali*
*Imza: Phantom Logos Sovereign Audit System*
