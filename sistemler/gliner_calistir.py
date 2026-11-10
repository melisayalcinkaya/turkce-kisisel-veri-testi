"""GLiNER sıfır-atış modelleri. Kullanım: python sistemler/gliner_calistir.py <veri> <model> [...]"""
import json
import os
import sys
import time

import torch
from gliner import GLiNER

torch.set_num_threads(1)
ETIKETLER = ["person", "phone number", "email", "address", "national id number", "iban",
             "credit card number", "license plate", "date of birth"]
veri = sys.argv[1]
kayitlar = [json.loads(s) for s in open(veri, encoding="utf-8")]
cikti = "tahmin/" + os.path.basename(veri).removesuffix(".jsonl")
os.makedirs(cikti, exist_ok=True)
for model in sys.argv[2:]:
    m = GLiNER.from_pretrained(model)
    ad = model.split("/")[-1]
    sure = []
    with open(f"{cikti}/{ad}.jsonl", "w", encoding="utf-8") as out:
        for k in kayitlar:
            t0 = time.perf_counter()
            r = m.predict_entities(k["metin"], ETIKETLER, threshold=0.5)
            sure.append(time.perf_counter() - t0)
            out.write(json.dumps({"id": k["id"], "tahminler": [{"bas": e["start"], "son": e["end"], "tur": e["label"]} for e in r]},
                                 ensure_ascii=False) + "\n")
    sure.sort()
    print(model, "ms_ortanca", round(1000 * sure[len(sure) // 2]), "parametre", sum(p.numel() for p in m.parameters()))
