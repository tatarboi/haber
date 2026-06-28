import urllib.request
import xml.etree.ElementTree as ET
import json
from datetime import datetime

# Geliştirilmiş OSINT Sorgularımız
SORGULAR = [
    '"Samsun"',
    '"Atakum" AND "Samsun"',
    '"Bafra" AND "Samsun"',
    '"Samsun" AND ("siber" OR "operasyon" OR "emniyet" OR "polis" OR "gözaltı")',
    '"Samsunspor" AND ("transfer" OR "maç" OR "süper lig")',
    '"Samsun" AND ("kaza" OR "trafik" OR "karayolu")'
]

GN_BASE = 'https://news.google.com/rss/search?hl=tr&gl=TR&ceid=TR:tr&q='
toplanan_haberler = []
görülen_linkler = set()

for sorgu in SORGULAR:
    url = GN_BASE + urllib.parse.quote(sorgu)
    try:
        # Kendimizi standart bir tarayıcı gibi tanıtıyoruz
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        response = urllib.request.urlopen(req, timeout=10).read()
        root = ET.fromstring(response)
        
        for item in root.findall('.//item'):
            link = item.find('link').text
            if link not in görülen_linkler:
                görülen_linkler.add(link)
                toplanan_haberler.append({
                    "id": link,
                    "t": item.find('title').text,
                    "u": link,
                    "src": item.find('source').text if item.find('source') is not None else "Google News",
                    "d": item.find('pubDate').text
                })
    except Exception as e:
        print(f"Hata ({sorgu}): {e}")

# Haberleri JSON olarak kaydet
with open('samsun_gundem.json', 'w', encoding='utf-8') as f:
    json.dump(toplanan_haberler, f, ensure_ascii=False, indent=4)

print(f"{len(toplanan_haberler)} adet haber başarıyla çekildi ve kaydedildi.")