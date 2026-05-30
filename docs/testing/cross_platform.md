# Platformlar Arası Uyum (Cross-Platform) Test Planı

Bu doküman, Phantom Logos sisteminin Windows dışındaki Unix-like (macOS, Linux vb.) işletim sistemlerinde sorunsuz çalışabilirliğini, sanal ortam bütünlüğünü ve dinamik yol çözümleme mekanizmalarını doğrulamak amacıyla hazırlanmıştır. [2:45 PM PT]

## 1. Sanal Ortam ve Bağımlılık Denetimi
- `pyproject.toml` içerisindeki tüm bağımlılıklar platformdan bağımsız olmalıdır.
- `keyring>=25.0.0` paketinin sanal ortama düzgünce yüklendiği ve import edilebildiği test edilmelidir.

## 2. Test Senaryoları

### Senaryo A: Akıllı MCP Yapılandırıcı (setup_mcp_config.py)
- **Adımlar:**
  1. `setup_mcp_config.py` betiğini çalıştırın.
  2. Üretilen `mcp_config.json` dosyasını açarak:
     - Windows'ta backslash (`\\`) ve `.venv\\Scripts\\python.exe` yollarının,
     - macOS/Linux'ta ise forward slash (`/`) ve `.venv/bin/python` yollarının kullanıldığını doğrulayın.
- **Beklenen Sonuç:** İşletim sistemine uygun formatta hatasız ve dinamik bir yapılandırma üretilmelidir.

### Senaryo B: Kabuk Betikleri (BAT ve SH Eşdeğerliği)
- **Adımlar:**
  1. Windows'ta `.bat` (örneğin `run_morpheus.bat`) ve `.vbs` betiklerinin,
  2. macOS/Linux'ta ise `.sh` (örneğin `run_morpheus.sh`) betiklerinin çalıştırılabilir izinleriyle birlikte (`chmod +x run_morpheus.sh`) sorunsuz başlatılabildiğini doğrulayın.
- **Beklenen Sonuç:** Her iki platformda da Morpheus arka plan daemon'ı başarıyla başlamalı ve log üretmelidir.
