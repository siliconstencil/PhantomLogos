# Python Mimari ve Kilitlenme (Deadlock) Analiz Raporu

Denetim Zamani: [02:11 PM PT]

## 1. Giris ve Python Ortami Analizi
Windows Pro sistemi üzerinde yürütülen `D:\Hank\.venv` sanal ortamındaki Python yapısı incelenmiştir. Kurulu olan kritik kütüphaneler (ör. `superlocalmemory`, `mcp`, `sqlite-vec`, `z3-solver`, `sympy`, `pywin32`, `psutil`) analiz edilmiş ve Python süreçlerinin Windows altında deadlock tetikleme mekanizmaları çıkarılmıştır.

---

## 2. Python Sureclerinde Kilitlenme (Deadlock) Senaryolari

### A. SQLite3 Veritabanı Yazma Çakışmaları ve GIL (Global Interpreter Lock)
*   **Sorun**: Sistemde üç farklı Python süreci (Morpheus Daemon, `agy.exe` Go aracı üzerinden çağrılan CLI betikleri ve aktif Ajan oturumu) aynı anda `data/mnemosyne.db` veritabanına yazma yapmaktadır.
*   **Deadlock Tetikleyicisi**: SQLite varsayılan olarak aynı anda sadece tek bir yazıcıya izin verir. Python'ın varsayılan SQLite bağlantısı `busy_timeout` süresince bekler. Ancak bir süreç `BEGIN DEFERRED` ile işlem başlatıp okuma kilidini yazma kilidine yükseltmeye çalışırken diğeri de aynı yükseltmeyi bekliyorsa, iki süreç birbirini kilitler (SQLite Lockup). Python GIL serbest bırakılsa bile işletim sistemi düzeyindeki dosya kilitleri çözülmez.

### B. WerFault.exe ve Görünmez Hata Penceresi Blokajı (Sandbox Süreçleri)
*   **Sorun**: `LightSandbox` içindeki kod çalıştırılırken ortam değişkenleri (`env`) agresif bir şekilde temizlenmektedir (`self._strip_env()`).
*   **Deadlock Tetikleyicisi**: Python yorumlayıcısı gerekli Windows sistem DLL'lerini veya `SystemDrive` değişkenini bulamadığında başlangıçta çöker. Windows Pro varsayılan olarak arka planda görünmez bir Hata Raporlama penceresi (`WerFault.exe`) açar. Bu pencere kullanıcı etkileşimi (Kapat düğmesine basılması) bekler. Süreç arka planda olduğu için pencere görünmez ve süreç 10 saniyelik timeout süresi dolana kadar askıda kalır. Bu durum, aracı çalıştıran thread pool işçisini kilitler.

### C. ProactorEventLoop ve Kapanmayan Subprocess Kanalları (IOCP)
*   **Sorun**: Windows'ta asenkron süreç yönetimi için `asyncio.ProactorEventLoop` (Giriş/Çıkış Tamamlama Portları - IOCP) kullanılmaktadır.
*   **Deadlock Tetikleyicisi**: Bir alt süreç (subprocess) zorla kapatıldığında veya zaman aşımına uğradığında, boru hatları (stdout/stderr) tamamen boşaltılmadan event loop sonlandırılırsa Windows handle'ları açık kalır. Proactor loop, bu handle'ları kapatmak için kilitlenir ve CPU kullanımını %100'e çıkararak IDE/süreç kilitlenmesine sebep olur.

### D. Thread Pool Tüketimi (asyncio.to_thread)
*   **Sorun**: `ToolBridge` dosya yazma (`_write_file`), değiştirme (`_replace_content`) ve doğrulama gibi tüm senkron işlemleri `asyncio.to_thread` ile arka plana atar.
*   **Deadlock Tetikleyicisi**: Eşzamanlı yoğun istek geldiğinde Python'ın varsayılan thread havuzu (maksimum iş parçacığı sınırı) tükenir. Havuzdaki tüm iş parçacıkları bloke olan veritabanı veya ağ işlemleriyle dolduğunda, yeni gelen tüm asenkron görevler askıda kalır ve tüm ajan döngüsü donar.

---

## 3. Cozum Onerileri ve Aksiyon Adimlari

1.  **SQLite busy_timeout ve WAL Ayarı**:
    *   Tüm SQLite bağlantı başlatma noktalarına (`mnemosyne.db`) `busy_timeout` değeri 10000ms (10 saniye) olarak set edilmeli ve `PRAGMA journal_mode=WAL;` aktif edilmelidir:
        ```python
        conn.execute("PRAGMA busy_timeout = 10000;")
        conn.execute("PRAGMA journal_mode = WAL;")
        ```
2.  **WerFault Engelleme (Windows Registry / Process Creation Flags)**:
    *   Süreçlerin hata pencerelerine takılmasını engellemek için `LightSandbox` alt süreç başlatma bayraklarına `SEM_NOGPFAULTERRORBOX` (0x0002) eklenmeli veya Windows Registry üzerinden `DontShowUI = 1` yapılandırılmalıdır.
3.  **Sandbox Ortamında Temel Sistem Değişkenlerinin Korunması**:
    *   `LightSandbox._strip_env()` metodunda, Python'ın Windows üzerinde kararlı DLL çözümlemesi yapabilmesi için `SystemDrive` ve `PATHEXT` değişkenleri whiteliste eklenmelidir:
        ```python
        keep_vars = ["SYSTEMROOT", "TEMP", "TMP", "USERNAME", "COMPUTERNAME", "SystemDrive", "PATHEXT"]
        ```
4.  **Asenkron Alt Süreç Kullanımı**:
    *   Senkron `subprocess.run` komutlarını thread pool içinde çalıştırmak yerine, doğrudan `asyncio.create_subprocess_exec` kullanılarak event loop'un blokajsız çalışması sağlanmalıdır.
