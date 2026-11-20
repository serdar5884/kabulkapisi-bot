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
    kelimeler = []
    for i, p in enumerate(parcalar.split("**")):
        for k in p.split():
            kelimeler.append((k, i % 2 == 1))
    satir, sw, lh = [], 0, int(f_ince.size * 1.32)
    bos = d.textlength(" ", font=f_ince)

    def bas(satir, y):
        xx = x
        for k, kalin in satir:
            f = f_kalin if kalin else f_ince
            d.text((xx, y), k, font=f, fill=renk)
            xx += d.textlength(k, font=f) + bos

    for k, kalin in kelimeler:
        w = d.textlength(k, font=f_kalin if kalin else f_ince)
        if satir and sw + w > en:
            bas(satir, y); y += lh; satir, sw = [], 0
        satir.append((k, kalin)); sw += w + bos
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
    for ln in _wrap(d, _ust(baslik), ft, W - 140):
        _orta(d, y, ln, ft, METIN)
        y += 80
    _sus(d, y + 22, 170, ZUMRUT)
    y += 70
    alt_sinir = H - 230 if dipnot else H - 140
    n = len(maddeler)
    # boyut: hepsi sığana kadar küçült
    for sz in range(46, 27, -1):
        fi, fk, fs = nf("medium", sz), nf("black", sz), nf("semibold", int(sz * 0.72))
        yuks = []
        for m, k in maddeler:
            tmp = _zengin(ImageDraw.Draw(Image.new("RGBA", (1, 1))), 0, 0, m, fi, fk, METIN, W - 330)
            yuks.append(tmp + int(fs.size * 1.5) + 44)
        bosluk = 18
        if sum(yuks) + bosluk * (n - 1) <= alt_sinir - y:
            break
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
    parcalar = [("KAYDET", f2), (" ve ihtiyacı olana ", f1), ("GÖNDER", f2), ("  ·  " + HANDLE, f1)]
    tw = sum(d.textlength(t, font=f) for t, f in parcalar)
    x = (W - tw - 46) / 2
    yb = H - 100
    d.polygon([(x, yb), (x + 26, yb), (x + 26, yb + 34), (x + 13, yb + 25), (x, yb + 34)], fill=ZUMRUT)
    x += 46
    for t, f in parcalar:
        d.text((x, yb), t, font=f, fill=ZUMRUT if f is f2 else METIN)
        x += d.textlength(t, font=f)
    img.convert("RGB").save(path, "JPEG", quality=94)
    return path


def kapak(path, ust, baslik, soru="Hangileri?", cagri="Detaylar Reels'te"):
    """Profil ızgarasında görünen merak kapağı (ortadaki 1080x1440 alan güvenli bölge)."""
    img = _zemin()
    d = ImageDraw.Draw(img, "RGBA")
    # büyük soru işareti filigranı
    fq = nf("black", 900)
    kat = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    kd = ImageDraw.Draw(kat)
    l, t, r, b = kd.textbbox((0, 0), "?", font=fq)
    kd.text(((W - (r - l)) / 2 - l, 560 - t), "?", font=fq, fill=ZUMRUT + (26,))
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


def reel(liste_jpg, kapak_jpg, out, sure=18, muzik_bas=47):
    """Kapak 1.2 sn → listeye yumuşak geçiş → liste sabit; müzikli."""
    import subprocess, video
    muzik = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ses", "muzik.mp3")
    cmd = ["ffmpeg", "-loglevel", "error", "-y",
           "-loop", "1", "-t", "2.0", "-i", kapak_jpg,
           "-loop", "1", "-t", str(sure), "-i", liste_jpg,
           "-ss", str(muzik_bas), "-i", muzik,
           "-filter_complex",
           f"[0:v]scale=1080:1920,format=yuv420p,fps=30[a];[1:v]scale=1080:1920,format=yuv420p,fps=30[b];"
           f"[a][b]xfade=transition=fade:duration=0.8:offset=1.2[v];"
           f"[2:a]afade=t=in:d=1,afade=t=out:st={sure + 0.4}:d=2[s]",
           "-map", "[v]", "-map", "[s]", "-t", str(sure + 2.4), "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "21", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    return out
