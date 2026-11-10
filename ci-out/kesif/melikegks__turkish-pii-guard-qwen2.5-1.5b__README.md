---
language:
- tr
license: apache-2.0
base_model: Qwen/Qwen2.5-1.5B-Instruct
pipeline_tag: text-generation
tags:
- pii
- pii-detection
- data-masking
- privacy
- turkish
- qwen2.5
---

# Turkish PII Guard 1.5B

Turkish PII Guard 1.5B, Türkçe metinlerdeki kişisel verileri tespit etmek ve
maskelemek amacıyla geliştirilmiş bir dil modelidir.

Model, `Qwen/Qwen2.5-1.5B-Instruct` taban modeli üzerine fine-tune edilmiştir.

TCKN, IBAN, telefon numarası, ad soyad, adres ve finansal bilgiler dahil olmak
üzere toplam 50 kişisel veri türünü destekler.

Model hem metindeki tüm kişisel verilerin maskelenmesini hem de talimata bağlı
seçici maskeleme işlemlerini destekler.

## Kullanım

Model, Hugging Face Transformers ile aşağıdaki model adı kullanılarak
yüklenebilir:

    melikegks/turkish-pii-guard-1.5b-v16

Model girdisi; sistem mesajı, maskeleme talimatı ve maskelenecek metinden
oluşmalıdır.

Örnek girdi:

    Metindeki tüm kişisel verileri maskele.

    Ben Melike Tanrıverdi. Bana 0532 111 22 33 numarasından ulaşabilirsiniz.

Beklenen çıktı:

    Ben [AD]. Bana [TEL] numarasından ulaşabilirsiniz.

## Değerlendirme

Her iki model de aynı Türkçe PII maskeleme benchmark'ı üzerinde
değerlendirilmiştir.

| Model | Şema-nötr tam eşleşme |
|---|---:|
| [Turkish PII Guard 0.8B](https://huggingface.co/saturday-labs/turkish-pii-guard-0.8b) | 0.922 |
| Turkish PII Guard 1.5B | 0.857 |

Şema-nötr değerlendirmede, modelin desteklediği 50 etiket arasında bulunmayan
etiketleri içeren benchmark örnekleri değerlendirme dışında bırakılmıştır.

## Sınırlılıklar

Model bazı seçici maskeleme talimatlarında, özellikle belirli bir kişisel veri
türünün açık bırakılması istendiğinde hata yapabilir.

Yüksek riskli veya düzenlemeye tabi iş akışlarında model çıktılarının ayrıca
doğrulanması önerilir.
