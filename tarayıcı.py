# -*- coding: utf-8 -*-
"""
Samsun Radar - Haber Tarayici Botu
-----------------------------------
Google News RSS ve yerel RSS kaynaklarini tarayip samsun_gundem.json
dosyasini gunceller.

v2 duzeltmeleri:
  - KRITIK BUG: `urllib.parse` modulu import edilmemisti, bu yuzden TUM
    Google News sorgulari sessizce basarisiz oluyordu (except: pass).
    Artik urllib.parse dogru sekilde import ediliyor.
  - ARTIK BIRLESTIRME (merge) YAPILIYOR: Eskiden script her calistiginda
    JSON dosyasinin TAMAMINI o anki taramayla degistiriyordu. Bir kaynak
    gecici olarak yanit vermediginde, o kaynaktan gelen onceki haberler
    bir sonraki commit'te tamamen siliniyordu ("haberler kaciyor").
    Simdi mevcut dosya okunuyor, yeni haberler onun uzerine ekleniyor,
    link bazinda tekillestiriliyor ve tarih bazinda sadece eski/asiri
    haberler budanıyor.
  - GUVENLI YAZMA: Bu calismada TEK bir kaynaktan bile veri alinamazsa
    (ornegin tum ag erisimi basarisizsa) dosyaya HIC dokunulmuyor; bir
    sonraki 15 dakikalik calismaya birakiliyor. Boylece gecici bir kesinti
    tum veriyi silmiyor.
  - PARALEL TARAMA: Kaynaklar ThreadPoolExecutor ile es zamanli taranarak
    hem hiz hem de tek bir yavas kaynagin tum calismayi kilitlemesi onleniyor.
  - DAHA IYI RESIM/TARIH CIKARIMI: media:content/media:thumbnail ve aciklama
    icindeki <img> etiketlerinden gorsel; RFC822 tarihlerin guvenli parse'i.
  - KATEGORI ETIKETI: Basit anahtar kelime tabanli kategori (Spor,
    Trafik/Kaza, Asayis, Ekonomi, Siyaset, Egitim, Saglik, Gundem) her
    habere "kat" alani olarak ekleniyor; arayuzde filtre olarak kullanilir.
  - DETAYLI LOG: Her kaynagin basarili/basarisiz oldugu ve kac haber
    getirdigi GitHub Actions loglarina yazdiriliyor (artik "sessiz"
    hatalar yok, sorun cikinca nedenini gormek mumkun).
"""

import json
import re
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from email.utils import parsedate_to_datetime
from urllib import request as urlrequest
from urllib import parse as urlparse
from urllib import error as urlerror
import xml.etree.ElementTree as ET

# --------------------------------------------------------------------------
# AYARLAR
# --------------------------------------------------------------------------

JSON_DOSYA = "samsun_gundem.json"
MAX_HABER = 1500          # Dosyada tutulacak azami haber sayisi
SAKLAMA_GUNU = 10         # Bu kadar gunden eski haberler budanir
ZAMAN_ASIMI = 12          # saniye, tek istek icin
DENEME_SAYISI = 2         # basarisiz istek icin tekrar deneme
PARALEL_ISCI = 8

socket.setdefaulttimeout(ZAMAN_ASIMI)

# 1. GOOGLE NEWS SORGULARI (Ulusal basindaki Samsun haberleri icin)
SORGULAR = [
    '"Samsun"',
    '"Atakum" AND "Samsun"',
    '"Bafra" AND "Samsun"',
    '"Samsun" AND ("siber" OR "operasyon" OR "emniyet" OR "polis" OR "gözaltı")',
    '"Samsunspor" AND ("transfer" OR "maç" OR "süper lig")',
    '"Samsun" AND ("kaza" OR "trafik" OR "karayolu")',
]

# 2. YEREL RSS KAYNAKLARI
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
    {"ad": "Denge Gazetesi", "url": "https://www.dengegazetesi.com.tr/service/rss.php"},
]

GN_BASE = "https://news.google.com/rss/search?hl=tr&gl=TR&ceid=TR:tr&q="

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
}

MEDIA_NS = {"media": "http://search.yahoo.com/mrss/"}

KATEGORILER = [
    ("Spor", ["spor", "samsunspor", "fenerbahçe", "galatasaray", "beşiktaş",
              "trabzonspor", "süper lig", "transfer", "futbol", " maç", "gol "]),
    ("Trafik/Kaza", ["kaza", "trafik", "karayolu", "çarpıştı", "devrildi",
                      "yaralandı", "kaza yaptı", "otoyol"]),
    ("Asayiş", ["polis", "emniyet", "gözaltı", "tutukland", "operasyon",
                 "siber", "hırsızlık", "cinayet", "uyuşturucu", "jandarma",
                 "dolandırıcılık", "silah"]),
    ("Siyaset", ["belediye", "vali", "başkan", "ak parti", "chp", "mhp",
                  "iyi parti", "meclis", "milletvekili", "bakan"]),
    ("Ekonomi", ["ekonomi", "zam", "fiyat", "ihracat", "ticaret", "esnaf",
                  "borsa", "dolar", "enflasyon", "market"]),
    ("Eğitim", ["üniversite", "okul", "öğrenci", "ondokuz mayıs", "eğitim",
                 "sınav", "ösym"]),
    ("Sağlık", ["hastane", "sağlık", "doktor", "aşı", "tedavi", "ameliyat"]),
]


# --------------------------------------------------------------------------
# YARDIMCI FONKSIYONLAR
# --------------------------------------------------------------------------

def temizle(metin):
    if not metin:
        return ""
    temiz = re.sub(r"<[^>]+>", "", metin)
    temiz = (
        temiz.replace("&amp;", "&")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&apos;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
    )
    return temiz.strip()


def tarih_normalize(tarih_str):
    """RFC822 / RFC2822 tarihini ISO 8601'e cevirir. Basarisizsa bos dondurur."""
    if not tarih_str:
        return ""
    try:
        dt = parsedate_to_datetime(tarih_str)
        if dt is None:
            return tarih_str
        return dt.isoformat()
    except Exception:
        return tarih_str


def kategori_bul(baslik, aciklama):
    metin = (baslik + " " + aciklama).lower()
    for kat_adi, kelimeler in KATEGORILER:
        for kw in kelimeler:
            if kw in metin:
                return kat_adi
    return "Gündem"


def resim_cikar(item):
    """enclosure, media:content, media:thumbnail veya aciklama icindeki img'den gorsel URL'si bulur."""
    enc = item.find("enclosure")
    if enc is not None and enc.get("type", "").startswith("image") and enc.get("url"):
        return enc.get("url")

    media_content = item.find("media:content", MEDIA_NS)
    if media_content is not None and media_content.get("url"):
        return media_content.get("url")

    media_thumb = item.find("media:thumbnail", MEDIA_NS)
    if media_thumb is not None and media_thumb.get("url"):
        return media_thumb.get("url")

    aciklama_ham = item.findtext("description") or ""
    m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', aciklama_ham)
    if m:
        return m.group(1)

    return ""


def istek_yap(url):
    """Basit retry mantigiyla HTTP GET yapar, bytes doner."""
    son_hata = None
    for deneme in range(DENEME_SAYISI):
        try:
            req = urlrequest.Request(url, headers=HEADERS)
            with urlrequest.urlopen(req, timeout=ZAMAN_ASIMI) as resp:
                return resp.read()
        except Exception as e:
            son_hata = e
            time.sleep(1.5)
    raise son_hata


def google_news_tara(sorgu):
    """Tek bir Google News sorgusunu tarar, (kaynak_adi, [haberler]) tuple'i doner."""
    url = GN_BASE + urlparse.quote_plus(sorgu)
    haberler = []
    try:
        veri = istek_yap(url)
        root = ET.fromstring(veri)
        for item in root.findall(".//item"):
            baslik = item.findtext("title")
            link = item.findtext("link") or item.findtext("guid")
            tarih = item.findtext("pubDate")
            kaynak = item.findtext("source") or "Google News"
            haberler.append({
                "baslik": baslik,
                "link": link,
                "kaynak": kaynak,
                "tarih": tarih,
                "aciklama": "",
                "resim": "",
            })
        return sorgu, haberler, None
    except Exception as e:
        return sorgu, haberler, e


def rss_tara(rss):
    """Tek bir yerel RSS kaynagini tarar, (kaynak_adi, [haberler], hata) tuple'i doner."""
    haberler = []
    try:
        veri = istek_yap(rss["url"])
        root = ET.fromstring(veri)
        for item in root.findall(".//item"):
            baslik = item.findtext("title")
            link = item.findtext("link") or item.findtext("guid")
            tarih = item.findtext("pubDate")
            aciklama = item.findtext("description")
            resim_url = resim_cikar(item)
            haberler.append({
                "baslik": baslik,
                "link": link,
                "kaynak": rss["ad"],
                "tarih": tarih,
                "aciklama": aciklama or "",
                "resim": resim_url,
            })
        return rss["ad"], haberler, None
    except Exception as e:
        return rss["ad"], haberler, e


# --------------------------------------------------------------------------
# ANA AKIS
# --------------------------------------------------------------------------

def iso_mu(deger):
    try:
        from datetime import datetime
        datetime.fromisoformat(deger)
        return True
    except Exception:
        return False


def mevcut_veriyi_yukle():
    try:
        with open(JSON_DOSYA, "r", encoding="utf-8") as f:
            veri = json.load(f)
            if not isinstance(veri, list):
                return []
            # Eski formatta (RFC822, orn "Fri, 03 Jul 2026 12:11:11 GMT")
            # kaydedilmis tarihleri ISO 8601'e gocur; boylece siralama ve
            # budama mantigi tum kayitlarda tutarli calisir.
            gocurulen = 0
            for h in veri:
                d = h.get("d", "")
                if d and not iso_mu(d):
                    yeni = tarih_normalize(d)
                    if yeni != d:
                        h["d"] = yeni
                        gocurulen += 1
            if gocurulen:
                print(f"GÖÇ: {gocurulen} eski kayittaki tarih formati ISO 8601'e cevrildi.")
            return veri
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"UYARI: Mevcut {JSON_DOSYA} okunamadi ({e}), sifirdan baslaniyor.")
    return []


def main():
    baslangic = time.time()
    mevcut = mevcut_veriyi_yukle()
    gorulen_linkler = {h["u"]: h for h in mevcut if h.get("u")}

    yeni_haberler = []
    basarili_kaynak = 0
    basarisiz_kaynak = 0
    toplam_kaynak = len(SORGULAR) + len(YEREL_RSS)

    print(f"BASLADI: {toplam_kaynak} kaynak taranacak "
          f"({len(SORGULAR)} Google News sorgusu + {len(YEREL_RSS)} yerel RSS).")

    with ThreadPoolExecutor(max_workers=PARALEL_ISCI) as havuz:
        gorevler = []
        for sorgu in SORGULAR:
            gorevler.append(havuz.submit(google_news_tara, sorgu))
        for rss in YEREL_RSS:
            gorevler.append(havuz.submit(rss_tara, rss))

        for gorev in as_completed(gorevler):
            ad, haberler, hata = gorev.result()
            if hata is not None:
                basarisiz_kaynak += 1
                print(f"  [BAŞARISIZ] {ad}: {hata}")
                continue
            basarili_kaynak += 1
            print(f"  [OK] {ad}: {len(haberler)} haber bulundu")
            yeni_haberler.extend(haberler)

    # --- GUVENLI YAZMA KONTROLU ---
    # Hicbir kaynaktan veri alinamadiysa (ornegin Actions runner'in agi
    # engellendiyse) dosyaya dokunma; mevcut veriyi koru.
    if basarili_kaynak == 0:
        print("HATA: Hicbir kaynaktan veri alinamadi. "
              "samsun_gundem.json DEGISTIRILMEDI, bir sonraki calismaya birakiliyor.")
        sys.exit(1)

    eklenen = 0
    for h in yeni_haberler:
        link = h["link"]
        baslik = h["baslik"]
        if not baslik or not link:
            continue
        if link in gorulen_linkler:
            continue
        aciklama_temiz = temizle(h["aciklama"])[:400]
        baslik_temiz = temizle(baslik)
        kayit = {
            "id": link,
            "t": baslik_temiz,
            "u": link,
            "src": h["kaynak"] or "Bilinmeyen Kaynak",
            "d": tarih_normalize(h["tarih"]),
            "desc": aciklama_temiz,
            "img": h["resim"] or "",
            "kat": kategori_bul(baslik_temiz, aciklama_temiz),
        }
        gorulen_linkler[link] = kayit
        eklenen += 1

    # --- BIRLESTIR, ESKI KAYITLARA DA KATEGORI EKLE, BUDA, SIRALA ---
    tum_haberler = list(gorulen_linkler.values())
    for h in tum_haberler:
        if "kat" not in h or not h.get("kat"):
            h["kat"] = kategori_bul(h.get("t", ""), h.get("desc", ""))

    def tarih_key(h):
        try:
            from datetime import datetime
            return datetime.fromisoformat(h["d"])
        except Exception:
            from datetime import datetime, timezone
            return datetime.fromtimestamp(0, tz=timezone.utc)

    tum_haberler.sort(key=tarih_key, reverse=True)

    # Cok eski haberleri buda (SAKLAMA_GUNU'nden eski)
    from datetime import datetime, timezone, timedelta
    sinir = datetime.now(timezone.utc) - timedelta(days=SAKLAMA_GUNU)

    def guncel_mi(h):
        try:
            dt = datetime.fromisoformat(h["d"])
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt >= sinir
        except Exception:
            return True  # tarihi parse edilemeyeni guvenli tarafta tut

    budanmis = [h for h in tum_haberler if guncel_mi(h)]
    # Azami sayiyi asarsa (zaten tarihe gore sirali) fazlasini at
    if len(budanmis) > MAX_HABER:
        budanmis = budanmis[:MAX_HABER]

    with open(JSON_DOSYA, "w", encoding="utf-8") as f:
        json.dump(budanmis, f, ensure_ascii=False, indent=2)

    sure = time.time() - baslangic
    print(
        f"BİTTİ: {basarili_kaynak}/{toplam_kaynak} kaynak basarili, "
        f"{eklenen} yeni haber eklendi, toplam {len(budanmis)} haber "
        f"dosyada tutuluyor. ({sure:.1f}s)"
    )


if __name__ == "__main__":
    main()
