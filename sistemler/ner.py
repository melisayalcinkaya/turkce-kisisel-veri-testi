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
CIKTI = "tahmin/" + os.path.basename(veri).removesuffix(".jsonl")
os.makedirs(CIKTI, exist_ok=True)
os.makedirs("ci-out", exist_ok=True)
hiz_yol = "ci-out/hiz.json"
hiz = json.load(open(hiz_yol)) if os.path.exists(hiz_yol) else {}
api = HfApi()

# "first": model kartının önerdiği toplama. "birlesik": ham token etiketleri,
# yalnızca boşluk/hiçbir şeyle ayrılan bitişik varlık token'ları tek parça yapılır.
# İlk koşuda "first" e-postaları ve parantezleri yanlış böldüğü için ikisi de ölçülür.
MOD = os.environ.get("NER_MOD", "first")


def birlestir(metin, tokenlar):
    parcalar = []
    for t in tokenlar:
        if t["entity"] == "O" or t.get("start") is None:
            continue
        bas, son = int(t["start"]), int(t["end"])
        tur = t["entity"].split("-", 1)[-1]
        if parcalar:
            onceki = parcalar[-1]
            ara = metin[onceki["son"]:bas]
            ayni_kelime = bas <= onceki["son"] or ara == ""
            devam = ara.strip() == "" and onceki["tur"] == tur and not t["entity"].startswith("B-")
            if ayni_kelime or devam:
                onceki["son"] = max(onceki["son"], son)
                continue
        parcalar.append({"bas": bas, "son": son, "tur": tur, "skor": float(t["score"])})
    return parcalar


for model in sys.argv[2:]:
    ad = model.split("/")[-1] + ("" if MOD == "first" else "__" + MOD)
    try:
        p = pipeline("token-classification", model=model, device=-1,
                     aggregation_strategy="first" if MOD == "first" else "none")
    except Exception as e:  # noqa: BLE001
        print(model, "YÜKLENEMEDİ", repr(e))
        continue
    parametre = sum(x.numel() for x in p.model.parameters())
    sureler = []
    with open(f"{CIKTI}/{ad}.jsonl", "w", encoding="utf-8") as out:
        for k in kayitlar:
            t0 = time.perf_counter()
            sonuc = p(k["metin"])
            sureler.append(time.perf_counter() - t0)
            if MOD == "first":
                tah = [{"bas": int(r["start"]), "son": int(r["end"]), "tur": r["entity_group"], "skor": float(r["score"])}
                       for r in sonuc]
            else:
                tah = birlestir(k["metin"], sonuc)
            out.write(json.dumps({"id": k["id"], "tahminler": tah}, ensure_ascii=False) + "\n")
    sureler.sort()
    hiz[f"{os.path.basename(CIKTI)}/{ad}"] = {"model": model, "parametre": parametre, "ms_ortanca": 1000 * sureler[len(sureler) // 2],
               "ms_ortalama": 1000 * sum(sureler) / len(sureler), "etiketler": sorted(set(p.model.config.id2label.values()))}
    print(model, json.dumps(hiz[f"{os.path.basename(CIKTI)}/{ad}"], ensure_ascii=False))
    del p
    json.dump(hiz, open(hiz_yol, "w"), ensure_ascii=False, indent=1)
