"""Bilgi serisi kartları: açık krem zemin, kahve tonlar, sade düzen (Nunito)."""
import math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter as _IF
from brand import W, H, _wrap, HANDLE

NUNITO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Nunito.ttf")
KREM = (248, 241, 230)
KART = (255, 252, 247)
KAHVE = (74, 44, 24)        # başlık
METIN = (70, 54, 42)        # gövde
ALTIN = (168, 116, 52)      # vurgu
CIZGI = (226, 210, 186)

SERI = {   # seri: (etiket, vurgu rengi)
    "adab":      ("DUANIN ADABI",           (150, 98, 44)),
    "vakit":     ("KABUL VAKİTLERİ",        (60, 110, 120)),
    "esma":      ("ESMÂ-ÜL HÜSNÂ",           (128, 72, 104)),
    "peygamber": ("PEYGAMBERLERİN DUALARI", (140, 92, 40)),
    "teselli":   ("TESELLİ AYETLERİ",       (82, 86, 140)),
    "gunluk":    ("GÜNLÜK HAYAT DUALARI",   (92, 118, 60)),
}
_AG = {"black": "Black", "bold": "ExtraBold", "semibold": "Bold", "medium": "Medium", "regular": "Regular"}


def nf(stil, boyut):
    f = ImageFont.truetype(NUNITO, boyut)
    f.set_variation_by_name(_AG.get(stil, "Regular"))
    return f


def _orta(d, y, metin, f, renk):
    l, t, r, b = d.textbbox((0, 0), metin, font=f)
    d.text(((W - (r - l)) / 2 - l, y - t), metin, font=f, fill=renk)


def _sus(d, cy, yari, renk):
    """ince çizgi + ortada küçük dört halkalı süs"""
    d.line([(W / 2 - yari, cy), (W / 2 - 22, cy)], fill=renk, width=2)
    d.line([(W / 2 + 22, cy), (W / 2 + yari, cy)], fill=renk, width=2)
    for a in range(4):
        x = W / 2 + 9 * math.cos(a * math.pi / 2)
        y = cy + 9 * math.sin(a * math.pi / 2)
        d.ellipse([x - 6, y - 6, x + 6, y + 6], outline=renk, width=2)


def zemin(seri=None):
    img = Image.new("RGB", (W, H), KREM)
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).ellipse([-200, -300, W + 200, H * 0.75], fill=255)
    img = Image.composite(Image.new("RGB", (W, H), (252, 248, 240)), img, g.filter(_IF.GaussianBlur(160)))
    return img.convert("RGBA")


def _kutu(img, box, r=28):
    golge = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(golge).rounded_rectangle([box[0], box[1] + 6, box[2], box[3] + 6], radius=r, fill=(120, 90, 60, 40))
    img.alpha_composite(golge.filter(_IF.GaussianBlur(12)))
    ImageDraw.Draw(img, "RGBA").rounded_rectangle(box, radius=r, fill=KART, outline=CIZGI, width=2)


def _ust(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def _etiket(d, y, metin, renk):
    f = nf("bold", 30)
    tw = d.textlength(metin, font=f)
    bw, bh = int(tw + 64), 54
    x = (W - bw) // 2
    d.rounded_rectangle([x, y, x + bw, y + bh], radius=bh // 2, fill=renk)
    l, t, r, b = d.textbbox((0, 0), metin, font=f)
    d.text((x + 32, y + (bh - (b - t)) / 2 - t), metin, font=f, fill=(255, 250, 240))


def _alt(img, y):
    """KAYDET / GÖNDER çağrısı + hesap adı"""
    d = ImageDraw.Draw(img, "RGBA")
    d.line([(90, y), (W - 90, y)], fill=CIZGI, width=2)
    f1, f2 = nf("medium", 33), nf("black", 33)
    parcalar = [("Bu gönderiyi ", f1), ("KAYDET", f2), (", ihtiyacı olan birine ", f1), ("GÖNDER", f2)]
    tw = sum(d.textlength(t, font=f) for t, f in parcalar)
    x = (W - tw - 52) / 2
    yy = y + 40
    d.polygon([(x, yy), (x + 30, yy), (x + 30, yy + 40), (x + 15, yy + 29), (x, yy + 40)], fill=ALTIN)
    x += 52
    for t, f in parcalar:
        d.text((x, yy + 2), t, font=f, fill=KAHVE)
        x += d.textlength(t, font=f)
    _orta(d, yy + 64, "ve bu hayra vesile ol.", f1, KAHVE)
    _orta(d, H - 62, HANDLE, nf("bold", 30), ALTIN)


def kapak(path, post, n_kart):
    etiket, renk = SERI.get(post["seri"], SERI["adab"])
    img = zemin()
    d = ImageDraw.Draw(img, "RGBA")
    _etiket(d, 170, etiket, renk)
    _sus(d, 300, 200, ALTIN)
    ft = nf("black", 100)
    satir = _wrap(d, _ust(post["baslik"]), ft, W - 160)
    y = 620 - len(satir) * 116 // 2
    for ln in satir:
        _orta(d, y, ln, ft, KAHVE)
        y += 116
    _orta(d, y + 30, post.get("alt", ""), nf("medium", 46), METIN)
    _sus(d, y + 130, 260, ALTIN)
    bf = nf("bold", 36)
    lab = f"{n_kart} KART  ·  KAYDIR"
    bw, bh = int(d.textlength(lab, font=bf) + 150), 72
    bx, by = (W - bw) // 2, 1010
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=bh // 2, fill=renk)
    l, t, r, b = d.textbbox((0, 0), lab, font=bf)
    d.text((bx + 45, by + (bh - (b - t)) / 2 - t), lab, font=bf, fill=(255, 250, 240))
    ax, ay = bx + bw - 88, by + bh // 2
    d.line([(ax, ay), (ax + 32, ay)], fill=(255, 250, 240), width=5)
    d.polygon([(ax + 44, ay), (ax + 27, ay - 12), (ax + 27, ay + 12)], fill=(255, 250, 240))
    _orta(d, H - 62, HANDLE, nf("bold", 30), ALTIN)
    img.convert("RGB").save(path, "JPEG", quality=93)
    return path


def kart(path, post, i):
    k = post["kartlar"][i]
    n = len(post["kartlar"])
    etiket, renk = SERI.get(post["seri"], SERI["adab"])
    img = zemin()
    d = ImageDraw.Draw(img, "RGBA")
    _etiket(d, 80, f"{etiket}  ·  {i + 1}/{n}", renk)
    cy = 250
    d.ellipse([W // 2 - 50, cy - 50, W // 2 + 50, cy + 50], fill=renk)
    _orta(d, cy - 30, str(i + 1), nf("black", 60), (255, 250, 240))
    ft = nf("black", 66)
    y = cy + 80
    for ln in _wrap(d, k["baslik"], ft, W - 180):
        _orta(d, y, ln, ft, KAHVE)
        y += 78
    _sus(d, y + 24, 140, ALTIN)
    kutu = (70, y + 70, W - 70, 1070)
    _kutu(img, kutu)
    d = ImageDraw.Draw(img, "RGBA")
    ic_ust, ic_alt = kutu[1] + 50, kutu[3] - (110 if k.get("kaynak") else 50)
    for sz in range(50, 31, -2):
        mf = nf("medium", sz)
        satir = _wrap(d, k["metin"], mf, kutu[2] - kutu[0] - 100)
        lh = int(sz * 1.42)
        if len(satir) * lh <= ic_alt - ic_ust:
            break
    ty = ic_ust + (ic_alt - ic_ust - len(satir) * lh) // 2
    for ln in satir:
        _orta(d, ty, ln, mf, METIN)
        ty += lh
    if k.get("kaynak"):
        d.line([(W / 2 - 60, kutu[3] - 92), (W / 2 + 60, kutu[3] - 92)], fill=CIZGI, width=2)
        _orta(d, kutu[3] - 68, k["kaynak"], nf("semibold", 30), ALTIN)
    _alt(img, 1112)
    img.convert("RGB").save(path, "JPEG", quality=93)
    return path


def hepsi(post, klasor, on_ek="bilgi"):
    os.makedirs(klasor, exist_ok=True)
    yollar = [kapak(os.path.join(klasor, f"{on_ek}_0.jpg"), post, len(post["kartlar"]))]
    for i in range(len(post["kartlar"])):
        yollar.append(kart(os.path.join(klasor, f"{on_ek}_{i + 1}.jpg"), post, i))
    return yollar


def reel(post, klasor, out, muzik_bas=64):
    """Kapak + kartlar → müzikli dikey Reels (kart başına okuma süresi kadar)."""
    import video
    yollar = hepsi(post, klasor)
    zp = os.path.join(klasor, "bilgi_zemin_dikey.jpg")
    zemin().convert("RGB").resize((1536, 1920)).crop((228, 0, 1308, 1920)).save(zp, quality=90)
    sureler = [video.okuma_suresi(k["baslik"] + " " + k["metin"], 6.5, 12.0) for k in post["kartlar"]]
    video.ozet_reel(yollar, zp, out, giris_sure=3.5, sureler_kart=sureler, muzik_bas=muzik_bas)
    return yollar, out
