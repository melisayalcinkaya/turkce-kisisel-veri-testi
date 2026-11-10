"""Modellerin kartlarını, etiketlerini ve boyutlarını indirir (ci-out/kesif/)."""
import json
import os
import sys

from huggingface_hub import HfApi, hf_hub_download

MODELLER = sys.argv[1:]
os.makedirs("ci-out/kesif", exist_ok=True)
api = HfApi()
ozet = {}
for m in MODELLER:
    tur = "dataset" if m.startswith("ds:") else "model"
    m = m.removeprefix("ds:")
    ad = m.replace("/", "__")
    bilgi = {}
    try:
        info = (api.dataset_info if tur == "dataset" else api.model_info)(m, files_metadata=True)
        bilgi["dosyalar"] = {s.rfilename: s.size for s in info.siblings}
        bilgi["lisans"] = (info.card_data or {}).get("license") if info.card_data else None
        bilgi["pipeline"] = info.pipeline_tag
    except Exception as e:  # noqa: BLE001
        bilgi["hata"] = repr(e)
    for dosya in ["README.md", "config.json", "tokenizer_config.json", "gliner_config.json", "chat_template.jinja"]:
        try:
            yol = hf_hub_download(m, dosya, repo_type=tur)
            with open(yol, encoding="utf-8") as f:
                icerik = f.read()
            with open(f"ci-out/kesif/{ad}__{dosya}", "w", encoding="utf-8") as f:
                f.write(icerik)
        except Exception as e:  # noqa: BLE001
            bilgi.setdefault("eksik", []).append(dosya)
    ozet[m] = bilgi
    print(m, "tamam", bilgi.get("hata", ""))
with open("ci-out/kesif/ozet.json", "w", encoding="utf-8") as f:
    json.dump(ozet, f, ensure_ascii=False, indent=1)
