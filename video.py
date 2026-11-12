"""
Kabul Kapısı — dua kartından Reels videosu (1080x1920, ~9 sn) ve hikâye görseli üretir.
Ses: ffmpeg ile üretilen sakin bir fon tonu (telif yok).
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


def reel(kart_path, zemin_path, out_path):
    kare = out_path.replace(".mp4", "_dikey.jpg")
    dikey_kare(kart_path, zemin_path, kare)
    fr = 30
    n = SURE * fr
    vf = (f"scale=2160:-1,zoompan=z='min(zoom+0.00018,1.05)':d={n}:"
          f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H}:fps={fr},"
          f"fade=t=in:st=0:d=0.6,format=yuv420p")
    ses = ("aevalsrc='0.05*sin(2*PI*196*t)+0.04*sin(2*PI*246.94*t)+0.035*sin(2*PI*293.66*t)"
           "+0.02*sin(2*PI*392*t)*(0.6+0.4*sin(2*PI*0.25*t))':s=44100:d=" + str(SURE))
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-loop", "1", "-i", kare,
           "-f", "lavfi", "-i", ses,
           "-vf", vf, "-af", f"lowpass=f=1800,afade=t=in:d=1.5,afade=t=out:st={SURE - 2}:d=2",
           "-t", str(SURE), "-r", str(fr),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
           "-movflags", "+faststart", "-shortest", out_path]
    subprocess.run(cmd, check=True)
    return out_path, kare
