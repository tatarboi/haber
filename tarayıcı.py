import feedparser
import json
from time import mktime
from datetime import datetime

# Sadece net Samsun haber kaynakları
RSS_KAYNAKLARI = [
    "https://www.samsunhaber.com/rss.xml",
    "https://www.hedefhalk.com/rss.xml",
    "https://www.samsunkenthaber.com.tr/rss.xml"
]

def haberleri_getir():
    tum_haberler = []
    
    for url in RSS_KAYNAKLARI:
        print(f"Taranıyor: {url}")
        feed = feedparser.parse(url)
        
        for entry in feed.entries[:20]: # Her siteden son 20 haber
            # Kusursuz sıralama için tarihleri makine diline çeviriyoruz
            try:
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    zaman_damgasi = mktime(entry.published_parsed)
                    okunabilir_tarih = datetime.fromtimestamp(zaman_damgasi).strftime("%d.%m.%Y %H:%M")
                else:
                    zaman_damgasi = 0
                    okunabilir_tarih = "Tarih Yok"
            except:
                zaman_damgasi = 0
                okunabilir_tarih = "Tarih Yok"

            haber = {
                "baslik": entry.title if hasattr(entry, 'title') else "Başlık Yok",
                "link": entry.link if hasattr(entry, 'link') else "#",
                "tarih": okunabilir_tarih,
                "timestamp": zaman_damgasi, # Sıralama için gizli veri
                "kaynak": feed.feed.title if hasattr(feed.feed, 'title') else "Samsun"
            }
            tum_haberler.append(haber)
            
    # Tüm haberleri saniyesine göre en yeniden en eskiye sıralıyoruz!
    tum_haberler.sort(key=lambda x: x['timestamp'], reverse=True)
    
    # JSON dosyası şişmesin diye sıralama bittikten sonra timestamp'i siliyoruz
    for h in tum_haberler:
        del h['timestamp']

    return tum_haberler

def json_kaydet(veri, dosya_adi="samsun_gundem.json"):
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)
    print(f"Sıralama kusursuz! {len(veri)} haber {dosya_adi} dosyasına yazıldı.")

if __name__ == "__main__":
    haberler = haberleri_getir()
    json_kaydet(haberler)
