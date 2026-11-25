"""Kabul Kapısı — kendi hesabının son gönderi istatistikleri (SADECE OKUR, hiçbir şey paylaşmaz)."""
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone

import requests

import insta

TR = timezone(timedelta(hours=3))
METRIKLER = ["reach", "saved", "shares", "total_interactions", "views", "plays", "likes", "comments"]


def get(path, **params):
    params["access_token"] = insta.IG_TOKEN
    r = requests.get(f"{insta.API}/{path}", params=params, timeout=60)
    try:
        j = r.json()
    except Exception:
        j = {"error": {"message": r.text[:200]}}
    return r.ok and "error" not in j, j


def insights(mid):
    out = {}
    # Önce hepsini tek istekte dene; olmazsa tek tek (desteklenmeyen metriği atla)
    ok, j = get(f"{mid}/insights", metric=",".join(METRIKLER))
    if ok:
        for d in j.get("data", []):
            out[d["name"]] = (d.get("values") or [{}])[0].get("value", d.get("total_value", {}).get("value"))
        return out, None
    hata = None
    for m in METRIKLER:
        ok, j = get(f"{mid}/insights", metric=m)
        if ok:
            for d in j.get("data", []):
                out[d["name"]] = (d.get("values") or [{}])[0].get("value")
        elif hata is None:
            hata = (j.get("error") or {}).get("message", "")[:160]
    return out, hata


def tur(m):
    c = (m.get("caption") or "")
    if "Cuma" in c[:80] or "cuma" in c[:80].lower():
        return "cuma"
    if "Kaynak" in c and ("1." in c or "liste" in c.lower()):
        return "liste?"
    return "dua"


def main():
    uid = insta._user_id()
    ok, prof = get(uid, fields="username,followers_count,follows_count,media_count")
    print("PROFIL", json.dumps(prof if ok else {"hata": prof.get("error", {}).get("message")}, ensure_ascii=False))
    ok, j = get(f"{uid}/media", fields="id,caption,media_product_type,media_type,timestamp,like_count,comments_count,permalink", limit=50)
    if not ok:
        print("MEDIA HATA", (j.get("error") or {}).get("message"))
        return
    satirlar, ilk_hata = [], None
    for m in j.get("data", []):
        ins, hata = insights(m["id"])
        if hata and not ilk_hata:
            ilk_hata = hata
        ts = datetime.strptime(m["timestamp"], "%Y-%m-%dT%H:%M:%S%z").astimezone(TR)
        s = {"t": ts.strftime("%m-%d %a %H:%M"), "saat": ts.strftime("%H"), "gun": ts.strftime("%a"),
             "tip": m.get("media_product_type"), "L": m.get("like_count"), "C": m.get("comments_count"),
             **ins, "cap": (m.get("caption") or "").replace("\n", " / ")[:260], "link": m.get("permalink")}
        satirlar.append(s)
        print("GONDERI", json.dumps(s, ensure_ascii=False))
    if ilk_hata:
        print("INSIGHTS UYARI:", ilk_hata)
    # Saat bazlı özet
    grup = defaultdict(list)
    for s in satirlar:
        grup[s["saat"]].append(s)
    for saat, ls in sorted(grup.items()):
        def ort(k):
            v = [x.get(k) for x in ls if isinstance(x.get(k), (int, float))]
            return round(sum(v) / len(v), 1) if v else None
        print(f"SAAT {saat}: n={len(ls)} begeni={ort('L')} yorum={ort('C')} erisim={ort('reach')} "
              f"izlenme={ort('views')} kaydet={ort('saved')} paylas={ort('shares')}")
    json.dump(satirlar, open("istatistik.json", "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
