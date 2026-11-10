---
language:
- tr
license: apache-2.0
library_name: transformers
base_model: ytu-ce-cosmos/modernbert-tr-base
base_model_relation: finetune
pipeline_tag: token-classification
metrics:
- f1
tags:
- modernbert
- pii
- kvkk
- ner
- privacy
- onnx
- encoderfile
---

<p align="center">
  <img src="assets/logo.webp" width="20%" alt="ModernBERT-TR PII recognition" />
</p>
<h1 align="center">ModernBERT-TR PII Recognition</h1>

A 150M-parameter Turkish token classifier with 25 KVKK-oriented entity types and 51 BIO labels.

## Results

Our model scores 80.85 +/- 0.19% overlap micro-F2 on a 300-document test set. The released checkpoint scores 81.01%.

The quantized int8 version scores 71.90% overlap micro-F2.

## Usage

```python
from transformers import pipeline

detect = pipeline(
    "token-classification",
    model="ytu-ce-cosmos/modernbert-tr-pii-ner",
    aggregation_strategy="first",
)
detect("Ayşe Yılmaz'a ayse@example.com adresinden ulaşabilirsiniz.")
```

You can call the tokenizer with `is_split_into_words=True` to allow the tokenizer to split the sentence into words, and keep the first WordPiece label for each word.

## Training

We finetune [`ytu-ce-cosmos/modernbert-tr-base`](https://huggingface.co/ytu-ce-cosmos/modernbert-tr-base) on an 8,014-document mixture of Turkish web PDFs, anonymized high-court decisions, born-labeled synthetic documents, and OCR-degraded synthetic documents; the loader retained 7,763 training documents. Real-document labels came from up to a three-model panel. We use learning rate `2e-5`, batch size 16, three epochs, cosine decay, 10% warmup, weight decay 0.01, normalized inverse-frequency weights raised to 0.3, and three seeds.

Standalone binaries are available in the [encoderfile repo](https://huggingface.co/ytu-ce-cosmos/modernbert-tr-pii-ner-encoderfile).

## License

Apache-2.0.
