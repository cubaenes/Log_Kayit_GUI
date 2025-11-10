# Aviyonik Günlük İzleme Arayüzü

Bu proje, günlük log kayıtlarının modern ve dinamik bir arayüzde tutulmasını ve canlı olarak izlenmesini sağlar. Aviyonik sistemlerden ilham alan radar görünümü ve tematik renkler ile girişler kolayca takip edilir. Kaydedilen tüm log girdileri tarih bazında `logs/` klasörü altında saklanır.

## Özellikler

- **Canlı günlük akışı:** Aynı gün için yapılan tüm girişler anında listeye eklenir.
- **Renkli durum seviyeleri:** Normal, uyarı ve kritik kayıtlar farklı renklerde vurgulanır.
- **Aviyonik görselleştirme:** Radar taraması ve HUD çizimleri içeren animasyonlu panel.
- **Geçmiş kayıtlar:** Tarih seçici üzerinden önceki günlerin log dosyalarını görüntüleme.
- **Otomatik dosya kaydı:** Her gün için ayrı `YYYY-MM-DD.jsonl` dosyaları oluşturulur.

## Gereksinimler

- Python 3.10 veya üzeri (Tkinter modülü varsayılan olarak gelir.)

## Çalıştırma

```bash
python app.py
```

Uygulama açıldıktan sonra sistem, durum ve mesaj alanlarını doldurup **Kaydı Ekle** butonuna tıklayarak log ekleyebilirsiniz. Kayıtlar `logs/` klasöründe tutulur ve tarih seçicisinden farklı günlere ait kayıtları görüntüleyebilirsiniz.
