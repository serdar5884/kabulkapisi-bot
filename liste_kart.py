"""Tek uzun liste görseli (Reels, 1080x1920) + merak uyandıran kapak. Krem/füme/zümrüt, Montserrat."""
import os
from PIL import Image, ImageDraw, ImageFilter as _IF
from bilgi_kart import nf, _orta, _sus, KREM, KART, METIN, ZUMRUT, CIZGI, _ust
from brand import _wrap, HANDLE

W, H = 1080, 1920
BEYAZ = (255, 252, 244)


def _zemin():
    img = Image.new("RGB", (W, H), KREM)
    g = Image.new("L", (W, H), 0)
    ImageDraw.Draw(g).ellipse([-250, -250, W + 250, H * 0.7], fill=255)
    img = Image.composite(Image.new("RGB", (W, H), (255, 250, 236)), img, g.filter(_IF.GaussianBlur(200)))
    img = img.convert("RGBA")
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([28, 28, W - 29, H - 29], outline=ZUMRUT + (120,), width=2)
    return img


def _kutu(img, box, r=26):
    golge = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(golge).rounded_rectangle([box[0], box[1] + 5, box[2], box[3] + 5], radius=r, fill=(90, 80, 50, 34))
    img.alpha_composite(golge.filter(_IF.GaussianBlur(10)))
    ImageDraw.Draw(img, "RGBA").rounded_rectangle(box, radius=r, fill=KART, outline=CIZGI, width=2)


def _zengin(d, x, y, parcalar, f_ince, f_kalin, renk, en):
    """**kalın** işaretli metni satırlara bölüp çizer; son y'yi döner."""
    kelimeler = []   # (kelime, kalın, önceki kelimeye yapışık)
    onceki = ""
    for i, p in enumerate(parcalar.split("**")):
        for j, k in enumerate(p.split()):
            yap = j == 0 and bool(kelimeler) and p[:1] not in (" ", "") and onceki[-1:] not in (" ", "")
            kelimeler.append((k, i % 2 == 1, yap))
        onceki = p if p else onceki
    satir, sw, lh = [], 0, int(f_ince.size * 1.32)
    bos = d.textlength(" ", font=f_ince)

    def bas(satir, y):
        xx = x
        for n, (k, kalin, yap) in enumerate(satir):
            f = f_kalin if kalin else f_ince
            if yap and n:
                xx -= bos
            d.text((xx, y), k, font=f, fill=renk)
            xx += d.textlength(k, font=f) + bos

    for k, kalin, yap in kelimeler:
        w = d.textlength(k, font=f_kalin if kalin else f_ince)
        if satir and sw + w > en and not yap:
            bas(satir, y); y += lh; satir, sw = [], 0
        satir.append((k, kalin, yap)); sw += w + bos
    if satir:
        bas(satir, y); y += lh
    return y


def liste(path, ust, baslik, maddeler, dipnot=None):
    """maddeler: [(metin_with_**kalın**, kaynak), ...]"""
    img = _zemin()
    d = ImageDraw.Draw(img, "RGBA")
    _orta(d, 110, _ust(ust), nf("bold", 32), ZUMRUT)
    ft = nf("black", 70)
    y = 175
    en = W - 140
    n0 = len(_wrap(d, _ust(baslik), ft, en))
    while en > 500 and len(_wrap(d, _ust(baslik), ft, en - 20)) == n0:
        en -= 20
    for ln in _wrap(d, _ust(baslik), ft, en):
        _orta(d, y, ln, ft, METIN)
        y += 80
    _sus(d, y + 22, 170, ZUMRUT)
    y += 70
    alt_sinir = H - 230 if dipnot else H - 140
    n = len(maddeler)
    # boyut: hepsi sığana kadar küçült
    for sz in range(56, 27, -1):
        fi, fk, fs = nf("medium", sz), nf("black", sz), nf("semibold", int(sz * 0.72))
        yuks = []
        for m, k in maddeler:
            tmp = _zengin(ImageDraw.Draw(Image.new("RGBA", (1, 1))), 0, 0, m, fi, fk, METIN, W - 330)
            yuks.append(tmp + int(fs.size * 1.5) + 44)
        bosluk = 18
        if sum(yuks) + bosluk * (n - 1) <= alt_sinir - y:
            break
    y += max(0, (alt_sinir - y - (sum(yuks) + bosluk * (n - 1))) // 2)   # kısa listeyi dikeyde ortala
    for i, ((m, k), hy) in enumerate(zip(maddeler, yuks)):
        box = (70, y, W - 70, y + hy)
        _kutu(img, box)
        d = ImageDraw.Draw(img, "RGBA")
        cx, cy = 140, y + hy // 2
        d.ellipse([cx - 38, cy - 38, cx + 38, cy + 38], fill=ZUMRUT)
        nfnt = nf("black", 40)
        l, t, r, b = d.textbbox((0, 0), str(i + 1), font=nfnt)
        d.text((cx - (r - l) / 2 - l, cy - (b - t) / 2 - t), str(i + 1), font=nfnt, fill=BEYAZ)
        yy = _zengin(d, 205, y + 22, m, fi, fk, METIN, W - 330)
        d.text((205, yy + 4), k, font=fs, fill=ZUMRUT)
        y += hy + bosluk
    d = ImageDraw.Draw(img, "RGBA")
    if dipnot:
        fd = nf("medium", 30)
        yy = H - 205
        for ln in _wrap(d, dipnot, fd, W - 200):
            _orta(d, yy, ln, fd, METIN)
            yy += 40
    # alt çağrı
    f1, f2 = nf("medium", 30), nf("black", 30)
    parcalar = [("KAYDET", f2), (", sonra rahatça oku  ·  ihtiyacı olana ", f1), ("GÖNDER", f2)]
    tw = sum(d.textlength(t, font=f) for t, f in parcalar)
    x = (W - tw - 46) / 2
    yb = H - 122
    d.polygon([(x, yb), (x + 26, yb), (x + 26, yb + 34), (x + 13, yb + 25), (x, yb + 34)], fill=ZUMRUT)
    x += 46
    for t, f in parcalar:
        d.text((x, yb), t, font=f, fill=ZUMRUT if f is f2 else METIN)
        x += d.textlength(t, font=f)
    _orta(d, H - 72, HANDLE, nf("bold", 26), ZUMRUT)
    img.convert("RGB").save(path, "JPEG", quality=94)
    return path


def kapak(path, ust, baslik, soru="Hangileri?", cagri="Detaylar Reels'te", filigran="?"):
    """Profil ızgarasında görünen merak kapağı (ortadaki 1080x1440 alan güvenli bölge)."""
    img = _zemin()
    d = ImageDraw.Draw(img, "RGBA")
    # büyük soru işareti filigranı
    fq = nf("black", 900)
    kat = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    kd = ImageDraw.Draw(kat)
    l, t, r, b = kd.textbbox((0, 0), "?", font=fq)
    if filigran == "?":
        kd.text(((W - (r - l)) / 2 - l, 560 - t), "?", font=fq, fill=ZUMRUT + (26,))
    elif filigran == "hilal":
        cx, cy, r0 = W / 2, 860, 380
        kd.ellipse([cx - r0, cy - r0, cx + r0, cy + r0], fill=ZUMRUT + (26,))
        kd.ellipse([cx - r0 + 150, cy - r0 - 60, cx + r0 + 150, cy + r0 - 60], fill=(0, 0, 0, 0))
    img.alpha_composite(kat)
    d = ImageDraw.Draw(img, "RGBA")
    _orta(d, 360, _ust(ust), nf("bold", 40), ZUMRUT)
    _sus(d, 440, 200, ZUMRUT)
    for bs in range(112, 60, -4):
        ft = nf("black", bs)
        satir = _wrap(d, _ust(baslik), ft, W - 150)
        if all(d.textlength(x, font=ft) <= W - 150 for x in satir) and len(satir) <= 4:
            break
    y = 860 - len(satir) * 126 // 2
    for ln in satir:
        _orta(d, y, ln, ft, METIN)
        y += 126
    # soru bandı
    fs = nf("black", 64)
    sw = d.textlength(soru, font=fs) + 110
    bx, by = (W - sw) / 2, y + 50
    d.rounded_rectangle([bx, by, bx + sw, by + 108], radius=54, fill=ZUMRUT)
    l, t, r, b = d.textbbox((0, 0), soru, font=fs)
    d.text((bx + 55 - l, by + (108 - (b - t)) / 2 - t), soru, font=fs, fill=BEYAZ)
    # çağrı + ok
    fc = nf("bold", 44)
    cw = d.textlength(cagri, font=fc)
    cx = (W - cw - 70) / 2
    cy = by + 175
    d.text((cx, cy), cagri, font=fc, fill=METIN)
    ax, ay = cx + cw + 22, cy + 26
    d.line([(ax, ay), (ax + 36, ay)], fill=ZUMRUT, width=6)
    d.polygon([(ax + 50, ay), (ax + 30, ay - 14), (ax + 30, ay + 14)], fill=ZUMRUT)
    _orta(d, 1580, HANDLE, nf("bold", 34), ZUMRUT)
    img.convert("RGB").save(path, "JPEG", quality=94)
    return path


def reel(liste_jpg, kapak_jpg, out, sure=9, muzik_bas=47):
    """Döngü için kısa Reels: doğrudan listeyle açılır, solma yok (kapak sadece profil kapağı olarak gider)."""
    import subprocess
    muzik = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ses", "muzik.mp3")
    cmd = ["ffmpeg", "-loglevel", "error", "-y",
           "-loop", "1", "-framerate", "30", "-t", str(sure), "-i", liste_jpg,
           "-ss", str(muzik_bas), "-t", str(sure), "-i", muzik,
           "-vf", "scale=1080:1920,format=yuv420p",
           "-map", "0:v", "-map", "1:a", "-t", str(sure), "-c:v", "libx264", "-preset", "veryfast",
           "-tune", "stillimage", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
           "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    return out


KONU = {"borç": "Borçlu için dua", "hasta": "Hasta için şifa duası", "dert": "Sıkıntılı kalpler için dua",
        "çocuk": "Evlat için dua", "aile": "Aile için dua"}


def dua_sayfa(path, konu, metin, kaynak=None, okunus=None):
    """Dua Reels'i için 9:16 sayfa: konu başlığı, beyaz kutuda dua, okunuş, kaynak."""
    img = _zemin()
    d = ImageDraw.Draw(img, "RGBA")
    ft = nf("black", 74)
    # önce yükseklikleri hesapla, sonra ortala
    en0 = W - 160
    bas_sat = _wrap(d, _ust(konu), ft, en0)
    for sz in range(64, 33, -2):
        mf = nf("medium", sz)
        sat = _wrap(d, metin, mf, W - 280)
        lh = int(sz * 1.42)
        of = nf("medium", int(sz * 0.62)) if okunus else None
        osat = _wrap(d, okunus, of, W - 300) if okunus else []
        olh = int(sz * 0.62 * 1.4) if okunus else 0
        top = len(sat) * lh + (len(osat) * olh + 50 if okunus else 0) + (80 if kaynak else 0)
        if top <= 1100:
            break
    blok = 60 + len(bas_sat) * 86 + 80 + top + 120 + 100
    y0 = max(250, (H - 200 - blok) // 2 + 60)
    _orta(d, y0, "KABUL KAPISI", nf("bold", 30), ZUMRUT)
    y = y0 + 60
    en = W - 160
    n0 = len(_wrap(d, _ust(konu), ft, en))
    while en > 500 and len(_wrap(d, _ust(konu), ft, en - 20)) == n0:
        en -= 20
    for ln in _wrap(d, _ust(konu), ft, en):
        _orta(d, y, ln, ft, METIN); y += 86
    _sus(d, y + 24, 170, ZUMRUT)
    kutu_ust = y + 80
    kutu_alt = kutu_ust + top + 120
    _kutu(img, (80, kutu_ust, W - 80, kutu_alt))
    d = ImageDraw.Draw(img, "RGBA")
    ty = kutu_ust + 60
    for ln in sat:
        _orta(d, ty, ln, mf, METIN); ty += lh
    if okunus:
        ty += 20
        d.line([(W / 2 - 60, ty), (W / 2 + 60, ty)], fill=CIZGI, width=2)
        ty += 30
        for ln in osat:
            _orta(d, ty, ln, of, (110, 110, 110)); ty += olh
    if kaynak:
        _orta(d, ty + 30, kaynak, nf("semibold", int(sz * 0.62)), ZUMRUT)
    # Âmin + alt çağrı
    _orta(d, kutu_alt + 60, "Âmin de, ihtiyacı olana gönder", nf("bold", 40), METIN)
    f1, f2 = nf("medium", 30), nf("black", 30)
    parcalar = [("KAYDET", f2), (", her gün oku  ·  sevdiklerine ", f1), ("GÖNDER", f2)]
    tw = sum(d.textlength(t, font=f) for t, f in parcalar)
    x = (W - tw - 46) / 2
    yb = H - 122
    d.polygon([(x, yb), (x + 26, yb), (x + 26, yb + 34), (x + 13, yb + 25), (x, yb + 34)], fill=ZUMRUT)
    x += 46
    for t, f in parcalar:
        d.text((x, yb), t, font=f, fill=ZUMRUT if f is f2 else METIN)
        x += d.textlength(t, font=f)
    _orta(d, H - 72, HANDLE, nf("bold", 26), ZUMRUT)
    img.convert("RGB").save(path, "JPEG", quality=94)
    return path
