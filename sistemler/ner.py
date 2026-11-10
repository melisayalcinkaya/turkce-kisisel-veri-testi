"""Token sınıflandırma (NER) modellerini test setinde çalıştırır.

Kullanım: python sistemler/ner.py <veri.jsonl> <model_id> [<model_id> ...]
Çıktı: tahmin/<model>.jsonl ve ci-out/hiz.json (metin başına süre, boyut)
"""
import json
import os
import sys
import time

import torch
from huggingface_hub import HfApi
from transformers import pipeline

torch.set_num_threads(1)  # tarayıcıdaki tek iş parçacığına yakın ölçüm

veri = sys.argv[1]
kayitlar = [json.loads(s) for s in open(veri, encoding="utf-8")]
os.makedirs("tahmin", exist_ok=True)
os.makedirs("ci-out", exist_ok=True)
hiz_yol = "ci-out/hiz.json"
hiz = json.load(open(hiz_yol)) if os.path.exists(hiz_yol) else {}
api = HfApi()

for model in sys.argv[2:]:
    ad = model.split("/")[-1]
    try:
        p = pipeline("token-classification", model=model, aggregation_strategy="first", device=-1)
    except Exception as e:  # noqa: BLE001
        print(model, "YÜKLENEMEDİ", repr(e))
        continue
    parametre = sum(x.numel() for x in p.model.parameters())
    sureler = []
    with open(f"tahmin/{ad}.jsonl", "w", encoding="utf-8") as out:
        for k in kayitlar:
            t0 = time.perf_counter()
            sonuc = p(k["metin"])
            sureler.append(time.perf_counter() - t0)
            tah = [{"bas": int(r["start"]), "son": int(r["end"]), "tur": r["entity_group"], "skor": float(r["score"])}
                   for r in sonuc]
            out.write(json.dumps({"id": k["id"], "tahminler": tah}, ensure_ascii=False) + "\n")
    sureler.sort()
    hiz[ad] = {"model": model, "parametre": parametre, "ms_ortanca": 1000 * sureler[len(sureler) // 2],
               "ms_ortalama": 1000 * sum(sureler) / len(sureler), "etiketler": sorted(set(p.model.config.id2label.values()))}
    print(model, json.dumps(hiz[ad], ensure_ascii=False))
    del p
    json.dump(hiz, open(hiz_yol, "w"), ensure_ascii=False, indent=1)
