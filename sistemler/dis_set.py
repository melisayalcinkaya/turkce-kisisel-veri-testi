"""Bağımsız test seti: cagrigungor/turkish-pii-masking-benchmark (CC0).

Yalnızca "tam" (tüm verileri maskele, 350) ve "negatif" (kişisel veri yok, 200)
satırları alınır; beklenen çıktıdaki [ETİKET]'ler girdideki aralıklara çevrilir.
Çıktı: veri/dis_test.jsonl
"""
import csv
import json
import sys

from huggingface_hub import hf_hub_download

sys.path.insert(0, "sistemler")
from hizalama import etiketli_hizala  # noqa: E402

yol = hf_hub_download("cagrigungor/turkish-pii-masking-benchmark", "benchmark_1000.csv", repo_type="dataset")
n = kesin = 0
with open(yol, encoding="utf-8") as f, open("veri/dis_test.jsonl", "w", encoding="utf-8") as out:
    for r in csv.DictReader(f):
        if r["kategori"] not in ("tam", "negatif"):
            continue
        if r["kategori"] == "negatif":
            assert r["expected_output"] == r["input"]
            spans, ok = [], True
        else:
            spans, ok = etiketli_hizala(r["input"], r["expected_output"])
        if not ok:
            print("hizalanamadı, atlandı:", r["id"])
            continue
        kesin += 1
        v = [{"bas": s["bas"], "son": s["son"], "tur": s["tur"], "deger": r["input"][s["bas"]:s["son"]]} for s in spans]
        out.write(json.dumps({"id": "d" + r["id"], "tur": "negatif" if r["kategori"] == "negatif" else "dis_" + (r["ozellikler"] or "duz"),
                              "metin": r["input"], "varliklar": v}, ensure_ascii=False) + "\n")
        n += 1
print(n, "satır yazıldı")
