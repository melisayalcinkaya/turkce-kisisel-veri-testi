---
language:
- tr
- en
license: gemma
base_model: cagrigungor/pii-guard-turkish-270m
pipeline_tag: text-generation
library_name: transformers
tags:
- pii
- pii-detection
- turkish-nlp
- personal-data
- data-redaction
- anonymization
- masking
- kvkk
- gdpr
- turkish
- privacy
- on-device
- data-masking
- redaction
- turkish-pii
- text-anonymization
- ner
- named-entity-recognition
- tckn
- iban
model-index:
- name: turkish-pii-detection
  results:
  - task:
      type: text-generation
      name: Instruction-conditional PII masking
    dataset:
      name: Turkish PII Masking Benchmark (1,000 rows)
      type: cagrigungor/turkish-pii-masking-benchmark
      split: test
    metrics:
    - type: exact_match
      name: Row-level exact match (all 1,000 rows)
      value: 0.944
    - type: exact_match
      name: Row-level exact match, schema-neutral (903 rows)
      value: 0.951
widget:
- example_title: "Tümünü maskele / Mask all"
  text: "Metindeki tüm kişisel verileri uygun etiketlerle maskele.\n\nMetin: müşteri Ayşe Yılmaz tc 12345678950 tel 0532 111 22 33 e-posta demo@example.com"
- example_title: "Yalnızca telefon / Phone only"
  text: "Metindeki yalnızca telefon numaralarını maskele; diğer tüm bilgileri olduğu gibi koru.\n\nMetin: Mehmet Demir'e 0505 444 55 66 numarasından ulaşabilirsiniz, IBAN TR33 0006 1005 1978 6457 8413 26."
---

# Turkish PII Detection and Masking — Türkçe Kişisel Veri Maskeleme (v02)

**What is this model?** turkish-pii-detection is a 270M Turkish model for local PII masking: following a Turkish instruction, it replaces personal data such as names, TCKN, IBAN, phone numbers, e-mail and postal addresses with one of 53 labels.

> **EN:** Turkish PII detection / KVKK data masking — a 270M model that masks Turkish personal data (names, TCKN, IBAN, phone, e-mail, address; 53 labels) following a Turkish instruction.
> **TR:** Türkçe kişisel veri (PII) tespiti / KVKK veri maskeleme — Türkçe talimata göre kişisel verileri 53 etiketle maskeleyen 270M model.
> **Model page & setup help / Model sayfası ve kurulum desteği:** [halilneed.agency/models/turkish-pii-detection](https://halilneed.agency/models/turkish-pii-detection/?utm_source=huggingface&utm_medium=model_card&utm_campaign=turkish-pii-detection&utm_content=top_site)

[![Try the demo](https://img.shields.io/badge/%F0%9F%A4%97%20Try%20the%20demo-Spaces-yellow)](https://huggingface.co/spaces/halilneed/turkish-pii-detection-demo)

**[halilneed/turkish-pii-detection](https://huggingface.co/halilneed/turkish-pii-detection)** is a **270M-parameter model for Turkish PII detection and instruction-conditioned masking**, by [halilneed](https://halilneed.agency/). PII means personally identifiable information. Give it Turkish text and a Turkish masking instruction: it generates text with the requested personal-data fields replaced by labels.

Choose **full masking**, **selected fields only**, or **everything except specified fields**. The model produces transformed text; it does not return named-entity recognition (NER) spans, token labels or character offsets. For a structured NER pipeline, choose a span-based detector.

**Türkçe:** Verilen talimata göre Türkçe metindeki kişisel verileri maskeleyen 270M parametreli model. Tümünü, yalnızca seçilen alanları veya belirtilen alanlar dışındakileri maskeleyebilirsiniz. Türkçe tanıtım, sonuçlar, eğitim tarifi ve kullanım açıklamaları aşağıda korunmuştur.

[Interactive browser demo / Metninizi deneyin](https://huggingface.co/spaces/halilneed/turkish-pii-detection-demo) · [Python tutorial and recorded examples](https://github.com/halilneed/turkish-pii-detection/blob/main/docs/python-turkish-pii-masking.md) · [Source code](https://github.com/halilneed/turkish-pii-detection) · [Model overview](https://halilneed.agency/models/turkish-pii-detection/) · [Türkçe tanıtım](https://halilneed.agency/models/turkish-pii-detection/tr/)

Ekipler için rehber: [Kişisel veri ve yapay zekâ](https://halilneed.agency/guides/personal-data/tr/) (metni bir modele göndermeden önce neyi maskelemeli, neyi içeride tutmalı)

## English technical guide

### What the model does

The 53-label masking schema and instruction families are inherited from v01. Names, national identifiers, phone numbers, email addresses and other personal-data expressions are transformed according to the policy. A restricted policy intentionally preserves fields that were not selected for masking.

Use cases include preparing Turkish support messages, application logs or document excerpts before passing them to an LLM or another system. Validate the output on representative data. Local CPU or GPU inference is supported after downloading the model and dependencies. The online browser demo accepts your own text and runs a separate quantized ONNX conversion on your device. Its first run downloads approximately 472 MB of model files, plus the runtime. The application does not send inputs to a backend. Quantized outputs can differ from the original Python model; the original benchmark scores have not been revalidated for this conversion. The local Python demo uses the original weights. Use fictional data while evaluating behavior.

The canonical repository serves **v02** on `main`. The old `turkish-pii-detection-v01` URL redirects here. Use `revision="v01"` for the earlier release. A commit SHA pins a specific snapshot; the examples below pin the recorded v02 weights revision.

### Python quick start: Turkish PII masking

The following is the tested CPU inference path. Install the dependencies in a fresh environment:

```bash
python -m pip install torch==2.8.0 transformers==4.56.1
```

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "halilneed/turkish-pii-detection"
REVISION = "28644718923ae38b0105c9f3d2be57312ad0ced3"

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=REVISION)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID, revision=REVISION, torch_dtype=torch.float32
).to("cpu").eval()
end_turn = tokenizer.convert_tokens_to_ids("<end_of_turn>")

def mask_turkish_pii(text, instruction):
    prompt = (
        f"{tokenizer.bos_token}<start_of_turn>user\n{instruction}\n\n"
        f"Metin: {text}<end_of_turn>\n<start_of_turn>model\n"
    )
    inputs = tokenizer(prompt, return_tensors="pt", add_special_tokens=False)
    with torch.inference_mode():
        sequence = model.generate(
            **inputs, max_new_tokens=512, do_sample=False,
            eos_token_id=end_turn, pad_token_id=tokenizer.eos_token_id,
        )
    generated = sequence[0, inputs["input_ids"].shape[1]:]
    return tokenizer.decode(generated, skip_special_tokens=True).strip()

text = "müşteri Ayşe Yılmaz tc 12345678901 tel 0532 111 22 33 e-posta demo@example.com."
print(mask_turkish_pii(text, "Metindeki tüm kişisel verileri uygun etiketlerle maskele."))
```

The BOS token and Gemma turn markers are part of the prompt contract. Keep `add_special_tokens=False` to avoid adding a second BOS token. Instructions and input text are Turkish; English documentation does not imply English-language detection capability.

For GPU inference, choose a dtype supported by your hardware and move both model and tensors to the same device. The original Turkish usage section below retains the GPU-oriented example. The companion `examples/mask.py` keeps its historical v01 default; pass the v02 revision explicitly.

### Compare three masking policies

Use the same fictional input with these Turkish instructions:

| Policy | Instruction |
| --- | --- |
| Mask all | `Metindeki tüm kişisel verileri uygun etiketlerle maskele.` |
| Phone only | `Metindeki yalnızca telefon numaralarını maskele; diğer tüm bilgileri olduğu gibi koru.` |
| Keep names | `Metindeki kişi isimleri hariç tüm kişisel verileri uygun etiketlerle maskele. Kişi isimlerini olduğu gibi koru.` |

The [interactive browser demo](https://huggingface.co/spaces/halilneed/turkish-pii-detection-demo) lets you enter your own text and compare the three policies using real client-side inference. Its quantized ONNX conversion reproduced the three recorded examples and passed a different phone/email example in browser checks; these checks do not establish general accuracy. Run the [local Python demo](https://github.com/halilneed/turkish-pii-detection/tree/main/demo) to use the original weights. The [Python tutorial](https://github.com/halilneed/turkish-pii-detection/blob/main/docs/python-turkish-pii-masking.md) records actual outputs from the pinned revision. These are functional examples, not a rerun of the 1,000-row benchmark.

### Evaluation results and their scope

Benchmark: [cagrigungor/turkish-pii-masking-benchmark](https://huggingface.co/datasets/cagrigungor/turkish-pii-masking-benchmark), 1,000 synthetic Turkish examples. The metric is **whole-row exact match**: the complete generated output must match the expected string.

| Metric / slice | v01 rerun | v02 |
| --- | ---: | ---: |
| Exact match, all 1,000 examples | 0.880 | **0.944** |
| Schema-neutral subset, 903 examples | 0.900 | **0.951** |
| B partition, 531 examples not used for selection | 0.885 | **0.945** |
| Full masking | 0.851 | 0.917 |
| Whitelist | 0.895 | 0.940 |
| Blacklist | 0.893 | 0.967 |
| Out of scope | 0.960 | 1.000 |
| Non-PII traps | 0.865 | 0.950 |
| Long text | 0.656 | 0.844 |
| Uppercase | 0.775 | 0.838 |
| Suffixed PII | 0.758 | 0.803 |
| Multiple people | 0.600 | 0.750 |
| Numbers written as words | 0.946 | 1.000 |
| Multi-field records | 0.968 | 0.980 |

These are the existing release results. The benchmark was **not rerun for this documentation or demo update**. The historical v01 card reported 0.882 / 0.902; the publisher attributes the 0.880 / 0.900 rerun difference to bf16 batched inference, affecting two rows.

Exact match is not entity recall or a guarantee that real documents are safe to share. This is an evaluation benchmark, not the training dataset. The Turkish section preserves the original result table and comparison context.

### Training recipe and benchmark use

1. **Synthetic generation:** 40,000 examples covering 53 labels, about 1,500 hand-written templates, Turkish suffixes, uppercase/ASCII transformations, numbers written as words and about 600 policy instructions.
2. **Teacher alignment:** retain v01's boundaries when its output is a valid masking of the input with the same label set. Remove 7,136 conflicting examples in semantic categories; 32,864 examples remain.
3. **Continued full fine-tuning:** initialize from v01; train for one epoch at learning rate 2e-5 and effective batch size 32, with loss on output tokens only.
4. **Weight interpolation:** combine 0.5 of the fine-tuned weights with 0.5 of v01. Standalone fine-tuning regressed to 0.844 on the benchmark; interpolation was selected to retain strengths from both models.

The original card says benchmark row contents were not used as training examples or templates, and synthetic data passed an automatic overlap filter. Aggregate benchmark feedback did influence development: slice scores and, once, aggregate label-group accuracy were reviewed.

The interpolation ratio was selected using the **A partition (469 rows)**, the generator's development set and internal probes. The **B partition (531 rows)** was not used for selection, according to the release account. Its reported comparison is **0.885 → 0.945**. This is the publisher's disclosed selection boundary, not an independent contamination audit.

### Limitations and failure handling

- Evaluation uses synthetic data. Test on your own representative Turkish text before relying on the model.
- Weaker slices include multiple people (0.750), suffixed PII (0.803) and uppercase text (0.838).
- Very short fields without person context can remain unmasked. A standalone tax-number fragment is a known example; include the relevant context and review the result.
- Generation can miss PII, modify unrelated text or produce labels outside the expected schema. Check preservation as well as masking.
- Empty output and output that reaches the token limit require review. The demo reports truncation instead of silently treating incomplete text as a successful result.
- Phone-only and keep-names policies deliberately leave some PII visible. Select a policy appropriate to the intended use.
- Masking alone does not establish irreversible anonymization or KVKK/GDPR compliance. Model weights and use are subject to [Gemma Terms of Use](https://ai.google.dev/gemma/terms).

The original release reports about 600 ms per short sentence and 1.6 GB RAM on an Intel i5-12400F, fp32, eight threads and batch size one. These figures describe that measurement setup; the public CPU demo and other hardware may differ.

### Related Turkish privacy models

[Turkish KVKK classifier](https://huggingface.co/halilneed/turkish-kvkk-classifier) predicts data categories that can inform a masking policy. [Turkish BSEBY classifier](https://huggingface.co/halilneed/turkish-bseby-classifier) classifies banking-data categories. These classifiers complement text masking; they do not perform the same task.

### Related models / İlgili modeller

- **[halilneed/turkish-pii-detection](https://huggingface.co/halilneed/turkish-pii-detection)** — instruction-conditioned PII masking / talimatla kişisel veri maskeleme (270M) (this model / bu model)
- [halilneed/turkish-pii-detection-GGUF](https://huggingface.co/halilneed/turkish-pii-detection-GGUF) — GGUF (BF16, Q8_0) for Ollama & llama.cpp, CPU / çevrimdışı GGUF sürümü
- [halilneed/turkish-kvkk-classifier](https://huggingface.co/halilneed/turkish-kvkk-classifier) — KVKK / VERBİS personal-data category classifier / kişisel veri kategori sınıflandırıcı
- [halilneed/turkish-bseby-classifier](https://huggingface.co/halilneed/turkish-bseby-classifier) — BSEBY banking data & secrecy classifier / bankacılık veri ve sır sınıflandırıcı
- [halilneed/turkish-prompt-injection-classifier](https://huggingface.co/halilneed/turkish-prompt-injection-classifier) — Turkish prompt injection detection / Türkçe prompt injection tespiti

All five in one collection / Hepsi tek koleksiyonda: [Turkish Privacy & Safety Models](https://huggingface.co/collections/halilneed/turkish-privacy-and-safety-models-6ade6ec9fb541af26bc42e0d)

## Türkçe tanıtım ve teknik açıklamalar

Türkçe metindeki kişisel verileri, metin bir LLM'e, log deposuna ya da üçüncü tarafa gitmeden önce maskeleyen 270M parametrelik model. Maskeleme politikasını talimat olarak okur: tümünü maskele, yalnızca şu alanları, şunlar hariç hepsini.

Bu repo daha önce `turkish-pii-detection-v01` adıyla yayındaydı; eski adres buraya yönlendirir. **v01** `revision="v01"` ile aynen erişilebilir. v02, v01'in devamıdır; aynı benchmark'ta **0.880'den 0.944'e** çıktı ve tüm dilimlerde iyileşti; en büyük kazanç uzun metinde (0.656 → 0.844) ve tuzaklarda (0.865 → 0.950).

```
Girdi : MÜŞTERİ SELİM ÖNAL TC 28459163012 TEL 05357213344, İŞYERİ ARÇELİK
Çıktı : MÜŞTERİ [AD] TC [TCKN] TEL [TEL], İŞYERİ [ISYERI]
```

Kullanım örnekleri ve değerlendirme aracı: [github.com/halilneed/turkish-pii-detection](https://github.com/halilneed/turkish-pii-detection)

v01'in nasıl eğitildiği ve hangi dilimlerin gerilediği: [Daha büyük model eğitmedim, zayıf dilimleri eğittim](https://halilneed.medium.com/daha-b%C3%BCy%C3%BCk-model-e%C4%9Fitmedim-zay%C4%B1f-dilimleri-e%C4%9Fittim-f4dcc4afaf5d) (Medium)

Maskeleme öncesi kategori tespiti: [halilneed/turkish-kvkk-classifier](https://huggingface.co/halilneed/turkish-kvkk-classifier) · değerlendirme seti: [halilneed/turkish-kvkk-classification-benchmark](https://huggingface.co/datasets/halilneed/turkish-kvkk-classification-benchmark)

Bankacılık veri sınıfı (hassas veri, müşteri sırrı, banka sırrı — BSEBY): [halilneed/turkish-bseby-classifier](https://huggingface.co/halilneed/turkish-bseby-classifier)

## Sonuçlar

Benchmark: [cagrigungor/turkish-pii-masking-benchmark](https://huggingface.co/datasets/cagrigungor/turkish-pii-masking-benchmark) — 1.000 sentetik test örneği, satır düzeyi tam eşleşme.

Bu veri seti değerlendirme benchmark’ıdır; eğitim verisi olarak listelenmez. Eğitimde kullanılan sentetik veri ve benchmark’ın geliştirme sırasında nasıl kullanıldığı aşağıdaki bölümlerde ayrı açıklanır. Tam eşleşme, varlık düzeyinde recall ya da gerçek belgelerin paylaşılmasının güvenli olduğu anlamına gelmez.

| | v01 | **v02** |
|---|---|---|
| **Tam eşleşme (1.000)** | 0.880 | **0.944** |
| **Şema-nötr (903)** | 0.900 | **0.951** |
| Benchmark'ın B yarısı (531, seçimde hiç kullanılmadı) | 0.885 | **0.945** |
| Tam maskeleme | 0.851 | 0.917 |
| Beyaz liste | 0.895 | 0.940 |
| Kara liste | 0.893 | 0.967 |
| Kapsam dışı | 0.960 | 1.000 |
| PII içermeyen tuzaklar | 0.865 | 0.950 |
| Uzun metin | 0.656 | **0.844** |
| BÜYÜK HARF | 0.775 | 0.838 |
| Ek almış PII ("Cem Aslan'ın") | 0.758 | 0.803 |
| Çok kişili metin | 0.600 | 0.750 |
| Sözle yazılmış sayılar | 0.946 | 1.000 |
| Çok alanlı kayıt | 0.968 | 0.980 |

v01 sütunu bu makinede, aynı değerlendirme betiğiyle yeniden ölçüldü (kartındaki 0.882 / 0.902'den bf16 toplu çıkarım farkıyla 2 satır aşağı).

Aynı benchmark'ta diğer modellerin **kendi kartlarında yayınladıkları** skorlar (yeniden koşulmadı): cagrigungor/pii-guard-turkish-0.8b 0.876 / 0.889 · melikegks/turkish-pii-guard-0.8b şema-nötr 0.922.

### Benchmark nasıl kullanıldı

Eğitim verisi benchmark satırlarına bakılmadan yazıldı ve otomatik kirlilik süzgecinden geçti (benchmark girdisiyle 8 kelimelik ortak dizi ya da birebir aynı talimat içeren satır atıldı). Geliştirme sırasında benchmark'tan toplu geri bildirim alındı: dilim skorları ve bir kez etiket grubu bazında toplu doğruluk. Bu yüzden benchmark id'ye göre ikiye bölündü; interpolasyon oranı A yarısı (469 satır), üreteç dev seti ve kendi yoklama cümlelerimize göre seçildi. **B yarısı (531 satır) seçimde kullanılmadı; temiz karşılaştırma 0.885 → 0.945'tir.** Satır içerikleri hiçbir aşamada eğitim ya da şablon için kullanılmadı.

## Nasıl eğitildi

1. **Sentetik veri üreteci:** 53 etiket, ~1.500 elle yazılmış şablon (bankacılık, İK, sağlık, telekom, e-ticaret, araç, BT logları, uzun e-posta/çağrı dökümü, çok kişili metin, çok alanlı kayıt, ~800 tuzak), ünlü uyumlu ek motoru, Türkçe BÜYÜK HARF / ASCII dönüşümü, sözle yazım ve ~600 farklı politika talimatı. 40.000 örnek.
2. **Öğretmen hizalaması:** Etiket sınırları v01'in sınırlarına hizalandı. v01'in çıktısı girdinin geçerli bir maskelemesiyse ve etiket kümesi aynıysa v01'in sınırları alındı. Anlamsal etiketlerde (sağlık, aile, biyometrik…) v01 ile çelişen 7.136 örnek atıldı. Kalan: 32.864 örnek.
3. **Devam eğitimi:** v01'den full fine-tune, 1 epoch, lr 2e-5, efektif batch 32, loss yalnızca çıktıda.
4. **Ağırlık interpolasyonu (WiSE-FT):** θ = 0.5·θ_fine-tune + 0.5·θ_v01. Tek başına fine-tune benchmark'ta 0.844'e geriledi (üreteç dağılımına kaydı); interpolasyon iki modelin güçlü yanlarını birleştirdi.

## Kullanım

Prompt biçimi v01 ile aynı; başta BOS token gerekir.

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL = "halilneed/turkish-pii-detection"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForCausalLM.from_pretrained(MODEL, dtype=torch.bfloat16, device_map="auto").eval()
# v01'i birebir kullanmak için: from_pretrained(MODEL, revision="v01")

def maskele(metin, talimat="Metindeki tüm kişisel verileri uygun etiketlerle maskele."):
    prompt = (f"{tokenizer.bos_token}<start_of_turn>user\n{talimat}\n\n"
              f"Metin: {metin}<end_of_turn>\n<start_of_turn>model\n")
    girdi = tokenizer(prompt, return_tensors="pt", add_special_tokens=False).to(model.device)
    with torch.inference_mode():
        cikti = model.generate(**girdi, max_new_tokens=512, do_sample=False,
                               eos_token_id=tokenizer.convert_tokens_to_ids("<end_of_turn>"),
                               pad_token_id=tokenizer.eos_token_id)
    return tokenizer.decode(cikti[0, girdi["input_ids"].shape[1]:], skip_special_tokens=True).strip()

print(maskele("müşteri Ayşe Yılmaz tc 12345678901 tel 0532 111 22 33"))
# -> müşteri [AD] tc [TCKN] tel [TEL]
```

CPU'da: `dtype=torch.float32` kullan, `device_map`'i kaldır. Ölçüm: Intel i5-12400F, fp32, 8 iş parçacığı, batch 1 → ~600 ms / cümle (ortalama 50 karakter), ~1.6 GB RAM.

Politikalar ve 53 etiketlik şema v01 ile aynıdır (tam, beyaz liste, kara liste, kategori, kapsam dışı).

## Sınırlar

- Sentetik veriyle değerlendirildi; üretime almadan önce kendi metninde ölç.
- **Bağlamsız kısa parçalarda temkinli:** "vergi numarası 4810271935" tek başına maskelenmeyebilir; kişi bağlamı olan cümlede ("müşterinin vergi numarası …") maskelenir. Tek alanlı kayıtları bağlamla birlikte ver.
- En zayıf dilimler: çok kişili metin (0.750), ek almış PII (0.803), BÜYÜK HARF (0.838).
- Şema dışı etiket üretebilir; çıktıyı etiket listesine karşı doğrula.
- KVKK/GDPR uyumu kullananın sorumluluğundadır. Lisans: [Gemma Terms of Use](https://ai.google.dev/gemma/terms).

## Frequently asked questions / Sık sorulan sorular

**Is this a Turkish NER model?** It generates masked text; it does not return token labels or entity offsets. For structured spans, use a span-based detector instead.

**Can it run locally?** Yes. Download the weights and dependencies first; the usage section includes CPU settings. Published latency measurements apply to the stated hardware and input length.

**How is it different from KVKK classification?** This model transforms text. The separate [Turkish KVKK classifier](https://huggingface.co/halilneed/turkish-kvkk-classifier) predicts data categories, which can inform a masking policy.

**Which version do I get?** The canonical repository serves v02 on `main`. Select `revision="v01"` for the older release or pin a commit SHA to reproduce a specific snapshot. The companion repository's inference example retains its historical v01 default; its quick-start command explicitly selects v02.

**KVKK uyumluluğu sağlar mı?** Maskeleme çıktısı tek başına hukuki uyumluluk veya geri döndürülemez anonimleştirme garantisi vermez. Çıktıyı ve kullanım bağlamını değerlendirin.

## Changelog

- **v02 — 2026-09-30:** 0.944 / 0.951. Yeni üreteç, öğretmen hizalaması, WiSE-FT. Repo `turkish-pii-detection-v01` → `turkish-pii-detection` olarak yeniden adlandırıldı. **Davranış değişikliği:** sürüm sabitlemeden indirenler artık v02'yi alır; v01 için `revision="v01"`.
- **v01 — 2026-09-17:** 0.882 / 0.902 (`revision="v01"`).

## Resources / Kaynaklar

- halilneed agency: [halilneed.agency/models/turkish-pii-detection](https://halilneed.agency/models/turkish-pii-detection/?utm_source=huggingface&utm_medium=model_card&utm_campaign=turkish-pii-detection&utm_content=resources)
