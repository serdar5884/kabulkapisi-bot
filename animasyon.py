"""
Kabul Kapısı — hareketli dua kartı (Reels)
Sıra: arka plan belirir -> cam panel açılır -> süs -> satırlar tek tek gelir -> kaynak -> buton -> alt bilgi
"""
import os
import subprocess
from datetime import datetime

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

import brand
from brand import (AYLAR, GOLD, GOLD_HI, HANDLE, W, H, _center, _ornament, _tokens, _wrap_tokens, font, brand_sigdir)

VW, VH = 1080, 1920
FPS = 30
CREAM = (250, 244, 230)


def _katman():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def katmanlar(metin, zemin, kaynak=None, date=None):
    date = date or datetime.now()
    bg = Image.open(zemin).convert("RGB").resize((W, H), Image.LANCZOS).convert("RGBA")
    box, f, lines, lh, ty0 = brand.yerlesim(metin, kaynak)
    px1, py1, px2, py2 = box

    # panel (bulanık cam + koyu örtü + parlayan kenar), arka planla birlikte hazır görüntü
    pan = bg.copy()
    blur = pan.crop(box).filter(ImageFilter.GaussianBlur(14))
    m = Image.new("L", blur.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, blur.width, blur.height], radius=34, fill=255)
    pan.paste(blur, box[:2], m)
    ov = _katman()
    ImageDraw.Draw(ov).rounded_rectangle(box, radius=34, fill=(16, 20, 30, 150))
    pan = Image.alpha_composite(pan, ov)
    gl = _katman()
    ImageDraw.Draw(gl).rounded_rectangle(box, radius=34, outline=(255, 200, 90, 220), width=8)
    pan = Image.alpha_composite(pan, gl.filter(ImageFilter.GaussianBlur(9)))
    ed = _katman()
    e = ImageDraw.Draw(ed)
    e.rounded_rectangle(box, radius=34, outline=GOLD_HI + (255,), width=3)
    e.rounded_rectangle([px1 + 16, py1 + 16, px2 - 16, py2 - 16], radius=24, outline=GOLD + (90,), width=1)
    pan = Image.alpha_composite(pan, ed)

    # kapanış parıltısı (son saniyelerde nabız gibi atar)
    par = _katman()
    ImageDraw.Draw(par).rounded_rectangle([box[0] - 4, box[1] - 4, box[2] + 4, box[3] + 4], radius=38, outline=(255, 205, 100, 255), width=30)
    par = par.filter(ImageFilter.GaussianBlur(20))
    ic = _katman()
    ImageDraw.Draw(ic).rounded_rectangle(box, radius=34, outline=(255, 225, 150, 255), width=10)
    par.alpha_composite(ic.filter(ImageFilter.GaussianBlur(6)))
    keskin = _katman()
    ImageDraw.Draw(keskin).rounded_rectangle(box, radius=34, outline=(255, 240, 190, 255), width=4)
    par.alpha_composite(keskin)

    # süs
    sus = _katman()
    oy = py1 + 70
    _ornament(ImageDraw.Draw(sus, "RGBA"), W // 2, oy)
    y = oy + 34

    # satırlar (her satır ayrı katman, gölgesiyle)
    foot_h, src_h = brand.FOOT_H, (62 if kaynak else 0)
    y = ty0
    box_h = py2 - y - foot_h - src_h
    d0 = ImageDraw.Draw(_katman())
    sp = d0.textlength(" ", font=f)
    cy = y + (box_h - lh * len(lines)) / 2
    satirlar = []
    for ln in lines:
        lay = _katman()
        ld = ImageDraw.Draw(lay)
        lw = sum(ld.textlength(w, font=f) for w, _ in ln) + sp * (len(ln) - 1)
        x = (W - lw) / 2
        for w, hi in ln:
            ld.text((x, cy), w, font=f, fill=(GOLD_HI if hi else CREAM) + (255,))
            x += ld.textlength(w, font=f) + sp
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        sh.putalpha(lay.getchannel("A").point(lambda a: int(a * 0.85)))
        tam = _katman()
        tam.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)), (2, 4))
        tam.alpha_composite(lay)
        satirlar.append([tam.filter(ImageFilter.GaussianBlur(r)) for r in (10, 6, 3, 1)] + [tam])
        cy += lh

    kay = None
    if kaynak:
        kay = _katman()
        _center(ImageDraw.Draw(kay, "RGBA"), cy + 14, "— " + kaynak, brand_sigdir("— " + kaynak, 36, W - 220), GOLD_HI)

    # alt bölüm: KAYDET / GÖNDER düğmeleri + çağrı satırı
    dug, cag, par_k, par_g, alt_y = brand.cta_katmanlari(py2)
    but = dug
    but.alpha_composite(cag)
    bpar = (par_k, par_g)

    alt = _katman()
    _center(ImageDraw.Draw(alt, "RGBA"), alt_y, HANDLE, font("semibold", 30), GOLD_HI)   # tarih yok
    return bg, pan, sus, satirlar, kay, but, alt, par, bpar


def _ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def _yerlestir(hedef, katman, a, dy=0):
    if a <= 0:
        return
    k = katman
    if a < 1:
        k = katman.copy()
        k.putalpha(katman.getchannel("A").point(lambda v: int(v * a)))
    hedef.alpha_composite(k, (0, int(dy)))


def hareketli_reel(metin, zemin, out_path, kaynak=None, date=None, ses_girdi=None, ses_filtre=None, ses_anahtar=None,
                   kapak=None, kapak_sure=1.6, ust_katman=None, bekle=6.0):
    """kapak: önce gösterilecek 9:16 görsel (sonra animasyona yumuşak geçiş). ust_katman: 9:16 RGBA (konu başlığı)."""
    bg, pan, sus, satirlar, kay, but, alt, par, bpar = katmanlar(metin, zemin, kaynak, date)
    import math
    t0 = kapak_sure if kapak else 0.0
    # zaman çizelgesi (sn) — kapaktan sonra başlar
    t_pan, t_sus, t_sat = (0.2, 0.8, 1.1) if kapak else (0.3, 0.8, 1.1)
    adim = 1.0          # satırlar arası
    belirme = 2.2       # bir satırın soluktan nete geçiş süresi
    t_kay = t_sat + adim * (len(satirlar) - 1) + belirme * 0.8
    t_but = t_kay + (0.5 if kay else 0.0)
    t_alt = t_but + 0.4
    sure_anim = max(10.0 - t0, t_alt + bekle)   # sonda yazı tam hâliyle 'bekle' sn kalır
    sure = t0 + sure_anim
    n = int(sure * FPS)
    kapak_img = Image.open(kapak).convert("RGB").resize((VW, VH)) if kapak else None

    # 9:16 arka zemin (bulanık), bir kez
    s = max(VW / bg.width, VH / bg.height)
    ark = bg.convert("RGB").resize((int(bg.width * s) + 1, int(bg.height * s) + 1), Image.LANCZOS)
    l, t = (ark.width - VW) // 2, (ark.height - VH) // 2
    ark = ImageEnhance.Brightness(ark.crop((l, t, l + VW, t + VH)).filter(ImageFilter.GaussianBlur(28))).enhance(0.55)
    oy = (VH - H) // 2
    if ust_katman is not None:
        ark = ark.convert("RGBA"); ark.alpha_composite(ust_katman); ark = ark.convert("RGB")

    if ses_anahtar and not ses_girdi:
        import video
        ses_girdi, ses_filtre = video._ses_girdi(ses_anahtar, sure)
    girdi = ses_girdi or ["-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo"]
    af = ses_filtre or "anull"
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{VW}x{VH}",
           "-r", str(FPS), "-i", "-", *girdi, "-af", af, "-t", f"{sure:.2f}",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
           "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2", "-movflags", "+faststart", out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    siyah = Image.new("RGB", (VW, VH), (0, 0, 0))
    for i in range(n):
        tg = i / FPS
        if kapak_img is not None and tg < t0:
            p.stdin.write(kapak_img.tobytes()); continue
        tt = tg - t0
        sure_k = sure_anim
        # 1) arka plan + paneli karıştır
        a_pan = _ease((tt - t_pan) / 0.5)
        kare = Image.blend(bg, pan, a_pan) if 0 < a_pan < 1 else (pan if a_pan >= 1 else bg)
        kare = kare.copy()
        # 2) öğeler
        _yerlestir(kare, sus, _ease((tt - t_sus) / 0.5))
        for j, seviyeler in enumerate(satirlar):
            # soluk + bulanıktan yavaşça nete: 5 bulanıklık seviyesi arasında yumuşak geçiş
            g = (tt - (t_sat + j * adim)) / belirme
            if g <= 0:
                continue
            g = _ease(min(1.0, g))
            pos = g * (len(seviyeler) - 1)
            i0 = int(pos)
            k = pos - i0
            opak = 0.15 + 0.85 * g
            if i0 >= len(seviyeler) - 1:
                _yerlestir(kare, seviyeler[-1], 1.0)
            else:
                _yerlestir(kare, seviyeler[i0], opak * (1 - k))
                _yerlestir(kare, seviyeler[i0 + 1], opak * k)
        if kay:
            _yerlestir(kare, kay, _ease((tt - t_kay) / 0.6))
        a = _ease((tt - t_but) / 0.5)
        _yerlestir(kare, but, a, (1 - a) * 30)
        _yerlestir(kare, alt, _ease((tt - t_alt) / 0.6))
        # paylaş butonu: belirdikten sonra yanıp söner
        if tt > t_but + 0.6:   # KAYDET ve GÖNDER sırayla parlar
            faz = (tt - t_but - 0.6) * 2 * math.pi / 1.6
            gir = _ease((tt - t_but - 0.6) / 0.4)
            _yerlestir(kare, bpar[0], gir * max(0.0, math.sin(faz)) ** 2)
            _yerlestir(kare, bpar[1], gir * max(0.0, -math.sin(faz)) ** 2)
        # son 3 saniye: çerçeve parlar (yumuşak nabız)
        kalan = sure_k - tt if kapak_img is not None else sure - tt
        if kalan <= 3.0:
            giris = _ease((3.0 - kalan) / 0.6)
            nabiz = 0.6 + 0.4 * math.sin((3.0 - kalan) * 2 * math.pi / 1.5 - math.pi / 2) ** 2
            _yerlestir(kare, par, giris * nabiz)
        # 3) yavaş yakınlaşma (tüm kart)
        z = 1.0 + 0.035 * (tt / (sure_anim if kapak_img is not None else sure))
        if z > 1.001:
            zw, zh = int(W * z), int(H * z)
            kare = kare.resize((zw, zh), Image.BILINEAR).crop(((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
        tam = ark.copy()
        tam.paste(kare.convert("RGB"), (0, oy))
        if kapak_img is not None:   # kapaktan yumuşak geçiş
            a0 = _ease(tt / 0.7)
            if a0 < 1:
                tam = Image.blend(kapak_img, tam, a0)
        else:   # başta karanlıktan açılış
            a0 = _ease(tt / 0.4)
            if a0 < 1:
                tam = Image.blend(siyah, tam, a0)
        p.stdin.write(tam.tobytes())
    p.stdin.close()
    p.wait()
    if p.returncode:
        raise RuntimeError("ffmpeg animasyon hatası")
    return out_path, sure
