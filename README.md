# Türkçe kişisel veri maskeleme testi

Mevcut Türkçe kişisel veri (PII) tespit araçlarını ve modellerini aynı test setinde karşılaştıran deney deposu.

- `veri/uret.py`: sentetik test setini üretir (`veri/test.jsonl`, 336 metin, 800 etiketli veri). Gerçek kişisel veri içermez.
- `sistemler/`: her araç için çalıştırıcı (kurallar, NER modelleri, …).
- `degerlendir.py`: "korunan oran" (verinin en az %90'ı maskelendiyse korundu) ve yanlış alarm.
- `.github/workflows/olc.yml`: `kosu.txt` değişince komutları GitHub Actions'ta çalıştırır, çıktıları `ci-out/` ve `tahmin/` altına commit'ler.
