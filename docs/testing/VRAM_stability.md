# VRAM Kararlilik ve Model Gecis Test Planı

Bu doküman, Phantom Logos sisteminin 7.0 GB GPU VRAM limit korumasını, Morpheus daemon bellek temizleme mekanizmasını ve model geçişlerindeki kararlılığı test etmek amacıyla hazırlanmıştır. [2:45 PM PT]

## 1. Gerekli Donanım ve Ortam
- En az 6 GB VRAM destekli NVIDIA GPU.
- Morpheus daemon aktif olmalıdır (python src/clotho/bootstrap.py --daemon).
- .env dosyasında GPU_TOTAL_VRAM_GB=7.0 ayarlanmış olmalıdır.

## 2. Test Senaryoları

### Senaryo A: Morpheus Daemon Başlatma ve Sağlık Kontrolü
- **Adımlar:**
  1. `python src/clotho/bootstrap.py --daemon` komutunu çalıştırın.
  2. `logs/system/morpheus/morpheus.log` dosyasını inceleyerek daemon'ın başarıyla başladığını doğrulayın.
- **Beklenen Sonuç:** Log dosyasında "Morpheus Daemon started successfully" ve PID bilgisi yer almalıdır.

### Senaryo B: Model Geçişi VRAM Temizliği (Morpheus.flush)
- **Adımlar:**
  1. `scripts/baseline_benchmark.py` betiğini çalıştırın.
  2. Model geçişi sırasında (örneğin L2'den L3 modeline geçerken) Morpheus daemon loglarını izleyin.
- **Beklenen Sonuç:** Morpheus'un `Morpheus.flush()` metodunu tetiklediği, eski modelin VRAM'den temizlendiği ve yeni model için yer açıldığı loglarda görülmelidir. Toplam VRAM kullanımı hiçbir aşamada 7.0 GB'ı aşmamalıdır.
