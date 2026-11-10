"""halilneed/turkish-pii-detection (270M, üretken). Model kartındaki istem biçimi.

Kullanım: python sistemler/uretken.py <veri> [<veri> ...]
Not: hız ölçümü 4 iş parçacığıyla (üretken model tek iş parçacığında çok yavaş).
"""
import json
import os
import sys
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

sys.path.insert(0, "sistemler")
from hizalama import etiketli_hizala  # noqa: E402

torch.set_num_threads(4)
MODEL_ID = "halilneed/turkish-pii-detection"
REVISION = "28644718923ae38b0105c9f3d2be57312ad0ced3"
TALIMAT = "Metindeki tüm kişisel verileri uygun etiketlerle maskele."
tok = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID, revision=REVISION, torch_dtype=torch.float32).eval()
son_tur = tok.convert_tokens_to_ids("<end_of_turn>")


def maskele(metin):
    istem = f"{tok.bos_token}<start_of_turn>user\n{TALIMAT}\n\nMetin: {metin}<end_of_turn>\n<start_of_turn>model\n"
    g = tok(istem, return_tensors="pt", add_special_tokens=False)
    with torch.inference_mode():
        s = model.generate(**g, max_new_tokens=g["input_ids"].shape[1] + 64, do_sample=False,
                           eos_token_id=son_tur, pad_token_id=tok.eos_token_id)
    return tok.decode(s[0, g["input_ids"].shape[1]:], skip_special_tokens=True).strip()


for veri in sys.argv[1:]:
    cikti = "tahmin/" + os.path.basename(veri).removesuffix(".jsonl")
    os.makedirs(cikti, exist_ok=True)
    sure, kesin, n = [], 0, 0
    with open(f"{cikti}/turkish-pii-detection.jsonl", "w", encoding="utf-8") as out:
        for s in open(veri, encoding="utf-8"):
            k = json.loads(s)
            t0 = time.perf_counter()
            m = maskele(k["metin"])
            sure.append(time.perf_counter() - t0)
            spans, ok = etiketli_hizala(k["metin"], m)
            kesin += ok
            n += 1
            out.write(json.dumps({"id": k["id"], "tahminler": spans, "cikti": m}, ensure_ascii=False) + "\n")
    sure.sort()
    print(veri, "ms_ortanca", round(1000 * sure[len(sure) // 2]), f"kesin hizalama {kesin}/{n}")
