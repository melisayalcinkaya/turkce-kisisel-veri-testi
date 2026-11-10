# İlk ölçüm: mevcut Türkçe kişisel veri araçları (10.11.2026)

Ölçüt: bir kişisel veri, boşluk dışı karakterlerinin en az %90'ı maskelendiyse "korundu" sayılır (etiket adı önemsiz). Hız: GitHub Actions CPU'sunda metin başına ortanca süre, tek iş parçacığı (üretken model 4 iş parçacığı).

## Kendi test setimiz (`veri/test.jsonl`, 336 metin, 800 kişisel veri)

| Sistem | Boyut | Hız | Korunan | İsim | TCKN | Tel | IBAN | E-posta | Adres | Temiz metinde alarm |
|---|---|---|---|---|---|---|---|---|---|---|
| halilneed/turkish-pii-detection (üretken) | 270M | 2,9 sn* | **%91,2** | 88 | 100 | 100 | 100 | 100 | 79 | 1/80 |
| kvkk-pii regex + cosmos | 150M | ~130 ms | %89,1 | 88 | 100 | 86 | 100 | 100 | 85 | 22/80 |
| gliner_multi_pii-v1 | 289M | ~400 ms | %85,8 | 99 | 60 | 100 | 23 | 92 | 52 | 24/80 |
| ytu-ce-cosmos/modernbert-tr-pii-ner | 150M | ~130 ms | %80,5 | 88 | 99 | 83 | 71 | 0 | 90 | 13/80 |
| kvkk-pii (tam hazır ayar) | ~560M | ~510 ms | %63,9 | 60 | 100 | 71 | 65 | 100 | 12 | 24/80 |
| Werea-KVKK-PII-150M | 150M | ~130 ms | %57,9 | 53 | 84 | 86 | 44 | 40 | 35 | 75/80 |
| OpenMed PII Turkish 335M | 335M | ~490 ms | %54,8 | 27 | 100 | 86 | 100 | 65 | 29 | 80/80 |
| Presidio desenleri | – | – | %38,1 | 0 | 100 | 100 | 69 | 100 | 0 | 9/80 |
| kvkk-pii yalnız regex | – | – | %34,8 | 1 | 100 | 71 | 65 | 100 | 0 | 0/80 |

\* 4 iş parçacığı. Tüm sayılar: `python degerlendir.py veri/test.jsonl tahmin/test/...`

## Bağımsız set (cagrigungor/turkish-pii-masking-benchmark, "tam" + "negatif", 550 satır)

Ortak 9 veri türünde (isim, TCKN, tel, IBAN, e-posta, adres, plaka, kart, doğum tarihi): halilneed %100, kvkk-pii regex + cosmos %81,3, GLiNER PII %80,0, cosmos %67,3, OpenMed %61,6, Werea %52,7, kvkk-pii tam %47,3.

Dikkat: bu set halilneed modelinin kendi geliştirme ailesine ait (taban modeli cagrigungor/pii-guard), yani o model için alan içi. Ayrıca setteki IBAN'ların hiçbiri, kartların 35/37'si sağlama hanesinden geçmiyor; sağlama kontrolü yapan kurallar bunları haklı olarak reddettiği için bu sette düşük görünüyor (gerçek IBAN'lar her zaman geçerlidir).

## Bulgular

1. **Küçük harfli isimler herkesin zayıf noktası.** cosmos'un kaçırdığı 46 ismin 35'i, halilneed'in 44'ünün 31'i küçük harfle yazılmış (`melek yarın gel`).
2. **cosmos e-postaları maskeleyemiyor.** Ham token çıktısıyla doğrulandı; model kartındaki kendi örneğinde bile (`ayse@example.com`) yalnızca ilk parçayı işaretliyor. Kural katmanıyla birleşince sorun kapanıyor.
3. **halilneed en isabetlisi ama**: geçerli kart numaralarının hiçbirini maskelemedi (0/8), "Selam", "Yakını", "Tanık", "Davalının" gibi kelimeleri isim sandı ve metin başına saniyeler sürüyor (üretken model, tarayıcıda tek iş parçacığında daha yavaş olur).
4. **Werea ve OpenMed** temiz metinlerin neredeyse hepsinde yanlış alarm veriyor.
5. **Boyut:** iyi sonuç veren hiçbir model tarayıcı eklentisi için küçük değil (cosmos int8 ONNX 150 MB ve model kartına göre nicemlenince 81 → 72 F2'ye düşüyor; GLiNER 1,1 GB; halilneed 536 MB). LockNet'teki BERT medium 41 MB'tı.

## Sınırlamalar

- Kendi test seti şablonlardan üretildi (32 şablon × 8 + 20 negatif × 4); yazım biçimleri bizim tahminimiz. Kart (8) ve doğum tarihi (24) örnekleri az.
- Modeller varsayılan ayarlarıyla, eşik ayarı yapılmadan çalıştırıldı.
- Hız ölçümü sunucu CPU'sunda PyTorch ile; tarayıcıdaki wasm süresi farklı olur.
