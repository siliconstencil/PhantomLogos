# Yol Temizliği ve Güvenlik Denetim Test Planı

Bu doküman, kod tabanındaki hardcoded yolların temizlendiğini, platform-agnostik yol doğrulama mekanizmalarını ve SQL injection / path traversal korumalarını doğrulamak amacıyla hazırlanmıştır. [2:45 PM PT]

## 1. Test Senaryoları

### Senaryo A: Hardcoded Yol Denetimi (Path Audit)
- **Adımlar:**
  1. Proje ana dizininde aşağıdaki PowerShell komutlarını çalıştırarak hardcoded yolların kalıp kalmadığını denetleyin:
     `Get-ChildItem -Path src/, scripts/ -Recurse -Include *.py | Select-String -Pattern "D:\\Hank"`
     `Get-ChildItem -Path src/, scripts/ -Recurse -Include *.py | Select-String -Pattern "C:\\Users\\Hakan"`
- **Beklenen Sonuç:** Her iki komutun da sıfır (0) sonuç dönmesi gerekmektedir.

### Senaryo B: Path Traversal Koruması
- **Adımlar:**
  1. `ls` veya dosya okuma araçları üzerinden proje kök dizininin dışındaki bir yola (örneğin `../../Windows/` veya `/etc/`) erişmeye çalışın.
- **Beklenen Sonuç:** Sistem `os.path.commonpath` veya benzeri korumalarla erişimi engelleyerek "Unsafe path detected" veya "Access denied" hatası fırlatmalıdır.
