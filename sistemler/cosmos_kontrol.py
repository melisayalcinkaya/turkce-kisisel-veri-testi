"""cosmos modelinin e-postaları neden kestiğini anlamak için ham token çıktısı."""
from transformers import AutoModelForTokenClassification, AutoTokenizer, pipeline
import torch

M = "ytu-ce-cosmos/modernbert-tr-pii-ner"
ornekler = ["Ayşe Yılmaz'a ayse@example.com adresinden ulaşabilirsiniz.",
            "Düzeltilmiş faturayı irem.duman@icloud.com adresine gönderebilir misiniz?",
            "melek yarın gel, iban tr870006205060454146590853"]
tok = AutoTokenizer.from_pretrained(M)
model = AutoModelForTokenClassification.from_pretrained(M).eval()
for s in ornekler:
    g = tok(s, return_tensors="pt", return_offsets_mapping=True)
    ofs = g.pop("offset_mapping")[0].tolist()
    with torch.no_grad():
        etk = model(**g).logits[0].argmax(-1).tolist()
    print(s)
    print("  ", [(s[a:b], model.config.id2label[e]) for (a, b), e in zip(ofs, etk) if b > a])
    print("  simple:", [(r["word"], r["entity_group"]) for r in pipeline("token-classification", model=model, tokenizer=tok, aggregation_strategy="simple")(s)])
