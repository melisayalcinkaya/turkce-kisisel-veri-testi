"""Maskeleme değerlendirmesi.

Bir kişisel veri "korundu" sayılır: değerinin boşluk dışı karakterlerinin
en az %90'ı herhangi bir tahminle örtülmüşse (tür önemsiz; maskelemede
etiketin adı değil, verinin gitmemesi önemli). Aksi halde "sızdı".

Yanlış alarm: hiçbir gerçek veriyle örtüşmeyen tahmin.

Kullanım: python degerlendir.py veri/test.jsonl tahmin/a.jsonl [tahmin/b.jsonl ...]
"""
import json
import sys
from collections import defaultdict

ESIK = 0.9


def oku(yol):
    with open(yol, encoding="utf-8") as f:
        return [json.loads(s) for s in f if s.strip()]


def degerlendir(altin, tahmin):
    tah = {t["id"]: t["tahminler"] for t in tahmin}
    eksik = [a["id"] for a in altin if a["id"] not in tah]
    assert not eksik, f"{len(eksik)} metin için tahmin yok"
    tur_toplam = defaultdict(int)
    tur_korunan = defaultdict(int)
    yanlis = 0
    tahmin_sayisi = 0
    negatif_alarm = 0
    negatif = 0
    sizanlar = []
    alarmlar = []
    for a in altin:
        metin = a["metin"]
        ortulu = [False] * len(metin)
        for t in tah[a["id"]]:
            for i in range(max(0, t["bas"]), min(len(metin), t["son"])):
                ortulu[i] = True
        for v in a["varliklar"]:
            idx = [i for i in range(v["bas"], v["son"]) if not metin[i].isspace()]
            oran = sum(ortulu[i] for i in idx) / len(idx)
            tur_toplam[v["tur"]] += 1
            if oran >= ESIK:
                tur_korunan[v["tur"]] += 1
            else:
                sizanlar.append((a["id"], v["tur"], v["deger"], round(oran, 2)))
        if a["tur"] == "negatif":
            negatif += 1
            if tah[a["id"]]:
                negatif_alarm += 1
        for t in tah[a["id"]]:
            tahmin_sayisi += 1
            if not any(t["bas"] < v["son"] and v["bas"] < t["son"] for v in a["varliklar"]):
                yanlis += 1
                alarmlar.append((a["id"], metin[t["bas"]:t["son"]]))
    toplam = sum(tur_toplam.values())
    korunan = sum(tur_korunan.values())
    return {
        "korunan_oran": korunan / toplam,
        "sizinti": toplam - korunan,
        "toplam": toplam,
        "tur": {k: (tur_korunan[k], tur_toplam[k]) for k in sorted(tur_toplam)},
        "yanlis_alarm": yanlis,
        "tahmin": tahmin_sayisi,
        "kesinlik": (tahmin_sayisi - yanlis) / tahmin_sayisi if tahmin_sayisi else 0.0,
        "negatif_alarm": (negatif_alarm, negatif),
        "sizanlar": sizanlar,
        "alarmlar": alarmlar,
    }


def main():
    altin = oku(sys.argv[1])
    turler = ["KISI", "TCKN", "TELEFON", "IBAN", "EPOSTA", "ADRES", "PLAKA", "KART", "DOGUM_TARIHI"]
    kisa = ["KİŞİ", "TCKN", "TEL", "IBAN", "EPOS", "ADR", "PLK", "KART", "DOĞ"]
    print(f"{'sistem':28} {'korunan':>8} " + " ".join(f"{k:>5}" for k in kisa) + f" {'kesinlik':>8} {'y.alarm':>7} {'neg':>6}")
    sonuc = {}
    for yol in sys.argv[2:]:
        ad = yol.rsplit("/", 1)[-1].removesuffix(".jsonl")
        r = degerlendir(altin, oku(yol))
        sonuc[ad] = r
        hucre = []
        for t in turler:
            k, n = r["tur"].get(t, (0, 0))
            hucre.append(f"{100 * k / n:5.0f}" if n else "    -")
        na, nn = r["negatif_alarm"]
        print(f"{ad:28} {100 * r['korunan_oran']:7.1f}% " + " ".join(hucre)
              + f" {100 * r['kesinlik']:7.1f}% {r['yanlis_alarm']:7d} {na:>2}/{nn}")
    with open("sonuc/ozet.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
