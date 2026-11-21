"""
Kabul Kapısı — yorumlara otomatik dua cevabı

Yorumu okur, kimin için (annem, kardeşim, Ahmet...) ve ne için (şifa, borç, sınav...)
dua istendiğini anahtar kelimelerle bulur, ona uygun bir dua cevabı yazar.
Ücretsiz: yapay zekâ API'si kullanmaz.
"""
import random
import re
from datetime import datetime, timedelta, timezone

import insta

HESAP = "kabulkapisi"
EN_FAZLA = 8           # bir çalışmada en fazla cevap (otomasyon işareti almamak için düşük)
BEKLE = (20, 60)       # cevaplar arası rastgele bekleme (sn)
GUN = 7                # son kaç günün gönderilerine bakılır

# ---------------------------------------------------------------- Türkçe ekler
ARKA = set("aıou")
ON = set("eiöü")
UNLU = ARKA | ON


def _son_unlu(w):
    for c in reversed(w.lower()):
        if c in UNLU:
            return c
    return "e"


def yonelme(kelime, ozel_isim=False):
    """'annen' -> 'annene', 'Ahmet' -> 'Ahmet'e', 'Ayşe' -> 'Ayşe'ye'"""
    u = _son_unlu(kelime)
    ek = "a" if u in ARKA else "e"
    kesme = "'" if ozel_isim else ""
    if kelime[-1].lower() in UNLU:
        return f"{kelime}{kesme}y{ek}"
    return f"{kelime}{kesme}{ek}"


# ------------------------------------------------------------ kim için?
YAKINLAR = ["annem", "babam", "anneannem", "babaannem", "dedem", "ninem", "eşim", "hanımım", "kocam",
            "beyim", "oğlum", "kızım", "çocuğum", "çocuklarım", "evladım", "evlatlarım", "kardeşim",
            "kardeşlerim", "ablam", "abim", "ağabeyim", "teyzem", "halam", "amcam", "dayım", "yeğenim",
            "torunum", "torunlarım", "nişanlım", "arkadaşım", "ailem", "kayınvalidem", "kayınpederim",
            "gelinim", "damadım", "komşum", "hocam", "anne babam", "annemle babam"]
KESIN_DEGIL = {"Allah", "Rabbim", "Rabbimiz", "Amin", "Âmin", "Kabul", "Kapısı", "Lütfen", "Bu", "Ben",
               "Benim", "Bizim", "Hepimiz", "Inşallah", "İnşallah", "Selam", "Selamün", "Hayırlı", "Cuma"}


EKLER = r"(?:e|a|ye|ya|i|ı|u|ü|in|ın|un|ün|le|la|den|dan|de|da|çün|cun)?"


def hedef_bul(metin):
    """(ad, yonelme_hali) döndürür. Bulamazsa ('sen', 'sana').
    'annem', 'anneme', 'Ercan kardeşime', 'Ahmet için' gibi kalıpları tanır."""
    t = metin.lower()
    for y in sorted(YAKINLAR, key=len, reverse=True):
        m = re.search(rf"\b{y}{EKLER}\b", t)
        if m:
            if y in ("anne babam", "annemle babam"):
                return "anne baban", "anne babana"
            iyelik = y[:-1] + "n"          # annem -> annen, kızım -> kızın
            # önünde isim var mı? "Ercan kardeşime" -> "Ercan kardeşin"
            once = metin[:m.start()].split()
            if once:
                isim = once[-1].strip(",.!?")
                if isim[:1].isupper() and isim not in KESIN_DEGIL and len(isim) > 2:
                    iyelik = f"{isim} {iyelik}"
            return iyelik, yonelme(iyelik)
    m = re.search(r"([A-ZÇĞİÖŞÜ][a-zçğıöşü]{2,})(?:\s+[a-zçğıöşü]+)?\s+için", metin)
    if m and m.group(1) not in KESIN_DEGIL:
        ad = m.group(1)
        return ad, yonelme(ad, ozel_isim=True)
    return "sen", "sana"


# ------------------------------------------------------------ ne için?
KONULAR = [
    ("vefat", ["vefat", "rahmetli", "kaybettim", "kaybettik", "öldü", "ahirete", "mekanı", "mekânı", "cenaze", "kabir"]),
    ("sifa", ["hasta", "şifa", "sifa", "ameliyat", "kanser", "tedavi", "yoğun bakım", "hastane", "ağrı", "kemoterapi",
              "tahlil", "rahatsız", "doğum", "kalp", "beyin", "felç", "sağlık"]),
    ("borc", ["borç", "borc", "kredi", "kira", "icra", "haciz", "maddi", "para", "geçim", "rızk", "rizk", "darlık"]),
    ("sinav", ["sınav", "sinav", "yks", "lgs", "kpss", "ales", "okul", "üniversite", "ders", "tez", "mülakat"]),
    ("is", ["iş ", "işsiz", "is bul", "iş bul", "işe gir", "işimiz", "terfi", "atama", "kadro", "dükkan", "esnaf"]),
    ("kismet", ["kısmet", "kismet", "evlilik", "evlen", "hayırlı eş", "nasip", "yuva kur", "düğün"]),
    ("evlat", ["evlat", "bebek", "hamile", "çocuk sahibi", "çocuğumuz olsun", "tüp bebek"]),
    ("huzur", ["huzur", "sıkıntı", "sikinti", "dert", "üzgün", "bunalım", "depresyon", "stres", "kaygı", "korku",
               "yalnız", "mutsuz", "ağlıyorum", "zor günler"]),
    ("hidayet", ["hidayet", "namaz", "yoldan çıktı", "kötü arkadaş", "bağımlı", "kumar", "alkol"]),
    ("yol", ["yolculuk", "askere", "asker", "gurbet", "yurt dışı", "yolda"]),
]

DUALAR = {
    "vefat": ["Allah rahmet eylesin, mekânı cennet olsun. {k_b} sabır ve metanet versin Rabbim 🤲",
              "Rabbim rahmetiyle muamele etsin, kabrini nurla doldursun. Başınız sağ olsun 🤲",
              "Allah rahmet eylesin, mekânı cennet, makamı âli olsun. Âmin 🤲"],
    "sifa": ["Âmin, Rabbim {k_y} acil şifalar versin, her ağrısını dindirsin 🤲",
             "Rabbim {k_y} şifa versin, tedavisini kolaylaştırsın, sağlıkla kavuştursun inşallah 🤲",
             "Âmin. Şifayı veren Rabbim {k_y} öyle bir şifa versin ki geride hiçbir hastalık bırakmasın 🤲"],
    "borc": ["Âmin, Rabbim {k_y} kimseye muhtaç etmeden borçlarını ödemeyi nasip etsin 🤲",
             "Rabbim {k_y} helalinden bol rızık versin, bütün borçlarını kolaylıkla kapattırsın 🤲",
             "Âmin. Rabbim darlığı genişliğe çevirsin, {k_y} beklemediği yerden rızık versin 🤲"],
    "sinav": ["Âmin, Rabbim {k_y} zihin açıklığı versin, emeğinin karşılığını en güzel şekilde alsın 🤲",
              "Rabbim {k_y} hayırlı bir başarı nasip etsin, kalbine sükûnet versin inşallah 🤲",
              "Âmin. Rabbim {k_y} sınavında kolaylık, sonucunda sevinç nasip etsin 🤲"],
    "is": ["Âmin, Rabbim {k_y} hayırlı, helal ve bereketli bir iş nasip etsin 🤲",
           "Rabbim {k_y} hayırlı kapılar açsın, emeğini bereketlendirsin inşallah 🤲",
           "Âmin. Rabbim {k_y} kimseye muhtaç etmeyecek hayırlı bir rızık kapısı açsın 🤲"],
    "kismet": ["Âmin, Rabbim {k_y} dinine ve gönlüne uygun hayırlı bir kısmet nasip etsin 🤲",
               "Rabbim {k_y} huzurlu ve mutlu bir yuva nasip etsin inşallah 🤲",
               "Âmin. Rabbim hayırlısıyla karşılaştırsın, kuracağı yuvayı mübarek kılsın 🤲"],
    "evlat": ["Âmin, Rabbim {k_y} hayırlı ve salih bir evlat nasip etsin 🤲",
              "Rabbim {k_y} gözünü aydınlatacak sağlıklı bir evlat versin inşallah 🤲",
              "Âmin. Rabbim kucağını hayırlı bir evlatla doldursun 🤲"],
    "huzur": ["Âmin, Rabbim {k_y} gönül ferahlığı versin, bütün dertlerini kolaylaştırsın 🤲",
              "Rabbim {k_n} kalbindeki yükü kaldırsın, yerine huzur ve sevinç koysun 🤲",
              "Âmin. Rabbim {k_y} öyle bir ferahlık versin ki bu günleri şükürle ansın 🤲"],
    "hidayet": ["Âmin, Rabbim {k_y} hidayet versin, kalbini iyiliğe ve hayra yöneltsin 🤲",
                "Rabbim {k_n} kalbini yumuşatsın, onu doğru yoldan ayırmasın inşallah 🤲",
                "Âmin. Rabbim {k_y} hayırlı arkadaşlar ve hayırlı bir yol nasip etsin 🤲"],
    "yol": ["Âmin, Rabbim {k_y} selamet versin, sağ salim sevdiklerine kavuştursun 🤲",
            "Rabbim yolunu açık etsin, her türlü kazadan beladan muhafaza etsin 🤲",
            "Âmin. Rabbim {k_y} hayırlı yolculuklar nasip etsin, hayırla döndürsün 🤲"],
    "genel": ["Âmin, Rabbim {k_y} gönlünden geçen bütün hayırlı dilekleri nasip etsin 🤲",
              "Rabbim {k_y} hayırlısını versin, dualarını kabul etsin inşallah 🤲",
              "Âmin. Rabbim {k_y} sağlık, huzur ve bereket versin 🤲",
              "Rabbim dualarını kabul etsin, {k_y} hayırlı kapılar açsın 🤲"],
    "amin": ["Âmin 🤲 Rabbim kabul etsin.", "Ecmain, Rabbim kabul etsin 🤲", "Âmin, Rabbim cümlemizin dualarını kabul etsin 💛",
             "Âmin âmin âmin 🤲", "Rabbim senin dualarını da kabul etsin 🤲", "Âmin, dualarda buluşmak dileğiyle 🤍",
             "Rabbim âmin diyen dilleri mahrum bırakmasın 🌿", "Âmin, Allah razı olsun 💛", "Ecmain 🤲 hayırlı günler",
             "Âmin, Rabbim gönlündeki hayırlı her muradı versin 🤍"],
}

# beddua, hakaret, reklam: cevap verilmez
ATLA = ["beddua", "lanet", "kahrolsun", "geberesi", "ölsün", "belasını", "http", "www.", "takip et", "dm at",
        "kazan", "bonus", "bahis", "kripto"]
REKLAM = re.compile(r"\bdm\b|\bdm[' ]?(ye|e|den)\b|mesaj att|istek kutu|isteklere|isteğe bak|bakar ?m[ıi]s[ıi]n[ıi]z|"
                    r"profilime|profilimize|sayfama|bio|link|takipleş|takip ederseniz|gt\b|karşılıklı", re.I)
SIKCA_AMIN = re.compile(r"^\W*(amin|âmin|amiin|amin+|ecmain|allah kabul etsin|inşallah|insallah)\W*$", re.I)


def konu_bul(metin):
    t = " " + metin.lower() + " "
    for konu, kelimeler in KONULAR:
        if any(k in t for k in kelimeler):
            return konu
    return None


def cevap_yaz(metin, seed=None):
    r = random.Random(seed)
    t = metin.lower()
    if any(a in t for a in ATLA) or REKLAM.search(metin):
        return None
    if SIKCA_AMIN.match(metin.strip()):
        return r.choice(DUALAR["amin"])
    konu = konu_bul(metin)
    istek = any(k in t for k in ["dua", "için", "icin", "inşallah", "rabbim", "allah"])
    if not konu and not istek:
        # dua isteği olmayan sıradan yorum: kısa teşekkür
        return r.choice(["Rabbim razı olsun 💛", "Allah razı olsun, dualarda buluşalım 🤲", "Teşekkürler, Rabbim kabul etsin 🤲",
                         "Çok teşekkür ederiz, hayırlı günler 🌿", "Allah razı olsun, selam ve dua ile 🤍",
                         "Güzel sözlerin için teşekkürler, Rabbim seni de hayırla ansın 💛"])
    ad, ad_y = hedef_bul(metin)
    sablon = r.choice(DUALAR[konu or "genel"])
    k_n = "senin" if ad == "sen" else ad + ("'in" if ad[0].isupper() else "in")
    if ad[0].isupper() and " " not in ad:   # özel isim: Ahmet'in
        u = _son_unlu(ad)
        ek = {"a": "ın", "ı": "ın", "o": "un", "u": "un", "e": "in", "i": "in", "ö": "ün", "ü": "ün"}[u]
        k_n = f"{ad}'{'n' if ad[-1].lower() in UNLU else ''}{ek}"
    elif ad != "sen":     # annen -> annenin
        u = _son_unlu(ad)
        k_n = ad + {"a": "ın", "ı": "ın", "o": "un", "u": "un", "e": "in", "i": "in", "ö": "ün", "ü": "ün"}[u]
    k_b = "Ailesine" if ad == "sen" else "Sana ve ailene"
    metin_c = sablon.format(k_y=ad_y, k_n=k_n, k_b=k_b)
    metin_c = metin_c.replace(" 🤲", " " + r.choice(["🤲", "🤲", "🤍", "💛", "🌿", "🤲🏻"]))
    if konu != "vefat" and r.random() < 0.3:
        metin_c += r.choice([" Selam ve dua ile.", " Hayırlı günler.", " Dualarımızdasın."])
    return metin_c[0].upper() + metin_c[1:]


# ------------------------------------------------------------ Instagram
def _get(path, **params):
    params["access_token"] = insta.IG_TOKEN
    r = insta.requests.get(f"{insta.API}/{path}", params=params, timeout=30)
    return insta._check(r, path)


def calistir(dry_run=False):
    import os, time
    dk = datetime.now(timezone.utc).minute
    if not dry_run and os.getenv("YORUM_HER_TUR", "0") != "1" and 15 <= dk < 45:
        print("[yorum] yarım saat turu atlandı (saatte bir kontrol ediliyor)")
        return 0
    uid = insta._user_id()
    sinir = datetime.now(timezone.utc) - timedelta(days=GUN)
    medya = _get(f"{uid}/media", fields="id,timestamp,comments_count", limit=25).get("data", [])
    cevaplanan = 0
    for m in medya:
        ts = datetime.strptime(m["timestamp"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
        if ts < sinir or not m.get("comments_count"):
            continue
        yorumlar = _get(f"{m['id']}/comments", fields="id,text,username,timestamp,replies{username}", limit=50).get("data", [])
        for y in yorumlar:
            if cevaplanan >= EN_FAZLA:
                print(f"[yorum] sınır ({EN_FAZLA}) doldu, kalanlar sonraki çalışmada")
                return cevaplanan
            if (y.get("username") or "").lower() == HESAP:
                continue
            cevaplar = (y.get("replies") or {}).get("data", [])
            if any((c.get("username") or "").lower() == HESAP for c in cevaplar):
                continue
            metin = y.get("text") or ""
            cevap = cevap_yaz(metin, seed=y["id"])
            if not cevap:
                print(f"[yorum] atlandı: {metin[:60]!r}")
                continue
            print(f"[yorum] @{y.get('username')}: {metin[:70]!r}\n        -> {cevap}")
            if not dry_run:
                if cevaplanan:
                    time.sleep(random.uniform(*BEKLE))   # insan hızında
                r = insta.requests.post(f"{insta.API}/{y['id']}/replies", timeout=30,
                                        data={"message": cevap, "access_token": insta.IG_TOKEN})
                insta._check(r, "yorum cevabı")
            cevaplanan += 1
    print(f"[yorum] {cevaplanan} yoruma cevap {'hazırlandı (DRY_RUN)' if dry_run else 'verildi'}")
    return cevaplanan


if __name__ == "__main__":
    ornekler = ["Annem için dua edin, yarın ameliyat olacak", "Amin", "Ahmet için dua eder misiniz, borç içinde",
                "Kızım YKS'ye girecek dua edin", "Ayşe için şifa duası lütfen", "Babamı geçen hafta kaybettim",
                "Hayırlı bir kısmet için dua edin", "Çok güzel paylaşım", "Benim için dua edin çok sıkıntıdayım",
                "Oğlum askere gidiyor", "Eşimle evlat bekliyoruz dua edin", "Kardeşim kötü arkadaşlara takıldı",
                "Allah kabul etsin", "Mehmet için dua edin işsiz kaldı", "Merhaba Dm bakabilirmisiniz",
                "isteklere bakar mısınız", "Dm ye bakar mısınız 🌺",
                "Ercan kardeşime dua et, bol para lazımmış", "Anneme şifa duası", "oğlumun sınavı var"]
    for o in ornekler:
        print(f"{o}\n   -> {cevap_yaz(o, seed=o)}")
