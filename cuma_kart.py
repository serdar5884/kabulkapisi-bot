"""Cuma paylaşımı: krem zemin, koyu yeşil el yazısı 'Hayırlı Cumalar', serif dua metni, zeytin dalı, 'Âmin' rozeti."""
import math, os, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
F = os.path.join(HERE, "fonts")
W, H = 1080, 1920
KREM, KREM2 = (233, 225, 204), (246, 241, 229)
YESIL = (38, 74, 44)
ZEYTIN = (128, 146, 88)
YAZI = (58, 46, 38)
BEYAZ = (252, 249, 240)


def _f(ad, s):
    return ImageFont.truetype(os.path.join(F, ad), s)


def _wrap(d, t, f, en):
    out, s = [], ""
    for k in t.split():
        y = (s + " " + k).strip()
        if d.textlength(y, font=f) <= en:
            s = y
        else:
            out.append(s); s = k
    if s:
        out.append(s)
    return out


def _orta(d, y, t, f, renk):
    l, tp, r, b = d.textbbox((0, 0), t, font=f)
    d.text(((W - (r - l)) / 2 - l, y - tp), t, font=f, fill=renk)
    return b - tp


def _yaprak(d, x, y, uz, aci, renk):
    """Uçları sivri yaprak (iki yay)."""
    pts = []
    for i in range(21):
        t = i / 20
        w = math.sin(math.pi * t) * uz * 0.28
        pts.append((t * uz, -w))
    for i in range(20, -1, -1):
        t = i / 20
        w = math.sin(math.pi * t) * uz * 0.28
        pts.append((t * uz, w))
    ca, sa = math.cos(aci), math.sin(aci)
    d.polygon([(x + px * ca - py * sa, y + px * sa + py * ca) for px, py in pts], fill=renk)
    d.line([(x, y), (x + uz * 0.9 * ca, y + uz * 0.9 * sa)], fill=tuple(max(0, c - 40) for c in renk[:3]) + renk[3:], width=2)


def _dal(img, x, y, boy, aci, ton=0, alfa=255, yaprak=9, olcek=1.0):
    """Zeytin dalı: gövde + karşılıklı yapraklar."""
    kat = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(kat)
    ca, sa = math.cos(aci), math.sin(aci)
    r = random.Random(int(x * 7 + y * 3))
    d.line([(x, y), (x + boy * ca, y + boy * sa)], fill=(96, 110, 66, alfa), width=max(2, int(4 * olcek)))
    for i in range(yaprak):
        t = 0.12 + 0.85 * i / max(1, yaprak - 1)
        px, py = x + boy * t * ca, y + boy * t * sa
        uz = (90 - 40 * t) * olcek
        renk = (ZEYTIN[0] - 20 * ((i + ton) % 3), ZEYTIN[1] - 18 * ((i + ton) % 2), ZEYTIN[2] - 10, alfa)
        yon = 1 if i % 2 else -1
        _yaprak(d, px, py, uz, aci + yon * (0.75 + r.uniform(-0.15, 0.15)), renk)
    _yaprak(d, x + boy * ca, y + boy * sa, 70 * olcek, aci, (ZEYTIN[0] - 10, ZEYTIN[1] - 6, ZEYTIN[2], alfa))
    img.alpha_composite(kat)


def zemin():
    img = Image.new("RGB", (W, H), KREM)
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).ellipse([-200, 150, W + 200, H - 250], fill=255)
    img = Image.composite(Image.new("RGB", (W, H), KREM2), img, g.filter(ImageFilter.GaussianBlur(220))).convert("RGBA")
    # köşelerde bulanık yapraklar (derinlik)
    bul = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    _dal(bul, -40, H - 40, 380, -1.0, 0, 200, 7, 1.5)
    _dal(bul, 70, H + 10, 320, -1.3, 1, 170, 6, 1.25)
    _dal(bul, W + 30, 120, 380, 2.4, 2, 120, 7, 1.2)
    img.alpha_composite(bul.filter(ImageFilter.GaussianBlur(3)))
    return img


def _logo(img):
    p = os.path.join(HERE, "gorseller", "logo.png")
    if not os.path.exists(p):
        return
    lg = Image.open(p).convert("RGBA").resize((190, 190))
    m = Image.new("L", lg.size, 0)
    ImageDraw.Draw(m).ellipse([0, 0, 189, 189], fill=255)
    lg.putalpha(m)
    halka = Image.new("RGBA", (206, 206), (0, 0, 0, 0))
    ImageDraw.Draw(halka).ellipse([0, 0, 205, 205], fill=YESIL + (255,))
    halka.alpha_composite(lg, (8, 8))
    img.alpha_composite(halka, (60, 250))


def kart(path, metin, baslik=("Hayırlı", "Cumalar"), amin="Âmin"):
    img = zemin()
    _logo(img)
    d = ImageDraw.Draw(img)
    fb = _f("GreatVibes.ttf", 230)
    y = 470
    for i, s in enumerate(baslik):
        l, t, r, b = d.textbbox((0, 0), s, font=fb)
        x = (W - (r - l)) / 2 - l + (-40 if i == 0 else 30)
        d.text((x, y - t), s, font=fb, fill=YESIL)
        y += 190
    # süs çizgisi + dal
    y += 60
    d.line([(W / 2 - 220, y), (W / 2 + 220, y)], fill=YESIL, width=3)
    _dal(img, W / 2 - 70, y + 40, 150, -0.25, 0, 255, 5, 0.7)
    d = ImageDraw.Draw(img)
    # metin
    y += 140
    for sz in (74, 70, 66, 62, 58, 54, 50):
        fm = _f("CrimsonPro-600.ttf", sz)
        sat = _wrap(d, metin, fm, W - 200)
        lh = int(sz * 1.3)
        if len(sat) * lh <= 1500 - y:
            break
    for s in sat:
        _orta(d, y, s, fm, YAZI)
        y += lh
    # Âmin rozeti
    y += 60
    fa = _f("CrimsonPro-700.ttf", 78)
    aw = d.textlength(amin, font=fa) + 120
    bx, by = (W - aw) / 2, y
    kat = Image.new("RGBA", img.size, (0, 0, 0, 0))
    kd = ImageDraw.Draw(kat)
    kd.rounded_rectangle([bx, by, bx + aw, by + 120], radius=60, fill=ZEYTIN + (235,))
    img.alpha_composite(kat.filter(ImageFilter.GaussianBlur(1.5)))
    d = ImageDraw.Draw(img)
    l, t, r, b = d.textbbox((0, 0), amin, font=_f("GreatVibes.ttf", 96))
    d.text(((W - (r - l)) / 2 - l, by + (120 - (b - t)) / 2 - t), amin, font=_f("GreatVibes.ttf", 96), fill=BEYAZ)
    d.line([(110, by + 60), (bx - 30, by + 60)], fill=YESIL, width=3)
    d.line([(bx + aw + 30, by + 60), (W - 110, by + 60)], fill=YESIL, width=3)
    _orta(d, H - 120, "@kabulkapisi", _f("CrimsonPro-600.ttf", 38), YESIL)
    img.convert("RGB").save(path, "JPEG", quality=95)
    return path


MESAJLAR = [
    "Rabbim; bu mübarek Cuma gününde gönüllerimize ferahlık, evlerimize bereket, sofralarımıza şükür versin.",
    "Allah'ım; Cuma'nın nuruyla kalbimizi aydınlat, dualarımızı geri çevirme, sevdiklerimizi koru.",
    "Rabbim; bu Cuma'nın hürmetine dertlilere derman, hastalara şifa, darda olanlara kolaylık ihsan eylesin.",
    "Allah'ım; haftamızı hayırla tamamla, Cuma'mızı rahmetinle süsle, ömrümüzü rızana uygun eyle.",
    "Rabbim; Cuma'nın bereketi evinden, huzuru gönlünden, rahmeti üzerinden eksik olmasın.",
    "Allah'ım; bu güzel günde açılan elleri boş çevirme, gönüllerden geçen hayırlı her muradı nasip eyle.",
    "Rabbim; dualarımızı kabul, günahlarımızı af, kalplerimizi huzurla doldursun.",
    "Allah'ım; Cuma'nın feyziyle kırgın gönülleri barıştır, yorgun kalplere sükûnet ver.",
    "Rabbim; bu mübarek günde sevdiklerimizi sağlıkla, yuvalarımızı muhabbetle, yarınlarımızı hayırla doldursun.",
    "Allah'ım; bu Cuma'yı bizim için rahmet, mağfiret ve kurtuluş vesilesi eyle.",
    "Rabbim; Cuma'nın sükûneti kalbine, bereketi rızkına, nuru yüzüne yansısın.",
    "Allah'ım; bu Cuma gününde bizi affettiğin ve duasını kabul ettiğin kullarından eyle.",
]
