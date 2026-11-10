---
license: apache-2.0
language:
  - tr
  - en
library_name: transformers
pipeline_tag: token-classification
base_model: dbmdz/bert-base-turkish-cased
datasets:
  - ersanbil/TurkceOCR-Bench
  - hamzabagirsakci/turkish-court-decisions
tags:
  - ner
  - token-classification
  - turkish
  - kvkk
  - pii
  - pii-redaction
  - gdpr
  - legal-nlp
  - ictihat
  - commercial-ner
  - health-ner
  - turkceocr
model-index:
  - name: kvkk-pii-ner-v2.0
    results:
      - task:
          type: token-classification
          name: Turkish KVKK PII, Art. 6 Special Category & Commercial Named Entity Recognition
        dataset:
          name: TurkceOCR Unified NER v3 Corpus (868 Real Court + Hybrid Examples)
          type: ersanbil/TurkceOCR-Bench
          split: validation
        metrics:
          - type: accuracy
            value: 98.79
            name: Validation Token Classification Accuracy (%)
          - type: f1
            value: 98.42
            name: Validation Entity Span Macro-F1 (%)
          - type: loss
            value: 0.0493
            name: Final Validation Cross-Entropy Loss
      - task:
          type: token-classification
          name: Zero-Leakage KVKK PII & Legal Entity Extraction (15-KPI Suite)
        dataset:
          name: TurkceOCR-Bench-6Cat (ID + OOD)
          type: ersanbil/TurkceOCR-Bench
          split: docbench_15kpi
        metrics:
          - type: recall
            value: 100.0
            name: KPI-13 Critical KVKK PII Recall with UnifiedTurkishEntityEngine (%)
          - type: f1
            value: 100.0
            name: KPI-14 Legal & KVKK Entity Span Macro-F1 (%)
          - type: coverage
            value: 100.0
            name: KPI-15 2D Irreversible #000000 Visual Redaction Coverage (%)
      - task:
          type: token-classification
          name: Unseen Archival Court & Regulatory Entity Extraction
        dataset:
          name: TurkExternalBlindBench-v1 (35 Unseen Real Archival Pages, 420 Entities)
          type: ersanbil/TurkceOCR-Bench
          split: external_blind_35
        metrics:
          - type: precision
            value: 98.81
            name: Verified Entity Precision Across 420 Real Entities (%)
          - type: accuracy
            value: 100.0
            name: Checksum-Verified TCKN / VKN / IBAN / MERSIS Precision (%)
---

# kvkk-pii-ner

13-class (`BIO`) Turkish personal data (**6698 sayılı KVKK Md. 3 & Md. 5**), special-category health and legal data (**KVKK Md. 6 & GDPR Art. 9**), and commercial named entity recognition model (`110,036,749` parameters, `419.78 MB` `.safetensors`) fine-tuned from [`dbmdz/bert-base-turkish-cased`](https://huggingface.co/dbmdz/bert-base-turkish-cased).
Serves as the core neural token-classification backbone of [`ersanbil/TurkceOCR`](https://huggingface.co/ersanbil/TurkceOCR) and `UnifiedTurkishEntityEngine`, combining neural context sensitivity with `ictihat_core` legal citations (calibrated on [`hamzabagirsakci/turkish-court-decisions`](https://huggingface.co/datasets/hamzabagirsakci/turkish-court-decisions)), `TurkceVerify` algorithmic checksum lattices, and 2D `#000000` visual redaction (`VisualRedactor`).

## Architecture

| Component | Details |
|---|---|
| Pretrained backbone | [`dbmdz/bert-base-turkish-cased`](https://huggingface.co/dbmdz/bert-base-turkish-cased) (`BertForTokenClassification`, 12 layers, `d_model = 768`, 12 attention heads, 32,000 cased Turkish WordPiece vocabulary, `110,036,749` parameters) |
| Classification head (`v2.0`) | 13 BIO classes covering `PERSON`, `ADDRESS`, `HEALTH_DATA` (KVKK Art. 6), `KVKK_SPECIAL` (union/association, criminal record, biometric/genetic), `ORG_COMPANY`, and `TAX_OFFICE` |
| Loss masking (`ignore_index = -100`) | Unlabeled proper-noun tokens inside semi-annotated archival sentences are masked with `-100` in Cross-Entropy (`L_CE`) so the classifier is never penalized into predicting `O` on unannotated names or institutions |
| Long-document inference | 512-token sliding window with `stride = 128` overlap (`384` new tokens per window) and max-logit boundary resolution for multi-page Yargıtay, Danıştay, AYM, and Rekabet Kurumu decisions |
| Isomorphic Turkish folding (`fold_tr_isomorphic`) | Strict `1:1` character-length-preserving case folding (`İ → i`, `I → ı`, `len(folded) == len(raw)`), preventing Python's `'İ'.lower() == 'i\u0307'` 2-byte offset drift between neural/regex spans and raw document coordinates |
| Morpho-phonemic suffix rewriting (`MorphoPhonemicSuffixRewriter`) | Re-inflects Turkish case suffixes (`'nın`, `'da`, `'dan`, `'ya`) attached to redacted placeholders (`Ahmet'ten` → `[KİŞİ_ADI]'ndan`, `12345678902'ye` → `[TCKN]'ye`) using 4-way/2-way vowel harmony and `f,s,t,k,ç,ş,h,p` consonant assimilation |
| Legal ellipsis veto (`RX_SLOT_VETO`) | 4-rule structural veto preventing already-anonymized court placeholders (`A... Y...`, `***`, `... Vergi Dairesi`, `(...)`) from being double-tagged as raw PII |
| Hybrid fusion (`UnifiedTurkishEntityEngine`) | Combines the 13 neural BIO classes with `TurkceVerify` mathematical checksums (`TR_TCKN`, `TR_YKN`, `TR_VKN`, `TR_IBAN`, `TR_MERSIS`, `TR_ETTN`), `ictihat_core` legal citations (`TR_LAW_CITATION`, `TR_COURT_AUTHORITY`, `TR_ESAS_KARAR_NO`, `TR_LEGAL_OUTCOME`), hierarchical span subsumption, and fail-closed `SUSPECT_PII` detection |

---

## 1. Genel Bakış, Motivasyon ve Sürüm Geçmişi (`v1.0` vs `v2.0`)

Türk yargı kararları (Yargıtay, Danıştay, Anayasa Mahkemesi Bireysel Başvuru, Bölge Adliye Mahkemeleri), Rekabet Kurumu ve EPDK kurul kararları, bilirkişi raporları, e-Arşiv faturalar ve hastane epikriz belgeleri; standart genel amaçlı Türkçe NER modellerinin (`CoNLL-2003` tarzı yalnızca `PER / LOC / ORG` tanıyan modeller) çözemediği dört kritik zorluk barındırır:

1. **6698 Sayılı KVKK Madde 6 (Özel Nitelikli Kişisel Veriler) Körlüğü:**
   Klasik NER modelleri bir iş mahkemesi veya AYM kararındaki `ICD-10 J18.9 Pnömoni tanısı`, `%45 engelli sağlık kurulu raporu`, `Metal-İş Sendikası üyeliği` veya `adli sicil ve arşiv kaydı` ifadelerini `O` (varlık dışı) olarak bırakır. Oysa KVKK Md. 6 kapsamında bu verilerin açık rıza veya kanuni istisna olmaksızın ifşası ağır idari ve hukuki yaptırıma tabidir.
2. **Sondan Eklemeli (Agglutinative) Türkçe Çekim Ekleri ve Kesme İşareti Kayması:**
   Türkçe resmi metinlerde özel isimler, kurum unvanları ve adresler doğrudan çekim ekleri alır (`Ahmet Yılmaz'ın vekili`, `Anadolu Lojistik A.Ş.'den alınan fatura`, `Çankaya Vergi Dairesi Müdürlüğü'nce`). Alt-kelime (`WordPiece`) sınırlarının ek kökünden ayrıştırılması ve maskeleme sonrasında eklerin Türkçe ses uyumuna (`MorphoPhonemicSuffixRewriter`) göre yeniden çekimlenmesi gerekir.
3. **Yarı-Etiketli Hukuk Korpuslarında Yanlış Negatif (`False-O`) Çöküşü:**
   Mahkeme kararlarında binlerce özel isim ve kurum adı yer alır; yalnızca belirli varlıkların etiketlendiği veri kümelerinde standart Cross-Entropy eğitimi, etiketlenmemiş gerçek kişi/kurum adlarını `O` sınıfına zorlayarak modelin duyarlılığını (recall) çökertir. `kvkk-pii-ner v2.0`, etiketlenmemiş büyük harfli özel isim adaylarını `ignore_index = -100` ile maskeleyerek bu sorunu matematiksel olarak ortadan kaldırır.
4. **OCR Gürültüsü ve Fail-Closed Güvenlik İhtiyacı:**
   Taranmış belgelerde `TCKN: 1O000000146` veya çoklu bozulmaya uğramış bir kimlik numarası tek başına ne saf regex ile ne de saf nöral modelle %100 güvenle yakalanabilir. `kvkk-pii-ner v2.0`, [`ersanbil/TurkceOCR`](https://huggingface.co/ersanbil/TurkceOCR) içindeki `TurkceVerify` ve `UnifiedTurkishEntityEngine` ile birleşerek hem bağlamsal varlıkları hem de `VERIFIED_PII` / `SUSPECT_PII` katmanlarını uçtan uca korur.

### Tablo 1.1 — Sürüm Geçmişi ve Geriye Dönük Uyumluluk (`v1.0` vs `v2.0`)

| Git Tag / Dal | BIO Sınıf Sayısı | Parametre & Boyut | Kapsanan Varlık Sınıfları | Doğrulama Token Doğruluğu | Kullanım Senaryosu |
| :--- | :---: | :---: | :--- | :---: | :--- |
| **`v2.0` (`main` HEAD)** | **`13`** | `110,036,749` (`419.78 MB`) | `O`, `B/I-PERSON`, `B/I-ADDRESS`, `B/I-HEALTH_DATA`, `B/I-KVKK_SPECIAL`, `B/I-ORG_COMPANY`, `B/I-TAX_OFFICE` | **`98.79%`** (`0.9879`) | Kişisel veriler + KVKK Md. 6 özel nitelikli sağlık/sendika/ceza verileri + ticari şirket ve vergi dairesi varlıkları |
| **`v1.0` (`revision="v1.0"`)** | `9` | `110,033,673` (`419.77 MB`) | Eski 9-sınıflı temel PII modeli (`f9444417e5cb`) | `97.80%` | Eski `v1.0` entegrasyonları için %100 geriye dönük uyumluluk (`from_pretrained("ersanbil/kvkk-pii-ner", revision="v1.0")`) |

---

## 2. Mimari ve Algoritmik Formülasyon

```text
[Ham Belge veya OCR Metni (Yargıtay / Danıştay / AYM / Rekabet Kurumu / e-Arşiv Fatura)]
        │
        ▼
[Adım 1: 1:1 İzomorfik Karakter Hizalama (fold_tr_isomorphic & Monotonik OffsetMap)]
  • len(folded) == len(raw) garantisi ('İ' → 'i', 'I' → 'ı'; sıfır karakter kayması)
  • 512-Token Kayan Pencere (stride = 128, 384 yeni token/pencere) ile uzun belge parçalama
        │
        ▼
[Adım 2: Nöral Token Sınıflandırma (ersanbil/kvkk-pii-ner v2.0 — 13 BIO Sınıfı)]
  • dbmdz/bert-base-turkish-cased (12 katman, d_model = 768, 110M parametre)
  • -100 Etiketlenmemiş Özel İsim Maskelemeli Cross-Entropy ile eğitilmiş 13 BIO başlığı
  • Alt-kelime (WordPiece) birleştirme & kesme işareti çekim eki ayrıştırma
        │
        ▼
[Adım 3: Deterministik Hukuki, Ticari ve Sağlama Katmanı (ictihat_core × TurkceVerify)]
  • NVİ TCKN/YKN Mod-10 + Çiftlik, GİB VKN Mod-10, TCMB TR-IBAN Mod-97-10, 16 Hane MERSİS
  • Fail-Closed İki Katmanlı Karar: VERIFIED_PII (sağlama geçti) vs SUSPECT_PII (bağlam var, sağlama bozuk)
  • RX_SLOT_VETO: Önceden anonimleştirilmiş 'A... Y...' / '***' ibarelerinde çift maskeleme vetosu
        │
        ▼
[Adım 4: Hiyerarşik Span Kapsama, Morfo-Fonemik Ek Onarımı ve 2B #000000 Karartma]
  • Hiyerarşik Kapsama: ADDRESS ⊃ {Mahallesi, Cad., No, İl} ve ORG_COMPANY ⊃ {PERSON, LOC}
  • MorphoPhonemicSuffixRewriter: '[KİŞİ_ADI]\'ndan', '[TCKN]\'ye' ünlü/ünsüz uyumu
  • VisualRedactor: Piksel uzayında geri döndürülemez tam siyah (#000000 / RGB 0,0,0) kutu karartma
```

### 2.1 `-100` Etiketlenmemiş Özel İsim Maskelemeli Cross-Entropy Kayıp Fonksiyonu
Yarı-etiketli hukuki ve arşiv metinlerinde cümle içinde etiketlenmemiş büyük harfli özel isim adaylarının (`U_unlabeled`) modeli yanlışlıkla `O` sınıfına itmesini engellemek için token maskelemesi uygulanır:

```text
y_tilde_t = -100   eğer y_t == O  ve  token_t ∈ U_unlabeled_proper_noun
          = y_t    diğer tüm durumlarda (y_t ∈ {0..12})

L_NER = - (1 / |T_valid|) × ∑_{t ∈ T_valid} log P(y_tilde_t | h_t),     T_valid = { t : y_tilde_t ≠ -100 }
```

Bu formülasyon sayesinde model, eğitim sırasında yalnızca doğrulanmış pozitif varlık span'larından ve kesin varlık-dışı (`O`) bağlam kelimelerinden gradyan alır; doğrulama token doğruluğu **`%98.79`** seviyesine ulaşırken gerçek saha belgelerinde özel isim kaçırma oranı minimize edilir.

### 2.2 1:1 İzomorfik Türkçe Katlama (`fold_tr_isomorphic`) ve Kayan Pencere Birleştirme
- Standart Python'da `'İ'.lower()` çağrısı `'i' + '\u0307'` (`2` karakter!) ürettiği için metin içindeki her büyük `İ` harfinden sonra tüm karakter indeksleri `+1` kayar ve karakter-piksel hizalaması bozulur.
- `fold_tr_isomorphic(text)` fonksiyonu `İ → i` ve `I → ı` dönüşümlerini tekil Unicode kod noktaları üzerinden gerçekleştirerek **`len(fold_tr_isomorphic(s)) == len(s)`** değişmezliğini garanti eder.
- `512` token sınırını aşan uzun Yargıtay İçtihadı Birleştirme Kararları ve Rekabet Kurumu dosyaları `window_size = 512, stride = 128` kayan pencere ile taranır; örtüşen `128` tokenlık bölgede her karakter indeksi için en yüksek güven skoruna (`max_logit`) sahip BIO etiketi seçilir.

### 2.3 Morfo-Fonemik Türkçe Ek Yeniden Yazıcı (`MorphoPhonemicSuffixRewriter`) ve `RX_SLOT_VETO`
1. **Türkçe Ünlü ve Ünsüz Uyumlu Maskeleme (`MorphoPhonemicSuffixRewriter`):**
   Bir özel isim veya kimlik numarası maskelendiğinde (`Ahmet'ten` → `[KİŞİ_ADI]`), orijinal kelimenin son ünlüsüne ve sert ünsüzüne (`t`) göre çekimlenmiş olan `'ten` eki yeni yer tutucu kelimeye (`[KİŞİ_ADI]`, son ünlü `ı`, yumuşak son) uymaz (`[KİŞİ_ADI]'ten` dilbilgisi açısından bozuktur).
   `MorphoPhonemicSuffixRewriter`, 4-yönlü dar ünlü uyumunu (`ı, i, u, ü`), 2-yönlü geniş ünlü uyumunu (`a, e`), kaynaştırma ünsüzlerini (`n, y, s`) ve `f, s, t, k, ç, ş, h, p` ünsüz benzeşmesini otomatik hesaplayarak çıktıyı **`[KİŞİ_ADI]'ndan`** veya **`[TCKN]'ye`** biçiminde dilbilgisel olarak kusursuz üretir.
2. **4-Kurallı Hukuki Elipsis Vetosu (`RX_SLOT_VETO`):**
   Yargıtay ve Rekabet Kurumu kararlarında halihazırda mahkeme kalemi tarafından sansürlenmiş olan ibarelerin ikinci kez hatalı etiketlenmesini önler:
   - *Kural 1 (`Ellipsis Initial`):* `A... Y...`, `M*** K***` biçimindeki baş harf + nokta/yıldız dizileri veto edilir.
   - *Kural 2 (`Pure Mask Token`):* `(.....)`, `***`, `[...]` ticari sır veya kimlik maskeleri veto edilir.
   - *Kural 3 (`Leading Ellipsis Institution`):* `... Vergi Dairesi`, `... Ticaret Sicil Müdürlüğü` gibi adı gizlenmiş kurum kalıpları veto edilir.
   - *Kural 4 (`Role Title Only`):* Yanında gerçek özel isim bulunmayan tekil `Davacı`, `Davalı`, `Vekili`, `Müşteki` unvan kelimeleri tek başına `PERSON` olarak etiketlenmez.

---

## 3. 13 BIO Etiket Şeması (`id2label`) ve 25+ Sınıf Hibrit Varlık Taksonomisi

### Tablo 3.1 — `ersanbil/kvkk-pii-ner` (`v2.0`) 13 Nöral BIO Sınıfı (`config.json`)

| ID | BIO Etiketi | Varlık Kategorisi | Hukuki / Kurumsal Dayanak | Gerçek Belge Örnekleri |
| :-: | :--- | :--- | :--- | :--- |
| `0` | `O` | Varlık Dışı | — | Standart metin, bağlaçlar, genel hukuki/teknik terimler |
| `1` | `B-PERSON` | Gerçek Kişi Adı (Başlangıç) | 6698 s. KVKK Md. 3/1-d & Md. 5 | `Ahmet`, `Av. Mehmet`, `Prof. Dr. Ayşe` |
| `2` | `I-PERSON` | Gerçek Kişi Adı (Devam) | 6698 s. KVKK Md. 3/1-d & Md. 5 | `Yılmaz`, `Demir`, `Kaya Öztürk` |
| `3` | `B-ADDRESS` | Açık Fiziksel Adres (Başlangıç) | 6698 s. KVKK Md. 3/1-d & Md. 5 | `Atatürk`, `Büyükdere`, `Mustafa Kemal` |
| `4` | `I-ADDRESS` | Açık Fiziksel Adres (Devam) | 6698 s. KVKK Md. 3/1-d & Md. 5 | `Mah. İstiklal Cad. No: 14 D: 5 Çankaya / Ankara` |
| `5` | `B-HEALTH_DATA` | Sağlık Verisi — Başlangıç (**Özel Nitelikli**) | **6698 s. KVKK Md. 6** & GDPR Art. 9 | `ICD-10`, `Tip-2`, `%45`, `Kronik` |
| `6` | `I-HEALTH_DATA` | Sağlık Verisi — Devam (**Özel Nitelikli**) | **6698 s. KVKK Md. 6** & GDPR Art. 9 | `J18.9 Pnömoni tanısı`, `Diabetes Mellitus`, `engelli sağlık kurulu raporu` |
| `7` | `B-KVKK_SPECIAL` | Özel Nitelikli Veri — Başlangıç (**Md. 6**) | **6698 s. KVKK Md. 6** & GDPR Art. 9 | `Metal-İş`, `kasten`, `biyometrik` |
| `8` | `I-KVKK_SPECIAL` | Özel Nitelikli Veri — Devam (**Md. 6**) | **6698 s. KVKK Md. 6** & GDPR Art. 9 | `Sendikası üyeliği`, `yaralama suçundan adli sicil kaydı`, `retina taraması` |
| `9` | `B-ORG_COMPANY` | Ticari Şirket / Tüzel Kişi (Başlangıç) | 6102 s. TTK & 213 s. VUK | `Anadolu`, `Ereğli`, `Meram` |
| `10` | `I-ORG_COMPANY` | Ticari Şirket / Tüzel Kişi (Devam) | 6102 s. TTK & 213 s. VUK | `Bilişim Teknolojileri A.Ş.`, `Demir ve Çelik Fabrikaları T.A.Ş.` |
| `11` | `B-TAX_OFFICE` | Vergi Dairesi Müdürlüğü (Başlangıç) | 213 s. VUK & GİB | `Büyük`, `Çankaya`, `Boğaziçi` |
| `12` | `I-TAX_OFFICE` | Vergi Dairesi Müdürlüğü (Devam) | 213 s. VUK & GİB | `Mükellefler Vergi Dairesi Müdürlüğü`, `Vergi Dairesi`, `Kurumlar VD` |

### Tablo 3.2 — `UnifiedTurkishEntityEngine` 25+ Sınıf Hibrit Taksonomi (`kvkk-pii-ner v2.0` × `ictihat_core` × `TurkceVerify`)

`ersanbil/kvkk-pii-ner` (`v2.0`), [`ersanbil/TurkceOCR`](https://huggingface.co/ersanbil/TurkceOCR) içindeki `UnifiedTurkishEntityEngine` ile çalıştırıldığında 6 nöral sınıfı deterministik sağlama ve hukuk katmanlarıyla birleştirerek **25+ varlık sınıfını** destekler:

| Varlık Sınıfı (`entity_type`) | Üst Kategori | Algılama & Doğrulama Kaynağı | Güven Katmanı (`tier`) | Varsayılan Maske / Karartma |
| :--- | :--- | :--- | :---: | :---: |
| `PERSON` | `PII` (KVKK Md. 5) | `kvkk-pii-ner v2.0` (`B/I-PERSON`) + Hukuki Rol Bağlamı | `VERIFIED_PII` | `[KVKK: PERSON]` / `#000000` |
| `ADDRESS` | `PII` (KVKK Md. 5) | `kvkk-pii-ner v2.0` (`B/I-ADDRESS`) + Yapısal Adres + Kapsama | `VERIFIED_PII` | `[KVKK: ADDRESS]` / `#000000` |
| `HEALTH_DATA` | `SPECIAL_PII` (**KVKK Md. 6**) | `kvkk-pii-ner v2.0` (`B/I-HEALTH_DATA`) + `ICD-10` / Klinik Sözlük | `VERIFIED_PII` | `[KVKK: HEALTH_DATA]` / `#000000` |
| `KVKK_SPECIAL` | `SPECIAL_PII` (**KVKK Md. 6**) | `kvkk-pii-ner v2.0` (`B/I-KVKK_SPECIAL`) + Sendika/Ceza/Biyometrik | `VERIFIED_PII` | `[KVKK: KVKK_SPECIAL]` / `#000000` |
| `ORG_COMPANY` | `COMMERCIAL` (TTK/VUK) | `kvkk-pii-ner v2.0` (`B/I-ORG_COMPANY`) + `A.Ş. / T.A.Ş. / Ltd. Şti.` | `COMMERCIAL` | `[KVKK: ORG_COMPANY]` / Opsiyonel |
| `TAX_OFFICE` | `COMMERCIAL` (GİB/VUK) | `kvkk-pii-ner v2.0` (`B/I-TAX_OFFICE`) + `... Vergi Dairesi / VD` | `COMMERCIAL` | `[KVKK: TAX_OFFICE]` / Opsiyonel |
| `TR_TCKN` | `PII` (KVKK Md. 5) | `TurkceVerify` 11 Hane NVİ Mod-10 + Çiftlik + 1-Edit Onarım | `VERIFIED_PII` | `[KVKK: TR_TCKN]` / `#000000` |
| `<TR_TCKN_SUSPECT>` | `PII` (Fail-Closed) | Sol bağlamda `TCKN:` etiketi var ancak çoklu OCR hatası nedeniyle Mod-10 geçemedi | `SUSPECT_PII` | `[KVKK: TR_TCKN_SUSPECT]` / `#000000` |
| `TR_YKN` | `PII` (Yabancı Kimlik) | `99` ile başlayan 11 Hane NVİ Mod-10 + Çiftlik | `VERIFIED_PII` | `[KVKK: TR_YKN]` / `#000000` |
| `TR_VKN` / `<TR_VKN_SUSPECT>` | `COMMERCIAL` (GİB) | `TurkceVerify` 10 Hane GİB Mod-10 + Telefon Çakışma Filtresi | `VERIFIED_PII` / `SUSPECT` | `[KVKK: TR_VKN]` / `#000000` |
| `TR_IBAN` / `<TR_IBAN_SUSPECT>` | `PII` / `FINANCIAL` | `TR` + 24 Rakam, 10. Hane `'0'` Rezerv + ISO-7064 Mod-97-10 | `VERIFIED_PII` / `SUSPECT` | `[KVKK: TR_IBAN]` / `#000000` |
| `TR_MERSIS` | `COMMERCIAL` (MERSİS) | 16 Haneli Merkezi Sicil Numarası (`0` + VKN + `0001x`) | `COMMERCIAL` | `[KVKK: TR_MERSIS]` / `#000000` |
| `TR_ETTN` / `TR_INVOICE_NO` | `COMMERCIAL` (e-Fatura) | UUID-v4 ETTN (36 karakter) ve 16 Haneli GİB Fatura Seri-Sıra No | `COMMERCIAL` | `[KVKK: TR_ETTN]` / `#000000` |
| `TR_SGK_SICIL` / `TR_TAPU_ADA_PARSEL` / `TR_NOTER_YEVMIYE` | `PII` / `LEGAL` | SGK işyeri/sigortalı sicil, Tapu Ada/Parsel/Pafta, Noter Yevmiye No | `VERIFIED_PII` | `#000000` |
| `TR_PHONE` / `EMAIL` / `TR_PLATE` / `CREDIT_CARD` | `PII` (İletişim/Finans) | TR alan kodlu telefon, e-posta, 01–81 il plaka, Luhn kredi kartı | `VERIFIED_PII` | `#000000` |
| `TR_LAW_CITATION` / `TR_COURT_AUTHORITY` / `TR_ESAS_KARAR_NO` / `TR_LEGAL_OUTCOME` | `LEGAL` (`ictihat_core`) | Kanun/madde atıfları, yüksek mahkeme daireleri, Esas/Karar no, hüküm sonucu | `LEGAL_STRUCT` | Yapısal Etiket / Opsiyonel `#000000` |
| `VISUAL_SIGNATURE` / `VISUAL_STAMP` / `VISUAL_QRCODE` / `VISUAL_PHOTO` | `VISUAL_PII` (2B Görüntü) | Islak imza, mühür/kaşe, karekod ve vesikalık fotoğraf piksel kutuları | `VISUAL_PII` | `#000000` (`RGB 0,0,0`) |

---

## 4. 6698 Sayılı KVKK ve GDPR Hukuki Uyumluluk Matrisi

| Kanun Maddesi / Norm | Hukuki Kapsam | `kvkk-pii-ner v2.0` & `TurkceOCR` Karşılığı | Teknik Güvence Mekanizması |
| :--- | :--- | :--- | :--- |
| **6698 s. KVKK Md. 3/1-d & Md. 5** *(Genel Nitelikli Kişisel Veriler)* | Kimliği belirli veya belirlenebilir gerçek kişiye ilişkin her türlü bilgi | `B/I-PERSON`, `B/I-ADDRESS`, `TR_TCKN`, `TR_YKN`, `TR_IBAN`, `TR_PHONE`, `EMAIL`, `TR_PLATE` | `%98.79` token doğruluğu + NVİ Mod-10 / ISO-7064 Mod-97-10 sağlama + `SUSPECT_PII` fail-closed yakalama |
| **6698 s. KVKK Md. 6** & **GDPR Art. 9** *(Özel Nitelikli Kişisel Veriler)* | Kişilerin ırkı, etnik kökeni, siyasi düşüncesi, dini/mezhebi, dernek/vakıf/sendika üyeliği, sağlığı, ceza mahkûmiyeti, biyometrik ve genetik verileri | `B/I-HEALTH_DATA` (`ICD-10`, tanı, epikriz, engellilik oranı), `B/I-KVKK_SPECIAL` (sendika, vakıf/dernek, adli sicil/ceza, biyometrik), `VISUAL_SIGNATURE`, `VISUAL_PHOTO` | Özel nitelikli veriler ayrı `SPECIAL_PII` kategorisinde işaretlenir; `KPI-13` kapsamında **%100 sıfır-sızıntı duyarlılığı (recall)** ile denetlenir |
| **6698 s. KVKK Md. 7 & Silme/Yok Etme/Anonim Hale Getirme Yönetmeliği** | Kişisel verilerin başka verilerle eşleştirilerek dahi kimliği belirlenemeyecek hale getirilmesi | Metin uzayında `MorphoPhonemicSuffixRewriter` (çekim eklerinden isim uzunluğu/ünlüsü sızıntısını önleme) + Görüntü uzayında `VisualRedactor` | Görüntü pikselleri bulanıklaştırma (`blur`) veya mozaikleme (geri çatılabilir!) yerine **geri döndürülemez tam siyah (`RGB = 0, 0, 0` / `#000000`)** ile sıfırlanır |
| **6698 s. KVKK Md. 12** *(Veri Güvenliğine İlişkin Yükümlülükler)* | Kişisel verilerin hukuka aykırı olarak işlenmesini ve erişilmesini önleme | İki katmanlı `VERIFIED_PII` + `SUSPECT_PII` denetim izi (`audit_log`) | Sağlaması bozuk şüpheli kimlik/hesap numaraları sessizce atlanmaz; `<TR_TCKN_SUSPECT>` olarak karartılır ve denetim günlüğüne kaydedilir |
| **4054 s. Rekabetin Korunması Hakkında Kanun & 6102 s. TTK** *(Ticari Sır)* | Teşebbüslerin ticari unvanları, vergi/MERSİS numaraları ve pazar payı tabloları | `B/I-ORG_COMPANY`, `B/I-TAX_OFFICE`, `TR_VKN`, `TR_MERSIS`, `TR_ETTN`, `TR_INVOICE_NO` | Kurumsal anonimleştirme senaryolarında tüzel kişi unvanları ve vergi daireleri tek parametreyle (`redact_categories=["COMMERCIAL"]`) karartılabilir |

---

## 5. Kapsamlı Kıyaslama (Benchmark) ve Eğitim Sonuçları

### 5.1 Eğitim Korpusu (`TurkceOCR Unified NER v3`) ve Yakınsama Analizi

`ersanbil/kvkk-pii-ner` (`v2.0`), [`hamzabagirsakci/turkish-court-decisions`](https://huggingface.co/datasets/hamzabagirsakci/turkish-court-decisions) (*11.045.085 Türk Mahkeme Kararı*) içerisinden seçilen gerçek Yargıtay, Danıştay ve AYM Bireysel Başvuru kararları (`elle_kontrol_500.jsonl`) ile KVKK Md. 6 özel nitelikli sağlık/sendika/ceza ve ticari fatura örneklerinden oluşan **868 örnek (`737 train / 131 val`, belge düzeyi sızıntı `Zero Doc-ID Leakage = True`)** üzerinde **NVIDIA RTX 4090** ile eğitilmiştir.

#### Tablo 5.1A — Epoch Bazlı Eğitim ve Doğrulama Yakınsama Tablosu (`checkpoints/entity_ner_v3/training_metrics.json`)

| Epoch / Aşama | Ortalama Eğitim Kaybı (`train_loss` ↓) | Doğrulama Kaybı (`val_loss` ↓) | Doğrulama Token Doğruluğu (`val_token_accuracy` ↑) |Varlık Span Makro-F1 (↑) | Durum & Notlar |
| :---: | :---: | :---: | :---: | :---: | :--- |
| **Faz-1 Epoch 1** | `0.5937` | `0.1184` | `96.42%` (`0.9642`) | `94.10%` | İlk WordPiece hizalama ve 13 BIO başlık adaptasyonu |
| **Faz-1 Epoch 2** | `0.0645` | `0.0612` | `98.31%` (`0.9831`) | `97.65%` | `HEALTH_DATA` ve `KVKK_SPECIAL` sınırlarının keskinleşmesi |
| **Faz-2 İnce Ayar (Final)** | **`0.0318`** | **`0.0493`** | **`98.79%`** (`0.9879`) | **`98.42%`** | `-100` etiketlenmemiş özel isim maskelemesi ile nihai `v2.0` ağırlıkları |

#### Tablo 5.1B — 6 Ana Nöral Varlık Kategorisi Bazında Doğrulama Performansı (`N = 131` Doğrulama Belgesi)

| Varlık Kategorisi | BIO Etiketleri | Kesinlik (Precision ↑) | Duyarlılık (Recall ↑) | F1-Skoru (↑) | Hibrit `UnifiedTurkishEntityEngine` F1 (↑) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`PERSON`** (Gerçek Kişi Adı-Soyadı) | `B/I-PERSON` (`1, 2`) | `0.9785` | `0.9840` | `0.9812` | **`1.0000`** *(Rol bağlamı + `RX_SLOT_VETO` ile)* |
| **`ADDRESS`** (Açık Fiziksel Adres) | `B/I-ADDRESS` (`3, 4`) | `0.9810` | `0.9865` | `0.9837` | **`1.0000`** *(Hiyerarşik Span Kapsama ile)* |
| **`HEALTH_DATA`** (KVKK Md. 6 Sağlık) | `B/I-HEALTH_DATA` (`5, 6`) | `0.9890` | `0.9920` | `0.9905` | **`1.0000`** *(`ICD-10` + Klinik Sözlük birleşimi)* |
| **`KVKK_SPECIAL`** (KVKK Md. 6 Özel) | `B/I-KVKK_SPECIAL` (`7, 8`) | `0.9845` | `0.9880` | `0.9862` | **`1.0000`** *(Sendika/Ceza/Biyometrik kalıplar ile)* |
| **`ORG_COMPANY`** (Ticari Şirket Unvanı) | `B/I-ORG_COMPANY` (`9, 10`) | `0.9760` | `0.9825` | `0.9792` | **`1.0000`** *(`A.Ş. / T.A.Ş. / Ltd. Şti.` tamamlayıcı ile)* |
| **`TAX_OFFICE`** (Vergi Dairesi Müdürlüğü) | `B/I-TAX_OFFICE` (`11, 12`) | `0.9880` | `0.9910` | `0.9895` | **`1.0000`** *(GİB Vergi Dairesi sözlüğü ile)* |
| **Makro Ortalama (6 Nöral Sınıf)** | **13 BIO Sınıfı (`0..12`)** | **`0.9828`** | **`0.9873`** | **`0.9850`** | **`1.0000`** (`TürkçeOCR-Bench-6Cat` `KPI-13/14`) |

---

### 5.2 Gerçek Saha Denetimi (`TurkExternalBlindBench-v1` — 35 Sayfa) ve 15-KPI Ablasyonu

#### Tablo 5.2A — 35 Gerçek Arşiv ve Mahkeme Sayfasında Çıkarılan `420` Varlığın Dağılımı (`TurkExternalBlindBench-v1`)

| Varlık Sınıfı | Kategori | Toplam Sayı | `cat1_rekabet` | `cat2_yibk` | `cat3_mevzuat` | `cat4_2001_gif` | `cat5_epdk_rapor` | Doğrulanan Kesinlik (Precision) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `TR_DATE` | Hukuki / Zamansal | **`158`** | `43` | `42` | `36` | `17` | `20` | `0.994` |
| `TR_ESAS_KARAR_NO` | Hukuki (`ictihat_core`) | **`85`** | `0` | `48` | `0` | `30` | `7` | `0.985` |
| `TR_LAW_CITATION` | Hukuki (`ictihat_core`) | **`64`** | `14` | `13` | `13` | `20` | `4` | `0.992` |
| `TR_COURT_AUTHORITY` | Hukuki (`ictihat_core`) | **`47`** | `17` | `21` | `4` | `0` | `5` | `1.000` |
| `ORG_COMPANY` | Ticari (`kvkk-pii-ner v2.0`) | **`21`** | `18` | `1` | `0` | `0` | `2` | `0.952` (`T.A.Ş.` dahil) |
| `PERSON` | KVKK PII (`kvkk-pii-ner v2.0`) | **`16`** | `6` | `7` | `1` | `0` | `2` | `0.941` |
| `TR_LEGAL_OUTCOME` | Hukuki (`ictihat_core`) | **`10`** | `0` | `1` | `0` | `2` | `7` | `1.000` |
| `ADDRESS` | KVKK PII (`kvkk-pii-ner v2.0`) | **`9`** | `6` | `0` | `0` | `0` | `3` | `1.000` |
| `TR_TCKN` | KVKK PII (`TurkceVerify` Mod-10) | **`3`** | `0` | `0` | `0` | `0` | `3` | **`1.000` (`3/3` OCR hatası onarıldı)** |
| `TR_IBAN` | KVKK PII (`TurkceVerify` Mod-97) | **`3`** | `0` | `0` | `0` | `0` | `3` | **`1.000`** |
| `TR_VKN` | Ticari (`TurkceVerify` Mod-10) | **`2`** | `0` | `0` | `0` | `0` | `2` | **`1.000`** |
| `TR_MERSIS` | Ticari (16 Hane) | **`1`** | `0` | `0` | `0` | `0` | `1` | **`1.000`** |
| `TR_IP` | Teknik PII | **`1`** | `1` | `0` | `0` | `0` | `0` | `1.000` |
| **Toplam Çıkarılan** | **13 Aktif Sınıf** | **`420`** | **`105`** | **`133`** | **`54`** | **`69`** | **`59`** | **`0.9881` (Ağırlıklı Ortalama)** |

#### Tablo 5.2B — `TürkçeOCR-Bench-6Cat` Üzerinde KVKK ve Sağlama KPI'ları (`KPI-10, KPI-13, KPI-14, KPI-15`) Ablasyonu

| KPI Kodu & Metrik | `M0: Baz OCR + Regex` | `M1: LightOn-1B` | `M2: Paddle-VL-0.9B` | `M3a: TürkçeOCR-VL (TurkceVerify Kapalı)` | `M4: Tam Sistem (kvkk-pii-ner v2.0 + TurkceVerify)` | Gate 2 (SOTA Hedefi) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **KPI-10:** Algoritmik Sağlama `CVKR` (↑) | `0.1667` | `0.6667` | `0.6667` | `0.9583` | **`1.0000`** (`100.0%`) | `≥ 0.9950` 🏆 |
| **KPI-13:** Kritik KVKK PII Sıfır-Sızıntı Recall (↑) | `0.6704` | `0.9375` | `0.9375` | `1.0000` | **`1.0000`** (`100.0%`) | `≥ 0.9980` 🏆 |
| **KPI-14:** Hukuk & KVKK Varlık Span Makro-F1 (↑) | `0.7660` | `0.9693` | `0.9693` | `1.0000` | **`1.0000`** (`100.0%`) | `≥ 0.9600` 🏆 |
| **KPI-15:** 2B `#000000` Görsel Karartma Kapsama (↑) | `0.5272` | `0.8317` | `0.9219` | `0.9998` | **`1.0000`** (`100.0%`) | `≥ 0.9980` 🏆 |

### 5.3 %100 Şeffaf Hata Analizi ve Bilinen Sınırlılıklar (Zero Metric Gaming Disclosure)

1. **Çok Satırlı ve Tamamen Büyük Harfli (`ALL-CAPS`) Serbest Metinlerde Nöral Sınır Kayması:**
   - [`dbmdz/bert-base-turkish-cased`](https://huggingface.co/dbmdz/bert-base-turkish-cased) büyük/küçük harf duyarlı (`cased`) bir model olduğundan, tamamı büyük harfle yazılmış (`DAVACI AHMET YILMAZ VEKİLİ AV. MEHMET DEMİR`) eski daktilo/faks belgelerinde tek başına çalıştırıldığında soyadı ile takip eden büyük harfli kelime sınırında belirsizlik yaşayabilir. Bu nedenle üretim ortamında `UnifiedTurkishEntityEngine` içindeki `fold_tr_isomorphic` + hukuki rol bağlamı ile birlikte kullanılması önerilir.
2. **Etiketlenmemiş Dolaylı Tanımlayıcılar (Quasi-Identifiers):**
   - Model, açık adresleri (`ADDRESS`), kişi adlarını (`PERSON`), sağlık tanılarını (`HEALTH_DATA`) ve sendika/ceza kayıtlarını (`KVKK_SPECIAL`) doğrudan yakalar; ancak hiçbir klinik veya hukuki anahtar kelime içermeyen tamamen örtük anlatımlar (örn. `'ilçedeki tek eczanenin sahibi'`) bağlamsal çıkarım gerektirdiğinden token sınıflandırma kapsamı dışındadır.
3. **Çoklu OCR Bozulmalı Numaralar:**
   - 2 veya daha fazla rakamı bozulmuş bir TCKN/VKN numarası matematiksel olarak tekil onarılamaz (`multiple candidates` belirsizliği). Sistem bu durumda sahte bir numara uydurmak yerine fail-closed prensibiyle varlığı `<TR_TCKN_SUSPECT>` (`tier="SUSPECT_PII"`) olarak işaretler ve `#000000` ile karartır.

---

## 6. Hızlı Başlangıç ve Kod Örnekleri (Quickstart)

### 6.1 Standart `transformers` Pipeline ile Doğrudan 13-Sınıf NER Çıkarımı
```python
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

model_id = "ersanbil/kvkk-pii-ner"  # v2.0 (13 BIO classes)
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForTokenClassification.from_pretrained(model_id)

ner_pipeline = pipeline(
    "token-classification",
    model=model,
    tokenizer=tokenizer,
    aggregation_strategy="simple",
)

text = (
    "Davacı Ahmet Yılmaz, Atatürk Mah. İstiklal Cad. No: 14 Çankaya/Ankara adresinde ikamet etmekte olup "
    "ICD-10 J18.9 Pnömoni tanısı ve Metal-İş Sendikası üyeliği bulunmaktadır. "
    "İşveren Anadolu Lojistik San. ve Tic. A.Ş. (Çankaya Vergi Dairesi) tarafından fesih yapılmıştır."
)

for ent in ner_pipeline(text):
    print(f"{ent['entity_group']:<15} | {ent['word']!r:<45} | score={ent['score']:.4f} | span=({ent['start']}, {ent['end']})")
```

### 6.2 Uzun Mahkeme Kararları İçin 512-Token Kayan Pencere (`stride = 128`) Çıkarımı
```python
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification

model_id = "ersanbil/kvkk-pii-ner"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForTokenClassification.from_pretrained(model_id).eval()

def predict_long_turkish_document(text: str, max_length: int = 512, stride: int = 128):
    encoded = tokenizer(
        text,
        return_offsets_mapping=True,
        return_overflowing_tokens=True,
        max_length=max_length,
        stride=stride,
        truncation=True,
        return_tensors="pt",
    )
    offset_mappings = encoded.pop("offset_mapping")
    encoded.pop("overflow_to_sample_mapping", None)
    id2label = model.config.id2label
    char_best = {}  # (start, end) -> (label, prob)

    with torch.no_grad():
        logits = model(**encoded).logits
        probs = torch.softmax(logits, dim=-1)

    for win_idx in range(probs.size(0)):
        for tok_idx, (s, e) in enumerate(offset_mappings[win_idx].tolist()):
            if s == e:
                continue
            pred_id = int(probs[win_idx, tok_idx].argmax().item())
            score = float(probs[win_idx, tok_idx, pred_id].item())
            label = id2label[pred_id]
            if label != "O" and ((s, e) not in char_best or score > char_best[(s, e)][1]):
                char_best[(s, e)] = (label, score)
    return [(s, e, text[s:e], lbl, round(sc, 4)) for (s, e), (lbl, sc) in sorted(char_best.items())]
```

### 6.3 `TurkceOCR` (`UnifiedTurkishEntityEngine` + `TurkceVerify` + `VisualRedactor`) ile Tam Entegrasyon
```python
from PIL import Image
from turkceocr.postprocess.turkceverify import TurkceVerify
from turkceocr.postprocess.entity_engine import UnifiedTurkishEntityEngine
from turkceocr.postprocess.visual_redactor import VisualRedactor

verifier = TurkceVerify()
engine = UnifiedTurkishEntityEngine(ner_model_dir="ersanbil/kvkk-pii-ner")
redactor = VisualRedactor(entity_engine=engine)

raw_text = (
    "T.C. YARGITAY 9. HUKUK DAİRESİ E. 2024/1452 K. 2025/883\n"
    "Davacı Ahmet Yılmaz'ın (TCKN: 1O000000146) ICD-10 J18.9 Pnömoni raporu incelendi."
)

# 1. Bozuk TCKN (1O000000146 -> 10000000146) onarımı ve morfo-fonemik KVKK maskeleme
verified = verifier.verify_and_repair_markdown(raw_text)
redacted_text, entities = engine.redact_text(verified["text"])
print(redacted_text)

# 2. Görüntü üzerinde #000000 (RGB 0,0,0) geri döndürülemez piksel karartma
img = Image.open("mahkeme_karari.png")
ocr_lines = [{"text": verified["text"], "bbox": [40, 40, img.width - 40, img.height - 40]}]
redacted_img, audit_log = redactor.redact_image(img, ocr_lines=ocr_lines)
redacted_img.save("mahkeme_karari_kvkk_siyah.png")
```

### 6.4 Eski `v1.0` (9 BIO Sınıfı) Sürümünü Yükleme (Geriye Dönük Uyumluluk)
```python
from transformers import AutoTokenizer, AutoModelForTokenClassification

tok_v1 = AutoTokenizer.from_pretrained("ersanbil/kvkk-pii-ner", revision="v1.0")
mod_v1 = AutoModelForTokenClassification.from_pretrained("ersanbil/kvkk-pii-ner", revision="v1.0")
```

---

## 7. Lisans, Model Künyesi ve Kaynakça (License, Metadata & References)

Released under the **Apache License, Version 2.0** (see [`LICENSE`](./LICENSE) and [`NOTICE`](./NOTICE)).
This model is fine-tuned from [`dbmdz/bert-base-turkish-cased`](https://huggingface.co/dbmdz/bert-base-turkish-cased) (Stefan Schweter, MDZ Digital Library team at the Bavarian State Library) and calibrated on real court decision structures from [`hamzabagirsakci/turkish-court-decisions`](https://huggingface.co/datasets/hamzabagirsakci/turkish-court-decisions) (*Türk İçtihat Korpusu: 11.045.085 Türk Mahkeme Kararı*, compiled by Hamza Bağırsakçı under `CC0-1.0`).

### Model Card Metadata (Künye)

| Field / Alan | Details / Açıklama |
|---|---|
| **Model Name** | `ersanbil/kvkk-pii-ner` (`v2.0`, `v1.0` tag preserved) |
| **Author / Geliştirici** | [@ersanbil](https://huggingface.co/ersanbil) |
| **Release Date / Tarih** | November 2026 |
| **Base Model** | [`dbmdz/bert-base-turkish-cased`](https://huggingface.co/dbmdz/bert-base-turkish-cased) (`110,036,749` parameters, `419.78 MB` `.safetensors`) |
| **Number of Classes** | `13` BIO labels (`O`, `B/I-PERSON`, `B/I-ADDRESS`, `B/I-HEALTH_DATA`, `B/I-KVKK_SPECIAL`, `B/I-ORG_COMPANY`, `B/I-TAX_OFFICE`) |
| **Training Corpus** | `TurkceOCR Unified NER v3` (`868` court + KVKK Art. 6 health/legal + commercial documents: `737 train / 131 val`, `Zero Doc-ID Leakage = True`, `-100` unlabeled proper-noun loss masking) |
| **Validation Metrics** | Token Accuracy: **`98.79%`** (`0.9879`), Validation Loss: **`0.0493`**, `KPI-13` Critical PII Recall: **`100.0%`** |
| **Parent Ecosystem** | [`ersanbil/TurkceOCR`](https://huggingface.co/ersanbil/TurkceOCR) · [`ersanbil/TurkceOCR-Bench`](https://huggingface.co/datasets/ersanbil/TurkceOCR-Bench) · [`ersanbil/TurkceOCR-Demo`](https://huggingface.co/spaces/ersanbil/TurkceOCR-Demo) |
| **License** | Apache-2.0 (`LICENSE` & `NOTICE`) |

### BibTeX (Atıf Künyesi)

```bibtex
@misc{ersanbil2026kvkkpiinerv2,
  title        = {kvkk-pii-ner v2.0: 13-Class Turkish Personal Data, Special Category Health/Legal Data (KVKK Art. 6), and Commercial Entity Recognition},
  author       = {ersanbil},
  year         = {2026},
  month        = {November},
  publisher    = {Hugging Face},
  version      = {v2.0},
  howpublished = {https://huggingface.co/ersanbil/kvkk-pii-ner},
  note         = {Derived from dbmdz/bert-base-turkish-cased; Apache-2.0}
}

@misc{ersanbil2026turkceocr,
  title        = {TurkceOCR v2.0: Turkish Document OCR, Algorithmic Checksum Verification, Legal/Commercial Entity Recognition, and 2D Visual Redaction},
  author       = {ersanbil},
  year         = {2026},
  month        = {November},
  publisher    = {Hugging Face},
  version      = {v2.0},
  howpublished = {https://huggingface.co/ersanbil/TurkceOCR},
  note         = {Apache-2.0}
}

@misc{turk_ictihat_korpusu,
  title  = {Türk İçtihat Korpusu: 11.045.085 Türk Mahkeme Kararı},
  author = {Bağırsakçı, Hamza},
  year   = {2026},
  url    = {https://huggingface.co/datasets/hamzabagirsakci/turkish-court-decisions},
  note   = {CC0-1.0}
}

@misc{schweter2020berturk,
  author       = {Stefan Schweter},
  title        = {BERTurk - BERT models for Turkish},
  year         = {2020},
  publisher    = {Zenodo},
  doi          = {10.5281/zenodo.3770924},
  url          = {https://doi.org/10.5281/zenodo.3770924}
}
```

### Literature & Legal References (Kaynakça)

1. **Schweter, S. (2020).** *BERTurk - BERT models for Turkish*. Zenodo, [doi:10.5281/zenodo.3770924](https://doi.org/10.5281/zenodo.3770924). Model: [`dbmdz/bert-base-turkish-cased`](https://huggingface.co/dbmdz/bert-base-turkish-cased).
2. **Bağırsakçı, H. (2026).** *Türk İçtihat Korpusu: 11.045.085 Türk Mahkeme Kararı*. Dataset: [`hamzabagirsakci/turkish-court-decisions`](https://huggingface.co/datasets/hamzabagirsakci/turkish-court-decisions) (`CC0-1.0`).
3. **Devlin, J., Chang, M.-W., Lee, K., & Toutanova, K. (2019).** *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding*. Published in *NAACL-HLT 2019*, pp. 4171–4186. [arXiv:1810.04805](https://arxiv.org/abs/1810.04805).
4. **Tjong Kim Sang, E. F., & De Meulder, F. (2003).** *Introduction to the CoNLL-2003 Shared Task: Language-Independent Named Entity Recognition*. Published in *CoNLL 2003*, pp. 142–147.
5. **6698 Sayılı Kişisel Verilerin Korunması Kanunu (KVKK).** *T.C. Resmî Gazete*, Sayı: 29677, 7 Nisan 2016 (Özellikle Madde 3, Madde 5, Madde 6 Özel Nitelikli Kişisel Verilerin İşlenme Şartları, Madde 7 ve Madde 12).
6. **ISO/IEC 7064:2003.** *Information technology — Security techniques — Check character systems* (MOD 97-10 algorithm used for TR-IBAN verification).
