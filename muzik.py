"""Reels müziği: iki parça dönüşümlü. muzik.mp3 (ney), muzik2.mp3 (Gemini, 'Breath of the Sanctuary' 0:58-2:02, canlı bölüm)."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
ESKI = [47, 15, 64, 33, 86, 75, 99, 110]
YENI = [2, 9, 16, 23, 30, 37, 44, 50]


def sec(n):
    """n: gün sırası + vakit; (dosya yolu, başlangıç sn) döner."""
    if n % 2 == 0:
        return os.path.join(HERE, "ses", "muzik.mp3"), ESKI[(n // 2) % 8]
    return os.path.join(HERE, "ses", "muzik2.mp3"), YENI[(n // 2) % 8]
