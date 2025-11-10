# Jira Esintili Günlük İzleme Arayüzü

Bu proje, günlük log kayıtlarının Atlassian Jira takvim görünümüne benzer modern bir arayüzde tutulmasını ve canlı olarak izlenmesini sağlar. Kart tabanlı zaman çizelgesi ve tablo bileşenleri ile kayıtlar kolayca takip edilir. Kaydedilen tüm log girdileri tarih bazında `logs/` klasörü altında saklanır.

## Özellikler

- **Canlı günlük akışı:** Aynı gün için yapılan tüm girişler anında listeye eklenir.
- **Renkli durum seviyeleri:** Normal, uyarı ve kritik kayıtlar farklı Atlassian tonları ile vurgulanır.
- **Zaman çizelgesi:** Haftalık plan görünümünü anımsatan çizelgede log kartları saat aralıklarına yerleşir.
- **Geçmiş kayıtlar:** Tarih seçici üzerinden önceki günlerin log dosyalarını görüntüleme.
- **Otomatik dosya kaydı:** Her gün için ayrı `YYYY-MM-DD.jsonl` dosyaları oluşturulur.

## Gereksinimler

- Python 3.10 veya üzeri (Tkinter modülü varsayılan olarak gelir.)

## Çalıştırma

```bash
python app.py
```

Uygulama açıldıktan sonra sistem, durum ve mesaj alanlarını doldurup **Kaydı Ekle** butonuna tıklayarak log ekleyebilirsiniz. Kayıtlar `logs/` klasöründe tutulur ve tarih seçicisinden farklı günlere ait kayıtları görüntüleyebilirsiniz.
