import feedparser
import json
from time import mktime
from datetime import datetime

# Sadece Samsun odaklı RSS kaynaklarımız
RSS_KAYNAKLARI = [
    "https://www.samsunhaber.com/rss.xml",
    "https://www.hedefhalk.com/rss.xml",
    "https://www.samsunkenthaber.com.tr/rss.xml"
]

def haberleri_getir():
    tum_haberler = []
    
    for url in RSS_KAYNAKLARI:
        print(f"Taranıyor: {url}")
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:20]: # Her siteden en güncel 20 haber
                try:
                    zaman_damgasi = mktime(entry.published_parsed)
                    okunabilir_tarih = datetime.fromtimestamp(zaman_damgasi).strftime("%d.%m.%Y %H:%M")
                except:
                    zaman_damgasi = 0
                    okunabilir_tarih = "Tarih Yok"

                haber = {
                    "baslik": entry.title if hasattr(entry, 'title') else "Başlık Yok",
                    "link": entry.link if hasattr(entry, 'link') else "#",
                    "tarih": okunabilir_tarih,
                    "timestamp": zaman_damgasi,
                    "kaynak": feed.feed.title if hasattr(feed.feed, 'title') else "Samsun Haber"
                }
                tum_haberler.append(haber)
        except Exception as e:
            print(f"Hata oluştu ({url}): {e}")
            
    # Saniyesine göre kusursuz sıralama
    tum_haberler.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # Gereksiz veriyi JSON'dan temizleme
    for h in tum_haberler:
        del h['timestamp']

    return tum_haberler

def json_kaydet(veri, dosya_adi="samsun_gundem.json"):
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)
    print(f"Sistem Başarılı! Toplam {len(veri)} adet haber {dosya_adi} dosyasına yazıldı.")

if __name__ == "__main__":
    haberler = haberleri_getir()
    json_kaydet(haberler)
