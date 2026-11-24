"""Elle paylaşılacak akşam (21:00) duası için şablon görselleri üretir.
Kullanım: python elle.py [YYYY-AA-GG] [vakit]  → cikti/elle_<tarih>/ içine 3 görsel + kapak + açıklama
Instagram şablonu (3 klip x 4 sn) için: 3 görselde de dua ekranda kalır, döngü bozulmaz."""
import os, sys
from datetime import date, datetime
from PIL import Image
import bot, brand, dua_reel

gun = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else bot.bugun()
# paylaşılamayan günün duası sonraki güne kaydırılır: {"bugün": "paylaşılamayan gün"}
YERINE = {"2026-11-24": "2026-11-23"}
asil_gun = gun
gun = date.fromisoformat(YERINE.get(gun.isoformat(), gun.isoformat()))
vakit = sys.argv[2] if len(sys.argv) > 2 else "aksam"
dua, tur, baslik, tags = bot.sec(gun, vakit)
zs = brand.zeminler()
zemin = zs[((gun - bot.BASLANGIC).days * len(bot.VAKITLER) + bot.VAKITLER.index(vakit)) % len(zs)]
k = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cikti", f"elle_{asil_gun}")
os.makedirs(k, exist_ok=True)
konu, kart, sayfa, kapak = dua_reel.hazirla(dua, tur, zemin, os.path.join(k, "_"), vakit=vakit)
s = Image.open(sayfa).convert("RGB")
s.save(os.path.join(k, "1.jpg"), quality=95)
s.save(os.path.join(k, "2.jpg"), quality=95)   # 3 klip de aynı: başa sarınca da aynı görünür
s.save(os.path.join(k, "3.jpg"), quality=95)
Image.open(kapak).convert("RGB").save(os.path.join(k, "kapak.jpg"), quality=95)
cap = f"🤲 {konu}\n\n" + bot.caption(dua, tur, baslik, tags)
open(os.path.join(k, "aciklama.txt"), "w", encoding="utf-8").write(cap)
print(k)
print(cap)
