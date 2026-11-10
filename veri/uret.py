"""Türkçe kişisel veri test seti üretici.

Gerçek kişisel veri kullanılamayacağı için metinler sentetiktir; ama
günlük yazım biçimlerini (küçük harf, kesme işaretsiz ekler, boşluklu
numaralar, sıradan kelime olan isimler) ve tuzakları (geçerli görünen
ama kişisel olmayan sayılar) bilerek içerir.

Şablonlarda {TUR:anahtar} ya da {TUR:anahtar:ek} yer tutucuları var.
Değer metne yazılır, etiket yalnızca değeri kapsar (ek hariç).
"""
import json
import random
import re
import sys

rnd = random.Random(2026)

# ---------------------------------------------------------------- isimler
ERKEK = ["Ahmet", "Mehmet", "Mustafa", "Ali", "Hüseyin", "Hasan", "İbrahim", "Murat",
         "Emre", "Burak", "Oğuz", "Serkan", "Volkan", "Kerem", "Yusuf", "Tolga",
         "Cem", "Onur", "Gökhan", "Selim", "Kaan", "Berk", "Halil", "Ömer", "Şükrü"]
KADIN = ["Ayşe", "Fatma", "Emine", "Zeynep", "Elif", "Merve", "Büşra", "Esra",
         "Gizem", "Sevgi", "Hülya", "Derya", "Özlem", "Tuğba", "Melek", "Şule",
         "İrem", "Nur", "Cansu", "Seda", "Gül", "Ebru", "Pınar", "Selin", "Dilek"]
# Sıradan kelime de olan isimler (zor örnekler)
KELIME_ISIM = ["Deniz", "Umut", "Barış", "Güneş", "Bahar", "Ekin", "Toprak", "Su",
               "Ilgın", "Yağmur", "Doğan", "Kader", "Hayat", "Sevda", "Ümit"]
SOYAD = ["Yılmaz", "Kaya", "Demir", "Şahin", "Çelik", "Yıldız", "Yıldırım", "Öztürk",
         "Aydın", "Özdemir", "Arslan", "Doğan", "Kılıç", "Aslan", "Çetin", "Kara",
         "Koç", "Kurt", "Özkan", "Şimşek", "Polat", "Korkmaz", "Erdoğan", "Güneş",
         "Aksoy", "Uçar", "Tekin", "Bulut", "Karaca", "Ateş", "Bozkurt", "Sarı",
         "Ekinci", "Güler", "Taş", "Eren", "Duman", "Coşkun", "Acar", "Turan"]

UNLULER = "aeıioöuüAEIİOÖUÜ"
KALIN = set("aıouAIOU")
YUVARLAK = set("oöuüOÖUÜ")
SERT = set("fstkçşhpFSTKÇŞHP")


def son_unlu(k):
    for c in reversed(k):
        if c in UNLULER:
            return c
    return "e"


def ek(kelime, tur):
    """Türkçe hal eki (kesme işaretsiz kısım)."""
    u = son_unlu(kelime)
    kalin = u in KALIN
    yuv = u in YUVARLAK
    unlu_bitis = kelime[-1] in UNLULER
    sert = kelime[-1] in SERT
    a = "a" if kalin else "e"
    if kalin:
        i = "u" if yuv else "ı"
    else:
        i = "ü" if yuv else "i"
    if tur == "yon":   # -e
        return ("y" if unlu_bitis else "") + a
    if tur == "ilgi":  # -in
        return ("n" if unlu_bitis else "") + i + "n"
    if tur == "belirtme":  # -i
        return ("y" if unlu_bitis else "") + i
    if tur == "bulunma":  # -de
        return ("t" if sert else "d") + a
    if tur == "ayrilma":  # -den
        return ("t" if sert else "d") + a + "n"
    if tur == "vasita":  # -le
        return ("y" if unlu_bitis else "") + "l" + a
    if tur == "hanim":
        return " Hanım"
    if tur == "bey":
        return " Bey"
    raise ValueError(tur)


def tr_lower(s):
    return s.replace("I", "ı").replace("İ", "i").lower()


# ---------------------------------------------------------------- numaralar
def tckn():
    d = [rnd.randint(1, 9)] + [rnd.randint(0, 9) for _ in range(8)]
    d10 = ((d[0] + d[2] + d[4] + d[6] + d[8]) * 7 - (d[1] + d[3] + d[5] + d[7])) % 10
    d.append(d10)
    d.append(sum(d) % 10)
    return "".join(map(str, d))


def gecersiz_tckn():
    while True:
        s = str(rnd.randint(10**10, 10**11 - 1))
        d = list(map(int, s))
        d10 = ((d[0] + d[2] + d[4] + d[6] + d[8]) * 7 - (d[1] + d[3] + d[5] + d[7])) % 10
        if d[9] != d10 or d[10] != sum(d[:10]) % 10:
            return s


def iban(bicim):
    banka = rnd.choice(["00010", "00012", "00015", "00046", "00062", "00064", "00067", "00111", "00134", "00205"])
    hesap = banka + "0" + "".join(str(rnd.randint(0, 9)) for _ in range(16))
    sayi = int(hesap + "2927" + "00")  # T=29 R=27
    kontrol = 98 - sayi % 97
    ham = f"TR{kontrol:02d}{hesap}"
    if bicim == "bosluklu":
        return " ".join(ham[i:i + 4] for i in range(0, len(ham), 4))
    if bicim == "kucuk":
        return ham.lower()
    return ham


def telefon(bicim):
    op = rnd.choice(["530", "532", "533", "535", "536", "537", "538", "539", "541", "542",
                     "543", "544", "545", "546", "505", "506", "507", "551", "552", "555", "559"])
    a, b, c = rnd.randint(100, 999), rnd.randint(10, 99), rnd.randint(10, 99)
    sabit = rnd.choice(["212", "216", "312", "232", "258", "224"])
    return {
        "0bosluk": f"0{op} {a} {b} {c}",
        "bitisik": f"0{op}{a}{b}{c}",
        "arti90": f"+90 {op} {a} {b} {c}",
        "arti90b": f"+90{op}{a}{b}{c}",
        "parantez": f"0 ({op}) {a} {b} {c}",
        "tire": f"{op}-{a}-{b}-{c}",
        "sifirsiz": f"{op} {a} {b}{c}",
        "sabit": f"0{sabit} {a} {b} {c}",
    }[bicim]


def kart():
    bas = [4] if rnd.random() < .5 else [5, rnd.randint(1, 5)]
    d = bas + [rnd.randint(0, 9) for _ in range(15 - len(bas))]
    for k in range(10):
        dd = d + [k]
        t = 0
        for i, x in enumerate(reversed(dd)):
            if i % 2 == 1:
                x *= 2
                x -= 9 if x > 9 else 0
            t += x
        if t % 10 == 0:
            s = "".join(map(str, dd))
            return rnd.choice([s, " ".join(s[i:i + 4] for i in range(0, 16, 4)),
                               "-".join(s[i:i + 4] for i in range(0, 16, 4))])


def plaka():
    il = rnd.choice(["34", "06", "35", "20", "16", "07", "01", "42", "61", "55"])
    harf = "".join(rnd.choice("ABCDEFGHJKLMNPRSTUVYZ") for _ in range(rnd.choice([1, 2, 3])))
    no = str(rnd.randint(10, 9999)) if len(harf) < 3 else str(rnd.randint(10, 999))
    return rnd.choice([f"{il} {harf} {no}", f"{il}{harf}{no}", f"{il} {harf}{no}"])


def eposta(ad, soyad):
    a, s = tr_lower(ad), tr_lower(soyad)
    for x, y in zip("çğıöşü", "cgiosu"):
        a, s = a.replace(x, y), s.replace(x, y)
    alan = rnd.choice(["gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "icloud.com", "firma.com.tr", "ogr.edu.tr"])
    return rnd.choice([f"{a}.{s}@{alan}", f"{a}{s}{rnd.randint(1, 99)}@{alan}", f"{a[0]}{s}@{alan}", f"{a}_{s}@{alan}"])


MAH = ["Atatürk", "Cumhuriyet", "Bahçelievler", "Yenimahalle", "Fatih", "İstiklal", "Kocatepe", "Gazi", "Esentepe", "Barbaros"]
SOK = ["Gül", "Lale", "Menekşe", "Çınar", "Akasya", "Papatya", "Zambak", "Ihlamur", "1203.", "45/2", "Mimar Sinan", "Kardelen"]
ILCE_IL = [("Kadıköy", "İstanbul"), ("Çankaya", "Ankara"), ("Bornova", "İzmir"), ("Pamukkale", "Denizli"),
           ("Merkezefendi", "Denizli"), ("Nilüfer", "Bursa"), ("Muratpaşa", "Antalya"), ("Seyhan", "Adana"),
           ("Selçuklu", "Konya"), ("Ortahisar", "Trabzon")]


def adres(bicim):
    m, s = rnd.choice(MAH), rnd.choice(SOK)
    ilce, il = rnd.choice(ILCE_IL)
    no, d = rnd.randint(1, 120), rnd.randint(1, 24)
    if bicim == "tam":
        return f"{m} Mah. {s} Sok. No:{no} D:{d} {ilce}/{il}"
    if bicim == "uzun":
        return f"{m} Mahallesi, {s} Sokak, No: {no}, Daire {d}, {ilce} / {il}"
    if bicim == "kisa":
        return f"{s} sok. no {no} daire {d}"
    return f"{tr_lower(m)} mah {tr_lower(s)} sk no {no}/{d} {tr_lower(ilce)}"


def dogum():
    g, a, y = rnd.randint(1, 28), rnd.randint(1, 12), rnd.randint(1955, 2006)
    return rnd.choice([f"{g:02d}.{a:02d}.{y}", f"{g}/{a}/{y}",
                       f"{g} {['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran','Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık'][a-1]} {y}"])


# ---------------------------------------------------------------- kişi
def kisi(kelime_isim=False):
    if kelime_isim:
        ad = rnd.choice(KELIME_ISIM)
    else:
        ad = rnd.choice(ERKEK + KADIN)
    soyad = rnd.choice(SOYAD)
    return ad, soyad


# ---------------------------------------------------------------- şablonlar
# Her şablon: (tür, metin). Yer tutucular:
#   {K1}       tam ad,  {K1a} yalnız ad, {K1s} yalnız soyad
#   {K1:yon}   tam ad + ek (kesmeli), {K1~yon} kesmesiz ek
#   {TC1} {IBAN1} {TEL1} {MAIL1} {ADR1} {PLK1} {KART1} {DOG1}
#   {TUZAK_TC} {SIPARIS} {TUTAR} vb. etiketsiz tuzaklar
SABLONLAR = [
    ("musteri_eposta", "Merhaba, ben {K1}. {SIPARIS} numaralı siparişim hâlâ gelmedi. Kargo {ADR1} adresine teslim edilecekti. Bana {TEL1} numarasından ulaşabilirsiniz."),
    ("musteri_eposta", "Sayın yetkili, iade tutarı olan {TUTAR} TL'nin {IBAN1} hesabına yatırılmasını rica ederim. Hesap sahibi: {K1}. Saygılarımla."),
    ("musteri_eposta", "İyi günler, faturamda adım yanlış yazılmış, doğrusu {K1} olacak. TC kimlik numaram {TC1}. Düzeltilmiş faturayı {MAIL1} adresine gönderebilir misiniz?"),
    ("musteri_eposta", "Selam, {K1a} ben. Geçen hafta konuştuğumuz konu hakkında {K2:ilgi} görüşünü de aldım, sizi {TEL1} üzerinden arayacak."),
    ("musteri_eposta", "Kartımdan iki kez çekim yapılmış ({KART1}). Toplam {TUTAR} TL. Lütfen iade edin. {K1}"),
    ("musteri_eposta", "Teslimat adresimi güncellemek istiyorum. Yeni adres: {ADR1}. Alıcı {K1}, telefon {TEL1}."),
    ("dilekce", "{KURUM_ADI} Müdürlüğüne\n\nMüdürlüğünüze ait {SIPARIS} sayılı dosyada adımın eksik yazıldığını öğrendim. Gereğinin yapılmasını arz ederim.\n\nAd Soyad: {K1}\nT.C. Kimlik No: {TC1}\nAdres: {ADR1}\nTel: {TEL1}"),
    ("dilekce", "Sayın Başkanlığa,\n{DOG1} doğumlu, {TC1} T.C. kimlik numaralı oğlum {K2:belirtme} okulunuza nakil yaptırmak istiyorum. Veli: {K1}, {TEL1}."),
    ("dilekce", "Kiracım {K2} {AY} ayından bu yana kira ödemiyor. Kira bedeli {TUTAR} TL olup {IBAN1} numaralı hesabıma yatırılması gerekmektedir. {K1}, {ADR1}"),
    ("ik_notu", "Aday değerlendirme: {K1}, {DOG1} doğumlu. Mülakatı {K2} ile birlikte yaptık. İletişim: {MAIL1} / {TEL1}. Maaş beklentisi {TUTAR} TL."),
    ("ik_notu", "{K1:ilgi} işe giriş evrakları eksik. SGK girişi için TC kimlik no {TC1}, ikametgah {ADR1}. Maaş hesabı {IBAN1}."),
    ("ik_notu", "Ekip toplantısı notu: {K1a} izinde, yerine {K2a} bakacak. {K3:ilgi} performans görüşmesi perşembeye ertelendi."),
    ("ik_notu", "{K1} işten ayrıldı. Son maaşı ve kıdem tazminatı {TUTAR} TL, {IBAN1} hesabına. Zimmetindeki {PLK1} plakalı araç teslim alındı."),
    ("destek", "Kullanıcı {MAIL1} giriş yapamadığını bildirdi. Hesap {K1} adına kayıtlı. Telefon doğrulaması {TEL1} numarasına gitmiyor."),
    ("destek", "Müşteri şikayeti: {K1} ({TC1}) poliçesinin yenilenmediğini söylüyor. Poliçe no {POLICE}. Araç plakası {PLK1}."),
    ("destek", "Arıza kaydı {SIPARIS}: {ADR1} adresinde internet yok. Abone {K1:hanimbey}, ulaşılabilecek numara {TEL1}."),
    ("mesaj", "{k1a} yarın {ADR1} adresine gel, {k2a} da gelecek"),
    ("mesaj", "abi {k1} hesabına at parayı {IBAN1} ama acele et"),
    ("mesaj", "{k1~yon} söyledim, numarası {TEL1} ararsan açar"),
    ("mesaj", "tc no lazımmış {TC1} bu benimki, annemin de {TC2}"),
    ("mesaj", "{k1a} hocanın maili {MAIL1} ödevi oraya atıcaz"),
    ("mesaj", "dün {k1~vasita} konuştum, {k2~ilgi} arabası {PLK1} plakalı olan değil mi"),
    ("rapor", "Hasta {K1}, {DOG1} doğumlu, kontrol muayenesine geldi. TC: {TC1}. Yakını {K2} ({TEL1}) bilgilendirildi."),
    ("rapor", "Tutanak: {TARIH} tarihinde {PLK1} plakalı araç ile {PLK2} plakalı araç çarpışmıştır. Sürücüler {K1} ve {K2}."),
    ("rapor", "Danışan {K1a} ilk görüşmede eşi {K2a} hakkında konuştu. Bir sonraki seans {TARIH}. İletişim {TEL1}."),
    ("muhasebe", "{K1} adına kesilen {SIPARIS} numaralı fatura {TUTAR} TL. Ödeme {IBAN1} hesabına {TARIH} tarihinde yapıldı."),
    ("muhasebe", "Serbest meslek makbuzu: {K1}, TCKN {TC1}, adres {ADR1}. Brüt tutar {TUTAR} TL."),
    ("muhasebe", "Cari hesap ekstresi {K1:ilgi} talebiyle {MAIL1} adresine gönderildi."),
    ("hukuk", "Müvekkilimiz {K1} ile davalı {K2} arasındaki kira uyuşmazlığına ilişkin dosya {ESAS} esas numarasıyla görülmektedir. Davalının adresi {ADR1}."),
    ("hukuk", "Tanık {K1} ({TC1}) olay günü {K2:belirtme} {ADR1} adresinde gördüğünü beyan etmiştir."),
    ("egitim", "Öğrenci {K1} ({OGRNO}) bu dönem iki dersten kaldı. Veli {K2} ile {TEL1} numarasından görüşüldü."),
    ("egitim", "{K1a} {K1s} ödevini {MAIL1} adresinden gönderdi. {K2a} hoca notunu yarın girecek."),
]

# Kişisel veri içermeyen ama tuzak içeren metinler
NEGATIF = [
    "Sipariş numaranız {SIPARIS}. Tahmini teslim tarihi {TARIH}. Toplam tutar {TUTAR} TL.",
    "Fatura no {TUZAK_TC} olan belgede KDV oranı yüzde 20 olarak hesaplanmıştır.",
    "Toplantı yarın saat 14:30'da Ankara şubesinde yapılacak. Gündem: bütçe ve işe alım.",
    "Ürün kodu {URUN} stokta yok, tedarikçi {AY} ayında yeni sevkiyat bekliyor.",
    "Deniz kenarında yürüyüş yaptık, güneş batarken umut dolu bir akşamdı.",
    "Barış görüşmeleri bahar aylarında yeniden başlayacak.",
    "Müşteri hizmetleri hattımız 0850 222 0 444 hafta içi 09:00-18:00 arası hizmet vermektedir.",
    "Çağrı merkezi: 444 0 333. Kampanya kodu {URUN} ile yüzde 15 indirim kazanın.",
    "Türkiye İş Bankası ve Ziraat Bankası mobil uygulamaları bugün bakımda.",
    "Atatürk Havalimanı'ndan Kadıköy'e metro ile yaklaşık bir saatte gidilir.",
    "Sözleşmenin 12.3 maddesi uyarınca {TUTAR} TL cezai şart uygulanır.",
    "Seri no {TUZAK_TC} olan cihazın garantisi {TARIH} tarihinde sona eriyor.",
    "Yazılım sürümü 2.14.3, derleme numarası {URUN}, test ortamında sorunsuz.",
    "Bu çeyrekte gelir {TUTAR} TL, gider {TUTAR2} TL olarak gerçekleşti.",
    "Toprak analizi sonuçları ekte; pH değeri 6,8 ve organik madde oranı yüzde 2,4.",
    "Kargo takip no: {KARGO}. Şube: Pamukkale/Denizli.",
    "Ekin zamanı yaklaşırken çiftçiler yağmur bekliyor.",
    "Doğan Holding ve Koç Holding yıllık raporlarını yayımladı.",
    "İstanbul Büyükşehir Belediyesi yeni otobüs hatlarını duyurdu.",
    "Kur {TARIH} itibarıyla 1 Euro = 48,25 TL; IBAN bilgileri için şubenize başvurun.",
]


def tutar():
    return f"{rnd.randint(150, 98000):,}".replace(",", ".") + rnd.choice(["", ",00", ",50"])


def tarih():
    return f"{rnd.randint(1, 28):02d}.{rnd.randint(1, 12):02d}.{rnd.choice([2025, 2026])}"


def doldur(sablon):
    """Şablonu doldurur; (metin, varliklar) döndürür."""
    kisiler = {}
    sayaclar = {}
    parcalar = []  # (metin, etiket|None)
    poz = 0
    for m in re.finditer(r"\{([^}]+)\}", sablon):
        parcalar.append((sablon[poz:m.start()], None))
        poz = m.end()
        anahtar = m.group(1)
        parcalar.extend(cozumle(anahtar, kisiler, sayaclar))
    parcalar.append((sablon[poz:], None))
    metin = ""
    varliklar = []
    for p, etiket in parcalar:
        if etiket:
            varliklar.append({"bas": len(metin), "son": len(metin) + len(p), "tur": etiket, "deger": p})
        metin += p
    return metin, varliklar


def cozumle(anahtar, kisiler, sayaclar):
    # Kişi yer tutucuları
    m = re.fullmatch(r"([Kk])(\d)([as]?)([:~]\w+)?", anahtar)
    if m:
        kucuk = m.group(1) == "k"
        no = m.group(2)
        parca = m.group(3)
        ekbilgi = m.group(4)
        if no not in kisiler:
            kisiler[no] = kisi(kelime_isim=rnd.random() < 0.25)
        ad, soyad = kisiler[no]
        if parca == "a":
            deger = ad
        elif parca == "s":
            deger = soyad
        else:
            deger = f"{ad} {soyad}"
        if kucuk:
            deger = tr_lower(deger)
        out = [(deger, "KISI")]
        if ekbilgi:
            tur = ekbilgi[1:]
            kesme = ekbilgi[0] == ":"
            if tur == "hanimbey":
                tur = "hanim" if ad in KADIN else "bey"
            e = ek(deger, tur)
            if tur in ("hanim", "bey"):
                out.append((e, None))
            else:
                out.append((("'" if kesme else "") + e, None))
        return out
    sabit = {
        "SIPARIS": lambda: str(rnd.randint(10**8, 10**10)),
        "TUTAR": tutar, "TUTAR2": tutar, "TARIH": tarih,
        "AY": lambda: rnd.choice(["Ocak", "Mart", "Haziran", "Eylül", "Kasım"]),
        "TUZAK_TC": gecersiz_tckn,
        "URUN": lambda: rnd.choice(["SKU-", "PRD", "ZX"]) + str(rnd.randint(10000, 999999)),
        "POLICE": lambda: str(rnd.randint(10**9, 10**10)),
        "ESAS": lambda: f"2026/{rnd.randint(10, 999)}",
        "OGRNO": lambda: str(rnd.randint(2022000000, 2022999999)),
        "KARGO": lambda: str(rnd.randint(10**11, 10**12)),
        "KURUM_ADI": lambda: rnd.choice(["Pamukkale İlçe Nüfus", "Kadıköy Tapu", "Çankaya Vergi Dairesi"]),
    }
    if anahtar in sabit:
        return [(sabit[anahtar](), None)]
    m = re.fullmatch(r"([A-Z]+)(\d)", anahtar)
    tur, no = m.group(1), m.group(2)
    k = (tur, no)
    if k not in sayaclar:
        if tur == "TC":
            sayaclar[k] = (tckn(), "TCKN")
        elif tur == "IBAN":
            sayaclar[k] = (iban(rnd.choice(["bosluklu", "bosluklu", "bitisik", "kucuk"])), "IBAN")
        elif tur == "TEL":
            sayaclar[k] = (telefon(rnd.choice(["0bosluk", "0bosluk", "bitisik", "arti90", "arti90b", "parantez", "tire", "sifirsiz", "sabit"])), "TELEFON")
        elif tur == "MAIL":
            ad, soyad = kisiler.get("1") or kisi()
            sayaclar[k] = (eposta(ad, soyad), "EPOSTA")
        elif tur == "ADR":
            sayaclar[k] = (adres(rnd.choice(["tam", "uzun", "kisa", "gunluk"])), "ADRES")
        elif tur == "PLK":
            sayaclar[k] = (plaka(), "PLAKA")
        elif tur == "KART":
            sayaclar[k] = (kart(), "KART")
        elif tur == "DOG":
            sayaclar[k] = (dogum(), "DOGUM_TARIHI")
        else:
            raise ValueError(anahtar)
    deger, etiket = sayaclar[k]
    return [(deger, etiket)]


def main():
    cikti = sys.argv[1]
    kayitlar = []
    n = 0
    for tekrar in range(8):
        for tur, s in SABLONLAR:
            metin, v = doldur(s)
            kayitlar.append({"id": f"p{n:04d}", "tur": tur, "metin": metin, "varliklar": v})
            n += 1
    for tekrar in range(4):
        for s in NEGATIF:
            metin, v = doldur(s)
            assert not v
            kayitlar.append({"id": f"n{n:04d}", "tur": "negatif", "metin": metin, "varliklar": []})
            n += 1
    with open(cikti, "w", encoding="utf-8") as f:
        for k in kayitlar:
            f.write(json.dumps(k, ensure_ascii=False) + "\n")
    from collections import Counter
    c = Counter(v["tur"] for k in kayitlar for v in k["varliklar"])
    print(len(kayitlar), "metin;", dict(c))


if __name__ == "__main__":
    main()
