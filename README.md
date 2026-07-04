# Samsun Radar

Samsun odakli haberleri Google News RSS sorgulari ve yerel RSS kaynaklari uzerinden tek ekranda izleyen statik haber paneli. Arka planda GitHub Actions ile her 15 dakikada bir calisan bir Python botu haberleri toplayip `samsun_gundem.json` dosyasina yazar; site bu dosyayi okuyup gosterir.

## Ozellikler

- Google News ve yerel RSS kaynaklarini paralel olarak tarar.
- Liste/kart gorunumu, kaynak filtresi, **kategori filtresi** (Spor, Trafik/Kaza, Asayis, Siyaset, Ekonomi, Egitim, Saglik, Gundem), arama ve benzer haber gizleme sunar.
- Koyu/acik tema ve kullanici tercihlerini tarayicida hatirlar.
- Yeni haberler eskilerin uzerine **eklenir** (merge edilir), tek bir kaynagin gecici olarak yanit vermemesi eskiden toplanmis haberleri silmez.
- Bir calismada hicbir kaynaga ulasilamazsa dosya hic degistirilmez; veri kaybı onlenir.
- 10 gunden eski haberler otomatik olarak budanir, dosya asiri buyumez.

## Kullanim

Projeyi GitHub Pages ile yayinlayabilir ya da `index.html` dosyasini tarayicida acabilirsiniz. Kok sayfa otomatik olarak guncel uygulama dosyasi olan `haber.html` sayfasina yonlenir.

Yerelde basit bir sunucu ile denemek icin:

```bash
python -m http.server 8000
```

Sonra `http://localhost:8000` adresini acin.

Botu elle calistirmak icin:

```bash
python "tarayıcı.py"
```

## GitHub Actions ile otomatik calisma

`.github/workflows/radar-bot.yml` her 15 dakikada bir `tarayıcı.py` scriptini calistirip degisiklik varsa `samsun_gundem.json` dosyasini commit'ler.

**Onemli:** Bu is akisinin `samsun_gundem.json` dosyasini commit edip push edebilmesi icin repo ayarlarindan:

`Settings -> Actions -> General -> Workflow permissions -> "Read and write permissions"`

secilmis olmali. Aksi halde script basariyla calissa bile push adimi sessizce basarisiz olur ve haberler hic guncellenmez (bu, gecmiste haberlerin "kaybolmasinin" en olasi nedenlerinden biriydi). Workflow dosyasi artik `permissions: contents: write` ile bunu acikca istiyor, ama repo genelinde de "Read and write" secili olmasi gerekiyor.

## Notlar

- RSS kaynaklari tarayici CORS sinirlari nedeniyle sunucu tarafinda (Actions runner'inda) okunur; tarayicida CORS sorunu yasanmaz cunku site sadece uretilen statik `samsun_gundem.json` dosyasini okur.
- Bir kaynak surekli basarisiz oluyorsa, Actions sekmesindeki calisma loglarinda `[BAŞARISIZ] <kaynak adi>: <hata>` seklinde gorunur; boylece hangi kaynagin URL'sinin degistigi ya da erisimin engellendigi kolayca tespit edilebilir.
