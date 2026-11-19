"""Bilgi serisi kartları: dua kartlarından ayrı, desenli renkli zemin."""
import math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter as _IF
from brand import (W, H, font, _wrap, _center, _gold_text, _ornament, cta_katmanlari,
                   GOLD, GOLD_HI, HANDLE)

CREAM = (250, 244, 230)
NUNITO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Nunito.ttf")
_AG = {"bold": "Black", "semibold": "ExtraBold", "medium": "Medium", "italic": "SemiBold"}
_OLC = {"bold": 0.86, "semibold": 0.9, "medium": 0.88, "italic": 0.86}


def nf(stil, boyut):
    """Bilgi kartları: NeHaberÖzet / Bugün Hava Nasıl ile aynı Nunito yazı tipi."""
    try:
        f = ImageFont.truetype(NUNITO, int(boyut * _OLC.get(stil, 0.9)))
        f.set_variation_by_name(_AG.get(stil, "Regular"))
        return f
    except Exception:
        return font(stil, boyut)

SERI = {   # seri: (etiket, koyu renk, açık renk)
    "adab":      ("DUANIN ADABI",          (10, 58, 46),  (24, 96, 76)),
    "vakit":     ("KABUL VAKİTLERİ",       (8, 48, 62),   (20, 86, 104)),
    "esma":      ("ESMÂ-ÜL HÜSNÂ",          (48, 18, 44),  (92, 38, 80)),
    "peygamber": ("PEYGAMBERLERİN DUALARI", (52, 34, 18),  (96, 64, 34)),
    "teselli":   ("TESELLİ AYETLERİ",      (28, 24, 60),  (56, 48, 110)),
    "gunluk":    ("GÜNLÜK HAYAT DUALARI",  (36, 46, 22),  (70, 86, 42)),
}


def _yildiz(d, cx, cy, r, renk, w=2):
    """8 köşeli yıldız (iki iç içe kare)."""
    for a0 in (0, math.pi / 4):
        pts = [(cx + r * math.cos(a0 + k * math.pi / 2), cy + r * math.sin(a0 + k * math.pi / 2)) for k in range(4)]
        d.polygon(pts, outline=renk, width=w)


def zemin(seri):
    _, koyu, acik = SERI.get(seri, SERI["adab"])
    img = Image.new("RGB", (W, H), koyu)
    # ortadan dışa radyal aydınlık
    g = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(g)
    for r in range(900, 0, -12):
        gd.ellipse([W / 2 - r, H * 0.42 - r, W / 2 + r, H * 0.42 + r], fill=int(255 * (1 - r / 900) ** 1.4))
    img = Image.composite(Image.new("RGB", (W, H), acik), img, g.filter(_IF.GaussianBlur(40)))
    # geometrik desen
    des = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(des)
    s = 135
    for j in range(-1, H // s + 2):
        for i in range(-1, W // s + 2):
            cx, cy = i * s + (s // 2 if j % 2 else 0), j * s
            _yildiz(d, cx, cy, 44, (230, 190, 100, 34), 2)
            d.ellipse([cx - 5, cy - 5, cx + 5, cy + 5], outline=(230, 190, 100, 30), width=2)
    img = img.convert("RGBA")
    img.alpha_composite(des)
    # kenar karartma
    v = Image.new("L", (W, H), 0)
    ImageDraw.Draw(v).rounded_rectangle([60, 60, W - 60, H - 60], radius=200, fill=255)
    v = v.filter(_IF.GaussianBlur(120))
    karanlik = Image.new("RGBA", (W, H), (0, 0, 0, 170))
    karanlik.putalpha(Image.eval(v, lambda p: int((255 - p) * 0.75)))
    img.alpha_composite(karanlik)
    # çift altın çerçeve
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([30, 30, W - 31, H - 31], outline=GOLD + (200,), width=3)
    d.rectangle([44, 44, W - 45, H - 45], outline=GOLD + (90,), width=1)
    for x, y in ((30, 30), (W - 31, 30), (30, H - 31), (W - 31, H - 31)):
        d.polygon([(x, y - 12), (x + 12, y), (x, y + 12), (x - 12, y)], fill=GOLD)
    return img


def _rozet(img, y, metin):
    d = ImageDraw.Draw(img, "RGBA")
    f = nf("bold", 30)
    tw = d.textlength(metin, font=f)
    bw, bh = int(tw + 70), 54
    x = (W - bw) // 2
    d.rounded_rectangle([x, y, x + bw, y + bh], radius=bh // 2, fill=(0, 0, 0, 90), outline=GOLD_HI + (255,), width=2)
    l, t, r, b = d.textbbox((0, 0), metin, font=f)
    d.text((x + 35, y + (bh - (b - t)) / 2 - t), metin, font=f, fill=GOLD_HI)


def _ust(s):
    return s.replace("i", "İ").replace("ı", "I").upper()


def kapak(path, post, n_kart):
    img = zemin(post["seri"])
    _rozet(img, 150, SERI[post["seri"]][0])
    d = ImageDraw.Draw(img, "RGBA")
    _ornament(d, W // 2, 330, half=200)
    ft = nf("bold", 96)
    lines = _wrap(d, _ust(post["baslik"]), ft, W - 200)
    y = 640 - len(lines) * 108 // 2
    for ln in lines:
        tl = _gold_text(None, ln, ft)
        img.alpha_composite(tl, ((W - tl.width) // 2, y))
        y += 108
    d = ImageDraw.Draw(img, "RGBA")
    _center(d, y + 30, post.get("alt", ""), nf("italic", 46), CREAM)
    _ornament(d, W // 2, y + 140, half=120)
    # kaydır göstergesi
    bf = nf("bold", 36)
    lab = f"{n_kart} KART · KAYDIR"
    bw, bh = int(d.textlength(lab, font=bf) + 150), 66
    bx, by = (W - bw) // 2, 1080
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=bh // 2, fill=(226, 180, 80))
    l, t, r, b = d.textbbox((0, 0), lab, font=bf)
    d.text((bx + 45, by + (bh - (b - t)) / 2 - t), lab, font=bf, fill=(22, 30, 44))
    ax, ay = bx + bw - 80, by + bh // 2
    d.line([(ax, ay), (ax + 34, ay)], fill=(22, 30, 44), width=5)
    d.polygon([(ax + 44, ay), (ax + 28, ay - 12), (ax + 28, ay + 12)], fill=(22, 30, 44))
    _center(d, 1228, HANDLE, nf("semibold", 32), GOLD_HI)
    img.convert("RGB").save(path, "JPEG", quality=93)
    return path


def kart(path, post, i):
    k = post["kartlar"][i]
    n = len(post["kartlar"])
    img = zemin(post["seri"])
    d = ImageDraw.Draw(img, "RGBA")
    _rozet(img, 110, f"{SERI[post['seri']][0]}  ·  {i + 1}/{n}")
    # numara madalyonu
    cy = 270
    d.ellipse([W // 2 - 52, cy - 52, W // 2 + 52, cy + 52], fill=(0, 0, 0, 80), outline=GOLD_HI + (255,), width=3)
    _yildiz(d, W // 2, cy, 66, GOLD + (150,), 2)
    numf = nf("bold", 62)
    tl = _gold_text(None, str(i + 1), numf)
    img.alpha_composite(tl, ((W - tl.width) // 2, cy - tl.height // 2 - 6))
    d = ImageDraw.Draw(img, "RGBA")
    # başlık
    ft = nf("bold", 64)
    y = 370
    for ln in _wrap(d, k["baslik"], ft, W - 200):
        tl = _gold_text(None, ln, ft)
        img.alpha_composite(tl, ((W - tl.width) // 2, y))
        y += 74
    d = ImageDraw.Draw(img, "RGBA")
    _ornament(d, W // 2, y + 26, half=130)
    # metin: alt sınıra sığana kadar küçült
    ust, alt = y + 70, 1040 - (60 if k.get("kaynak") else 0)
    for sz in range(52, 33, -2):
        mf = nf("medium", sz)
        satir = _wrap(d, k["metin"], mf, W - 190)
        lh = int(sz * 1.32)
        if len(satir) * lh <= alt - ust:
            break
    ty = ust + (alt - ust - len(satir) * lh) // 2
    for ln in satir:
        _center(d, ty, ln, mf, CREAM)
        ty += lh
    if k.get("kaynak"):
        _center(d, alt + 18, "— " + k["kaynak"], nf("italic", 32), GOLD_HI)
    import brand
    eski, brand.font = brand.font, nf          # düğmeler de Nunito
    try:
        dug, cag, _, _, alt_y = cta_katmanlari(H - 20)
    finally:
        brand.font = eski
    img.alpha_composite(dug)
    img.alpha_composite(cag)
    d = ImageDraw.Draw(img, "RGBA")
    _center(d, alt_y, HANDLE, nf("semibold", 30), GOLD_HI)
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
    z = zemin(post["seri"]).resize((1080, 1350))
    dz = Image.new("RGB", (1080, 1920), SERI[post["seri"]][1])
    dz.paste(z.convert("RGB").resize((1536, 1920)).crop((228, 0, 1308, 1920)), (0, 0))
    dz.save(zp, quality=90)
    sureler = [video.okuma_suresi(k["baslik"] + " " + k["metin"], 6.5, 12.0) for k in post["kartlar"]]
    video.ozet_reel(yollar, zp, out, giris_sure=3.5, sureler_kart=sureler, muzik_bas=muzik_bas)
    return yollar, out
