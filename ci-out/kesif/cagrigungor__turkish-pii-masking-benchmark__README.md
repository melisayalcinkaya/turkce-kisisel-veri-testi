---
language:
- tr
license: cc0-1.0
task_categories:
- text-generation
tags:
- pii
- masking
- benchmark
- turkish
- kvkk
size_categories:
- 1K<n<10K
configs:
- config_name: default
  data_files:
  - split: test
    path: benchmark_1000.csv
---

# Turkish PII Masking Benchmark (1,000 test cases)

A hand-built, fully synthetic benchmark for evaluating **instruction-conditional PII masking**
in Turkish. Designed to stress-test small LLMs (0.3B-1B) fine-tuned for privacy filtering in
banking/ERP user messages. All values are synthetic (no real persons); all sentence patterns
were written specifically for this benchmark (no training-set overlap).

## Task
Given `instruction` (the masking policy) and `input`, the model must produce `expected_output`:

| kategori | n | policy |
|---|---|---|
| tam | 350 | mask ALL PII fields |
| beyaz_liste | 200 | mask ONLY the listed fields |
| kara_liste | 150 | mask everything EXCEPT the listed fields |
| kapsam_disi | 100 | requested tag absent from text -> output must equal input |
| negatif | 200 | no PII at all (trap sentences) -> output must equal input |

## Hard slices (`ozellikler` column)
`kayit` multi-field records (5-9 tags) · `caps` ALL-UPPERCASE · `uzun` long inputs ·
`ekli` Turkish suffix-attached PII ("Cem Aslan'ın", vowel-harmony) · `sozle` spelled-out
numbers ("yedi bir dokuz yedi") · `cok_kisi` multiple persons · `tuzak` PII-lookalike
negatives (invoice numbers, city-named projects, PII *words* without PII values) ·
`olmayan_etiket_talebi` instruction mentions a tag not in the text

## Columns
`id, kategori, ozellikler, instruction, input, expected_output, metindeki_etiketler,
maskelenecek_etiketler`

Covers all **53 mask tags** ([TCKN], [AD], [IBAN], [TEL], [SAGLIK], ... [YAS], [CINSIYET], [UYRUK]).

Also on Kaggle: https://www.kaggle.com/datasets/aiwithcagri/turkish-pii-masking-benchmark

## Scoring
```python
import pandas as pd
df = pd.read_csv("benchmark_1000.csv")
df["dogru"] = [model(r.instruction, r.input) == r.expected_output for r in df.itertuples()]
print(df.groupby("kategori").dogru.mean())
```
Exact match is the intended metric; per-slice breakdown via `kategori` x `ozellikler`.
