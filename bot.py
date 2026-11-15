"""
Kabul Kapısı — Instagram dua botu

Her çalıştığında bugünün duasını seçer, kartını çizer ve Instagram'a paylaşır.
  Günde 4 paylaşım: 07:00 özel dua, 13:00 Kur'an duası, 17:00 özel dua, 21:00 hadis duası
  * Cuma sabahı      -> Cuma duası
  * Kandil akşamı    -> kandile özel dua (dualar.json > kandil_tarihleri)

Ortam değişkenleri:
  DRY_RUN=1        sadece kartı ve açıklamayı üretir, paylaşmaz
  MODE=post        (varsayılan) bugünün duasını paylaşır
  MODE=onizleme    önümüzdeki 3 günün (9 kart) kartlarını gorseller/onizleme/ içine çizer
  TARIH=2026-12-10 testi belirli bir güne göre yapar (YYYY-AA-GG)
  VAKIT=sabah|ogle|ikindi|aksam|ozet  boşsa Türkiye saatine göre seçilir
"""
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone

import brand
import insta
import video

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


VAKITLER = ("sabah", "ogle", "ikindi", "aksam")
# her vaktin türü: sabah özel dua, öğle Kur'an duası, akşam hadis duası
VAKIT_HAVUZ = {"sabah": "ozel", "ogle": "kuran", "ikindi": "ozel", "aksam": "hadis"}
VAKIT_BASLIK = {"sabah": "Günün Duası", "ogle": "Kur'an'dan Bir Dua", "ikindi": "Günün Duası", "aksam": "Hadislerden Bir Dua"}
VAKIT_TAG = {"sabah": ["#gününduası", "#sabahduası"], "ogle": ["#kuran", "#ayet"], "ikindi": ["#gününduası"], "aksam": ["#hadis", "#akşamduası"]}


def vakit_bul():
    v = (os.getenv("VAKIT") or "").strip().lower()
    if v in VAKITLER or v == "ozet":
        return v
    saat = datetime.now(TR_TZ).hour
    return "sabah" if saat < 11 else ("ogle" if saat < 15 else ("ikindi" if saat < 19 else "aksam"))


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
    zit = {"sabah": ("aksam",), "ikindi": ("sabah", "aksam"), "aksam": ("sabah",)}.get(vakit, ())
    havuz = [e for e in DB[VAKIT_HAVUZ[vakit]] if e.get("vakit") not in zit]
    if VAKIT_HAVUZ[vakit] == "ozel":   # günde 2 özel dua: sabah çift, ikindi tek sıradaki
        dua = havuz[(gecen * 2 + (1 if vakit == "ikindi" else 0)) % len(havuz)]
    else:
        dua = havuz[gecen % len(havuz)]
    tema_tag = {"borç": ["#borçduası"], "hasta": ["#şifaduası"], "dert": ["#sıkıntıduası"],
                "çocuk": ["#evlatduası"], "aile": ["#aileduası"]}.get(dua.get("tema"), [])
    vtag = VAKIT_TAG[vakit]
    if vakit == "aksam" and dua.get("tur") != "hadis":
        vtag = ["#akşamduası", "#duaistegi"]
    return dua, vakit, VAKIT_BASLIK[vakit], tema_tag + vtag + ["#amin"]


def caption(dua, tur, baslik, tags):
    acilis = {"sabah": "🌅 Hayırlı sabahlar, bu satırları okuyan sana bir dua var",
              "ikindi": "🤲 Bu satırları okuyan sana bir dua var",
              "ogle": "📖 Kur'an-ı Kerim'den bir dua, bu satırları okuyan herkes için",
              "aksam": "🌙 Hayırlı akşamlar, Peygamber Efendimizin dualarından biri sana",
              "cuma": "🕌 Hayırlı Cumalar",
              "kandil": f"✨ {baslik} mübarek olsun"}[tur]
    if tur == "aksam" and dua.get("tur") != "hadis":
        acilis = "🌙 Hayırlı akşamlar, bu satırları okuyan sana bir dua var"
    parts = [acilis]
    if dua.get("okunus"):
        parts.append(f"🕋 Okunuşu: {dua['okunus']}")
    parts.append(("Anlamı: " if dua.get("okunus") else "") + dua["metin"])
    if dua.get("kaynak"):
        parts.append(f"📖 {dua['kaynak']}")
    parts.append("Âmin yazmayı unutma 🤲\nDuaya ihtiyacı olan birini etiketle 👇\nSevdiklerine gönder, bu dua onlara da ulaşsın 💛")
    alltags = []
    for t in tags + insta.BASE_TAGS:
        if t.lower() not in [a.lower() for a in alltags]:
            alltags.append(t)
    parts.append(" ".join(alltags[:5]))   # Instagram sınırı: en fazla 5 etiket
    return "\n\n".join(parts)[:2150]


def kart(gun, dua, tur, baslik, out, vakit="ogle"):
    dt = datetime(gun.year, gun.month, gun.day)
    zs = brand.zeminler()
    if zs:   # arkaplanlar/ klasöründeki görseller sırayla döner
        zemin = zs[((gun - BASLANGIC).days * len(VAKITLER) + VAKITLER.index(vakit)) % len(zs)]
        brand.make_photo_card(out, dua["metin"], zemin, baslik=baslik, kaynak=dua.get("kaynak"),
                              date=dt, kandil=(tur == "kandil"))
        return zemin
    brand.make_card(out, dua["metin"], baslik=baslik, kaynak=dua.get("kaynak"),
                    date=dt, kandil=(tur == "kandil"))
    return None


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


DERLEME = [("borç", "Borçlular İçin 5 Dua", "#borçduası"), ("hasta", "Hastalar İçin 5 Şifa Duası", "#şifaduası"),
           ("çocuk", "Çocuklarımız İçin 5 Dua", "#evlatduası"), ("dert", "Dertliler İçin 5 Dua", "#sıkıntıduası"),
           ("aile", "Ailemiz İçin 5 Dua", "#aileduası")]


def derleme(gun):
    """Pazar ikindisi: bir temadan 5 dua + kapak (kaydırmalı gönderi)."""
    hafta = (gun - BASLANGIC).days // 7
    tema, baslik, tag = DERLEME[hafta % len(DERLEME)]
    lst = [e for e in DB["ozel"] if e.get("tema") == tema]
    tur = hafta // len(DERLEME)
    secilen = [lst[(tur * 5 + i) % len(lst)] for i in range(5)]
    zs = brand.zeminler()
    dt = datetime(gun.year, gun.month, gun.day)
    yollar = [brand.make_cover(os.path.join(brand.OUT_DIR, f"derleme_{gun}_0.jpg"), baslik,
                               "Kaydır, sana uygun olanı kaydet", zs[hafta % len(zs)])]
    for i, e in enumerate(secilen, 1):
        yollar.append(brand.make_photo_card(os.path.join(brand.OUT_DIR, f"derleme_{gun}_{i}.jpg"), e["metin"],
                                            zs[(hafta + i) % len(zs)], date=dt))
    cap = "\n\n".join([f"🤲 {baslik}", "Kaydır, sana en çok dokunanı kaydet ve ihtiyacı olana gönder.",
                        "Âmin yazmayı unutma 🤲\nDuaya ihtiyacı olan birini etiketle 👇",
                        " ".join([tag, "#dua", "#amin", "#kabulkapisi"])])
    return yollar, cap


def hikaye(kart_path, zemin):
    if os.getenv("STORY", "1") != "1":
        return
    try:
        dikey = video.dikey_kare(kart_path, zemin, kart_path.replace(".jpg", "_story.jpg"))
        insta.publish_story(dikey)
    except Exception as e:
        print("[insta] hikâye paylaşılamadı (gönderi yine de yayında):", e)


def gunun_ozeti():
    """Akşam: o gün paylaşılan 4 duanın hepsi tek Reels'te (22:30)."""
    gun = bugun()
    anahtar = f"{gun.isoformat()}_ozet"
    hist = gecmis_oku()
    if anahtar in hist.get("paylasilanlar", []) and not DRY_RUN:
        print("Bugünün özeti zaten paylaşıldı."); return
    zs = brand.zeminler()
    tarih = f"{gun.day} {brand.AYLAR[gun.month - 1]} {gun.year}"
    kapak = brand.make_cover(os.path.join(brand.OUT_DIR, f"ozet_{gun}_0.jpg"), "Bugünün Duaları",
                             tarih, zs[(gun - BASLANGIC).days % len(zs)])
    kartlar, ozet_satir, sureler = [kapak], [], []
    for i, v in enumerate(("sabah", "ogle", "ikindi", "aksam"), 1):
        dua, tur, baslik, tags = sec(gun, v)
        p = os.path.join(brand.OUT_DIR, f"ozet_{gun}_{i}.jpg")
        kart(gun, dua, tur, baslik, p, v)
        kartlar.append(p)
        sureler.append(video.okuma_suresi(dua["metin"]))
        ozet_satir.append(f"{['🌅', '📖', '🤲', '🌙'][i - 1]} {dua['metin'][:60].rsplit(' ', 1)[0]}…")
    mp4 = video.ozet_reel(kartlar, zs[0], os.path.join(brand.OUT_DIR, f"ozet_{gun}.mp4"), sureler_kart=sureler)
    print("[özet] kart süreleri (sn):", sureler)
    cap = "\n\n".join([f"🌙 Bugünün duaları bir arada · {tarih}", "\n".join(ozet_satir),
                        "Gün içinde kaçırdıysan hepsini tek videoda izle. Hangisine âmin dersin? 🤲",
                        "Duaya ihtiyacı olan birini etiketle 👇",
                        "#dua #gününduaları #amin #akşamduası #kabulkapisi"])
    print(cap)
    if DRY_RUN:
        print("DRY_RUN=1 -> özet paylaşılmadı:", mp4); return
    if not insta.enabled():
        sys.exit(1)
    insta.publish_reel(mp4, cap, kapak)
    hikaye(kapak, zs[0])
    son = (hist.get("paylasilanlar", []) + [anahtar])[-30:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"paylasilanlar": son}, f)


def kontrol():
    """Paylaşım yapmadan anahtarları dener."""
    hata = False
    for ad, val in (("IG_ACCESS_TOKEN", insta.IG_TOKEN), ("IMGBB_API_KEY", insta.IMGBB_KEY), ("GH_PAT", insta.GH_PAT)):
        print(f"{ad}: {'VAR' if val else 'EKSİK'}")
        hata |= not val
    if insta.SYSTEM_TOKEN:
        print("Token türü: EAA (Unified/Facebook) -> IG_USER_ID:", insta.IG_USER_ID or "EKSİK")
        for path, fields in (("me", "id,name"), ("me/accounts", "name,instagram_business_account{id,username}")):
            r = insta.requests.get(f"{insta.API}/{path}", params={"fields": fields, "access_token": insta.IG_TOKEN}, timeout=30)
            print(f"{path}:", r.text[:600])
        if insta.IG_USER_ID:
            r = insta.requests.get(f"{insta.API}/{insta.IG_USER_ID}", params={"fields": "username", "access_token": insta.IG_TOKEN}, timeout=30)
            j = r.json(); print("Instagram hesabı:", j.get("username"), j.get("error", {}).get("message", ""))
            hata |= j.get("username", "").lower() != "kabulkapisi"
        else:
            hata = True
    else:
      try:
        r = insta.requests.get(f"{insta.API}/me", params={"fields": "user_id,username", "access_token": insta.IG_TOKEN}, timeout=30)
        j = r.json()
        print("Instagram hesabı:", j.get("username"), "| hata:" if "error" in j else "", j.get("error", {}).get("message", ""))
        if j.get("username", "").lower() != "kabulkapisi":
            hata = True
      except Exception as e:
        print("Instagram kontrol hatası:", e); hata = True
    try:
        test = os.path.join(brand.OUT_DIR, "logo.png")
        print("imgbb yükleme:", insta.upload_public(test))
    except Exception as e:
        print("imgbb hatası:", e); hata = True
    if hata:
        sys.exit("KONTROL BAŞARISIZ")
    print("KONTROL BAŞARILI")


def main():
    if MODE == "kontrol":
        kontrol()
        return
    if MODE == "yorum":   # yorumlara dua cevabı
        import yorum
        if not insta.enabled():
            sys.exit(1)
        yorum.calistir(dry_run=DRY_RUN)
        return
    if MODE == "sabit":   # sabit/ klasöründeki tanıtım Reels'ini bir kez paylaşır
        d = os.path.join(HERE, "sabit")
        cap = open(os.path.join(d, "aciklama.txt"), encoding="utf-8").read().strip()
        if DRY_RUN:
            print("DRY_RUN=1 -> sabit gönderi paylaşılmadı"); return
        insta.publish_reel(os.path.join(d, "sabit_reels.mp4"), cap, os.path.join(d, "sabit_kart.jpg"))
        try:
            insta.publish_story(video.dikey_kare(os.path.join(d, "sabit_kart.jpg"), None, os.path.join(d, "story.jpg")))
        except Exception as e:
            print("[insta] hikâye paylaşılamadı:", e)
        return
    if MODE == "post" and vakit_bul() == "ozet":
        return gunun_ozeti()
    if MODE == "reels_test":   # videoyu yükler ama YAYINLAMAZ
        gun = bugun(); dua, tur, baslik, tags = sec(gun, "sabah")
        out = os.path.join(brand.OUT_DIR, "test.jpg"); z = kart(gun, dua, tur, baslik, out, "sabah")
        mp4, _ = video.reel(out, z, out.replace(".jpg", ".mp4"))
        cid = insta.reel_container(mp4, "test")
        print("REELS TEST BAŞARILI (yayınlanmadı), kapsayıcı:", cid)
        return
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

    if vakit == "ikindi" and gun.weekday() == 6 and os.getenv("DERLEME", "1") == "1":   # Pazar: haftalık derleme
        yollar, cap = derleme(gun)
        print(f"--- {gun} {vakit} [derleme] ---\n{cap}\n---")
        if DRY_RUN:
            print("DRY_RUN=1 -> paylaşılmadı:", yollar)
            return
        if not insta.enabled():
            sys.exit(1)
        insta.publish_carousel(yollar, cap)
        hikaye(yollar[0], None)
    else:
        dua, tur, baslik, tags = sec(gun, vakit)
        out = os.path.join(brand.OUT_DIR, f"kart_{anahtar}.jpg")
        zemin = kart(gun, dua, tur, baslik, out, vakit)
        cap = caption(dua, tur, baslik, tags)
        print(f"--- {gun} {vakit} [{tur}] ---\n{cap}\n---")
        mp4 = None
        reels_vakit = os.getenv("REELS_VAKITLER", "sabah,aksam").split(",")
        if os.getenv("REELS", "1") == "1" and vakit in reels_vakit:   # 13:00 ve 17:00 normal fotoğraf
            try:
                mp4, _ = video.reel(out, zemin, out.replace(".jpg", ".mp4"))
            except Exception as e:
                print("[video] üretilemedi, görsel olarak paylaşılacak:", e)
        if DRY_RUN:
            print("DRY_RUN=1 -> paylaşılmadı. Kart:", out, "Video:", mp4)
            return
        if not insta.enabled():
            sys.exit(1)
        paylasildi = False
        if mp4:
            try:
                insta.publish_reel(mp4, cap)
                paylasildi = True
            except Exception as e:
                print("[insta] Reels başarısız, görsel gönderiye dönülüyor:", e)
        if not paylasildi:
            insta.publish_carousel([out], cap)
        hikaye(out, zemin)
    son = (hist.get("paylasilanlar", []) + [anahtar])[-30:]
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump({"paylasilanlar": son}, f)
    if vakit == "aksam":
        insta.refresh_token()


if __name__ == "__main__":
    main()
