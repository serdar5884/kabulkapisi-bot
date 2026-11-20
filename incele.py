"""Başka bir işletme/üretici hesabını Business Discovery ile inceler (sadece okur)."""
import json, os, sys, requests
import insta
hesap = sys.argv[1] if len(sys.argv) > 1 else "duasensin"
alan = ("business_discovery.username(%s){username,name,biography,followers_count,follows_count,media_count,website,"
        "media.limit(60){caption,media_type,media_product_type,like_count,comments_count,timestamp,permalink}}" % hesap)
r = requests.get(f"{insta.API}/{insta._user_id() if hasattr(insta,'_user_id') else insta.IG_USER_ID}",
                 params={"fields": alan, "access_token": insta.IG_TOKEN}, timeout=60)
print(r.status_code)
open("incele.json", "w").write(r.text)
print(r.text[:300])
try:
    d = r.json()
    b = d["business_discovery"]
    print("PROFIL", json.dumps({k: b.get(k) for k in ("username", "name", "biography", "followers_count", "follows_count", "media_count", "website")}, ensure_ascii=False))
    for m in b["media"]["data"]:
        c = (m.get("caption") or "").replace("\n", " / ")
        print(f"GONDERI {m['timestamp'][5:16]} {m.get('media_product_type')} {m['media_type']} L{m.get('like_count')} C{m.get('comments_count')} | {c[:400]}")
except Exception as e:
    print("ozet yok:", e)
