# Coordinate Transformation — Çevrimdışı Jeodezik Koordinat Dönüşümü

![Python](https://img.shields.io/badge/Python-3.10%E2%80%933.13-3776AB?logo=python&logoColor=white)
![Kivy](https://img.shields.io/badge/Kivy-2.3-1D6FA5)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS%20%7C%20Android-555)
![Tests](https://img.shields.io/badge/Testler-çekirdek%20%2B%20arayüz-2E7D32)

Python + **Kivy** ile yazılmış, kurulumdan sonra **internet bağlantısı gerektirmeden** çalışan bir jeodezik koordinat dönüşüm uygulaması. Coğrafi ⇄ Kartezyen dönüşümü, farklı elipsoitler, Bursa-Wolf / Molodensky-Badekas datum dönüşümleri ve ITRF'ler arası zamana bağlı **IERS 14 parametreli** Helmert dönüşümü tek bir arayüzde toplanmıştır.

Proje, İTÜ Geomatik Mühendisliği yüksek lisans dersi (GEO532 — *Location Based Systems and Mobile Mapping Technologies*) kapsamında **öğretim ve deneysel kullanım** amacıyla geliştirilmiştir. Hesaplama çekirdeği yalnızca Python'un `math` modülünü kullanır (numpy yok), bu yüzden Android'e paketlemek de kolaydır.

<p align="center">
  <img src="docs/ekran_datum.png" width="49%" alt="Datum / Çerçeve sekmesi: WGS84 (G2139) → ITRF96 IERS 14 parametre dönüşümü">
  <img src="docs/ekran_parametre.png" width="49%" alt="Model Parametreleri sekmesi: ED50 → WGS84 için EPSG:1784 Bursa-Wolf parametreleri otomatik dolduruldu">
</p>

---

## İçindekiler

- [Özellikler](#özellikler)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Python modülü olarak kullanım](#python-modülü-olarak-kullanım)
- [Testler](#testler)
- [Proje yapısı](#proje-yapısı)
- [Android'e paketleme (APK)](#androide-paketleme-apk)
- [Jeodezik doğruluk uyarıları](#jeodezik-doğruluk-uyarıları)
- [Kaynaklar](#kaynaklar)

---

## Özellikler

| Özellik | Durum |
| --- | --- |
| Coğrafi (φ, λ, h) → Kartezyen (X, Y, Z) | Var (kapalı formül) |
| Kartezyen → Coğrafi | Var — **iteratif** (1e-12 rad) ve **Bowring** yöntemi, geri-dönüş kapanma hatası raporlanır |
| Elipsoitler | GRS80, WGS84, Hayford (International 1924), Krassovsky 1940, Bessel 1841 |
| Açı girişi | Ondalık derece veya derece-dakika-saniye (`39 55 30.0`, `39°55'30"`, `32 51 7.5 W`, Türkçe K/G/D/B) |
| Bursa-Wolf 7 parametre | Var — PV (Position Vector) ve CF (Coordinate Frame) konvansiyonu |
| Molodensky-Badekas (7 p. + Xm, Ym, Zm) | Var |
| IERS 14 parametre (zamana bağlı Helmert) | Var — P(t) = P(t0) + Ṗ·(t − t0), ölçü epoğu girilir |
| 7 parametre Helmert (hızsız, t0) | Var — hızları ihmal etmenin etkisini görmek için |
| Yalnız elipsoit değişimi | Var — aynı XYZ, farklı φ, λ, h |
| Sistemler arası zincirleme | Var — sistem grafı üzerinde BFS ile en kısa yol (örn. `WGS84 (G2139) → ITRF2014 → ITRF2020 → ITRF96`) |
| Otomatik parametre seçimi | Var — (kaynak, hedef, model) üçlüsüne göre kayıtlı set; kayıt yoksa alanlar **boş** kalır, uydurma/örnek değer kullanılmaz |
| Kesin ters dönüşüm | Var — kayıtlı set ters yöndeyse parametreler değiştirilmeden iteratif kesin ters çözüm |
| Manuel parametre girişi | Var (Bursa-Wolf / Molodensky-Badekas) |
| Kayma raporu | dX, dY, dZ + yerel Doğu-Kuzey-Yukarı (ENU) + 3B uzunluk + dφ, dλ, dh |
| Ortak noktalardan parametre kestirimi (EKK) | **Henüz yok** |
| UTM / TM projeksiyon | **Henüz yok** |
| Hazır Android APK | **Bu depoda yok** (buildozer ile derlenebilir, aşağıya bakın) |

### Tanımlı referans sistemleri

| Sistem | Elipsoit | Bağlantı (parametre kaynağı) |
| --- | --- | --- |
| ITRF2020 | GRS80 | Merkez düğüm |
| ITRF2014, ITRF2008, ITRF2005, ITRF2000, ITRF97, ITRF96 (TUREF) | GRS80 | IERS: ITRF2020 → geçmiş ITRF'ler (t0 = 2015.0) |
| ITRF2014 → ITRF2008 | GRS80 | IERS (t0 = 2010.0) |
| ETRF2000 (ETRS89) | GRS80 | EUREF TN-1: ITRF2014 → ETRF2000 (t0 = 2010.0) |
| WGS84 (G2296 / G2139 / G1762) | WGS84 | ITRF2020 / ITRF2014 / ITRF2008 ile özdeş kabul (NGA resmî dönüşüm yayınlamaz) |
| WGS84 (EPSG ensemble) | WGS84 | EPSG:1149 ETRS89 → WGS 84 (null, 1 m) |
| ED50 (Hayford) | Hayford | EPSG:1783 ED50 → ETRS89 (9) ve EPSG:1784 ED50 → WGS 84 (30), Türkiye, 2 m |

Yeni bir elipsoit, sistem ya da parametre seti eklemek için `jeodezi.py` içindeki `ELIPSOITLER`, `SISTEMLER`, `DONUSUMLER` ve `parametre_kaydet(...)` yeterlidir; arayüz listeleri kendiliğinden günceller.

---

## Kurulum

**Gerekenler:** Python **3.10 – 3.13** (geliştirme ve testler 3.13 ile yapıldı) ve yalnızca ilk kurulum için internet. Kivy 2.3 için bu sürümlerin hazır paketleri vardır.

### Windows — hızlı kurulum (önerilen)

1. Python'u [python.org](https://www.python.org/downloads/windows/) adresinden kurun. Kurulumda **Add python.exe to PATH** seçeneğini işaretleyin.
2. Bu sayfada yeşil **Code → Download ZIP** ile projeyi indirin ve **Tümünü ayıkla** ile bir klasöre çıkarın. (`.bat` dosyalarını ZIP'in içinden çalıştırmayın.)
3. `KURULUM.bat` dosyasına çift tıklayın. Proje klasöründe `.venv` adlı sanal ortam oluşturulur ve Kivy kurulur.
4. `BASLAT.bat` dosyasına çift tıklayın; uygulama penceresi açılır.
5. (İsteğe bağlı) `TEST.bat` ile hesap çekirdeğinin ve arayüzün testlerini çalıştırın.

### Windows — PowerShell ile

```powershell
git clone https://github.com/salihtatci/coordinate_transformation.git
cd coordinate_transformation

python -m venv .venv
$env:PYTHONUTF8 = "1"          # klasör yolunda Türkçe karakter varsa gerekli
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

.\.venv\Scripts\python.exe test_jeodezi.py     # önce matematiği doğrula
.\.venv\Scripts\python.exe main.py             # uygulamayı başlat
```

### Linux / macOS

```bash
git clone https://github.com/salihtatci/coordinate_transformation.git
cd coordinate_transformation

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python test_jeodezi.py
python main.py
```

> Linux'ta Kivy penceresi için sistemde OpenGL/SDL2 desteği gerekir; masaüstü dağıtımlarında genellikle hazırdır.

### Sık karşılaşılan sorunlar

- **`python` komutu bulunamadı:** Python'u PATH'e ekleyerek yeniden kurun ve **yeni** bir terminal açın.
- **Başka bilgisayardan kopyalanan `.venv` çalışmıyor:** `.venv` klasörü, oluşturulduğu bilgisayardaki Python yoluna bağlıdır. Klasörü silip `KURULUM.bat` ile yeniden kurun. Projeyi paylaşırken `.venv` klasörünü göndermeyin (`.gitignore` bunu zaten dışarıda bırakır).
- **Türkçe karakterli klasör yolunda kurulum hatası:** `PYTHONUTF8=1` ortam değişkenini ayarlayın (`.bat` dosyaları bunu otomatik yapar).
- **Uygulama hemen kapanıyor:** `BASLAT.bat` hata durumunda pencereyi açık tutar; hata metnini kaydedip inceleyin.

---

## Kullanım

Uygulama dört sekmeden oluşur.

### 1. Coğrafi ⇄ Kartezyen

- Elipsoidi ve ters çözüm yöntemini (`iteratif` / `bowring`) seçin.
- Enlem, boylam ve elipsoidal yüksekliği girip **Coğrafi → Kartezyen**'e basın. Çıktıda a, 1/f, e², N ve her adımın formülü gösterilir.
- X, Y, Z girip **Kartezyen → Coğrafi**'ye basın. Çıktıda iterasyon sayısı ve geri-dönüş kapanma hatası yer alır.

Örnek (GRS80): φ = 39° 55′ 30.0″, λ = 32° 50′ 12.84″, h = 938 m → X = 4116037.2588 m, Y = 2656358.3524 m, Z = 4072204.7958 m

### 2. Datum / Çerçeve

1. **Kaynak sistem**, **hedef sistem** ve **dönüşüm modeli**ni seçin.
2. IERS 14 parametre modelinde **ölçü epoğu t**'yi (ondalık yıl, örn. `2025.0`) girin.
3. Giriş türünü (`Kartezyen` / `Cografi`) seçip koordinatları yazın ve **Dönüştür**'e basın.
4. Çıktı; kullanılan parametreleri ve kaynağını, zincirdeki her adımı, hedef sistemdeki X, Y, Z ve φ, λ, h değerlerini, ayrıca kaymanın ENU bileşenlerini gösterir.
5. **Kaynak ⇄ Hedef** düğmesi yönü çevirir; kayıtlı set ters yöndeyse kesin ters çözüm otomatik uygulanır.

### 3. Model Parametreleri

- Seçilen (kaynak, hedef, model) için parametreler **otomatik doldurulur** ve salt okunurdur. Başlıkta parametrenin kaynağı (EPSG / IERS / EUREF), yönü, konvansiyonu ve epoğu yazar.
- Kayıtlı set yoksa alanlar boş kalır ve dönüşüm **yapılmaz**.
- Bursa-Wolf / Molodensky-Badekas için **Manuel parametre girişi** kutusunu işaretleyerek kendi parametrelerinizi girebilirsiniz. Birimler: T [m], D [ppm], R [yay saniyesi]. Konvansiyonu (PV/CF) ve gerekiyorsa **Ters yönde uygula** seçeneğini kendiniz belirleyin.
- **Test örneği: EPSG 7-2** düğmesi, EPSG Guidance Note 7-2'deki WGS72 → WGS84 Bursa-Wolf örneğini manuel giriş olarak yükler; beklenen sonuç (3657660.78, 255778.43, 5201387.75) m'dir.

### 4. Bilgi

Datum/çerçeve ile elipsoit farkı, IERS 14 parametre modeli, WGS84 gerçekleştirmeleri ve formüllerin kısa özeti.

Matematiğin ve Kivy tasarımının adım adım anlatımı için [`OGREN.md`](OGREN.md) dosyasına bakın.

---

## Python modülü olarak kullanım

`jeodezi.py` arayüzden tamamen bağımsızdır; Kivy kurmadan da kullanılabilir:

```python
import jeodezi as jz

# Coğrafi -> Kartezyen (GRS80)
X = jz.geo_to_cart(39.925, 32.8369, 938.0, "GRS80")
# (4116037.2588, 2656358.3524, 4072204.7958)

# Kartezyen -> Coğrafi (iteratif)
phi, lam, h, n_iter = jz.cart_to_geo(*X, "GRS80", yontem="iteratif")
# (39.925, 32.8369, 938.0, 4)

# WGS84 (G2139) -> ITRF96, IERS 14 parametre, t = 2025.0 (otomatik zincir)
Y, eslesme, rapor = jz.donustur(X, "WGS84 (G2139)", "ITRF96 (TUREF)", jz.MODEL_IERS, epok=2025.0)
# Y ≈ (4116037.2835, 2656358.3705, 4072204.7063)

# ED50 -> WGS 84, Bursa-Wolf (EPSG:1784 otomatik seçilir)
Z, eslesme, _ = jz.donustur(X, "ED50 (Hayford)", "WGS84 (EPSG ensemble)", jz.MODEL_BW)
print(eslesme.kod)   # EPSG:1784  ED50 to WGS 84 (30)

# Derece-dakika-saniye yardımcıları
jz.aci_oku("39 55 30.0")   # 39.925
jz.dms(39.925)             # 39° 55' 30.00000"
```

Model kodları: `MODEL_IERS`, `MODEL_SABIT` (hızsız 7 p.), `MODEL_BW`, `MODEL_MB`, `MODEL_ELIPS`. Kayıtlı parametre bulunamazsa `donustur` bir `ParametreBulunamadi` hatası fırlatır.

---

## Testler

```powershell
.\.venv\Scripts\python.exe test_jeodezi.py   # hesap çekirdeği (Kivy gerekmez)
.\.venv\Scripts\python.exe test_arayuz.py    # gerçek Kivy arayüzü, gizli pencerede
```

Windows'ta ikisini birden çalıştırmak için `TEST.bat` yeterlidir.

- **`test_jeodezi.py`** — tüm elipsoitlerde ve iki yöntemle gidiş-dönüş kapanması; EPSG 7-2 Bursa-Wolf (PV/CF) ve Molodensky-Badekas (La Canoa) örnekleri; M-B (merkez = 0) ile Bursa-Wolf eşdeğerliği; WGS84–GRS80 farkı; ITRF zinciri gidiş-dönüşü; otomatik parametre seçimi, kesin ters yön, PV/CF korunumu ve IERS epok hesabı.
- **`test_arayuz.py`** — Model Parametreleri sekmesinin kaynak/hedef/model/epok değiştikçe güncellenmesi, Kaynak ⇄ Hedef ters çözümü, manuel giriş ve EPSG test düğmesi.

> Testlerin geçmesi, tüm datum/epok dönüşümlerinin bağımsız dış referanslarla doğrulandığı anlamına gelmez.

---

## Proje yapısı

```text
coordinate_transformation/
├── main.py              # Kivy arayüzü (KV dili + olay işleyiciler); buildozer için adı main.py olmalı
├── jeodezi.py           # Hesaplama çekirdeği: elipsoitler, Helmert modelleri, sistem grafı, parametre DB
├── test_jeodezi.py      # Çekirdek testleri (EPSG örnekleri, kapanma, otomatik parametre)
├── test_arayuz.py       # Arayüz testleri (gizli Kivy penceresi)
├── requirements.txt     # kivy[base]>=2.3
├── KURULUM.bat          # Windows: .venv oluştur + bağımlılıkları kur
├── BASLAT.bat           # Windows: uygulamayı başlat
├── TEST.bat             # Windows: tüm testleri çalıştır
├── OGREN.md             # Öğrenme rehberi: formüller, model seçimi, Kivy mantığı, APK
├── docs/                # README ekran görüntüleri
└── .gitignore
```

İş mantığı (`jeodezi.py`) ile arayüz (`main.py`) bilinçli olarak ayrılmıştır: hesaplar arayüzsüz test edilebilir ve aynı çekirdek başka bir arayüzle (Tkinter, web, komut satırı) yeniden kullanılabilir.

---

## Android'e paketleme (APK)

Buildozer Linux gerektirir; Windows'ta **WSL (Ubuntu)** kullanılabilir.

```bash
pip install buildozer cython
buildozer init
# buildozer.spec içinde:
#   title = Koordinat Donusum
#   requirements = python3,kivy
#   source.include_exts = py,png,kv
buildozer -v android debug     # .apk dosyası bin/ klasöründe oluşur
```

Uygulama numpy vb. kullanmadığı için ek bağımlılık gerekmez ve telefonda internetsiz çalışır.

---

## Jeodezik doğruluk uyarıları

- **GRS80 ve WGS84 birer elipsoittir.** Elipsoit değiştirmek tek başına datum dönüşümü değildir; X, Y, Z'yi çerçeve/datum belirler, elipsoit yalnızca φ, λ, h ifadesini etkiler.
- **`ITRF96 (TUREF)` etiketi sadeleştirilmiştir.** TUREF'in referans epoğu **2005.0**'dır. Program ITRF2020 → ITRF96 çerçeve dönüşümünü seçilen ölçü epoğunda yapar, ancak noktayı hız modeliyle 2005.0 epoğuna **taşımaz**. ITRF96 (2025.0) sonucunu TUREF (2005.0) koordinatı saymayın.
- **WGS84 gerçekleştirmeleri** (G1762, G2139, G2296) karşılık gelen ITRF ile sıfır parametreli özdeşlik olarak modellenmiştir (cm düzeyinde uyum).
- **ED50 bağlantıları EPSG kayıtlarına dayanır ve doğrulukları ~1–2 m'dir.** ED50 içeren bir zincir (örneğin IERS modeli seçiliyken ED50 → ITRF2020) bu metre düzeyindeki belirsizliği taşır.
- **Bursa-Wolf / Molodensky-Badekas küçük açı yaklaşımıyla** hesaplanır; büyük dönüklükler için tam 3B dönüklük matrisi içermez.
- **Konvansiyon önemlidir:** Aynı sayılar PV ve CF konvansiyonunda zıt işaretli dönüklük anlamına gelir (IERS / EPSG:1033 = PV, EPSG:1032 = CF). Manuel girişte kaynak/hedef sırası, birimler ve konvansiyon kullanıcının sorumluluğundadır.
- Programdaki IERS/EUREF/EPSG parametreleri ders amaçlıdır. **Resmî veya hassas işlerde** değerleri güncel [ITRF](https://itrf.ign.fr/en/solutions/transformations), [EUREF](https://epncb.oma.be/) ve [EPSG](https://epsg.org/) tablolarıyla doğrulayın.

---

## Kaynaklar

- IERS / IGN — [ITRF dönüşüm parametreleri](https://itrf.ign.fr/en/solutions/transformations)
- Altamimi, Z. — *EUREF Technical Note 1: Relationship and Transformation between the International and the European Terrestrial Reference Systems*
- IOGP — [EPSG Geodetic Parameter Dataset](https://epsg.org/) ve *Guidance Note 7-2: Coordinate Conversions and Transformations including Formulas*
- Bowring, B. R. (1976). *Transformation from spatial to geographical coordinates.* Survey Review, 23(181)
- [PROJ dokümantasyonu](https://proj.org/) — Helmert dönüşümleri
- [Kivy dokümantasyonu](https://kivy.org/doc/stable/)

---

**Geliştirici:** Salih ([@salihtatci](https://github.com/salihtatci)) — İstanbul Teknik Üniversitesi, Geomatik Mühendisi, Elektrik Mühendisi
