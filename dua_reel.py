"""Dua Reels'i (önceki gece/altın tasarımla): konu kapağı + kısa döngülü video."""
import os
from PIL import Image, ImageDraw
import brand, video

KONU = {"borç": "Borçlu İçin Dua", "hasta": "Hasta İçin Şifa Duası", "dert": "Sıkıntılı Kalpler İçin Dua",
        "çocuk": "Evlat İçin Dua", "aile": "Aile İçin Dua"}


def konu_bul(dua, tur, vakit=None):
    if dua.get("konu"):
        return dua["konu"]
    if dua.get("tema") in KONU:
        return KONU[dua["tema"]]
    if tur == "kuran":
        return "Kur'an'dan Bir Dua"
    if tur in ("hadis", "dua") and dua.get("tur") == "hadis":
        return "Peygamberimizin Duası"
    if tur == "cuma":
        return "Cuma Duası"
    if tur == "kandil":
        return "Kandil Duası"
    return {"sabah": "Sabah Duası", "aksam": "Akşam Duası"}.get(vakit, "Günün Duası")


def ust_katman(metin):
    """9:16 saydam katman: üst boşlukta altın konu başlığı."""
    img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    f = brand.font("bold", 64)
    t = metin.replace("i", "İ").replace("ı", "I").upper()
    tl = brand._gold_text(None, t, f)
    y = (1920 - 1350) // 2 - tl.height - 40
    img.alpha_composite(tl, ((1080 - tl.width) // 2, max(150, y)))
    return img


def hareketli(dua, tur, zemin, klasor, out, vakit=None, date=None, muzik_bas=47):
    """Kapak → kart animasyonu (yazılar soluktan belirir) → yazı ekranda kalır."""
    import animasyon
    konu, kart, sayfa, kapak = hazirla(dua, tur, zemin, klasor, vakit, date)
    with montserrat():
        mp4, sure = animasyon.hareketli_reel(dua["metin"], zemin, out, kaynak=dua.get("kaynak"), date=date,
                                             ses_anahtar=os.path.basename(out),
                                             ust_katman=ust_katman(konu), bekle=4.0)   # kapak sadece ızgarada
    return konu, kapak, mp4, sure


def _ust_baslik(path, metin):
    """9:16 görselin üst boşluğuna altın konu başlığı yazar."""
    img = Image.open(path).convert("RGBA")
    d = ImageDraw.Draw(img)
    f = brand.font("bold", 64)
    t = metin.replace("i", "İ").replace("ı", "I").upper()
    tl = brand._gold_text(None, t, f)
    y = (1920 - 1350) // 2 - tl.height - 40
    img.alpha_composite(tl, ((1080 - tl.width) // 2, max(150, y)))
    img.convert("RGB").save(path, "JPEG", quality=94)
    return path


class montserrat:
    """with montserrat(): ... → kart, kapak ve animasyon Montserrat ile çizilir."""
    def __enter__(self):
        self.eski, brand.FONT_AILE = brand.FONT_AILE, "montserrat"

    def __exit__(self, *a):
        brand.FONT_AILE = self.eski


def hazirla(dua, tur, zemin, klasor, vakit=None, date=None):
    with montserrat():
        return _hazirla(dua, tur, zemin, klasor, vakit, date)


def _hazirla(dua, tur, zemin, klasor, vakit=None, date=None):
    os.makedirs(klasor, exist_ok=True)
    konu = konu_bul(dua, tur, vakit)
    kart = brand.make_photo_card(os.path.join(klasor, "kart.jpg"), dua["metin"], zemin,
                                 kaynak=dua.get("kaynak"), date=date, kandil=(tur == "kandil"))
    sayfa = video.dikey_kare(kart, zemin, os.path.join(klasor, "sayfa.jpg"))
    _ust_baslik(sayfa, konu)
    kap45 = brand.make_cover(os.path.join(klasor, "kapak45.jpg"), konu, "Oku ve Âmin de", zemin,
                             buton="ÂMİN DE", ok=False)
    kapak = video.dikey_kare(kap45, zemin, os.path.join(klasor, "kapak.jpg"))
    return konu, kart, sayfa, kapak


def reel(sayfa, out, sure=8, muzik_bas=47):
    import liste_kart
    return liste_kart.reel(sayfa, None, out, sure=sure, muzik_bas=muzik_bas)


def sabit(dua, tur, zemin, klasor, out, vakit=None, date=None, muzik_bas=47, parca=3, sure=4.0):
    """Animasyonsuz: aynı dua sayfası 3 parça x 4 sn (duasensin/şablon düzeni). Başa sarınca da aynısı görünür."""
    import subprocess
    konu, kart, sayfa, kapak = hazirla(dua, tur, zemin, klasor, vakit, date)
    muzik = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ses", "muzik.mp3")
    toplam = parca * sure
    girdiler, filtre = [], ""
    for i in range(parca):
        girdiler += ["-loop", "1", "-framerate", "30", "-t", str(sure), "-i", sayfa]
        filtre += f"[{i}:v]scale=1080:1920,format=yuv420p,setsar=1[v{i}];"
    filtre += "".join(f"[v{i}]" for i in range(parca)) + f"concat=n={parca}:v=1:a=0[v]"
    cmd = ["ffmpeg", "-loglevel", "error", "-y", *girdiler, "-ss", str(muzik_bas), "-t", str(toplam), "-i", muzik,
           "-filter_complex", filtre, "-map", "[v]", "-map", f"{parca}:a", "-t", str(toplam),
           "-c:v", "libx264", "-preset", "veryfast", "-tune", "stillimage", "-crf", "20",
           "-force_key_frames", ",".join(str(i * sure) for i in range(parca)),
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    return konu, kapak, out, toplam
