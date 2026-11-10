"""kvkk-pii tam hazır ayarı (regex + XLM-R NER + GLiNER). Kullanım: python sistemler/kvkk_tam.py <veri>"""
import json
import os
import sys
import time

import torch
from kvkk_pii import presets

torch.set_num_threads(1)
veri = sys.argv[1]
cikti = "tahmin/" + os.path.basename(veri).removesuffix(".jsonl")
os.makedirs(cikti, exist_ok=True)
d = presets.turkish(download_policy="auto")
sure = []
with open(f"{cikti}/kvkk_pii_tam.jsonl", "w", encoding="utf-8") as out:
    for s in open(veri, encoding="utf-8"):
        k = json.loads(s)
        t0 = time.perf_counter()
        r = d.analyze(k["metin"])
        sure.append(time.perf_counter() - t0)
        out.write(json.dumps({"id": k["id"], "tahminler": [{"bas": e.start, "son": e.end, "tur": str(e.entity_type)} for e in r.entities]},
                             ensure_ascii=False) + "\n")
sure.sort()
print("kvkk_pii_tam ms_ortanca", round(1000 * sure[len(sure) // 2]))
