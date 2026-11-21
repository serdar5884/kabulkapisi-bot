"""
Kabul Kapısı — marka ve Instagram dua kartı (1080x1350)
Renkler: gece mavisi zemin, altın vurgu, krem metin.
"""
import os
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(BASE, "fonts")
OUT_DIR = os.path.join(BASE, "gorseller")

NAME = "Kabul Kapısı"
HANDLE = "@kabulkapisi"

BG = (30, 42, 56)          # #1E2A38
BG_DEEP = (22, 31, 42)
GOLD = (212, 175, 55)      # #D4AF37
CREAM = (245, 235, 211)    # #F5EBD3
GOLD_SOFT = (212, 175, 55, 90)

W, H = 1080, 1350

AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
         "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]


FONT_AILE = "cormorant"   # dua Reels'i için "montserrat" yapılır (beyaz formatla aynı yazı tipi)
_MONT = {"semibold": 500, "medium": 500, "italic": 500, "bold": 700}


def font(style, size):
    if FONT_AILE == "montserrat":
        return ImageFont.truetype(os.path.join(FONTS, f"Montserrat-{_MONT.get(style, 500)}.ttf"), max(10, int(size * 0.8)))
    files = {"semibold": "CormorantGaramond-600-normal.ttf",
             "medium": "CormorantGaramond-500-normal.ttf",
             "italic": "CormorantGaramond-500-italic.ttf",
             "bold": "CormorantGaramond-700-normal.ttf"}
    return ImageFont.truetype(os.path.join(FONTS, files[style]), size)


def _wrap(d, text, f, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=f) <= max_w:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _fit(d, text, max_w, max_h, start=68, low=40, style="medium"):
    for size in range(start, low - 1, -2):
        f = font(style, size)
        lines = _wrap(d, text, f, max_w)
        lh = int(size * 1.32)
        if lh * len(lines) <= max_h:
            return f, lines, lh
    f = font(style, low)
    return f, _wrap(d, text, f, max_w), int(low * 1.32)


def _center(d, y, text, f, fill):
    w = d.textlength(text, font=f)
    d.text(((W - w) / 2, y), text, font=f, fill=fill)


def _frame(img):
    d = ImageDraw.Draw(img, "RGBA")
    # hafif alt gölge degrade
    for i in range(300):
        a = int(70 * i / 300)
        d.line([(0, H - 300 + i), (W, H - 300 + i)], fill=BG_DEEP + (a,))
    # ince çift altın çerçeve
    d.rounded_rectangle([36, 36, W - 36, H - 36], radius=28, outline=GOLD + (150,), width=3)
    d.rounded_rectangle([50, 50, W - 50, H - 50], radius=20, outline=GOLD + (60,), width=1)
    return d


def _stars(d, n=26, seed=7):
    import random
    r = random.Random(seed)
    for _ in range(n):
        x, y = r.randint(80, W - 80), r.randint(80, 420)
        s = r.choice([1, 1, 2, 2, 3])
        d.ellipse([x - s, y - s, x + s, y + s], fill=CREAM + (r.randint(60, 160),))


def make_card(path, metin, baslik="GÜNÜN DUASI", kaynak=None, date=None, kandil=False):
    date = date or datetime.now()
    img = Image.new("RGB", (W, H), BG)
    d = _frame(img)
    if kandil:
        _stars(d)

    # üstte logo işareti
    mark = Image.open(os.path.join(OUT_DIR, "isaret.png")).convert("RGBA")
    mh = 230 if kandil else 200
    mark = mark.resize((int(mh * 240 / 300), mh), Image.LANCZOS)
    img.paste(mark, ((W - mark.width) // 2, 96), mark)
    d = ImageDraw.Draw(img, "RGBA")

    y = 96 + mh + 34
    ft = font("semibold", 58 if kandil else 36)
    spaced = " ".join(baslik.upper()) if not kandil else baslik
    _center(d, y, spaced, ft, GOLD)
    y += 84 if kandil else 62
    d.line([(W / 2 - 70, y), (W / 2 + 70, y)], fill=GOLD + (170,), width=2)
    d.ellipse([W / 2 - 5, y - 5, W / 2 + 5, y + 5], fill=GOLD)
    y += 46

    # dua metni
    foot_h = 210
    src_h = 70 if kaynak else 0
    box_h = H - y - foot_h - src_h
    f, lines, lh = _fit(d, metin, W - 230, box_h)
    total = lh * len(lines)
    ty = y + (box_h - total) / 2
    for ln in lines:
        _center(d, ty, ln, f, CREAM)
        ty += lh

    if kaynak:
        _center(d, ty + 22, "— " + kaynak, font("italic", 36), GOLD)

    # alt bilgi
    fy = H - 170
    _center(d, fy, "Âmin demeyi unutma", font("italic", 38), CREAM + (230,))
    tarih = f"{date.day} {AYLAR[date.month - 1]} {date.year}"
    _center(d, fy + 62, f"{HANDLE}   ·   {tarih}", font("semibold", 28), GOLD + (220,))

    img.save(path, "JPEG", quality=94)
    return path


ZEMIN_DIR = os.path.join(BASE, "arkaplanlar")


def zeminler():
    if not os.path.isdir(ZEMIN_DIR):
        return []
    return sorted(os.path.join(ZEMIN_DIR, f) for f in os.listdir(ZEMIN_DIR)
                  if f.lower().endswith((".jpg", ".jpeg", ".png")))


def _make_photo_card_v1(path, metin, zemin, baslik="Günün Duası", kaynak=None, date=None, kandil=False):
    """Hazır arka plan görselinin üstüne buzlu cam panelde dua metni yazar."""
    from PIL import ImageFilter
    date = date or datetime.now()
    img = Image.open(zemin).convert("RGB").resize((W, H), Image.LANCZOS)

    # panel: sağ üstteki logonun altından başlar
    px1, py1, px2, py2 = 90, 400, W - 90, 1170
    box = (px1, py1, px2, py2)
    blur = img.crop(box).filter(ImageFilter.GaussianBlur(18))
    mask = Image.new("L", blur.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, blur.width, blur.height], radius=36, fill=255)
    img.paste(blur, box[:2], mask)
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    od.rounded_rectangle(box, radius=36, fill=(18, 24, 34, 175), outline=GOLD + (200,), width=3)
    od.rounded_rectangle([px1 + 14, py1 + 14, px2 - 14, py2 - 14], radius=26, outline=GOLD + (70,), width=1)
    img = Image.alpha_composite(img.convert("RGBA"), over)
    d = ImageDraw.Draw(img, "RGBA")

    # başlık
    y = py1 + 50
    if kandil:
        _center(d, y, baslik, font("semibold", 60), GOLD)
        y += 82
    else:
        _center(d, y, " ".join(baslik.upper()), font("semibold", 38), GOLD)
        y += 62
    d.line([(W / 2 - 70, y), (W / 2 + 70, y)], fill=GOLD + (190,), width=2)
    d.ellipse([W / 2 - 5, y - 5, W / 2 + 5, y + 5], fill=GOLD)
    y += 38

    # metin
    foot_h = 120
    src_h = 64 if kaynak else 0
    box_h = py2 - y - foot_h - src_h
    f, lines, lh = _fit(d, metin, (px2 - px1) - 120, box_h, start=60, low=36)
    ty = y + (box_h - lh * len(lines)) / 2
    for ln in lines:
        _center(d, ty, ln, f, CREAM)
        ty += lh
    if kaynak:
        _center(d, ty + 18, "— " + kaynak, font("italic", 34), GOLD)

    # alt bilgi
    fy = py2 - 108
    _center(d, fy, "Âmin demeyi unutma", font("italic", 36), CREAM)
    tarih = f"{date.day} {AYLAR[date.month - 1]} {date.year}"
    _center(d, fy + 50, f"{HANDLE}   ·   {tarih}", font("semibold", 27), GOLD)

    img.convert("RGB").save(path, "JPEG", quality=93)
    return path


# --- v2: örnek görseldeki stil (kalın altın başlık, vurgulu kelimeler, gölgeli metin) ---
import re as _re
from PIL import ImageFilter as _IF

GOLD_HI = (240, 205, 120)
VURGU_KOK = ("huzur", "şifa", "bereket", "rahmet", "rızk", "hayır", "hayırlı", "nur", "sabır", "af",
             "kabul", "sevinç", "ferah", "selamet", "şefaat", "hidayet", "takva", "cennet", "sağlık",
             "dua", "kalb", "gönl", "yüz", "düğüm", "haber", "iyilik", "merhamet", "huzur")
VURGU_EK = ("sün", "sın", "sin", "sun", "eyle", "ver", "et", "kıl", "bağışla", "ırım", "irim")


def _vurgu_mu(w):
    c = w.strip(".,;:!?\"'’()").lower()
    if len(c) < 4:
        return False
    if c.endswith(VURGU_EK) and len(c) > 5:
        return True
    return any(c.startswith(k) for k in VURGU_KOK)


def _tokens(metin):
    """*kelime* işaretli metin -> [(kelime, vurgulu)]. İşaret yoksa otomatik seçer."""
    if "*" in metin:
        out, on = [], False
        for part in _re.split(r"(\*)", metin):
            if part == "*":
                on = not on
                continue
            out += [(w, on) for w in part.split()]
        return out
    words = metin.split()
    marks = [_vurgu_mu(w) for w in words]
    # çok fazla vurgu olmasın: en fazla 6
    n = 0
    for i, m in enumerate(marks):
        if m:
            n += 1
            if n > 6:
                marks[i] = False
    return list(zip(words, marks))


def _wrap_tokens(d, toks, f, max_w):
    lines, cur = [], []
    sp = d.textlength(" ", font=f)
    for t in toks:
        trial = cur + [t]
        w = sum(d.textlength(x[0], font=f) for x in trial) + sp * (len(trial) - 1)
        if w <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = [t]
    if cur:
        lines.append(cur)
    return lines


def _gold_text(size, text, f):
    """Dikey altın degrade dolgulu metin katmanı döndürür."""
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    l, t, r, b = tmp.textbbox((0, 0), text, font=f)
    w, h = r - l + 8, b - t + 8
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((4 - l, 4 - t), text, font=f, fill=255)
    grad = Image.new("RGBA", (w, h))
    gd = ImageDraw.Draw(grad)
    top, mid, bot = (255, 236, 170), (226, 180, 80), (180, 128, 40)
    for y in range(h):
        k = y / max(h - 1, 1)
        if k < 0.5:
            c = tuple(int(top[i] + (mid[i] - top[i]) * k * 2) for i in range(3))
        else:
            c = tuple(int(mid[i] + (bot[i] - mid[i]) * (k - 0.5) * 2) for i in range(3))
        gd.line([(0, y), (w, y)], fill=c + (255,))
    grad.putalpha(mask)
    return grad


def _ornament(d, cx, y, half=150):
    g = GOLD + (230,)
    d.line([(cx - half, y), (cx - 22, y)], fill=g, width=2)
    d.line([(cx + 22, y), (cx + half, y)], fill=g, width=2)
    d.polygon([(cx, y - 9), (cx + 9, y), (cx, y + 9), (cx - 9, y)], fill=GOLD)
    for s in (-1, 1):
        d.arc([cx + s * 22 - 12 if s > 0 else cx - 34, y - 12, cx + s * 22 + 12 if s > 0 else cx - 10, y], 
              0, 180, fill=g, width=2)
        d.ellipse([cx + s * half - 4, y - 4, cx + s * half + 4, y + 4], fill=GOLD)




def _yer_imi(d, x, y, renk):
    """kaydet (yer imi) simgesi; (x,y) sol üst"""
    d.polygon([(x, y), (x + 22, y), (x + 22, y + 30), (x + 11, y + 21), (x, y + 30)], fill=renk)


def _ucak(d, x, y, renk, golge=(70, 60, 40)):
    """gönder (kağıt uçak) simgesi; (x,y) sol orta"""
    d.polygon([(x, y + 2), (x + 34, y - 14), (x + 22, y + 16), (x + 15, y + 6)], fill=renk)
    d.polygon([(x + 15, y + 6), (x + 34, y - 14), (x + 13, y + 15)], fill=golge)


def cta_katmanlari(py2):
    """Alt bölüm: [KAYDET] [GÖNDER] düğmeleri + çağrı satırı.
    (dugmeler, cagri, parilti_kaydet, parilti_gonder, alt_y) döndürür; alt_y = @hesap satırının y'si."""
    navy = (22, 30, 44)
    bf = font("bold", 36)
    dugmeler, cagri = Image.new("RGBA", (W, H), (0, 0, 0, 0)), Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(dugmeler, "RGBA")
    bh, ara = 64, 26
    etiket = [("KAYDET", 36), ("GÖNDER", 40)]
    gen = [int(d.textlength(t, font=bf) + iw + 74) for t, iw in etiket]
    x = (W - (sum(gen) + ara)) // 2
    by = py2 - 212
    kutular, parilti = [], []
    for (t, iw), bw in zip(etiket, gen):
        kutular.append((x, by, x + bw, by + bh))
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(g).rounded_rectangle([x - 9, by - 9, x + bw + 9, by + bh + 9], radius=bh // 2 + 9, outline=(255, 215, 120, 255), width=12)
        g = g.filter(_IF.GaussianBlur(10))
        k = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(k).rounded_rectangle([x - 3, by - 3, x + bw + 3, by + bh + 3], radius=bh // 2 + 3, outline=(255, 245, 200, 255), width=3)
        g.alpha_composite(k)
        parilti.append(g)
        x += bw + ara
    # hafif sabit hale
    hale = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hale)
    for (x1, y1, x2, y2) in kutular:
        hd.rounded_rectangle([x1 - 6, y1 - 6, x2 + 6, y2 + 6], radius=bh // 2 + 6, fill=(255, 200, 90, 110))
    dugmeler.alpha_composite(hale.filter(_IF.GaussianBlur(10)))
    for (x1, y1, x2, y2), (t, iw) in zip(kutular, etiket):
        bw = x2 - x1
        pm = Image.new("L", (bw, bh), 0)
        ImageDraw.Draw(pm).rounded_rectangle([0, 0, bw - 1, bh - 1], radius=bh // 2, fill=255)
        grad = Image.new("RGBA", (bw, bh))
        gd = ImageDraw.Draw(grad)
        for yy in range(bh):
            kk = yy / (bh - 1)
            gd.line([(0, yy), (bw, yy)], fill=tuple(int((255, 230, 160)[i] + ((200, 150, 55)[i] - (255, 230, 160)[i]) * kk) for i in range(3)) + (255,))
        grad.putalpha(pm)
        dugmeler.alpha_composite(grad, (x1, y1))
    d = ImageDraw.Draw(dugmeler, "RGBA")
    for (x1, y1, x2, y2), (t, iw) in zip(kutular, etiket):
        cy = (y1 + y2) // 2
        if t == "KAYDET":
            _yer_imi(d, x1 + 30, cy - 15, navy)
        else:
            _ucak(d, x1 + 28, cy, navy)
        l, tt, r, b = d.textbbox((0, 0), t, font=bf)
        d.text((x1 + 30 + iw, cy - (b - tt) / 2 - tt), t, font=bf, fill=navy)
    _center(ImageDraw.Draw(cagri, "RGBA"), py2 - 128, "İhtiyacı olan birine ulaştır, duasına vesile ol", font("italic", 34), (250, 244, 230))
    return dugmeler, cagri, parilti[0], parilti[1], py2 - 72


FOOT_H = 225   # alt bölüm: KAYDET/GÖNDER + çağrı satırı + @hesap

# --- yerleşim: uzun metinde yazıyı küçültmek yerine paneli genişlet ---
PANEL = (70, 390, W - 70, 1175)
GENIS_KENAR = 34                             # uzun metinde yan boşluk (normalde 70)
PANEL_EN_UST, PANEL_EN_ALT = 280, 1328       # büyüme sınırları (önce aşağı büyür)
YAZI_EN_AZ = 56                              # bu boyutun altına inmeden önce panel büyür


def yerlesim(metin, kaynak=None):
    """(box, font, satırlar, satır_yüksekliği, yazı_başlangıç_y) döndürür."""
    d0 = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    toks = _tokens(metin)
    px1, py1, px2, py2 = PANEL
    foot_h, src_h = FOOT_H, (62 if kaynak else 0)
    ust_bosluk = 104                          # süs + boşluk

    def dene(size, x1, x2, y1, y2):
        f = font("semibold", size)
        lines = _wrap_tokens(d0, toks, f, (x2 - x1) - 100)
        lh = int(size * 1.36)
        return f, lines, lh, lh * len(lines) <= (y2 - y1 - ust_bosluk - foot_h - src_h)

    # 1) normal panelde 72..YAZI_EN_AZ
    for size in range(72, YAZI_EN_AZ - 1, -2):
        f, lines, lh, ok = dene(size, px1, px2, py1, py2)
        if ok:
            return (px1, py1, px2, py2), f, lines, lh, py1 + ust_bosluk
    # 2) yanlara genişlet, sonra önce aşağı, gerekirse yukarı uzat
    x1, x2 = GENIS_KENAR, W - GENIS_KENAR
    f, lines, lh, ok = dene(YAZI_EN_AZ, x1, x2, py1, py2)
    if ok:
        return (x1, py1, x2, py2), f, lines, lh, py1 + ust_bosluk
    gerek = lh * len(lines) + ust_bosluk + foot_h + src_h + 16
    y1, y2 = py1, min(PANEL_EN_ALT, py1 + gerek)
    if y2 - y1 < gerek:
        y1 = max(PANEL_EN_UST, y2 - gerek)
    # 3) hâlâ sığmıyorsa en büyük panelde yazıyı küçült
    for size in range(YAZI_EN_AZ, 34, -2):
        f, lines, lh, ok = dene(size, x1, x2, y1, y2)
        if ok:
            break
    return (x1, y1, x2, y2), f, lines, lh, y1 + ust_bosluk


def brand_sigdir(metin, boyut, en, stil="italic"):
    """Tek satırlık metni verilen genişliğe sığana kadar küçültür."""
    olc = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    while boyut > 20 and olc.textlength(metin, font=font(stil, boyut)) > en:
        boyut -= 2
    return font(stil, boyut)


def make_photo_card(path, metin, zemin, baslik="Günün Duası", kaynak=None, date=None, kandil=False):
    date = date or datetime.now()
    img = Image.open(zemin).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
    box, f, lines, lh, ty0 = yerlesim(metin, kaynak)
    px1, py1, px2, py2 = box

    # buzlu cam panel
    blur = img.crop(box).filter(_IF.GaussianBlur(14))
    m = Image.new("L", blur.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, blur.width, blur.height], radius=34, fill=255)
    img.paste(blur, box[:2], m)
    over = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(over).rounded_rectangle(box, radius=34, fill=(16, 20, 30, 150))
    img = Image.alpha_composite(img, over)
    # parlayan altın kenar
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle(box, radius=34, outline=(255, 200, 90, 220), width=8)
    img = Image.alpha_composite(img, glow.filter(_IF.GaussianBlur(9)))
    edge = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ed = ImageDraw.Draw(edge)
    ed.rounded_rectangle(box, radius=34, outline=GOLD_HI + (255,), width=3)
    ed.rounded_rectangle([px1 + 16, py1 + 16, px2 - 16, py2 - 16], radius=24, outline=GOLD + (90,), width=1)
    img = Image.alpha_composite(img, edge)

    # başlık yok: üstte sadece süslü ayraç
    d = ImageDraw.Draw(img, "RGBA")
    oy = py1 + 70
    _ornament(d, W // 2, oy)
    y = oy + 34

    # gövde metni
    foot_h, src_h = FOOT_H, (62 if kaynak else 0)
    y = ty0
    box_h = py2 - y - foot_h - src_h
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    sp = ld.textlength(" ", font=f)
    cy = y + (box_h - lh * len(lines)) / 2
    for ln in lines:
        lw = sum(ld.textlength(w, font=f) for w, _ in ln) + sp * (len(ln) - 1)
        x = (W - lw) / 2
        for w, hi in ln:
            ld.text((x, cy), w, font=f, fill=(GOLD_HI if hi else (250, 244, 230)) + (255,))
            x += ld.textlength(w, font=f) + sp
        cy += lh
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.putalpha(layer.getchannel("A").point(lambda a: int(a * 0.85)))
    img.alpha_composite(shadow.filter(_IF.GaussianBlur(5)), (2, 4))
    img.alpha_composite(layer)
    d = ImageDraw.Draw(img, "RGBA")
    if kaynak:
        _center(d, cy + 14, "— " + kaynak, brand_sigdir("— " + kaynak, 36, W - 220), GOLD_HI)

    # alt bölüm: KAYDET / GÖNDER + çağrı + @hesap
    dug, cag, _, _, alt_y = cta_katmanlari(py2)
    img.alpha_composite(dug)
    img.alpha_composite(cag)
    d = ImageDraw.Draw(img, "RGBA")
    _center(d, alt_y, HANDLE, font("semibold", 30), GOLD_HI)   # tarih yazılmaz: gönderi eskimiş görünmesin

    img.convert("RGB").save(path, "JPEG", quality=93)
    return path



def make_cover(path, baslik, alt, zemin, buton="KAYDIR", ok=True):
    """Haftalık derleme (kaydırmalı gönderi) kapağı: büyük altın başlık + 'Kaydır' butonu."""
    img = Image.open(zemin).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
    box = (90, 470, W - 90, 1110)
    blur = img.crop(box).filter(_IF.GaussianBlur(14))
    m = Image.new("L", blur.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, blur.width, blur.height], radius=34, fill=255)
    img.paste(blur, box[:2], m)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(ov).rounded_rectangle(box, radius=34, fill=(16, 20, 30, 160))
    img = Image.alpha_composite(img, ov)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle(box, radius=34, outline=(255, 200, 90, 220), width=8)
    img = Image.alpha_composite(img, glow.filter(_IF.GaussianBlur(9)))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle(box, radius=34, outline=GOLD_HI + (255,), width=3)
    _ornament(d, W // 2, box[1] + 70)
    ft = font("bold", 92)
    up = baslik.replace("i", "İ").replace("ı", "I").upper()
    lines = _wrap(d, up, ft, box[2] - box[0] - 100)
    y = box[1] + 120
    for ln in lines:
        tl = _gold_text(None, ln, ft)
        img.alpha_composite(tl, ((W - tl.width) // 2, y))
        y += 104
    d = ImageDraw.Draw(img, "RGBA")
    _center(d, y + 20, alt, font("italic", 44), (250, 244, 230))
    # kaydır butonu
    bf = font("bold", 38)
    lab = buton
    bw, bh = int(d.textlength(lab, font=bf) + (150 if ok else 90)), 66
    bx, by = (W - bw) // 2, box[3] - 130
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=bh // 2, fill=(226, 180, 80))
    l, t, r, b = d.textbbox((0, 0), lab, font=bf)
    d.text((bx + 45, by + (bh - (b - t)) / 2 - t), lab, font=bf, fill=(22, 30, 44))
    if ok:
        ax, ay = bx + bw - 80, by + bh // 2
        d.line([(ax, ay), (ax + 34, ay)], fill=(22, 30, 44), width=5)
        d.polygon([(ax + 44, ay), (ax + 28, ay - 12), (ax + 28, ay + 12)], fill=(22, 30, 44))
    _center(d, box[3] - 48, HANDLE, font("semibold", 29), GOLD_HI)
    img.convert("RGB").save(path, "JPEG", quality=93)
    return path


if __name__ == "__main__":
    zs = zeminler()
    if zs:
        make_photo_card(os.path.join(OUT_DIR, "ornek_gunluk.jpg"),
                        "Bu satırları okuyan kardeşim; Rabbim bugün yüzünü güldürsün, kalbindeki düğümleri bir bir çözsün, beklediğin hayırlı haberi en güzel vaktinde sana ulaştırsın.", zs[0])
        make_photo_card(os.path.join(OUT_DIR, "ornek_ayet.jpg"),
                        "Rabbimiz! Bize dünyada da iyilik ver, ahirette de iyilik ver ve bizi ateş azabından koru.", zs[1],
                        kaynak="Bakara Suresi, 201. ayet (meali)")
        make_photo_card(os.path.join(OUT_DIR, "ornek_cuma.jpg"),
                        "Hayırlı Cumalar. Bu mübarek günün hürmetine Rabbim bu satırları okuyanın günahlarını affetsin, dualarını kabul eylesin, kalbine huzur versin.", zs[2],
                        baslik="Hayırlı Cumalar")
        make_photo_card(os.path.join(OUT_DIR, "ornek_kandil.jpg"),
                        "Regaip Kandiliniz mübarek olsun. Üç ayların bu ilk kandilinde Rabbim bu satırları okuyanın dualarını kabul etsin; Recep'i ve Şaban'ı bereketli kılıp hepimizi sağlıkla Ramazan'a ulaştırsın.", zs[3],
                        baslik="Regaip Kandili", kandil=True)
        make_photo_card(os.path.join(OUT_DIR, "ornek_hadis.jpg"),
                        "Allah'ım! Kaygıdan ve üzüntüden, acizlikten ve tembellikten, cimrilikten ve korkaklıktan, borcun ağırlığından ve insanların baskısından sana sığınırım.", zs[4],
                        kaynak="Buhârî, Daavât")
        print("fotoğraflı örnek kartlar yazıldı")
        raise SystemExit


if False:
    os.makedirs(OUT_DIR, exist_ok=True)
    make_card(os.path.join(OUT_DIR, "ornek_gunluk.jpg"),
              "Bu satırları okuyan kardeşim; Rabbim bugün yüzünü güldürsün, kalbindeki düğümleri bir bir çözsün, beklediğin hayırlı haberi en güzel vaktinde sana ulaştırsın.")
    make_card(os.path.join(OUT_DIR, "ornek_ayet.jpg"),
              "Rabbimiz! Bize dünyada da iyilik ver, ahirette de iyilik ver ve bizi ateş azabından koru.",
              kaynak="Bakara Suresi, 201. ayet (meali)")
    make_card(os.path.join(OUT_DIR, "ornek_cuma.jpg"),
              "Hayırlı Cumalar. Bu mübarek günün hürmetine Rabbim bu satırları okuyanın günahlarını affetsin, dualarını kabul eylesin, kalbine huzur versin.",
              baslik="Hayırlı Cumalar")
    make_card(os.path.join(OUT_DIR, "ornek_kandil.jpg"),
              "Regaip Kandiliniz mübarek olsun. Üç ayların bu ilk kandilinde Rabbim bu satırları okuyanın dualarını kabul etsin; Recep'i ve Şaban'ı bereketli kılıp hepimizi sağlıkla Ramazan'a ulaştırsın.",
              baslik="Regaip Kandili", kandil=True)
    print("örnek kartlar gorseller/ klasörüne yazıldı")
