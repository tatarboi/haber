import feedparser
import json
import os
from datetime import datetime

# Samsun haberlerini çekeceğimiz RSS kaynakları
RSS_KAYNAKLARI = [
    "https://www.samsunhaber.com/rss.xml",
    "https://www.hedefhalk.com/rss.xml",
    "https://www.samsunkenthaber.com.tr/rss.xml"
    # Buraya dilediğin kadar yeni RSS linki ekleyebilirsin.
]

def haberleri_getir():
    tum_haberler = []
    
    for url in RSS_KAYNAKLARI:
        print(f"Taranıyor: {url}")
        feed = feedparser.parse(url)
        
        for entry in feed.entries[:15]:  # Her kaynaktan son 15 haberi alalım
            haber = {
                "baslik": entry.title if hasattr(entry, 'title') else "Başlık Yok",
                "link": entry.link if hasattr(entry, 'link') else "#",
                "ozet": entry.description if hasattr(entry, 'description') else "",
                "tarih": entry.published if hasattr(entry, 'published') else datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "kaynak": feed.feed.title if hasattr(feed.feed, 'title') else "Samsun Haber"
            }
            tum_haberler.append(haber)
            
    # Haberleri tarihe göre yeniden eskiye doğru sıralayalım
    tum_haberler.sort(key=lambda x: x.get('tarih'), reverse=True)
    return tum_haberler

def json_kaydet(veri, dosya_adi="samsun_gundem.json"):
    with open(dosya_adi, 'w', encoding='utf-8') as f:
        json.dump(veri, f, ensure_ascii=False, indent=4)
    print(f"Toplam {len(veri)} haber başarıyla {dosya_adi} dosyasına kaydedildi.")

if __name__ == "__main__":
    haberler = haberleri_getir()
    json_kaydet(haberler)
