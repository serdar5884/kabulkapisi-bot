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
import os, re
import sys
from datetime import date, datetime, timedelta, timezone

import animasyon
import brand
import insta
import video

HERE = os.path.dirname(os.path.abspath(__file__))
TR_TZ = timezone(timedelta(hours=3))
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"
ZORLA = os.getenv("ZORLA", "0") == "1"
# elle paylaşılacak vakitler (bot bu vakitleri atlar): "YYYY-AA-GG_vakit"
ELLE = {"2026-11-22_ozet"}   # elle paylaşılacak "YYYY-AA-GG_vakit" anahtarları (bot bunları atlar)
ELLE_VAKITLER = set(filter(None, os.getenv("ELLE_VAKITLER", "aksam").split(",")))   # her gün elle paylaşılan vakitler (21:00 şablonlu Reels)
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


def _tanri_yok(dua):
    """Hiçbir duada 'tanrı' kelimesi geçmesin (Allah / ilah kullanılır)."""
    if isinstance(dua, dict) and dua.get("metin"):
        m = re.sub(r"\b[Tt]anrı", "ilah", dua["metin"])
        if m != dua["metin"]:
            dua = dict(dua, metin=m)
    return dua


def sec(gun, vakit):
    r = _sec(gun, vakit)
    return (_tanri_yok(r[0]),) + tuple(r[1:])


def _sec(gun, vakit):
    """Günün ve vaktin duasını döndürür: (dua, tur, baslik, etiketler)."""
    kandil = DB.get("kandil_tarihleri", {}).get(gun.isoformat())
    if vakit == "aksam" and kandil and kandil in DB["kandil"]:
        k = DB["kandil"][kandil]
        return k, "kandil", k["baslik"], [KANDIL_TAG.get(kandil, "#kandil"), "#kandilmesajları"]
    gecen = (gun - BASLANGIC).days
    if vakit == "sabah" and gun.weekday() == 4:   # Cuma sabahı
        cuma = DB["cuma"]
        return cuma[(gecen // 7) % len(cuma)], "cuma", "Hayırlı Cumalar", ["#hayırlıcumalar", "#cumamesajları"]
    zit = {"sabah": ("aksam",), "ikindi": ("sabah", "aksam"), "aksam": ("sabah",), "ogle": ("sabah", "aksam")}.get(vakit, ())
    havuz_adi = VAKIT_HAVUZ[vakit]
    if vakit in ("ogle", "aksam"):   # gün aşırı yer değiştirir: çift gün öğle Kur'an/akşam hadis, tek gün tersi
        havuz_adi = ("kuran", "hadis")[(gecen + (vakit == "aksam")) % 2]
    if havuz_adi in ("kuran", "hadis"):   # sıra her gün bir ilerler; öğleye akşam duası düşerse sonrakine geç
        liste = DB[havuz_adi]
        i = gecen % len(liste)
        while liste[i].get("vakit") in zit:
            i = (i + 1) % len(liste)
        dua = liste[i]
        havuz = None
    else:
        havuz = [e for e in DB[havuz_adi] if e.get("vakit") not in zit]
    if havuz is None:
        pass
    elif havuz_adi == "ozel":   # günde 2 özel dua: sabah çift, ikindi tek sıradaki
        dua = havuz[(gecen * 2 + (1 if vakit == "ikindi" else 0)) % len(havuz)]
    else:
        dua = havuz[gecen % len(havuz)]
    tema_tag = {"borç": ["#borçduası"], "hasta": ["#şifaduası"], "dert": ["#sıkıntıduası"],
                "çocuk": ["#evlatduası"], "aile": ["#aileduası"]}.get(dua.get("tema"), [])
    vtag = VAKIT_TAG[vakit]
    baslik = VAKIT_BASLIK[vakit]
    if havuz_adi == "kuran":
        vtag, baslik = ["#kuran", "#ayet"], "Kur'an'dan Bir Dua"
    elif havuz_adi == "hadis":
        vtag = (["#hadis"] if dua.get("tur") == "hadis" else ["#duaistegi"]) + (["#akşamduası"] if vakit == "aksam" else [])
        baslik = "Hadislerden Bir Dua" if dua.get("tur") == "hadis" else VAKIT_BASLIK["sabah"]
    tur = havuz_adi if havuz_adi in ("kuran", "hadis") else vakit
    return dua, tur, baslik, tema_tag + vtag + ["#amin"]


def caption(dua, tur, baslik, tags):
    acilis = {"sabah": "🌅 Hayırlı sabahlar, bu satırları okuyan sana bir dua var",
              "ikindi": "🤲 Bu satırları okuyan sana bir dua var",
              "ogle": "📖 Kur'an-ı Kerim'den bir dua, bu satırları okuyan herkes için",
              "aksam": "🌙 Hayırlı akşamlar, bu satırları okuyan sana bir dua var",
              "kuran": "📖 Kur'an-ı Kerim'den bir dua, bu satırları okuyan herkes için",
              "hadis": "🤲 Peygamber Efendimizin dualarından biri, bu satırları okuyan sana",
              "cuma": "🕌 Hayırlı Cumalar",
              "kandil": f"✨ {baslik} mübarek olsun"}[tur]
    if tur == "hadis" and dua.get("tur") != "hadis":
        acilis = "🤲 Bu satırları okuyan sana bir dua var"
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


BILGI_BASLANGIC = date(2026, 11, 20)
BILGI_TAG = {"adab": ["#duanınadabı", "#dua"], "vakit": ["#duavakitleri", "#dua"], "esma": ["#esmaülhüsna", "#esma"],
             "peygamber": ["#peygamberlerinduaları", "#dua"], "teselli": ["#ayet", "#teselli"],
             "gunluk": ["#günlükdualar", "#dua"]}


def bilgi(gun):
    """17:00 bilgi gönderisi: kaynaklı seri (adab, esmâ, peygamberler, teselli, vakitler, günlük dualar)."""
    import bilgi_kart
    with open(os.path.join(HERE, "bilgi.json"), encoding="utf-8") as f:
        posts = json.load(f)
    post = posts[(gun - BILGI_BASLANGIC).days % len(posts)]
    klasor = os.path.join(brand.OUT_DIR, f"bilgi_{gun}")
    yollar = bilgi_kart.hepsi(post, klasor)
    mp4 = None
    if os.getenv("REELS", "1") == "1":
        try:
            _, mp4 = bilgi_kart.reel(post, klasor, os.path.join(klasor, "bilgi.mp4"))
        except Exception as e:
            print("[bilgi] Reels üretilemedi:", e)
    kaynaklar = []
    for k in post["kartlar"]:
        if k.get("kaynak") and k["kaynak"] not in kaynaklar:
            kaynaklar.append(k["kaynak"])
    tags = ["#kabulkapisi"] + BILGI_TAG.get(post["seri"], ["#dua"]) + ["#amin"]
    parcalar = [f"📚 {post['baslik']}", post.get("ozet", "")]
    if kaynaklar:
        parcalar.append("📖 Kaynaklar:\n" + "\n".join("• " + k for k in kaynaklar))
    parcalar += ["Kaydet, dua ederken hatırla 🤲\nİhtiyacı olan birine gönder 👇", " ".join(tags[:5])]
    return yollar, mp4, "\n\n".join(p for p in parcalar if p)


def liste_gonderi(gun, secim=None):
    """Liste Reels'i: merak kapağı + tek uzun kaynaklı liste görseli. secim: başlıktan bir parça."""
    import liste_kart
    with open(os.path.join(HERE, "listeler.json"), encoding="utf-8") as f:
        posts = json.load(f)
    p = posts[(gun - BILGI_BASLANGIC).days % len(posts)]
    if secim:
        uy = [x for x in posts if secim.lower() in x["baslik"].lower()]
        if not uy:
            raise SystemExit(f"Liste bulunamadı: {secim}")
        p = uy[0]
    k = os.path.join(brand.OUT_DIR, f"liste_{gun}")
    os.makedirs(k, exist_ok=True)
    lst = liste_kart.liste(os.path.join(k, "liste.jpg"), p["ust"], p["baslik"], p["maddeler"], p.get("dipnot"))
    kap = liste_kart.kapak(os.path.join(k, "kapak.jpg"), p["ust"], p["kapak"], p.get("soru", "Hangileri?"))
    mp4 = liste_kart.reel(lst, kap, os.path.join(k, "liste.mp4"), muzik_bas=[47, 64, 86, 99][gun.toordinal() % 4])
    tags = list(dict.fromkeys(["#kabulkapisi"] + p.get("etiket", []) + ["#dua", "#amin"]))[:5]
    cap = "\n\n".join([p["acilis"], "Yetişemediysen durdurup oku 👆\n📌 Kaydet, ihtiyacı olana gönder. Kaynaklar görselde.", p["yorum"], " ".join(tags)])
    return kap, lst, mp4, cap


def hikaye(kart_path, zemin):
    if os.getenv("STORY", "1") != "1":
        return
    try:
        dikey = video.dikey_kare(kart_path, zemin, kart_path.replace(".jpg", "_story.jpg"))
        insta.publish_story(dikey)
    except Exception as e:
        print("[insta] hikâye paylaşılamadı (gönderi yine de yayında):", e)


def gunun_ozeti():
    """Akşam: o gün paylaşılan duaların hepsi tek Reels'te (22:30)."""
    gun = bugun()
    anahtar = f"{gun.isoformat()}_ozet"
    hist = gecmis_oku()
    if anahtar in hist.get("paylasilanlar", []) and not DRY_RUN and not ZORLA:
        print("Bugünün özeti zaten paylaşıldı."); return
    ozet_vakit = [v for v in VAKITLER if not (v == "ikindi" and (os.getenv("BILGI", "0") == "1" or os.getenv("LISTE", "0") == "1"))]
    zs = brand.zeminler()
    tarih = f"{gun.day} {brand.AYLAR[gun.month - 1]} {gun.year}"
    kapak = brand.make_cover(os.path.join(brand.OUT_DIR, f"ozet_{gun}_0.jpg"), "Günün Duaları",
                             "Sabah · Öğle · İkindi · Akşam", zs[(gun - BASLANGIC).days % len(zs)], buton=f"{len(ozet_vakit)} DUA BİR ARADA", ok=False)
    kartlar, ozet_satir, sureler = [kapak], [], []
    simge = {"sabah": "🌅", "ogle": "📖", "ikindi": "🤲", "aksam": "🌙"}
    gun_tag = []
    for i, v in enumerate(ozet_vakit, 1):
        dua, tur, baslik, tags = sec(gun, v)
        gun_tag.extend(t for t in tags if t in ("#borçduası", "#şifaduası", "#sıkıntıduası", "#evlatduası", "#aileduası"))
        p = os.path.join(brand.OUT_DIR, f"ozet_{gun}_{i}.jpg")
        kart(gun, dua, tur, baslik, p, v)
        kartlar.append(p)
        sureler.append(video.okuma_suresi(dua["metin"]))
        ozet_satir.append(f"{simge[v]} {dua['metin'][:60].rsplit(' ', 1)[0]}…")
    mp4 = video.ozet_reel(kartlar, zs[0], os.path.join(brand.OUT_DIR, f"ozet_{gun}.mp4"), sureler_kart=sureler)
    print("[özet] kart süreleri (sn):", sureler)
    cap = "\n\n".join(["🌙 Günün duaları bir arada", "\n".join(ozet_satir),
                        "Gün içinde kaçırdıysan hepsini tek videoda izle. Hangisine âmin dersin? 🤲",
                        "Duaya ihtiyacı olan birini etiketle 👇",
                        " ".join(list(dict.fromkeys(["#kabulkapisi", "#borçduası", "#şifaduası"] + gun_tag +
                                                    ["#gününduaları", "#dua"]))[:5])])
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
        if f"{bugun().isoformat()}_ozet" in ELLE and not ZORLA:
            print("Bugünün özeti atlanıyor (ELLE).")
            return
        return gunun_ozeti()
    if MODE == "dua_reel":   # yeni dua Reels formatını tek bir duayla dener (LISTE_SEC: tema, örn. borç)
        import dua_reel
        with open(os.path.join(HERE, "dualar.json"), encoding="utf-8") as f:
            havuz = json.load(f)
        tema = os.getenv("LISTE_SEC", "").strip() or "borç"
        aday = [("hadis", e) for e in havuz["hadis"] if e.get("tema") == tema] + \
               [("ozel", e) for e in havuz["ozel"] if e.get("tema") == tema]
        tur, dua = aday[0]
        gun = bugun()
        zs = brand.zeminler()
        k = os.path.join(brand.OUT_DIR, f"dua_reel_{gun}")
        konu, _, sayfa, kap = dua_reel.hazirla(dua, tur, zs[gun.toordinal() % len(zs)], k,
                                              date=datetime(gun.year, gun.month, gun.day))
        mp4 = dua_reel.reel(sayfa, os.path.join(k, "dua.mp4"))
        tags = {"borç": "#borçduası", "hasta": "#şifaduası", "dert": "#sıkıntıduası",
                "çocuk": "#evlatduası", "aile": "#aileduası"}.get(tema, "#dua")
        cap = (f"🤲 {konu}\n\n{dua['metin']}\n\n📖 {dua.get('kaynak', '')}\n\n"
               "Âmin yazmayı unutma 🤲\nDuaya ihtiyacı olan birini etiketle 👇\n\n"
               f"#kabulkapisi #dua {tags} #amin #duaistegi")
        print(f"--- dua_reel ---\n{cap}\n---")
        if DRY_RUN:
            print("DRY_RUN=1 -> paylaşılmadı:", mp4); return
        if not insta.enabled():
            sys.exit(1)
        insta.publish_reel(mp4, cap, kap)
        return
    if MODE == "liste":   # tek bir listeyi elle Reels olarak paylaş (LISTE_SEC: başlıktan parça)
        kap, lst, mp4, cap = liste_gonderi(bugun(), os.getenv("LISTE_SEC", "").strip())
        print(f"--- liste ---\n{cap}\n---")
        if DRY_RUN:
            print("DRY_RUN=1 -> paylaşılmadı:", mp4); return
        if not insta.enabled():
            sys.exit(1)
        insta.publish_reel(mp4, cap, kap)
        return
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
    if (anahtar in ELLE or vakit in ELLE_VAKITLER) and not ZORLA:
        print(f"{anahtar} elle paylaşılacak, bot atlıyor.")
        return
    hist = gecmis_oku()
    if anahtar in hist.get("paylasilanlar", []) and not DRY_RUN and not ZORLA:
        print(f"{gun} {vakit} paylaşımı zaten yapıldı, tekrar paylaşılmıyor.")
        return

    if vakit == "ikindi" and os.getenv("LISTE", "0") == "1" and os.path.exists(os.path.join(HERE, "listeler.json")):
        kap, lst, mp4, cap = liste_gonderi(gun)   # 17:00: kapak + liste Reels'i
        print(f"--- {gun} {vakit} [liste] ---\n{cap}\n---")
        if DRY_RUN:
            print("DRY_RUN=1 -> paylaşılmadı:", mp4)
            return
        if not insta.enabled():
            sys.exit(1)
        insta.publish_reel(mp4, cap, kap)
        if os.getenv("STORY", "1") == "1":
            try:
                insta.publish_story(lst)   # liste zaten 9:16
            except Exception as e:
                print("[insta] hikâye paylaşılamadı:", e)
    elif vakit == "ikindi" and os.getenv("BILGI", "0") == "1":   # 17:00: bilgi gönderisi (carousel + Reels)
        yollar, mp4, cap = bilgi(gun)
        print(f"--- {gun} {vakit} [bilgi] ---\n{cap}\n---")
        if DRY_RUN:
            print("DRY_RUN=1 -> paylaşılmadı:", yollar, mp4)
            return
        if not insta.enabled():
            sys.exit(1)
        insta.publish_carousel(yollar, cap)
        if mp4:
            try:
                insta.publish_reel(mp4, cap, yollar[0])
            except Exception as e:
                print("[insta] bilgi Reels'i paylaşılamadı (carousel yayında):", e)
        hikaye(yollar[0], None)
    elif vakit == "ikindi" and gun.weekday() == 6 and os.getenv("DERLEME", "1") == "1":   # Pazar: haftalık derleme
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
        reels_vakit = os.getenv("REELS_VAKITLER", "sabah,ogle,ikindi,aksam").split(",")
        kapak_reel = out
        if os.getenv("REELS", "1") == "1" and vakit in reels_vakit and os.getenv("DUA_REEL", "1") == "1":
            try:   # konu kapağı (ızgara) + hareketli kart, üstte konu başlığı
                import dua_reel
                yap = dua_reel.hareketli if os.getenv("ANIMASYON", "0") == "1" else dua_reel.sabit
                konu, kapak_reel, mp4, _ = yap(dua, tur, zemin, out.replace(".jpg", "_reel"),
                                              out.replace(".jpg", ".mp4"), vakit=vakit,
                                              date=datetime(gun.year, gun.month, gun.day),
                                              muzik_bas=[47, 15, 64, 33, 86, 75, 99, 110][(gun.toordinal() + VAKITLER.index(vakit)) % 8])
                cap = f"🤲 {konu}\n\n" + cap
            except Exception as e:
                print("[dua_reel] olmadı, eski hareketli karta dönülüyor:", e)
                kapak_reel, mp4 = out, None
        if not mp4 and os.getenv("REELS", "1") == "1" and vakit in reels_vakit:   # 13:00 ve 17:00 normal fotoğraf
            try:
                try:   # hareketli kart (arşiv/yedek): arka plan -> panel -> yazılar soluktan nete -> parlayan buton
                    mp4, _ = animasyon.hareketli_reel(dua["metin"], zemin, out.replace(".jpg", ".mp4"),
                                                      kaynak=dua.get("kaynak"), date=datetime(gun.year, gun.month, gun.day),
                                                      ses_anahtar=os.path.basename(out))
                except Exception as e:
                    print("[animasyon] olmadı, sade video:", e)
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
                insta.publish_reel(mp4, cap, kapak_reel)   # ızgara kapağı
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
