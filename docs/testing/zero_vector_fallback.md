# Embedding Zero-Vector Fallback Test Planı

Bu doküman, K1.4 kapsamında Embedding oluşturulurken boş liste döndüğünde veya zero-vector oluştuğunda sistemin (matryoshka, theoria vb.) güvenli fallback durumuna geçerek çalışmaya devam ettiğini doğrulamak amacıyla hazırlanmıştır. [2:45 PM PT]

## 1. Test Senaryoları

### Senaryo A: SLM Client Boş Liste Fallback Testi
- **Adımlar:**
  1. `tests/test_zero_vector.py` içerisinde yer alan smoke testi çalıştırın:
     `D:\Hank\.venv\Scripts\pytest.exe tests/test_zero_vector.py -v`
  2. Testin SLMClient.embed() metodunu boş liste döndürecek şekilde mock'ladığını ve matryoshka/theoria bileşenlerinin hata fırlatmadan local fallback modeline geçtiğini doğrulayın.
- **Beklenen Sonuç:** Test başarıyla geçmeli ve fallback durumunun aktif olduğu loglarda görülmelidir.
