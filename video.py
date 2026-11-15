"""
Kabul Kapısı — dua kartından Reels videosu (1080x1920, ~9 sn) ve hikâye görseli üretir.
Ses: ses/ klasöründeki ney kayıtları (sırayla). Klasör boşsa sakin bir fon tonu üretilir.
"""
import os
import subprocess

from PIL import Image, ImageFilter, ImageEnhance

W, H = 1080, 1920
SURE = 9


def dikey_kare(kart_path, zemin_path, out_path):
    """4:5 kartı, bulanık zemin üstünde 9:16 dikey görsele yerleştirir (Reels / hikâye)."""
    kart = Image.open(kart_path).convert("RGB")
    bg = Image.open(zemin_path or kart_path).convert("RGB")
    s = max(W / bg.width, H / bg.height)
    bg = bg.resize((int(bg.width * s) + 1, int(bg.height * s) + 1), Image.LANCZOS)
    l, t = (bg.width - W) // 2, (bg.height - H) // 2
    bg = bg.crop((l, t, l + W, t + H)).filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.55)
    kart = kart.resize((W, int(kart.height * W / kart.width)), Image.LANCZOS)
    bg.paste(kart, (0, (H - kart.height) // 2))
    bg.save(out_path, "JPEG", quality=94)
    return out_path


SES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ses")
MUZIK = os.path.join(SES_DIR, "muzik.mp3")       # Pixabay: Alex Morgan - Islamic Music
BOLUMLER = [47, 15, 64, 33, 86, 75, 99, 110]      # parçanın güzel 9 sn'lik bölümleri (saniye)


def bolum_sec(anahtar):
    return BOLUMLER[sum(map(ord, anahtar)) % len(BOLUMLER)]


def _ses_girdi(anahtar, sure):
    """(ffmpeg girdi argümanları, ses filtresi)"""
    if os.path.exists(MUZIK):
        bas = bolum_sec(anahtar)
        return (["-ss", str(bas), "-t", str(sure + 1), "-i", MUZIK],
                f"afade=t=in:d=0.8,afade=t=out:st={sure - 1.7}:d=1.7,loudnorm=I=-16:TP=-1.5")
    ses = ("aevalsrc='0.05*sin(2*PI*196*t)+0.04*sin(2*PI*246.94*t)+0.035*sin(2*PI*293.66*t)':s=44100:d=" + str(sure))
    return (["-f", "lavfi", "-i", ses], f"lowpass=f=1800,afade=t=in:d=1.5,afade=t=out:st={sure - 2}:d=2")


def reel(kart_path, zemin_path, out_path):
    kare = out_path.replace(".mp4", "_dikey.jpg")
    dikey_kare(kart_path, zemin_path, kare)
    fr = 30
    n = SURE * fr
    vf = (f"scale=2160:-1,zoompan=z='min(zoom+0.00018,1.05)':d={n}:"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={fr},"
          f"fade=t=in:st=0:d=0.6,format=yuv420p")
    girdi, af = _ses_girdi(os.path.basename(out_path), SURE)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-loop", "1", "-i", kare,
           *girdi,
           "-vf", vf, "-af", af,
           "-t", str(SURE), "-r", str(fr),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
           "-movflags", "+faststart", "-shortest", out_path]
    subprocess.run(cmd, check=True)
    return out_path, kare


def okuma_suresi(metin, en_az=8.0, en_cok=15.0):
    """Yavaş okuyan biri için: ~2 kelime/sn + 3 sn pay."""
    return max(en_az, min(en_cok, len(metin.split()) / 2.0 + 3.0))


def ozet_reel(kartlar, zemin_path, out_path, giris_sure=3.5, kart_sure=5.0, gecis=1.0, sureler_kart=None):
    """Günün kartlarını (ilki kapak) yumuşak geçişlerle tek dikey videoda birleştirir."""
    fr = 30
    dikeyler = []
    for i, k in enumerate(kartlar):
        p = out_path.replace(".mp4", f"_{i}.jpg")
        dikey_kare(k, zemin_path, p)
        dikeyler.append(p)
    sureler = [giris_sure] + (list(sureler_kart) if sureler_kart else [kart_sure] * (len(kartlar) - 1))
    toplam = sum(sureler) - gecis * (len(kartlar) - 1)
    args = []
    for p, d in zip(dikeyler, sureler):
        args += ["-loop", "1", "-t", str(d), "-framerate", str(fr), "-i", p]
    girdi, af = _ses_girdi("ozet" + os.path.basename(out_path), toplam)
    # uzun özet için parçanın başından (15. sn) itibaren; yetmezse başa sarar
    if os.path.exists(MUZIK):
        girdi = ["-stream_loop", "-1", "-ss", "15", "-t", str(toplam + 1), "-i", MUZIK]
    fc, son, ofs = [], "[0:v]", 0.0
    for i in range(len(dikeyler)):
        fc.append(f"[{i}:v]scale={W}:{H},setsar=1,format=yuv420p[v{i}]")
    son = "[v0]"
    for i in range(1, len(dikeyler)):
        ofs += sureler[i - 1] - gecis
        fc.append(f"{son}[v{i}]xfade=transition=fade:duration={gecis}:offset={ofs:.2f}[x{i}]")
        son = f"[x{i}]"
    na = len(dikeyler)
    fc.append(f"[{na}:a]{af}[a]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *args, *girdi,
           "-filter_complex", ";".join(fc), "-map", son, "-map", "[a]",
           "-t", f"{toplam:.2f}", "-r", str(fr), "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
           "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-ac", "2",
           "-movflags", "+faststart", out_path]
    subprocess.run(cmd, check=True)
    return out_path
