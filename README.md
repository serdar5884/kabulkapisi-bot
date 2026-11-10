# Kabul Kapısı — Instagram Dua Botu

**Profil:** Kabul Kapısı · @kabulkapisi

| Saat (TR) | Ne paylaşır |
|---|---|
| 07:00 | 🤲 Günün Duası: okuyana hitap eden özel dua (Cuma sabahı: Cuma duası) |
| 13:00 | 📖 Kur'an'dan Bir Dua: ayet duası + sure/ayet kaynağı |
| 21:00 | 🌙 Hadislerden Bir Dua: hadis duası + kaynak (kandil akşamı: kandil duası) |

Maliyet: **0 TL**. Claude API, X kredisi yok. Instagram API, imgbb ve GitHub Actions ücretsiz.

## 1) Profili hazırla
- Hesabı **Profesyonel hesap** yap (Ayarlar → Hesap türü ve araçlar → Profesyonel hesaba geç → İçerik üreticisi).
- **Profil fotoğrafı:** `gorseller/logo.png`
- **Slogan önerisi (biyografiye):** Dualarda Buluşalım
- **Ad:** Kabul Kapısı
- **Biyografi:**
  ```
  🤲 Bu satırları okuyan sana bir dua var.
  Günde 3 dua: özel • Kur'an • hadis
  Amin demeyi unutma 💛
  ```

## 2) Anahtarlar (NeHaberÖzet'teki Instagram kurulumunun aynısı)
1. **Instagram:** developers.facebook.com → NeHaberÖzet için kullandığın uygulama → Instagram →
   *API setup with Instagram login* → **Generate access tokens** → **Add account** ile @kabulkapisi'yi ekle
   → token'ı kopyala (IGAA… ile başlar, 60 gün geçerli; `GH_PAT` varsa bot her gün kendisi yeniler).
   Sistem kullanıcısı (EAA…) token'ı kullanırsan `IG_USER_ID` de gerekir.
2. **imgbb:** NeHaberÖzet'teki `IMGBB_API_KEY` aynen kullanılabilir.
3. **GH_PAT (önerilir):** github.com/settings/tokens → Fine-grained → yalnızca bu repo → *Secrets: Read and write*.

## 3) GitHub'a yükle
1. github.com/new → **private** repo, adı örn. `kabulkapisi-bot`.
2. Klasördeki her şeyi yükle (`fonts/`, `gorseller/`, `.github/workflows/` dahil).
3. Settings → Secrets and variables → Actions → **Secrets**:
   `IG_ACCESS_TOKEN`, `IMGBB_API_KEY`, `GH_PAT` (ve gerekiyorsa `IG_USER_ID`).

## 4) Test → yayın
Actions → "Kabul Kapisi Botu" → **Run workflow**:
- `mode = onizleme` → önümüzdeki 3 günün 9 kartı, işin sonunda **Artifacts → onizleme** içinden indir
- `mode = post`, `vakit = sabah/ogle/aksam`, `dry_run = 1` → log'da o vaktin açıklama metnini gör, kartı **Artifacts → kartlar**'dan indir
- `tarih = 2026-12-10` ile Regaip Kandili kartını, `2026-11-13` ile Cuma kartını test edebilirsin
- Beğendiysen `dry_run = 0` ile bir kez gerçek paylaşım yap.

## 5) Otomatik zamanlama (cron-job.org) — 3 ayrı iş
Her biri için aynı ayarlar, sadece saat ve `vakit` farklı:
- **URL:** `https://api.github.com/repos/<KULLANICI>/kabulkapisi-bot/actions/workflows/gunluk-dua.yml/dispatches`
- **Method:** POST · **Saat dilimi:** Europe/Istanbul
- **Headers:** `Authorization: Bearer <GitHub token'ın>` · `Accept: application/vnd.github+json`

| İş | Saat | Body |
|---|---|---|
| Sabah | 07:00 | `{"ref":"main","inputs":{"mode":"post","dry_run":"0","vakit":"sabah"}}` |
| Öğle | 13:00 | `{"ref":"main","inputs":{"mode":"post","dry_run":"0","vakit":"ogle"}}` |
| Akşam | 21:00 | `{"ref":"main","inputs":{"mode":"post","dry_run":"0","vakit":"aksam"}}` |

Bot aynı vakit için ikinci kez tetiklenirse paylaşmaz (çift gönderi koruması).

## Dua havuzu (`dualar.json`)
- `ozel`: 60 özel dua (sabah paylaşımı). `"vakit": "aksam"` olanlar sabah atlanır.
- `kuran`: 27 Kur'an duası (öğle paylaşımı), sure ve ayet numarasıyla.
- `hadis`: 18 hadis duası (akşam paylaşımı). `"vakit": "sabah"` olanlar akşam atlanır.
- Her havuz kendi içinde sırayla döner, bitince baştan başlar (aynı dua birkaç hafta sonra tekrar gelir).
- `cuma`: 8 Cuma duası (Cuma sabahı). `kandil`: 5 kandil duası (kandil akşamı).
- `kandil_tarihleri`: Regaip 10 Aralık 2026, Miraç 4 Ocak 2027, Berat 22 Ocak 2027.
  **Kadir ve Mevlid 2027 tarihlerini Diyanet takviminden ekle.**
- Yeni dua eklemek için ilgili listeye aynı kalıpla ekle. Altın vurgulu kelimeleri `*yıldız*` arasına yazabilirsin.
- ⚠️ Ayet mealleri ve hadis metinleri yayına girmeden önce Diyanet meali ve kaynak kitapla karşılaştırılmalı.

## Arka plan görselleri (`arkaplanlar/`)
- Kartlar bu klasördeki görsellerin üstüne çizilir, her gün sıradaki görsel kullanılır (şu an 5 tane).
- Yeni görsel eklemek için 4:5 oranlı (örn. 1080×1350) bir JPG/PNG'yi klasöre at; sağ üst köşede logo için yer bırak.
- Klasör boşsa bot düz lacivert kart tasarımına döner.

## Değiştirmek istersen
- Renkler, kart düzeni, alt yazı: `brand.py` (örnek kart üretmek için `python brand.py`)
- Açıklama metni ve etiketler: `bot.py` içindeki `caption()`
- Saat: cron-job.org'daki zaman

## Hatalar
- **imgbb / Instagram 400:** token süresi dolmuş olabilir → yeni token üret, Secret'ı güncelle.
- **Paylaşılmadı, "zaten paylaşıldı":** o gün zaten gönderi atılmış.
- GitHub 60 gün işlem olmayan repoda Actions'ı durdurabilir → Actions'tan tekrar etkinleştir.
