# Antigravity Sistem Tarama ve Aksiyon Raporu

Raporlama Zamani: [03:05 PM PT]

## 1. Giris ve Baglam
Bu rapor, Windows Pro isletim sistemi uzerinde calisan Antigravity (Windsurf IDE / Go / Python) altyapisinin yasadigi terminal donmalari, veritabanı kilitlenmeleri (deadlock) ve arka plan daemon (Morpheus / Watchdog) yonetim sorunlarini gidermek amaciyla yapilan tarama sonuclarini icerir. Rapor, diger ajanlarin sistemi otomatik olarak onarabilmesi icin net kod degisiklik talimatlari sunar.

---

## 2. Tarama Bulgulari ve Kritik Risk Analizi

### A. ConPTY Devre Disi Kalmasi ve Terminal Kilitlenmeleri
*   **Dosya**: `.vscode/settings.json`
*   **Sorun**: `"terminal.integrated.windowsEnableConpty": false` yapilandirmasi bulunmaktadir.
*   **Neden Kilitleniyor**: ConPTY devre disi kaldiginda VS Code, eski winpty screen scraping yontemini kullanir. Python ve Go betiklerinin yogun terminal ciktisi urettigi senaryolarda winpty arabellegi dolar ve terminal tamamen donar (terminal lockup).

### B. SQLite3 Eşzamanlılık (Concurrency) ve Deadlock Riski
*   **Dosyalar**:
    *   `cognition/mnemosyne/reflection_store.py`
    *   `src/architrave/context_cache.py`
    *   `src/architrave/opencode_store.py`
    *   `src/lachesis/snapshot_manager.py`
    *   `src/clotho/orchestrator.py`
*   **Sorun**: sqlite3 baglantilari timeout parametresi olmadan (varsayilan 5sn) veya WAL moduna alinmadan kurulmaktadir.
*   **Neden Kilitleniyor**: Ayni anda Morpheus, Watchdog ve aktif ajan veritabanina yazma istegi gonderdiginde SQLite anlik kilitlenmeye duser ve `database is locked` hatasiyla surecleri askida birakir.

### C. Sandbox WerFault ve DLL Yukleme Engelleri
*   **Dosya**: `src/utils/sandbox.py`
*   **Sorun**: `LightSandbox._strip_env()` metodu, `SystemDrive` ve `PATHEXT` ortam degiskenlerini silmektedir.
*   **Neden Kilitleniyor**: Windows altinda Python, gerekli DLL dosyalarini yuklemek icin bu degiskenleri arar. Bunlar bulunamadiginda isletim sistemi arka planda gorunmez bir hata raporlama penceresi (`WerFault.exe`) acar ve kullanici etkileşimi bekler. Arka planda donan bu surec, sandbox thread'ini sonsuza kadar bloke eder.

### D. Taskkill CMDLINE Uyumsuzlugu ve Zombie Surecler
*   **Dosyalar**: `stop_morpheus.bat`, `stop_watchdog_daemon.bat`
*   **Sorun**: `taskkill /FI "CMDLINE eq ..."` filtresi Windows Home ve bazi Pro surumlerinde desteklenmemektedir.
*   **Neden Kilitleniyor**: Filtre calismadiginda arka plandaki `pythonw.exe` surecleri kapatilamaz. Ajan her calistiginda arka planda zombi surecler biririk, RAM ve dosya kilitlenme riskleri katlanarak artar.

### E. Morpheus Embedding Yukleme Hatasi
*   **Dosya**: `cognition/morpheus/loader.py`
*   **Sorun**: `nomic-embed-text-v2-moe-q8:latest` embedding modeli yuklenmeye calisilirken `client.chat` metodu cagirilarak model sorgulanmakta ve `ResponseError: ... does not support chat (status code: 400)` hatasi alinmaktadir.
*   **Neden Kilitleniyor**: Embedding modelleri chat isteklerini desteklemez. Loader bu model icin chat yerine `client.embeddings` cagirmalidir.

### F. IDE Eklentileri ve Yapilandirma Hatalari
*   **Kurulum Yolu**: `D:\Google\Antigravity IDE`
*   **Sorunlar**:
    1.  **Mac'e Ozel Komut Hatasi**: Windows uzerinde `workbench.action.installCommandLine` cagrisi yapilmaya calisilmakta ve komut bulunamadi hatasi uretmektedir.
    2.  **Antigravity Eklenti Komutlari**: Menulerde referans verilen bazi `antigravity.*` komutlari eklentinin `package.json` dosyasinda tanimlanmamistir.
    3.  **Python Eklentileri Yetki Hatalari (Proposed API)**: Python eklentilerinin ihtiyac duydugu API yetkileri `product.json` icinde eksiktir.
    4.  **Git Eklentisi Baslik Hatasi**: Git eklentisindeki Antigravity komutlarinin `title` alani eksiktir.
    5.  **Eksik Yukleme Gorseli**: Arayuzde `loading_dark.svg` dosyasi bulunamadigi icin 404 hatasi olusmaktadir.
    6.  **Python Ortami API Uyumsuzlugu**: `ms-python.vscode-python-envs` eklentisi `product.json` üzerinde `terminalShellIntegration` izni yerine `terminalShellEnv` iznine ihtiyac duymaktadir.
    7.  **Yerel HTTPS Sertifika Hatasi**: Ajan ile IDE/Gateway arasindaki yerel asenkron baglantilarda self-signed (kendinden imzali) sertifikalar yuzunden `ERR_CERT_AUTHORITY_INVALID` hatasi olusmakta ve iletisim kesilmektedir.
*   **Neden Kilitleniyor / Hata Veriyor**: IDE bu entegrasyon hatalari yuzunden konsolda surekli hata kayitlari uretir, thread'leri mesgul eder ve arayuz donmalarina yol acar.

---

## 3. Kod Duzeltme ve Aksiyon Talimatlari

Diger calisacak ajanlar, asagidaki adimlari birebir takip ederek altyapiyi onarmalidir:

### 3.1. ConPTY Yapilandirmasinin Duzeltilmesi
`.vscode/settings.json` dosyasindaki ilgili satiri bulun ve asagidaki sekilde guncelleyin ya da terminal GPU hizlandirmasini kapatin:
```json
{
  "terminal.integrated.windowsEnableConpty": true,
  "terminal.integrated.gpuAcceleration": "off"
}
```

### 3.2. SQLite Baglantilarinin Sertlestirilmesi (Hardening)
1.  `reflection_store.py`, `context_cache.py`, `opencode_store.py` ve `snapshot_manager.py` dosyalarindaki `sqlite3.connect` cagrilarini asagidaki yardimci fonksiyon uzerinden yapacak sekilde degistirin:
    ```python
    def _get_secure_connection(db_path: str) -> sqlite3.Connection:
        import sqlite3
        conn = sqlite3.connect(db_path, timeout=30)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout = 30000;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        return conn
    ```
2.  `src/clotho/orchestrator.py` dosyasindaki checkpointer baglantisini guncelleyin:
    ```python
    conn = sqlite3.connect(db_path, timeout=30, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    ```
3.  `cognition/mnemosyne/` altindaki tum SQLAlchemy tabanli store modullerinde `create_engine` fonksiyonuna `connect_args={"timeout": 30}` ekleyin ve hepsine connect event listener pragma ayarlarini entegre edin.

### 3.3. Sandbox Ortam Degiskenlerinin Whitelist'e Alinmasi
`src/utils/sandbox.py` icindeki `LightSandbox._strip_env()` metodunda yer alan `keep_vars` listesini asagidaki gibi guncelleyin:
```python
keep_vars = ["SYSTEMROOT", "TEMP", "TMP", "USERNAME", "COMPUTERNAME", "SystemDrive", "PATHEXT"]
```

### 3.4. PID-Tabanli Surec Yonetimi
Arka plan daemon baslatilirken olusan PID'leri `data/morpheus.pid` ve `data/watchdog.pid` dosyalarina kaydedin. `stop_morpheus.bat` ve `stop_watchdog_daemon.bat` betiklerini, bu dosyalardan PID okuyarak `taskkill /F /PID <pid>` seklinde calisacak sekilde guncelleyin.

### 3.5. Morpheus Embedding Yukleme Hatasinin Giderilmesi
`cognition/morpheus/loader.py` dosyasinda, modelin embedding modeli olup olmadigini dogrulayan `_is_embedding_model` kontrolunun tum model yukleme/bosaltma noktalarinda (ozellikle VRAM bosaltma ve baslangic yukleme asamalarinda) calistigindan emin olun. Embedding modelleri icin `client.chat` cagrisi yapilmasini kesinlikle engelleyin ve dogrudan `client.embeddings` cagrisini aktif tutun.

### 3.6. IDE Eklentileri ve Yapilandirma Duzeltmelerinin Uygulanmasi
IDE kurulum yolu `D:\Google\Antigravity IDE` olarak kabul edilerek su adimlar uygulanmalidir:
1.  **Mac Komut Yamasi**: `resources/app/out/vs/workbench/workbench.desktop.main.js` icindeki `_installAntigravityInPath()` metodu yamanarak Windows'ta calismasi engellenmelidir (yalnizca `darwin` kontrolu eklenmeli).
2.  **package.json Yamasi**: `resources/app/extensions/antigravity/package.json` dosyasina `antigravity.importAntigravitySettings`, `antigravity.importAntigravityExtensions` ve `antigravity.prioritized.chat.open` komutlari eklenmelidir.
3.  **product.json Proposed API Yetkileri**: `resources/app/product.json` icindeki `extensionAllowedProposedApi` altina `ms-python.python` ve `ms-python.vscode-python-envs` eklentileri icin gerekli API yetkileri eklenmelidir. `ms-python.vscode-python-envs` icin `terminalShellIntegration` yerine tam adiyla `terminalShellEnv` yetkisinin tanimlandigindan emin olunmalidir.
4.  **Git package.json Basliklari**: `resources/app/extensions/git/package.json` icindeki `git.antigravityCloneNonInteractive` ve `git.antigravityGetRemoteUrl` komutlarina gecerli `title` alanlari atanmalidir.
5.  **loading_dark.svg Kopyalama**: `resources/app/extensions/media-preview/media/loading*.svg` dosyalari `resources/app/out/vs/workbench/` altina `loading_dark.svg` ve `loading_hc.svg` olarak kopyalanmalidir.
6.  **Yerel HTTPS Sertifika Yamasi**: `resources/app/out/main.js` dosyasi yamanarak, sadece yerel makinedeki (`127.0.0.1` veya `localhost`) HTTPS cagrilarinda self-signed (kendinden imzali) sertifika hata kontrollerinin (`ERR_CERT_AUTHORITY_INVALID`) bypass edilmesi (ignore edilmesi) saglanmalidir.
    *(Not: Bu islemler icin `<PROJECT_ROOT>\scratch\update_package_json.py` ve `update_git_package_json.py` betiklerindeki yollar `D:\Google\Antigravity IDE` dizinine gore revize edilerek calistirilmalidir).*
