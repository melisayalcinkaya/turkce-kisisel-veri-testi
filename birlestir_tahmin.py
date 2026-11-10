"""İki tahmin dosyasını birleştirir (kural + model katmanı). Kullanım: python birlestir_tahmin.py a.jsonl b.jsonl cikti.jsonl"""
import json
import sys

a = {json.loads(s)["id"]: json.loads(s)["tahminler"] for s in open(sys.argv[1], encoding="utf-8")}
b = {json.loads(s)["id"]: json.loads(s)["tahminler"] for s in open(sys.argv[2], encoding="utf-8")}
with open(sys.argv[3], "w", encoding="utf-8") as f:
    for k in a:
        f.write(json.dumps({"id": k, "tahminler": a[k] + b[k]}, ensure_ascii=False) + "\n")
