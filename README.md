# GEO532 — Çevrimdışı Jeodezik Koordinat Dönüşümü

Python + **Kivy** ile geliştirilmiş, internet bağlantısı olmadan hesaplama yapabilen **Windows masaüstü** koordinat dönüştürücüsü. Bu depo, öğretim ve deneysel kullanım içindir; resmî jeodezik üretimde kullanılmadan önce dönüşüm parametreleri ve sonuçları yetkili kaynaklarla doğrulanmalıdır.

![Uygulamadan ekran görüntüsü](docs/ornek_ekran.png)

## Yeni başlayanlar: Windows'ta kurulum (5 adım)

**Gerekenler:** Windows 10/11; tercihen **Python 3.11 veya 3.12**, internet (yalnızca ilk kurulumda). Python 3.13 de uygun Kivy paketi bulunduğunda çalışabilir. Python kurulurken `Add python.exe to PATH` seçeneği işaretlenebilir.

1. GitHub sayfasından yeşil **Code → Download ZIP** seçeneğine tıklayın. İnen ZIP'i **Tümünü ayıkla** ile çıkarın. `.bat` dosyaları ZIP içinden çalıştırılmamalıdır.
2. Çıkardığınız klasörde `KURULUM.bat` dosyasına **çift tıklayın**. Bu işlem bilgisayarınızda `.venv` adlı sanal Python ortamı kurar ve Kivy'yi yükler. İlk kurulum için internet gerekir.
3. Kurulum bittiğinde `BASLAT.bat` dosyasına **çift tıklayın**. Program penceresi açılır.
4. İlk sekmeden bir **elipsoit** seçin, enlem/boylam/yükseklik girerek **Coğrafi → Kartezyen** düğmesine basın; ters dönüşüm için X/Y/Z ve **Kartezyen → Coğrafi** düğmesini kullanın.
5. `Datum / Çerçeve` sekmesinde kaynak/hedef sistemini ve modeli seçin. **Bursa-Wolf veya Molodensky-Badekas** için `Model Parametreleri` sekmesine ilgili sistem çiftine uygun, kaynağı belli değerleri girmeniz zorunludur.

> **Arkadaşınıza gönderirken `.venv` klasörünü asla göndermeyin.** Başka bilgisayardaki Python yoluna (`C:\Users\...\pythonw.exe`) bağlı olabilir. Bu depo `.gitignore` ile `.venv` klasörünü dışarıda bırakır. Kullanıcı kendi bilgisayarında `KURULUM.bat` ile yeniden oluşturur.

### PowerShell ile alternatif kurulum

Proje klasöründe terminal açın:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe test_jeodezi.py
.\.venv\Scripts\python.exe main.py
```

`python` komutu bulunamazsa Python'ı kurup yeni bir terminal açın. Eski `.venv` taşınmışsa yalnızca `.venv` klasörünü silin ve kurulumu yeniden yapın. Sanal ortamın kurulumunu başka bilgisayardan kopyalayarak düzeltmeye çalışmayın.

## Şu anda neler yapar?

| Özellik | Durum |
| --- | --- |
| Coğrafi (φ, λ, h) → Kartezyen (X, Y, Z) | Var |
| Kartezyen → Coğrafi (iteratif / Bowring) | Var |
| GRS80, WGS84, Hayford, Krassovsky, Bessel elipsoitleri | Var |
| 7 parametreli **küçük açılı** Bursa-Wolf (PV/CF) | Var; kullanıcı parametreli |
| Molodensky-Badekas | Var; kullanıcı parametreli |
| IERS 14 parametreli çerçeve dönüşümü | Kısmi; tanımlı yollarla ve açıklanan yaklaşımlarla |
| İleri / ters hesap | Var; yöntemine bağlı yaklaşık çözümler olabilir |
| Ortak noktalardan otomatik parametre kestirimi | **Henüz yok** |
| Veis, UTM/TM ve HGM karşılaştırma | **Henüz yok** |
| Android APK | **Bu depoda yok**; ayrı derleme gerekir |

## Jeodezik doğruluk uyarıları

- **GRS80 ve WGS84 birer referans elipsoididir**; bunları değiştirmek kendiliğinden datum dönüşümü yapmaz. ED50, WGS84 gerçekleşimleri ve ITRF ise datum/referans çerçevesi bağlamında değerlendirilir.
- Uygulamadaki **`ITRF96 (TUREF)` etiketi sadeleştirilmiş/yanıltıcı olabilir**: TUREF'in referans epoğu **2005.0**'dır. Kod bir ITRF çerçeve dönüşümü yapsa da, noktanın 2025.0 koordinatlarını 2005.0 epoğuna hız modeliyle otomatik taşımaz. **ITRF96 (2025.0) sonucunu TUREF (2005.0) saymayın.**
- Bazı WGS84 gerçekleşimlerinden belirli ITRF'lere geçiş kodda **sıfır parametreli yaklaşık özdeşlik** olarak modellenmiştir; yüksek hassasiyet garantisi vermez.
- Bursa-Wolf ve Molodensky-Badekas dönüklükleri **küçük açı yaklaşımı** ile hesaplanır. Büyük açılara uygun tam 3B dönüklük modeli içermez.
- Kullanıcı parametrelerinde **doğru kaynak/hedef sırası, birimler (m, ppm, yay saniyesi), PV/CF konvansiyonu ve ters yön** önemlidir. Kaynak/hedef düğmesine basmak tek başına kullanıcı parametrelerini ters çevirmez.
- En küçük karelerden parametre kestirimi ve bağımsız saha verisiyle doğruluk analizi henüz bulunmadığından, bu sürüm **öğretici prototip** olarak değerlendirilmelidir.

## Proje dosyaları

```text
GEO532/
├── main.py              # Kivy arayüzü
├── jeodezi.py           # Matematiksel hesaplama çekirdeği
├── test_jeodezi.py      # Temel otomatik testler
├── requirements.txt     # Kivy bağımlılığı
├── BASLAT.bat           # Windows: uygulamayı başlat
├── KURULUM.bat          # Windows: ilk kurulum
├── TEST.bat             # Windows: testler
├── OGREN.md             # Matematiği ve Kivy tasarımını öğren
├── docs/ornek_ekran.png # Örnek ekran görüntüsü
└── .gitignore           # Yerel/derlenmiş dosyaları Git'ten hariç tut
```

## Testler

```powershell
.\.venv\Scripts\python.exe test_jeodezi.py
```

Mevcut testler ileri–ters kapanmayı, EPSG 7 parametre örneğini, bazı matematiksel eşdeğerlikleri ve çerçeve zinciri kapanmasını kontrol eder. **Testlerin geçmesi bütün datum/epok dönüşümlerinin dış referanslara göre doğrulandığı anlamına gelmez.**

## Kaynaklar ve öğrenme

- [ITRF resmî dönüşüm tabloları](https://itrf.ign.fr/en/solutions/transformations)
- [EPSG Geodetic Parameter Dataset](https://epsg.org/)
- [PROJ dönüşüm dokümantasyonu](https://proj.org/)
- [Kivy dokümantasyonu](https://kivy.org/doc/stable/)
- Matematik ve arayüz açıklamaları için [`OGREN.md`](OGREN.md) dosyasına bakın.

