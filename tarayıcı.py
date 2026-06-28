import urllib.request
import xml.etree.ElementTree as ET
import json
import re

# 1. GOOGLE NEWS SORGULARI (Ulusal basındaki Samsun haberleri için)
SORGULAR = [
    '"Samsun"',
    '"Atakum" AND "Samsun"',
    '"Bafra" AND "Samsun"',
    '"Samsun" AND ("siber" OR "operasyon" OR "emniyet" OR "polis" OR "gözaltı")',
    '"Samsunspor" AND ("transfer" OR "maç" OR "süper lig")',
    '"Samsun" AND ("kaza" OR "trafik" OR "karayolu")'
]

# 2. SENİN YEREL RSS KAYNAKLARIN (Eksiksiz eklendi)
YEREL_RSS = [
    {"ad": "Açık Gazete", "url": "https://www.acikgazete.com/feed/"},
    {"ad": "Samsun Gazetesi", "url": "https://www.samsungazetesi.com/rss"},
    {"ad": "Samsun Haber", "url": "https://www.samsunhaber.com/rss"},
    {"ad": "Samsun Haber Ajansı", "url": "https://www.samsunhaberajansi.com/rss.xml"},
    {"ad": "Samsun Haber X", "url": "https://www.samsunhaberx.com/rss_samsun-haberleri_2.xml"},
    {"ad": "Gazete Gerçek", "url": "https://www.gazetegercek.com.tr/rss_samsun-haber_20.xml"},
    {"ad": "Hedef Halk", "url": "https://www.hedefhalk.com/rss_samsun-haber_1764.xml"},
    {"ad": "Samsun TV", "url": "https://www.samsuntv.com.tr/rss/samsun-haber-12"},
    {"ad": "Samsun Canlı Haber", "url": "https://www.samsuncanlihaber.com/rss"},
    {"ad": "Samsun Kent Haber", "url": "https://www.samsunkenthaber.com.tr/rss_samsun-haber_30.xml"},
    {"ad": "Gazete Arena", "url": "https://www.gazetearena.com/rss.xml"},
    {"ad": "Samsun Etik Haber", "url": "https://www.samsunetikhaber3.com/rss.xml"},
    {"ad": "Denge Gazetesi", "url": "https://www.dengegazetesi.com.tr/service/rss.php"}
]

GN_BASE = 'https://news.google.com/rss/search?hl=tr&gl=TR&ceid=TR:tr&q='
toplanan_haberler = []
görülen_linkler = set()

def temizle(metin):
    """HTML etiketlerini ve gereksiz boşlukları temizler"""
    if not metin: return ""
    temiz = re.sub(r'<[^>]+>', '', metin)
    return temiz.replace('&amp;', '&').replace('&quot;', '"').strip()

def haber_ekle(baslik, link, kaynak, tarih, aciklama="", resim=""):
    if not baslik or not link: return
    # Aynı haberi iki kez eklememek için link kontrolü
    if link not in görülen_linkler:
        görülen_linkler.add(link)
        toplanan_haberler.append({
            "id": link,
            "t": temizle(baslik),
            "u": link,
            "src": kaynak,
            "d": tarih or "",
            "desc": temizle(aciklama)[:400], # Çok uzun açıklamaları frontend'i yormaması için kesiyoruz
            "img": resim
        })

# --- 1. AŞAMA: GOOGLE NEWS TARAMASI ---
for sorgu in SORGULAR:
    url = GN_BASE + urllib.parse.quote(sorgu)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req, timeout=10).read()
        root = ET.fromstring(response)
        
        for item in root.findall('.//item'):
            baslik = item.findtext('title')
            link = item.findtext('link') or item.findtext('guid')
            tarih = item.findtext('pubDate')
            kaynak = item.findtext('source') or "Google News"
            
            haber_ekle(baslik, link, kaynak, tarih)
    except Exception as e:
        print(f"Uyarı (Google News - {sorgu}): Veri çekilemedi.")

# --- 2. AŞAMA: YEREL RSS TARAMASI ---
for rss in YEREL_RSS:
    try:
        req = urllib.request.Request(rss["url"], headers={'User-Agent': 'Mozilla/5.0'})
        # Yerel siteler bazen yavaş yanıt verir, timeout'u 15 saniyeye çıkardık
        response = urllib.request.urlopen(req, timeout=15).read()
        root = ET.fromstring(response)
        
        for item in root.findall('.//item'):
            baslik = item.findtext('title')
            link = item.findtext('link') or item.findtext('guid')
            tarih = item.findtext('pubDate')
            aciklama = item.findtext('description')
            
            # Resim çıkarma (Enclosure tag'i kullanan siteler için)
            resim_url = ""
            enc = item.find('enclosure')
            if enc is not None and enc.get('type', '').startswith('image'):
                resim_url = enc.get('url', '')
                
            haber_ekle(baslik, link, rss["ad"], tarih, aciklama, resim_url)
    except Exception as e:
        print(f"Uyarı (Yerel RSS - {rss['ad']}): Site yanıt vermedi.")

# --- 3. AŞAMA: JSON DOSYASINI OLUŞTURMA ---
# Dosyayı yazarken Türkçe karakterlerin (ş,ğ,ü vb.) bozulmaması için ensure_ascii=False kullanıyoruz
with open('samsun_gundem.json', 'w', encoding='utf-8') as f:
    json.dump(toplanan_haberler, f, ensure_ascii=False, indent=4)

print(f"BİLGİ: Toplam {len(toplanan_haberler)} adet haber başarıyla çekildi ve 'samsun_gundem.json' dosyasına yazıldı.")
