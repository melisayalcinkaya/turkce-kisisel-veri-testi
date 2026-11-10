"""Model gerektirmeyen (kural tabanlı) sistemler.

Kullanım: python sistemler/kural.py veri/test.jsonl tahmin/
"""
import json
import os
import sys


def kvkk_pii_regex():
    from kvkk_pii.detector import PiiDetector
    from kvkk_pii.layers.regex_layer import DEFAULT_RECOGNIZERS
    from kvkk_pii.recognizers.kisi_adi import KisiAdiRecognizer
    from kvkk_pii.recognizers.adres import AdresRecognizer
    d = PiiDetector(layers=["regex"], recognizers=DEFAULT_RECOGNIZERS + [KisiAdiRecognizer(), AdresRecognizer()])

    def calistir(metin):
        return [{"bas": e.start, "son": e.end, "tur": str(e.entity_type)} for e in d.analyze(metin).entities]
    return calistir


def presidio_desen():
    import presidio_analyzer.predefined_recognizers as p
    tanimlar = [
        p.EmailRecognizer(), p.IbanRecognizer(), p.CreditCardRecognizer(),
        p.PhoneRecognizer(supported_regions=("TR",)), p.TrNationalIdRecognizer(),
        p.TrLicensePlateRecognizer(), p.IpRecognizer(),
    ]

    def calistir(metin):
        out = []
        for r in tanimlar:
            for s in r.analyze(metin, r.supported_entities, None) or []:
                if s.score > 0:
                    out.append({"bas": s.start, "son": s.end, "tur": s.entity_type})
        return out
    return calistir


SISTEMLER = {"kvkk_pii_regex": kvkk_pii_regex, "presidio_desen": presidio_desen}


def main():
    veri, klasor = sys.argv[1], sys.argv[2]
    os.makedirs(klasor, exist_ok=True)
    kayitlar = [json.loads(s) for s in open(veri, encoding="utf-8")]
    for ad, kur in SISTEMLER.items():
        f = kur()
        with open(os.path.join(klasor, ad + ".jsonl"), "w", encoding="utf-8") as out:
            for k in kayitlar:
                out.write(json.dumps({"id": k["id"], "tahminler": f(k["metin"])}, ensure_ascii=False) + "\n")
        print(ad, "tamam")


if __name__ == "__main__":
    main()
