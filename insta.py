"""
Kabul Kapısı — Instagram paylaşımı (Instagram API with Instagram Login)

Akış:  slaytlar (JPEG) -> imgbb'ye yükle (herkese açık link, 1 gün sonra silinir)
       -> Instagram'da carousel kapsayıcısı oluştur -> yayınla

Gerekli GitHub Secrets:
  IG_ACCESS_TOKEN   Instagram uzun süreli erişim anahtarı (60 gün geçerli)
  IMGBB_API_KEY     imgbb.com ücretsiz API anahtarı (görselleri geçici barındırmak için)
İsteğe bağlı:
  GH_PAT            GitHub token'ı (Secrets: Read and write). Varsa bot her gece
                    Instagram anahtarını yeniler ve GitHub'a kaydeder -> 60 gün sorunu biter.
"""
import base64
import os
import time

import requests

IG_TOKEN = os.getenv("IG_ACCESS_TOKEN", "").strip()
IG_USER_ID = os.getenv("IG_USER_ID", "").strip()     # Unified login (sistem kullanıcısı) için gerekli
IMGBB_KEY = os.getenv("IMGBB_API_KEY", "").strip()
GH_PAT = os.getenv("GH_PAT", "").strip()
_VER = os.getenv("IG_API_VERSION", "v23.0")
# EAA... = Facebook/Unified login sistem kullanıcısı anahtarı (süresiz) -> graph.facebook.com
# IGAA... = Instagram login anahtarı (60 gün) -> graph.instagram.com
SYSTEM_TOKEN = IG_TOKEN.startswith("EAA")
API = ("https://graph.facebook.com/" if SYSTEM_TOKEN else "https://graph.instagram.com/") + _VER

BASE_TAGS = ["#dua", "#kabulkapisi"]


def enabled():
    if not IG_TOKEN:
        print("[insta] IG_ACCESS_TOKEN yok -> Instagram atlandı")
        return False
    if not IMGBB_KEY:
        print("[insta] IMGBB_API_KEY yok -> Instagram atlandı")
        return False
    return True


# ---------------------------------------------------------------------------
def _check(r, what):
    try:
        j = r.json()
    except Exception:
        j = {}
    if not r.ok or "error" in j:
        raise RuntimeError(f"{what} başarısız: {r.status_code} {j.get('error', r.text[:300])}")
    return j


def upload_public(path):
    """Görseli imgbb'ye yükler, herkese açık doğrudan linkini döndürür (24 saat sonra silinir)."""
    with open(path, "rb") as f:
        data = {"key": IMGBB_KEY, "image": base64.b64encode(f.read()).decode(), "expiration": 86400}
    r = requests.post("https://api.imgbb.com/1/upload", data=data, timeout=60)
    return _check(r, "imgbb yükleme")["data"]["url"]


def _user_id():
    if IG_USER_ID:
        return IG_USER_ID
    if SYSTEM_TOKEN:
        raise RuntimeError("IG_USER_ID secret'ı eksik (Unified login anahtarı için gerekli)")
    r = requests.get(f"{API}/me", params={"fields": "user_id,username", "access_token": IG_TOKEN},
                     timeout=30)
    j = _check(r, "Instagram hesap bilgisi")
    print(f"[insta] hesap: @{j.get('username')}")
    return j.get("user_id") or j["id"]


def _wait(container_id, tries=20):
    for _ in range(tries):
        r = requests.get(f"{API}/{container_id}",
                         params={"fields": "status_code", "access_token": IG_TOKEN}, timeout=30)
        st = _check(r, "durum sorgusu").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram medyayı işleyemedi: {st}")
        time.sleep(3)
    raise RuntimeError("Instagram medya işleme zaman aşımı")


def publish_carousel(image_paths, caption):
    uid = _user_id()
    urls = [upload_public(p) for p in image_paths[:10]]
    print(f"[insta] {len(urls)} görsel yüklendi")
    children = []
    for u in urls:
        r = requests.post(f"{API}/{uid}/media", timeout=60, data={
            "image_url": u, "is_carousel_item": "true", "access_token": IG_TOKEN})
        cid = _check(r, "slayt oluşturma")["id"]
        _wait(cid)
        children.append(cid)
    if len(children) == 1:   # tek görsel: normal gönderi
        r = requests.post(f"{API}/{uid}/media", timeout=60, data={
            "image_url": urls[0], "caption": caption, "access_token": IG_TOKEN})
    else:
        r = requests.post(f"{API}/{uid}/media", timeout=60, data={
            "media_type": "CAROUSEL", "children": ",".join(children),
            "caption": caption, "access_token": IG_TOKEN})
    container = _check(r, "carousel oluşturma")["id"]
    _wait(container)
    r = requests.post(f"{API}/{uid}/media_publish", timeout=60,
                      data={"creation_id": container, "access_token": IG_TOKEN})
    mid = _check(r, "yayınlama")["id"]
    print(f"[insta] ✅ paylaşıldı (medya id: {mid})")
    return mid


# ---------------------------------------------------------------------------
def make_caption(head, items, tags, foot="Özet Haberler için Takip Et & 🔔 Bildirimleri Aç",
                 credits=(), bullet=True):
    alltags = []
    for t in list(tags) + BASE_TAGS:
        if t.lower() not in [a.lower() for a in alltags]:
            alltags.append(t)
    body = "\n\n".join(f"🔸 {i}" if bullet else i for i in items)
    parts = [head, body, foot]
    if credits:
        parts.append("\n".join(credits))
    parts.append(" ".join(alltags[:5]))
    cap = "\n\n".join(p for p in parts if p)
    return cap[:2150]


def refresh_token():
    """Instagram anahtarını yeniler (60 gün daha) ve GH_PAT varsa GitHub Secret'ını günceller."""
    if SYSTEM_TOKEN:
        return True   # sistem kullanıcısı anahtarı süresiz, yenilemeye gerek yok
    if not GH_PAT:
        print("[insta] GH_PAT yok: Instagram anahtarını 60 günde bir elle yenilemen gerekir")
        return False
    try:
        r = requests.get("https://graph.instagram.com/refresh_access_token", timeout=30,
                         params={"grant_type": "ig_refresh_token", "access_token": IG_TOKEN})
        new = _check(r, "anahtar yenileme")["access_token"]
        from nacl import encoding, public   # PyNaCl
        repo = os.environ["GITHUB_REPOSITORY"]
        h = {"Authorization": f"Bearer {GH_PAT}", "Accept": "application/vnd.github+json"}
        k = requests.get(f"https://api.github.com/repos/{repo}/actions/secrets/public-key",
                         headers=h, timeout=30).json()
        box = public.SealedBox(public.PublicKey(k["key"].encode(), encoding.Base64Encoder()))
        enc = base64.b64encode(box.encrypt(new.encode())).decode()
        r = requests.put(f"https://api.github.com/repos/{repo}/actions/secrets/IG_ACCESS_TOKEN",
                         headers=h, json={"encrypted_value": enc, "key_id": k["key_id"]}, timeout=30)
        if r.status_code in (201, 204):
            print("[insta] 🔑 Instagram anahtarı yenilendi (60 gün daha geçerli)")
            return True
        print(f"[insta] anahtar GitHub'a kaydedilemedi: {r.status_code} {r.text[:200]}")
    except Exception as e:
        print(f"[insta] anahtar yenilenemedi: {e}")
    return False


# ---------------------------------------------------------------------------
# Reels (doğrudan dosya yükleme — imgbb gerekmez) ve Hikâye
RUPLOAD = "https://rupload.facebook.com/ig-api-upload/" + _VER


def _wait_long(container_id, tries=60, sleep=5):
    for _ in range(tries):
        r = requests.get(f"{API}/{container_id}",
                         params={"fields": "status_code,status", "access_token": IG_TOKEN}, timeout=30)
        j = _check(r, "durum sorgusu")
        st = j.get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram videoyu işleyemedi: {st} {j.get('status', '')}")
        time.sleep(sleep)
    raise RuntimeError("Instagram video işleme zaman aşımı")


def reel_container(video_path, caption, cover_path=None):
    """Reels kapsayıcısı oluşturur, videoyu yükler ve işlenmesini bekler. Kapsayıcı id döner."""
    uid = _user_id()
    data = {"media_type": "REELS", "upload_type": "resumable", "caption": caption,
            "share_to_feed": "true", "access_token": IG_TOKEN}
    if cover_path:
        data["cover_url"] = upload_public(cover_path)
    r = requests.post(f"{API}/{uid}/media", timeout=60, data=data)
    j = _check(r, "reels kapsayıcısı")
    cid = j["id"]
    url = j.get("uri") or f"{RUPLOAD}/{cid}"
    size = os.path.getsize(video_path)
    with open(video_path, "rb") as f:
        r = requests.post(url, data=f.read(), timeout=300, headers={
            "Authorization": f"OAuth {IG_TOKEN}", "offset": "0", "file_size": str(size)})
    _check(r, "video yükleme")
    print(f"[insta] video yüklendi ({size // 1024} KB), işleniyor...")
    _wait_long(cid)
    return cid


def yakinda_paylasildi(caption, dakika=30):
    """Son birkaç gönderide aynı açıklama son `dakika` içinde var mı? (zaman aşımına rağmen yayınlanmış olabilir)"""
    try:
        from datetime import datetime, timedelta, timezone
        r = requests.get(f"{API}/{_user_id()}/media", timeout=30, params={
            "fields": "id,caption,timestamp", "limit": 6, "access_token": IG_TOKEN})
        sinir = datetime.now(timezone.utc) - timedelta(minutes=dakika)
        for m in _check(r, "son gönderiler").get("data", []):
            ts = datetime.strptime(m["timestamp"][:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
            if ts >= sinir and (m.get("caption") or "")[:80] == caption[:80]:
                return m["id"]
    except Exception as e:
        print("[insta] son gönderi kontrolü yapılamadı:", e)
    return None


def publish_reel(video_path, caption, cover_path=None, deneme=3):
    uid = _user_id()
    for i in range(deneme):   # Instagram bazen geçici "ProcessingFailedError" veriyor: yeniden dene
        try:
            cid = reel_container(video_path, caption, cover_path)
            break
        except Exception as e:
            if i == deneme - 1:
                raise
            print(f"[insta] video yüklenemedi ({e}); {20 * (i + 1)} sn sonra yeniden denenecek")
            time.sleep(20 * (i + 1))
    for i in range(2):   # yayınlama zaman aşımına uğrarsa önce gerçekten yayınlanıp yayınlanmadığına bak
        try:
            r = requests.post(f"{API}/{uid}/media_publish", timeout=60,
                              data={"creation_id": cid, "access_token": IG_TOKEN})
            mid = _check(r, "reels yayınlama")["id"]
            break
        except Exception as e:
            time.sleep(20)
            var = yakinda_paylasildi(caption)
            if var:
                print(f"[insta] yayınlama hata verdi ama gönderi yayında ({var}); tekrar paylaşılmayacak")
                return var
            if i == 1:
                raise
            print(f"[insta] yayınlama hatası ({e}); bir kez daha denenecek")
    print(f"[insta] ✅ Reels paylaşıldı (medya id: {mid})")
    return mid


def publish_story(image_path):
    uid = _user_id()
    url = upload_public(image_path)
    r = requests.post(f"{API}/{uid}/media", timeout=60, data={
        "image_url": url, "media_type": "STORIES", "access_token": IG_TOKEN})
    cid = _check(r, "hikâye oluşturma")["id"]
    _wait(cid)
    r = requests.post(f"{API}/{uid}/media_publish", timeout=60,
                      data={"creation_id": cid, "access_token": IG_TOKEN})
    mid = _check(r, "hikâye yayınlama")["id"]
    print(f"[insta] ✅ hikâye paylaşıldı (medya id: {mid})")
    return mid
