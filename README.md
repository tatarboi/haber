# Samsun Radar

Samsun odakli haberleri Google News RSS sorgulari ve yerel RSS kaynaklari uzerinden tek ekranda izleyen statik haber paneli.

## Ozellikler

- Son 24 saatin Samsun haberlerini listeler.
- Google News ve yerel RSS kaynaklarini birlikte tarar.
- Liste/kart gorunumu, kaynak filtresi, arama ve benzer haber gizleme sunar.
- Koyu/acik tema ve kullanici tercihlerini tarayicida hatirlar.
- Chrome bildirimleriyle yeni haberleri duyurabilir.

## Kullanim

Projeyi GitHub Pages ile yayinlayabilir ya da `index.html` dosyasini tarayicida acabilirsiniz. Kok sayfa otomatik olarak guncel uygulama dosyasi olan `haber.html` sayfasina yonlenir.

Yerelde basit bir sunucu ile denemek icin:

```bash
python -m http.server 8000
```

Sonra `http://localhost:8000` adresini acin.

## Notlar

RSS kaynaklari tarayici CORS sinirlari nedeniyle public proxy servisleri uzerinden okunur. Bu servislerden biri gecici olarak cevap vermezse uygulama siradaki proxy ile devam etmeye calisir.
