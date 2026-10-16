"""
main.py  -  Kivy arayuzu (internetsiz calisir)
================================================

Kivy'de bir uygulamanin 3 parcasi vardir:
  1) App sinifi      : uygulamanin kendisi; build() ana widget'i dondurur.
  2) KV dili          : arayuzun "nasil gorunecegini" anlatan bildirimsel dil
                        (HTML/CSS'e benzer).  Asagida KV = \"\"\"...\"\"\" icinde.
  3) Python mantigi   : dugmeye basilinca ne olacagi (AnaPanel'in metotlari).

KV icinde `id: t1_phi` diye isim verdigimiz widget'a Python'da
`self.ids.t1_phi` ile ulasiriz.  `on_release: root.t1_geo2cart()` ise
dugme birakildiginda AnaPanel.t1_geo2cart() metodunu cagirir.

Not: Android paketleyicisi (buildozer) giris dosyasinin adinin main.py olmasini ister.
"""
import os
import math
import traceback

os.environ.setdefault("KIVY_NO_ARGS", "1")   # Kivy'nin komut satiri argumanlarini yutmasini engelle

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.core.window import Window
from kivy.clock import Clock

import jeodezi as jz

# Model adlari (Spinner'da gorunecek)
M_IERS = "IERS 14-parametre (zamana bagli)"
M_SABIT = "7-parametre Helmert (hizsiz, t0)"
M_BW = "Bursa-Wolf (otomatik / manuel)"
M_MB = "Molodensky-Badekas (otomatik / manuel)"
M_ELIPS = "Yalniz elipsoit degisimi"
MODELLER = [M_IERS, M_SABIT, M_BW, M_MB, M_ELIPS]
MODEL_ANAHTARLARI = {
    M_IERS: "IERS14",
    M_SABIT: "HELMERT7",
    M_BW: "BURSA_WOLF",
    M_MB: "MOLODENSKY_BADEKAS",
}

KV = r"""
#:import jz jeodezi
#:import main __main__

# ---------- Tekrar kullanilan "sablon" widget'lar ----------
<Etiket@Label>:
    size_hint_y: None
    height: dp(40)
    halign: 'left'
    valign: 'middle'
    text_size: self.size
    font_size: '15sp'

<Giris@TextInput>:
    size_hint_y: None
    height: dp(40)
    multiline: False
    write_tab: False
    font_size: '15sp'
    padding: dp(8), dp(10)

<Secim@Spinner>:
    size_hint_y: None
    height: dp(40)
    font_size: '14sp'

<Dugme@Button>:
    size_hint_y: None
    height: dp(48)
    font_size: '15sp'
    background_normal: ''
    background_color: 0.13, 0.42, 0.75, 1

<Sonuc@TextInput>:
    readonly: True
    font_name: 'RobotoMono-Regular'
    font_size: '12.5sp'
    size_hint_y: None
    height: max(dp(300), self.minimum_height)
    background_normal: ''
    background_active: ''
    background_color: 0.07, 0.08, 0.10, 1
    foreground_color: 0.80, 1.00, 0.80, 1

<Form@GridLayout>:
    cols: 2
    spacing: dp(6)
    size_hint_y: None
    height: self.minimum_height
    cols_minimum: {0: dp(150)}

<Sayfa@BoxLayout>:
    orientation: 'vertical'
    padding: dp(10)
    spacing: dp(8)
    size_hint_y: None
    height: self.minimum_height

# ---------- Ana panel: sekmeler ----------
<AnaPanel>:
    do_default_tab: False
    tab_width: dp(185)
    tab_height: dp(44)

    # ================= SEKME 1 =================
    TabbedPanelItem:
        text: 'Cografi <-> Kartezyen'
        ScrollView:
            Sayfa:
                Form:
                    Etiket:
                        text: 'Elipsoit'
                    Secim:
                        id: t1_elips
                        text: 'GRS80'
                        values: list(jz.ELIPSOITLER)
                    Etiket:
                        text: 'Ters cozum yontemi'
                    Secim:
                        id: t1_yontem
                        text: 'iteratif'
                        values: ['iteratif', 'bowring']
                    Etiket:
                        text: 'Enlem  φ'
                    Giris:
                        id: t1_phi
                        hint_text: '39.925  veya  39 55 30.0'
                        text: '39 55 30.0'
                    Etiket:
                        text: 'Boylam  λ'
                    Giris:
                        id: t1_lam
                        hint_text: '32.8369  veya  32 50 12.84'
                        text: '32 50 12.84'
                    Etiket:
                        text: 'Elipsoidal yukseklik h (m)'
                    Giris:
                        id: t1_h
                        text: '938.000'
                Dugme:
                    text: 'Cografi  ->  Kartezyen'
                    on_release: root.t1_geo2cart()
                Form:
                    Etiket:
                        text: 'X (m)'
                    Giris:
                        id: t1_x
                    Etiket:
                        text: 'Y (m)'
                    Giris:
                        id: t1_y
                    Etiket:
                        text: 'Z (m)'
                    Giris:
                        id: t1_z
                Dugme:
                    text: 'Kartezyen  ->  Cografi'
                    on_release: root.t1_cart2geo()
                Sonuc:
                    id: t1_out

    # ================= SEKME 2 =================
    TabbedPanelItem:
        text: 'Datum / Cerceve'
        ScrollView:
            Sayfa:
                Form:
                    Etiket:
                        text: 'Kaynak sistem'
                    Secim:
                        id: t2_kaynak
                        text: 'WGS84 (G2139)'
                        values: list(jz.SISTEMLER)
                        on_text: root.parametreleri_guncelle()
                    Etiket:
                        text: 'Hedef sistem'
                    Secim:
                        id: t2_hedef
                        text: 'ITRF96 (TUREF)'
                        values: list(jz.SISTEMLER)
                        on_text: root.parametreleri_guncelle()
                    Etiket:
                        text: 'Donusum modeli'
                    Secim:
                        id: t2_model
                        text: main.M_IERS
                        values: main.MODELLER
                        on_text: root.parametreleri_guncelle()
                    Etiket:
                        text: 'Olcu epogu t (yil)'
                    Giris:
                        id: t2_epok
                        text: '2025.0'
                        disabled: t2_model.text != main.M_IERS
                        on_text: root.parametreleri_guncelle()
                    Etiket:
                        text: 'Giris koordinat turu'
                    Secim:
                        id: t2_tip
                        text: 'Kartezyen'
                        values: ['Kartezyen', 'Cografi']
                    Etiket:
                        text: 'Enlem  φ' if t2_tip.text == 'Cografi' else 'X (m)'
                    Giris:
                        id: t2_a
                        text: '4116037.2588'
                    Etiket:
                        text: 'Boylam  λ' if t2_tip.text == 'Cografi' else 'Y (m)'
                    Giris:
                        id: t2_b
                        text: '2656358.3524'
                    Etiket:
                        text: 'h (m)' if t2_tip.text == 'Cografi' else 'Z (m)'
                    Giris:
                        id: t2_c
                        text: '4072204.7958'
                BoxLayout:
                    size_hint_y: None
                    height: dp(48)
                    spacing: dp(6)
                    Dugme:
                        text: 'Donustur'
                        on_release: root.t2_donustur()
                    Dugme:
                        text: 'Kaynak <-> Hedef'
                        background_color: 0.35, 0.35, 0.40, 1
                        on_release: root.t2_yer_degistir()
                Sonuc:
                    id: t2_out

    # ================= SEKME 3 =================
    TabbedPanelItem:
        text: 'Model Parametreleri'
        ScrollView:
            Sayfa:
                Etiket:
                    text: 'Secilen donusume ait model parametreleri otomatik getirilir.'
                Etiket:
                    id: p_status
                    height: dp(86)
                    color: 0.75, 0.90, 0.75, 1
                    font_size: '13sp'
                    text: 'Parametre durumu burada gorunecek.'
                Form:
                    Etiket:
                        text: 'Manuel parametre girisi'
                    CheckBox:
                        id: p_manual
                        size_hint_y: None
                        height: dp(40)
                        active: False
                    Etiket:
                        text: 'Tx (m)'
                    Giris:
                        id: p_tx
                        text: '0'
                        readonly: not p_manual.active
                    Etiket:
                        text: 'Ty (m)'
                    Giris:
                        id: p_ty
                        text: '0'
                        readonly: not p_manual.active
                    Etiket:
                        text: 'Tz (m)'
                    Giris:
                        id: p_tz
                        text: '0'
                        readonly: not p_manual.active
                    Etiket:
                        text: 'Olcek D (ppm)'
                    Giris:
                        id: p_d
                        text: '0'
                        readonly: not p_manual.active
                    Etiket:
                        text: 'Rx (yay sn)'
                    Giris:
                        id: p_rx
                        text: '0'
                        readonly: not p_manual.active
                    Etiket:
                        text: 'Ry (yay sn)'
                    Giris:
                        id: p_ry
                        text: '0'
                        readonly: not p_manual.active
                    Etiket:
                        text: 'Rz (yay sn)'
                    Giris:
                        id: p_rz
                        text: '0'
                        readonly: not p_manual.active
                    Etiket:
                        text: 'Donukluk konvansiyonu'
                    Secim:
                        id: p_konv
                        text: 'PV (Position Vector)'
                        values: ['PV (Position Vector)', 'CF (Coordinate Frame)']
                        disabled: not p_manual.active
                    Etiket:
                        text: 'Xm (m)  [yalniz M-B]'
                    Giris:
                        id: p_xm
                        text: '0'
                        readonly: not p_manual.active
                    Etiket:
                        text: 'Ym (m)  [yalniz M-B]'
                    Giris:
                        id: p_ym
                        text: '0'
                        readonly: not p_manual.active
                    Etiket:
                        text: 'Zm (m)  [yalniz M-B]'
                    Giris:
                        id: p_zm
                        text: '0'
                        readonly: not p_manual.active
                    Etiket:
                        text: 'Ters yonde uygula'
                    CheckBox:
                        id: p_ters
                        size_hint_y: None
                        height: dp(40)
                        disabled: not p_manual.active
                Dugme:
                    text: 'EPSG 7-2 test ornegini doldur'
                    background_color: 0.35, 0.35, 0.40, 1
                    on_release: root.ornek_epsg()
                Etiket:
                    height: dp(120)
                    color: 0.8, 0.8, 0.8, 1
                    font_size: '13sp'
                    text: main.PARAM_NOTU

    # ================= SEKME 4 =================
    TabbedPanelItem:
        text: 'Bilgi'
        ScrollView:
            Label:
                size_hint_y: None
                height: self.texture_size[1] + dp(30)
                text_size: self.width - dp(30), None
                padding: dp(15), dp(15)
                font_size: '14sp'
                markup: True
                text: main.BILGI
"""

PARAM_NOTU = ("Parametreler kaynak + hedef + model secimine gore otomatik doldurulur. "
              "Kayit yoksa program sifir/uydurma parametre kullanmaz; Manuel parametre girisi acilabilir. "
              "PV ve CF ayni sayilarla farkli sonuc verir. Ters yon, kayitli parametrenin yonune gore otomatik belirlenir.")

BILGI = """[b][size=18sp]Ne neyi belirler?[/size][/b]

[b]Cerceve / datum[/b] (ITRF2020, WGS84(G2139), ETRF2000 ...) noktanin [b]X, Y, Z[/b] degerini belirler.
[b]Elipsoit[/b] (GRS80, WGS84 ...) ise ayni X, Y, Z'nin [b]φ, λ, h[/b] olarak nasil ifade edilecegini belirler.

[b]WGS84 <-> GRS80[/b]: Bu iki elipsoitin a'si aynidir, yalniz 1/f farklidir (b'de ~0.105 mm).
Ayni cercevede XYZ hic degismez; φ ayni kalir (~1e-9 derece), h en fazla ~0.1 mm degisir.
Bunu 'Yalniz elipsoit degisimi' modeli ile kendiniz gorebilirsiniz.

[b]ITRF'ler arasi[/b]: IERS 14 parametre yayinlar (7 parametre + bunlarin yillik hizlari).
  P(t) = P(t0) + Pdot (t - t0)
  X2 = X1 + T + D X1 + R X1
Hizlari ihmal etmek (7-parametre, t0'da sabit) yillar ilerledikce cm duzeyinde hata yapar;
iki modeli karsilastirarak farki gorun.

[b]WGS84 gerceklestirmeleri[/b]: G1762 ~ ITRF2008, G2139 ~ ITRF2014, G2296 ~ ITRF2020
(cm duzeyinde ortusur, bu yuzden aralarinda sifir parametre kabul edilir).

[b]Bursa-Wolf[/b]: X2 = T + (1 + D) R X1   (donukluk dunya merkezi etrafinda)
[b]Molodensky-Badekas[/b]: X2 = Xm + T + (1 + D) R (X1 - Xm)   (agirlik merkezi etrafinda)

[b]Cografi -> Kartezyen[/b] (kesin):
  N = a / sqrt(1 - e² sin² φ)
  X = (N + h) cos φ cos λ,  Y = (N + h) cos φ sin λ,  Z = (N(1 - e²) + h) sin φ
[b]Kartezyen -> Cografi[/b]: iteratif ya da Bowring yontemi.

[color=ffaa55]Uyari: Program icindeki IERS/EUREF parametreleri ders amaclidir.
Resmi islerde guncel tablolarla (itrf.ign.fr, epncb.eu) karsilastirin.[/color]
"""


def sayi(metin):
    """'1.234' veya '1,234' -> float"""
    return float(metin.strip().replace(",", "."))


def hata_metni(e):
    return f"HATA: {e}\n\n(Ayrinti)\n{traceback.format_exc(limit=2)}"


class AnaPanel(TabbedPanel):
    # ---------------- Sekme 1 ----------------
    def t1_geo2cart(self):
        i = self.ids
        try:
            phi, lam, h = jz.aci_oku(i.t1_phi.text), jz.aci_oku(i.t1_lam.text), sayi(i.t1_h.text)
            el = i.t1_elips.text
            X, Y, Z = jz.geo_to_cart(phi, lam, h, el)
            a, b, f, e2, _ = jz.elipsoit_sabitleri(el)
            N = a / math.sqrt(1 - e2 * math.sin(math.radians(phi)) ** 2)
            i.t1_x.text, i.t1_y.text, i.t1_z.text = f"{X:.4f}", f"{Y:.4f}", f"{Z:.4f}"
            i.t1_out.text = (
                f"COGRAFI -> KARTEZYEN   [{el}]\n"
                f"a = {a:.3f} m   1/f = {1/f:.9f}   e² = {e2:.15f}\n"
                f"-----------------------------------------------\n"
                f"φ = {phi:.10f}°  ({jz.dms(phi)})\n"
                f"λ = {lam:.10f}°  ({jz.dms(lam)})\n"
                f"h = {h:.4f} m\n"
                f"N = a/sqrt(1-e²sin²φ) = {N:.4f} m\n"
                f"-----------------------------------------------\n"
                f"X = (N+h)cosφ cosλ   = {X:15.4f} m\n"
                f"Y = (N+h)cosφ sinλ   = {Y:15.4f} m\n"
                f"Z = (N(1-e²)+h)sinφ  = {Z:15.4f} m\n")
        except Exception as e:
            i.t1_out.text = hata_metni(e)

    def t1_cart2geo(self):
        i = self.ids
        try:
            X, Y, Z = sayi(i.t1_x.text), sayi(i.t1_y.text), sayi(i.t1_z.text)
            el, yon = i.t1_elips.text, i.t1_yontem.text
            phi, lam, h, n = jz.cart_to_geo(X, Y, Z, el, yon)
            # kontrol: geri hesapla, kapanma hatasi
            Xg = jz.geo_to_cart(phi, lam, h, el)
            kap = math.sqrt(sum((Xg[k] - v) ** 2 for k, v in enumerate((X, Y, Z))))
            i.t1_phi.text, i.t1_lam.text, i.t1_h.text = f"{phi:.10f}", f"{lam:.10f}", f"{h:.4f}"
            i.t1_out.text = (
                f"KARTEZYEN -> COGRAFI   [{el}, {yon}, {n} iterasyon]\n"
                f"-----------------------------------------------\n"
                f"X = {X:.4f}   Y = {Y:.4f}   Z = {Z:.4f}\n"
                f"p = sqrt(X²+Y²) = {math.hypot(X, Y):.4f} m\n"
                f"-----------------------------------------------\n"
                f"φ = {phi:.10f}°  ({jz.dms(phi)})\n"
                f"λ = {lam:.10f}°  ({jz.dms(lam)})\n"
                f"h = {h:.4f} m\n"
                f"Geri donus kapanma hatasi = {kap:.2e} m\n")
        except Exception as e:
            i.t1_out.text = hata_metni(e)

    # ---------------- Sekme 2 ----------------
    # ---------------- Sekme 2 ----------------
    def parametreleri_guncelle(self, *args):
        """Kaynak/hedef/model/epok değiştiğinde parametre ekranını otomatik yeniler."""
        i = self.ids
        try:
            kay, hed, model = i.t2_kaynak.text, i.t2_hedef.text, i.t2_model.text
            if not kay or not hed or not model:
                return

            # Model Parametreleri sekmesindeki manuel giriş açıksa kullanıcı
            # değerlerini ezme.
            if i.p_manual.active:
                i.p_status.text = (
                    "MANUEL PARAMETRE GIRISI AKTIF.\n"
                    f"Secim: {kay} -> {hed} | {model}\n"
                    "Otomatik doldurma manuel alanlari ezmiyor."
                )
                return

            epok = sayi(i.t2_epok.text) if i.t2_epok.text.strip() else 0.0
            anahtar = MODEL_ANAHTARLARI.get(model)

            if anahtar is None or model == M_ELIPS:
                self._parametre_alanlarini_temizle()
                i.p_status.text = (
                    f"Model: {model}\n"
                    "Bu modelde 7-parametre otomatik girişi gerekmiyor."
                )
                return

            bilgi = jz.otomatik_parametreler(kay, hed, anahtar, epok)
            self._parametre_bilgisini_uygula(bilgi, kay, hed, model)
        except Exception as e:
            # Kullanıcı epok alanını yazarken geçici olarak eksik sayı bırakabilir.
            i.p_status.text = f"PARAMETRE DURUMU:\n{e}"

    def _parametre_alanlarini_temizle(self):
        i = self.ids
        for w in (i.p_tx, i.p_ty, i.p_tz, i.p_d, i.p_rx, i.p_ry, i.p_rz,
                  i.p_xm, i.p_ym, i.p_zm):
            w.text = "0"
        i.p_konv.text = "PV (Position Vector)"
        i.p_ters.active = False

    def _parametre_bilgisini_uygula(self, bilgi, kay, hed, model):
        i = self.ids
        durum = bilgi.get("durum")

        if durum == "single":
            p = bilgi["params"]
            for w, v in zip((i.p_tx, i.p_ty, i.p_tz, i.p_d, i.p_rx, i.p_ry, i.p_rz), p):
                w.text = f"{v:.12g}"

            c = bilgi.get("center", (0.0, 0.0, 0.0))
            for w, v in zip((i.p_xm, i.p_ym, i.p_zm), c):
                w.text = f"{v:.12g}"

            i.p_konv.text = "CF (Coordinate Frame)" if bilgi.get("konvansiyon") == "CF" else "PV (Position Vector)"
            i.p_ters.active = bool(bilgi.get("ters", False))

            lines = [
                "✓ PARAMETRELER OTOMATIK DOLDURULDU",
                f"Kaynak -> Hedef: {kay} -> {hed}",
                f"Model: {model}",
                f"Kaynak: {bilgi.get('kaynak', 'belirtilmemis')}",
                f"Kayit: {bilgi.get('kod', 'belirtilmemis')}",
            ]
            if bilgi.get("epok") is not None:
                lines.append(f"Uygulama epoğu: {bilgi['epok']:.4f}")
            if bilgi.get("dogruluk"):
                lines.append(f"Belirtilen doğruluk: {bilgi['dogruluk']}")
            if bilgi.get("not"):
                lines.append(bilgi["not"])
            if bilgi.get("ters"):
                lines.append("Ters yön: kayıt ters yönde bulundu; dönüşüm ters çözümle uygulanacak.")
            i.p_status.text = "\n".join(lines)
            return

        if durum == "chain":
            self._parametre_alanlarini_temizle()
            adimlar = bilgi.get("adimlar", [])
            lines = [
                "✓ OTOMATIK DONUSUM ZINCIRI BULUNDU",
                f"Kaynak -> Hedef: {kay} -> {hed}",
                f"Model: {model}",
                f"{len(adimlar)} Helmert adımı var; tek bir 7-parametreye indirgenmedi."
            ]
            for s in adimlar:
                lines.append(
                    f"{s['adim']} | "
                    f"T={s['T'][0]:.4f},{s['T'][1]:.4f},{s['T'][2]:.4f} m | "
                    f"D={s['D']:.6f} ppm | "
                    f"R={s['R'][0]:.6f},{s['R'][1]:.6f},{s['R'][2]:.6f}\""
                )
            lines.append("Dönüştür butonu bu zinciri doğrudan kullanacaktır.")
            i.p_status.text = "\n".join(lines)
            return

        self._parametre_alanlarini_temizle()
        i.p_status.text = (
            "⚠ OTOMATIK PARAMETRE BULUNAMADI\n"
            f"{bilgi.get('mesaj', 'Bu kaynak-hedef-model kombinasyonu için kayıt yok.')}\n"
            "Yanlış/default değer kullanılmayacak. İsterseniz Manuel parametre girişini açın."
        )

    def t2_yer_degistir(self):
        i = self.ids
        i.t2_kaynak.text, i.t2_hedef.text = i.t2_hedef.text, i.t2_kaynak.text
        i.t2_out.text = ""
        self.parametreleri_guncelle()

    def _kullanici_param(self):
        i = self.ids
        p = [sayi(w.text) for w in (i.p_tx, i.p_ty, i.p_tz, i.p_d, i.p_rx, i.p_ry, i.p_rz)]
        merkez = (sayi(i.p_xm.text), sayi(i.p_ym.text), sayi(i.p_zm.text))
        konv = "CF" if i.p_konv.text.startswith("CF") else "PV"
        return p, merkez, konv, i.p_ters.active

    def t2_donustur(self):
        i = self.ids
        try:
            kay, hed, model = i.t2_kaynak.text, i.t2_hedef.text, i.t2_model.text
            el_k, el_h = jz.SISTEMLER[kay], jz.SISTEMLER[hed]
            a, b, c = i.t2_a.text, i.t2_b.text, i.t2_c.text
            o = [f"MODEL : {model}", f"YON   : {kay} [{el_k}]  ->  {hed} [{el_h}]",
                 "=" * 56]

            # 1) Girisi Kartezyen'e getir (kaynak sistemin elipsoidi ile)
            if i.t2_tip.text == "Cografi":
                phi, lam, h = jz.aci_oku(a), jz.aci_oku(b), sayi(c)
                X1 = jz.geo_to_cart(phi, lam, h, el_k)
                o.append(f"1) Giris cografi -> kartezyen ({el_k})")
            else:
                X1 = (sayi(a), sayi(b), sayi(c))
                phi, lam, h, _ = jz.cart_to_geo(*X1, el_k)
                o.append("1) Giris zaten kartezyen")
            o.append(f"   X1 = {X1[0]:15.4f} {X1[1]:15.4f} {X1[2]:15.4f}")

            # 2) Modeli uygula
            o.append("2) Donusum")
            # Kaynak/hedef/model değiştiyse parametre ekranını da senkronize et.
            self.parametreleri_guncelle()
            if model in (M_IERS, M_SABIT):
                hiz = model == M_IERS
                epok = sayi(i.t2_epok.text)
                X2, rapor = jz.sistemler_arasi(X1, kay, hed, epok, hiz)
                if not rapor:
                    o.append("   Kaynak = hedef, donusum yok.")
                for r in rapor:
                    T, D, R = r["T_mm"], r["D_ppb"], r["R_mas"]
                    o += [f"   * {r['adim']}   (t = {r['epok']:.2f})",
                          f"     T[mm] = {T[0]:8.3f} {T[1]:8.3f} {T[2]:8.3f}   D[ppb] = {D:7.3f}",
                          f"     R[mas]= {R[0]:8.4f} {R[1]:8.4f} {R[2]:8.4f}",
                          "     dX[mm]= " + " ".join(f"{v*1000:8.2f}" for v in r["fark_m"])]
            elif model in (M_BW, M_MB):
                p, merkez, konv, ters = self._kullanici_param()
                if not i.p_manual.active:
                    bilgi = jz.otomatik_parametreler(kay, hed, MODEL_ANAHTARLARI[model], sayi(i.t2_epok.text))
                    if bilgi.get("durum") != "single":
                        raise ValueError(
                            "Bu kaynak-hedef-model için otomatik 7-parametre bulunamadı. "
                            "Model Parametreleri sekmesinden 'Manuel parametre girişi'ni açın."
                        )
                    p = list(bilgi["params"])
                    merkez = tuple(bilgi.get("center", (0.0, 0.0, 0.0)))
                    konv = bilgi.get("konvansiyon", "PV")
                    ters = bool(bilgi.get("ters", False))
                if model == M_BW:
                    f, args = jz.bursa_wolf, p
                else:
                    f, args = jz.molodensky_badekas, p + [merkez]
                X2 = (jz.ters_cevir_7(X1, f, *args, konvansiyon=konv) if ters
                      else f(X1, *args, konvansiyon=konv))
                o += [f"   T[m] = {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}   D = {p[3]:.4f} ppm",
                      f"   R[\"] = {p[4]:.5f} {p[5]:.5f} {p[6]:.5f}   konvansiyon = {konv}"
                      + ("   (TERS)" if ters else "")]
                if model == M_MB:
                    o.append(f"   Xm  = {merkez[0]:.3f} {merkez[1]:.3f} {merkez[2]:.3f}")
            else:  # yalniz elipsoit
                X2 = X1
                o.append("   Cerceve ayni kabul edildi: X, Y, Z degismez.")

            # 3) Hedef elipsoit ile cografiye cevir
            phi2, lam2, h2, _ = jz.cart_to_geo(*X2, el_h)
            d = [X2[k] - X1[k] for k in range(3)]
            e_, n_, u_ = jz.enu_farki(d, phi, lam)
            o += ["=" * 56, f"SONUC ({hed})",
                  f"   X2 = {X2[0]:15.4f}",
                  f"   Y2 = {X2[1]:15.4f}",
                  f"   Z2 = {X2[2]:15.4f}",
                  f"   φ2 = {phi2:.10f}°  ({jz.dms(phi2)})",
                  f"   λ2 = {lam2:.10f}°  ({jz.dms(lam2)})",
                  f"   h2 = {h2:.4f} m  [{el_h}]",
                  "-" * 56,
                  "KAYMA (hedef - kaynak)",
                  f"   dX,dY,dZ [m] = {d[0]:.4f} {d[1]:.4f} {d[2]:.4f}",
                  f"   Dogu, Kuzey, Yukari [m] = {e_:.4f} {n_:.4f} {u_:.4f}",
                  f"   3B uzunluk = {math.sqrt(sum(v*v for v in d)):.4f} m",
                  f"   dφ = {(phi2-phi)*3600:.6f}\"  dλ = {(lam2-lam)*3600:.6f}\"  "
                  f"dh = {(h2-h)*1000:.3f} mm"]
            i.t2_out.text = "\n".join(o)
        except Exception as e:
            i.t2_out.text = hata_metni(e)

    # ---------------- Sekme 3 ----------------
    def ornek_epsg(self):
        """EPSG Guidance Note 7-2 Position Vector testini otomatik parametreyle yukler."""
        i = self.ids
        i.p_manual.active = False
        i.t2_model.text, i.t2_tip.text = M_BW, "Kartezyen"
        i.t2_a.text, i.t2_b.text, i.t2_c.text = "3657660.66", "255768.55", "5201382.11"
        i.t2_kaynak.text, i.t2_hedef.text = "WGS72", "WGS84 (ensemble)"
        self.parametreleri_guncelle()
        self.switch_to(self.tab_list[-2])          # 'Datum / Cerceve' sekmesine gec
        self.t2_donustur()


class KoordinatApp(App):
    title = "Koordinat Donusum - Cevrimdisi"

    def build(self):
        Window.clearcolor = (0.12, 0.12, 0.14, 1)
        Window.softinput_mode = "below_target"   # Android'de klavye kutuyu ortmesin
        Builder.load_string(KV)
        kok = AnaPanel()
        Clock.schedule_once(lambda dt: kok.parametreleri_guncelle(), 0)
        # Test/ekran goruntusu icin: KOORD_SCREENSHOT=dosya.png verilirse kaydedip kapanir
        yol = os.environ.get("KOORD_SCREENSHOT")
        if yol:
            adimlar = [
                lambda: kok.t1_geo2cart(),
                lambda: (kok.switch_to(kok.tab_list[2]), kok.t2_donustur()),
                lambda: kok.ornek_epsg(),
            ]

            def calistir(n):
                if n > 0:
                    Window.screenshot(name=yol)
                if n == len(adimlar):
                    print(kok.ids.t1_out.text, kok.ids.t2_out.text, sep="\n")
                    self.stop()
                    return
                adimlar[n]()
                Clock.schedule_once(lambda dt: calistir(n + 1), 1)
            Clock.schedule_once(lambda dt: calistir(0), 1.5)
        return kok


if __name__ == "__main__":
    KoordinatApp().run()
