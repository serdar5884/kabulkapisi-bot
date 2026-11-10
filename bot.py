"""
Kabul Kapısı — Instagram dua botu

Her çalıştığında bugünün duasını seçer, kartını çizer ve Instagram'a paylaşır.
  Günde 3 paylaşım: sabah 07:00 özel dua, öğle 13:00 Kur'an duası, akşam 21:00 hadis duası
  * Cuma sabahı      -> Cuma duası
  * Kandil akşamı    -> kandile özel dua (dualar.json > kandil_tarihleri)

Ortam değişkenleri:
  DRY_RUN=1        sadece kartı ve açıklamayı üretir, paylaşmaz
  MODE=post        (varsayılan) bugünün duasını paylaşır
  MODE=onizleme    önümüzdeki 3 günün (9 kart) kartlarını gorseller/onizleme/ içine çizer
  TARIH=2026-12-10 testi belirli bir güne göre yapar (YYYY-AA-GG)
  VAKIT=sabah|ogle|aksam  boşsa Türkiye saatine göre seçilir
"""
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone

import brand
import insta

HERE = os.path.dirname(os.path.abspath(__file__))
TR_TZ = timezone(timedelta(hours=3))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"
MODE = (os.getenv("MODE") or "post").strip().lower()
BASLANGIC = date(2026, 11, 11)          # sıralamanın başladığı gün
HISTORY_FILE = os.path.join(HERE, "gecmis.json")

with open(os.path.join(HERE, "dualar.json"), encoding="utf-8") as f:
    DB = json.load(f)

KANDIL_TAG = {"regaip": "#regaipkandili", "mirac": "#miraçkandili", "berat": "#beratkandili",
              "kadir": "#kadirgecesi", "mevlid": "#mevlidkandili"}


def bugun():
    t = os.getenv("TARIH", "").strip()
    return date.fromisoformat(t) if t else datetime.now(TR_TZ).date()


VAKITLER = ("sabah", "ogle", "aksam")
# her vaktin türü: sabah özel dua, öğle Kur'an duası, akşam hadis duası
VAKIT_HAVUZ = {"sabah": "ozel", "ogle": "kuran", "aksam": "hadis"}
VAKIT_BASLIK = {"sabah": "Günün Duası", "ogle": "Kur'an'dan Bir Dua", "aksam": "Hadislerden Bir Dua"}
VAKIT_TAG = {"sabah": ["#gününduası", "#sabahduası"], "ogle": ["#kuran", "#ayet"], "aksam": ["#hadis", "#akşamduası"]}


def vakit_bul():
    v = (os.getenv("VAKIT") or "").strip().lower()
    if v in VAKITLER:
        return v
    saat = datetime.now(TR_TZ).hour
    return "sabah" if saat < 11 else ("ogle" if saat < 17 else "aksam")


def sec(gun, vakit):
    """Günün ve vaktin duasını döndürür: (dua, tur, baslik, etiketler)."""
    kandil = DB.get("kandil_tarihleri", {}).get(gun.isoformat())
    if vakit == "aksam" and kandil and kandil in DB["kandil"]:
        k = DB["kandil"][kandil]
        return k, "kandil", k["baslik"], [KANDIL_TAG.get(kandil, "#kandil"), "#kandilmesajları"]
    gecen = (gun - BASLANGIC).days
    if vakit == "sabah" and gun.weekday() == 4:   # Cuma sabahı
        cuma = DB["cuma"]
        return cuma[(gecen // 7) % len(cuma)], "cuma", "Hayırlı Cumalar", ["#hayırlıcumalar", "#cumamesajları"]
    zit = {"sabah": "aksam", "aksam": "sabah"}.get(vakit)
    havuz = [e for e in DB[VAKIT_HAVUZ[vakit]] if not zit or e.get("vakit") != zit]
    dua = havuz[gecen % len(havuz)]
    return dua, vakit, VAKIT_BASLIK[vakit], VAKIT_TAG[vakit] + ["#amin"]


def caption(dua, tur, baslik, tags):
    acilis = {"sabah": "🌅 Hayırlı sabahlar, bu satırları okuyan sana bir dua var",
              "ogle": "📖 Kur'an-ı Kerim'den bir dua, bu satırları okuyan herkes için",
              "aksam": "🌙 Hayırlı akşamlar, Peygamber Efendimizin dualarından biri sana",
              "cuma": "🕌 Hayırlı cumalar",
              "kandil": f"✨ {baslik} mübarek olsun"}[tur]
    parts = [acilis, dua["metin"]]
    if dua.get("kaynak"):
        parts.append(f"📖 {dua['kaynak']}")
    parts.append("Âmin yazmayı unutma 🤲\nSevdiklerine gönder, bu dua onlara da ulaşsın 💛")
    alltags = []
    for t in tags + insta.BASE_TAGS:
        if t.lower() not in [a.lower() for a in alltags]:
            alltags.append(t)
    parts.append(" ".join(alltags[:6]))
    return "\n\n".join(parts)[:2150]


def kart(gun, dua, tur, baslik, out, vakit="ogle"):
    dt = datetime(gun.year, gun.month, gun.day)
    zs = brand.zeminler()
    if zs:   # arkaplanlar/ klasöründeki görseller sırayla döner
        zemin = zs[((gun - BASLANGIC).days * 3 + VAKITLER.index(vakit)) % len(zs)]
        return brand.make_photo_card(out, dua["metin"], zemin, baslik=baslik, kaynak=dua.get("kaynak"),
                                     date=dt, kandil=(tur == "kandil"))
    return brand.make_card(out, dua["metin"], baslik=baslik, kaynak=dua.get("kaynak"),
                           date=dt, kandil=(tur == "kandil"))


def gecmis_oku():
    try:
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def onizleme():
    d = os.path.join(brand.OUT_DIR, "onizleme")
    os.makedirs(d, exist_ok=True)
    g = bugun()
    for i in range(3):
        gun = g + timedelta(days=i)
        for v in VAKITLER:
            dua, tur, baslik, tags = sec(gun, v)
            kart(gun, dua, tur, baslik, os.path.join(d, f"{gun.isoformat()}_{v}_{tur}.jpg"), v)
            print(f"{gun} {v} [{tur}] {dua['metin'][:60]}...")


def main():
    if MODE == "onizleme":
        onizleme()
        return
    gun = bugun()
    vakit = vakit_bul()
    anahtar = f"{gun.isoformat()}_{vakit}"
    hist = gecmis_oku()
    if anahtar in hist.get("paylasilanlar", []) and not DRY_RUN:
        print(f"{gun} {vakit} paylaşımı zaten yapıldı, tekrar paylaşılmıyor.")
        return

    dua, tur, baslik, tags = sec(gun, vakit)
    out = os.path.join(brand.OUT_DIR, f"kart_{anahtar}.jpg")
    kart(gun, dua, tur, baslik, out, vakit)
    cap = caption(dua, tur, baslik, tags)
    print(f"--- {gun} {vakit} [{tur}] ---\n{cap}\n---")

    if DRY_RUN:
        print("DRY_RUN=1 -> paylaşılmadı. Kart:", out)
        return
    if not insta.enabled():
        sys.exit(1)
    insta.publish_carousel([out], cap)
    son = (hist.get("paylasilanlar", []) + [anahtar])[-30:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"paylasilanlar": son}, f)
    if vakit == "aksam":
        insta.refresh_token()


if __name__ == "__main__":
    main()
