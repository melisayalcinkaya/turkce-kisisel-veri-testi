"""Maskelenmiş çıktıyı (ör. "Ben [AD].") girdideki karakter aralıklarına çevirir."""
import difflib
import re

ETIKET = re.compile(r"\[[A-ZÇĞİÖŞÜ0-9_]+\]")


def etiketli_hizala(girdi, cikti):
    """Çıktıdaki her [ETİKET]'in girdide hangi aralığın yerine geçtiğini bulur.

    Önce kesin yol: etiket dışındaki parçalar girdide aynen sırayla geçiyorsa
    aradaki boşluklar değerdir. Olmazsa karakter farkına (difflib) düşer.
    """
    parcalar = ETIKET.split(cikti)
    etiketler = ETIKET.findall(cikti)
    desen = "^" + "(.+?)".join(re.escape(p) for p in parcalar) + "$"
    m = re.match(desen, girdi, re.DOTALL)
    if m:
        return [{"bas": m.start(i + 1), "son": m.end(i + 1), "tur": etiketler[i].strip("[]")}
                for i in range(len(etiketler))], True
    return fark_hizala(girdi, cikti), False


def fark_hizala(girdi, cikti):
    out = []
    sm = difflib.SequenceMatcher(None, girdi, cikti, autojunk=False)
    for op, i1, i2, _j1, _j2 in sm.get_opcodes():
        if op in ("replace", "delete") and girdi[i1:i2].strip():
            out.append({"bas": i1, "son": i2, "tur": "FARK"})
    return out
