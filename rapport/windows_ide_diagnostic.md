# Windsurf & Windows Powershell Haberlesme Tehdit ve Analiz Raporu

Denetim Zamani: [02:08 PM PT]

## 1. Giris ve Baglam
VS Code çatalları (ag Windsurf) ve Go tabanlı ajan yöneticisi (agy/ag2) Windows işletim sistemi üzerinde çalışırken `run_command` veya Python betikleri yürütülmesi esnasında terminalin ve IDE'nin tamamen kilitlendiği (freeze/lockup) bildirilmiştir. Bu rapor, sistemde bu kilitlenmeyi tetikleyebilecek olası yapılandırma hatalarını ve Windows-Powershell iletişimindeki darboğazları analiz eder.

---

## 2. Tespit Edilen Kritik Bulgular ve Tetikleyiciler

### A. ConPTY Devre Disi Birakilmasi (En Kritik Hata)
*   **Bulgu**: `.vscode/settings.json` dosyasında `"terminal.integrated.windowsEnableConpty": false` yapılandırması tespit edilmiştir.
*   **Açıklama**: ConPTY (Windows Pseudo Console), Windows'un modern terminal akış arabirimidir. Bu ayar `false` yapıldığında, IDE terminal yönetimi için eski ve kararsız olan `winpty` katmanına geri döner.
*   **Etki**: `winpty`, terminal ekranını tarayarak (screen scraping) çalışır. Go/Python gibi çok iş parçacıklı ve yüksek çıktılı araçlar çalıştırıldığında arabellek aşımı ve eşzamanlı yazma çakışmaları yaratarak terminal akışını kilitler (deadlock).

### B. Taskkill CMDLINE Filtresi Uyumsuzlugu (Windows Home)
*   **Bulgu**: `stop_morpheus.bat` and `stop_watchdog_daemon.bat` dosyalarında `taskkill /FI "CMDLINE eq *..."` filtresi kullanılmaktadır.
*   **Açıklama**: Windows Home sürümlerinde `taskkill` aracı `CMDLINE` filtreleme özelliğini desteklemez.
*   **Etki**: Komut çalıştırıldığında `Filtre tanınamadı` hatası döner ve arka plandaki `pythonw.exe` (bootstrap/morpheus daemon) süreçleri kapatılamaz. Bu durum, arka planda birden fazla hayalet (zombie) sürecin birikmesine ve kilitlenmelere yol açar.

### C. PowerShell Hata Akisi (Stderr) Yonlendirme Davranisi
*   **Bulgu**: PowerShell, arka planda çalıştırılan Python betiklerinin standart hata akışına (stderr) yazdığı uyarıları (örneğin deprecation/FutureWarning) doğrudan birer hata nesnesi (NativeCommandError / RemoteException) olarak yorumlar.
*   **Etki**: Terminal sarıcıları bu hata akışını senkron olarak bekliyorsa veya akış yönetimi doğru izole edilmemişse, PowerShell akışı durdurur ve terminalin yanıt vermesini engeller.

### D. Arabellek (Pipe Buffer) Dolmasi
*   **Açıklama**: Windows sistemlerinde boru hattı (pipe) varsayılan arabellek boyutu oldukça küçükür (4KB - 8KB).
*   **Etki**: Eğer arka planda çalışan süreç (Go agent manager veya Python betiği) standart çıktıya hızlı ve büyük miktarda veri yazıyorsa ve ana süreç bu çıktıyı asenkron olarak tüketmiyorsa, boru hattı dolar. Çocuk süreç `write()` çağrısında sonsuza kadar bloke olur (pipe deadlock).

### E. Etkinlestirme Betigi ve Execution Policy Engelleri
*   **Açıklama**: Windows üzerinde default execution policy `Restricted` olarak ayarlanmıştır.
*   **Etki**: Ajan veya terminal, sanal ortamı (`Activate.ps1`) çalıştırmayı denediğinde, sistem arka planda kullanıcıdan onay isteyen ("Bu betiği çalıştırmak istiyor musunuz? [Y/N]") interaktif bir prompt tetikler. Terminal arka planda (non-interactive) çalıştığı için bu prompt hiçbir zaman yanıtlanamaz ve süreç kilitli kalır.

---

## 3. Cozum Onerileri ve Aksiyon Adimlari

1.  **ConPTY Ayarinin Duzeltilmesi**:
    *   `.vscode/settings.json` içindeki `"terminal.integrated.windowsEnableConpty": false` satırını silin veya `true` yapın.
2.  **GPU Hızlandırmasının Kapatılması (Rendering Kilitlenmeleri İçin)**:
    *   Terminal görsel donmalarını engellemek için settings.json içine şu satırı ekleyin:
        `"terminal.integrated.gpuAcceleration": "off"`
3.  **Daemon Süreç Kapatma Mantığının Güvenli Hale Getirilmesi**:
    *   `taskkill` komutlarında `/FI "CMDLINE..."` filtresi yerine, Python tarafında süreçlerin PID'lerini `data/morpheus.pid` gibi dosyalara yazıp kapatırken bu PID'leri okuyarak doğrudan sonlandırmak (Windows Home uyumluluğu için).
4.  **PowerShell Çağrılarına Non-Interactive Parametresi Eklenmesi**:
    *   Komut satırı çağrılarına `-NonInteractive -ExecutionPolicy Bypass` parametreleri eklenerek güvenlik onay pencerelerinin oluşması engellenmelidir.
5.  **Boru Hattı Akışının Asenkron Tüketilmesi**:
    *   Go aracı (ag2) tarafında, komut çıktılarını (`StdoutPipe` ve `StderrPipe`) senkron beklemek yerine ayrı goroutine'ler vasıtasıyla dinamik olarak okumak.
