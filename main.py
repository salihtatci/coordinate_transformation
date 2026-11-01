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

Gorunum: web surumuyle (new_coordinate_trans_web) ayni shadcn/ui tasarim sistemi.
Renkler `Tema` sinifinda token olarak durur (background, card, border, primary ...);
KV'de `app.t.primary` gibi kullanilir.  Tema degisince bu token'lar degisir ve
Kivy baglamalari (binding) sayesinde tum arayuz kendiliginden yeniden boyanir.
Yazi tipi Inter, ikonlar Lucide (fonts/ klasorunde; internet gerekmez).

Not: Android paketleyicisi (buildozer) giris dosyasinin adinin main.py olmasini ister.
"""
import os
import sys
import json
import math
import subprocess
import traceback

os.environ.setdefault("KIVY_NO_ARGS", "1")   # Kivy'nin komut satiri argumanlarini yutmasini engelle

from kivy.app import App
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import BooleanProperty, ColorProperty, StringProperty
from kivy.utils import get_color_from_hex as hx

import jeodezi as jz

# ---------------------------------------------------------------- yazi tipleri
_KLASOR = os.path.dirname(os.path.abspath(__file__))
_F = lambda ad: os.path.join(_KLASOR, "fonts", ad)
# 'Roboto' Kivy'nin varsayilan yazi tipidir; Inter ile degistirince tum Label'lar Inter olur.
LabelBase.register("Roboto", _F("Inter-Regular.ttf"), fn_bold=_F("Inter-SemiBold.ttf"))
LabelBase.register("Inter", _F("Inter-Regular.ttf"), fn_bold=_F("Inter-SemiBold.ttf"))
LabelBase.register("InterMedium", _F("Inter-Medium.ttf"))
LabelBase.register("InterSemiBold", _F("Inter-SemiBold.ttf"))
LabelBase.register("Lucide", _F("lucide.ttf"))

# Lucide ikonlarinin kod noktalari (fonts/lucide.ttf yalniz bunlari icerir)
IKON = {
    "globe": "", "layers": "", "info": "", "sun": "", "moon": "",
    "monitor": "", "github": "", "arrow-down": "", "arrow-up": "",
    "swap": "", "copy": "", "check": "", "chevron": "",
    "terminal": "", "flask": "", "locate": "", "sliders": "",
}

# Model adlari (Spinner'da gorunecek)
M_IERS = "IERS 14 parametre (zamana bağlı)"
M_SABIT = "7 parametre Helmert (hızsız, t0)"
M_BW = "Bursa-Wolf 7 parametre"
M_MB = "Molodensky-Badekas (7p + Xm, Ym, Zm)"
M_ELIPS = "Yalnız elipsoit değişimi"
MODELLER = [M_IERS, M_SABIT, M_BW, M_MB, M_ELIPS]
# Arayuz adi -> jeodezi model kodu (parametre_bul anahtarinin 3. elemani)
MODEL_KODU = {M_IERS: jz.MODEL_IERS, M_SABIT: jz.MODEL_SABIT, M_BW: jz.MODEL_BW,
              M_MB: jz.MODEL_MB, M_ELIPS: jz.MODEL_ELIPS}
KONV_ADI = {"PV": "PV (Position Vector)", "CF": "CF (Coordinate Frame)"}
MANUEL_YOK = ("Bu kaynak-hedef-model kombinasyonu için kayıtlı parametre bulunamadı. "
              "Lütfen manuel parametre girişi yapın.")


def cografi_mi(metin):
    return metin in ("Cografi", "Coğrafi")


# ---------------------------------------------------------------- tema (renk token'lari)
ACIK = {
    "background": "#FAFAFA", "card": "#FFFFFF", "foreground": "#09090B", "muted": "#F4F4F5",
    "muted_foreground": "#71717A", "border": "#E4E4E7", "input": "#E4E4E7",
    "primary": "#1F6B57", "primary_down": "#164F41", "primary_foreground": "#FFFFFF",
    "primary_soft": "#E8F3EE", "secondary": "#F4F4F5", "ring": "#1F6B5759",
    "success": "#15803D", "destructive": "#DC2626", "info": "#2563EB", "rapor_bg": "#FAFAFA",
}
KOYU = {
    "background": "#09090B", "card": "#111113", "foreground": "#FAFAFA", "muted": "#1C1C1F",
    "muted_foreground": "#A1A1AA", "border": "#27272A", "input": "#303035",
    "primary": "#4FB394", "primary_down": "#3D9A7E", "primary_foreground": "#04130E",
    "primary_soft": "#12261F", "secondary": "#1C1C1F", "ring": "#4FB39466",
    "success": "#4ADE80", "destructive": "#F87171", "info": "#60A5FA", "rapor_bg": "#0B0B0D",
}


class Tema(EventDispatcher):
    """shadcn token'lari.  Her biri ColorProperty: degisince KV'deki baglamalar tetiklenir."""
    background = ColorProperty(); card = ColorProperty(); foreground = ColorProperty()
    muted = ColorProperty(); muted_foreground = ColorProperty(); border = ColorProperty()
    input = ColorProperty(); primary = ColorProperty(); primary_down = ColorProperty()
    primary_foreground = ColorProperty(); primary_soft = ColorProperty(); secondary = ColorProperty()
    ring = ColorProperty(); success = ColorProperty(); destructive = ColorProperty()
    info = ColorProperty(); rapor_bg = ColorProperty()
    koyu = BooleanProperty(False)

    def uygula(self, koyu):
        for ad, renk in (KOYU if koyu else ACIK).items():
            setattr(self, ad, hx(renk))
        self.koyu = koyu


def sistem_koyu_mu():
    """Isletim sisteminin koyu tema ayarini okur (Windows, macOS, Android). Bilinmiyorsa False."""
    try:
        if sys.platform == "win32":
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                               r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
            return winreg.QueryValueEx(k, "AppsUseLightTheme")[0] == 0
        if sys.platform == "darwin":
            r = subprocess.run(["defaults", "read", "-g", "AppleInterfaceStyle"],
                               capture_output=True, text=True, timeout=2)
            return "Dark" in r.stdout
        if "ANDROID_ARGUMENT" in os.environ:
            from jnius import autoclass
            ayar = autoclass("org.kivy.android.PythonActivity").mActivity.getResources().getConfiguration()
            return (ayar.uiMode & 0x30) == 0x20          # UI_MODE_NIGHT_YES
    except Exception:
        pass
    return False


KV = r"""
#:import jz jeodezi
#:import main __main__
#:import FadeTransition kivy.uix.screenmanager.FadeTransition

# ======================= Temel bilesenler (shadcn karsiliklari) =======================

# Kendi yuksekligini metne gore ayarlayan yazi
<Yazi@Label>:
    size_hint_y: None
    text_size: self.width, None
    height: self.texture_size[1]
    halign: 'left'
    valign: 'top'
    font_size: '14sp'
    line_height: 1.25
    color: app.t.foreground
    markup: True

<Soluk@Yazi>:
    font_size: '13sp'
    color: app.t.muted_foreground

<Etiket@Yazi>:
    font_name: 'InterMedium'
    font_size: '13sp'

<Ikon@Label>:
    font_name: 'Lucide'
    font_size: '16sp'
    size_hint: None, None
    size: dp(18), dp(18)
    color: app.t.muted_foreground

# Card
<Kart@BoxLayout>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    padding: dp(20)
    spacing: dp(12)
    canvas.before:
        Color:
            rgba: app.t.card
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
        Color:
            rgba: app.t.border
        Line:
            rounded_rectangle: self.x + .5, self.y + .5, self.width - 1, self.height - 1, dp(14)
            width: 1

<KartBaslik@BoxLayout>:
    baslik: ''
    aciklama: ''
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    spacing: dp(3)
    Yazi:
        text: root.baslik
        font_name: 'InterSemiBold'
        font_size: '15sp'
    Soluk:
        text: root.aciklama
        height: self.texture_size[1] if root.aciklama else 0
        opacity: 1 if root.aciklama else 0

# Button: tur = 'birincil' | 'ikincil' | 'hayalet'
<Dugme@Button>:
    tur: 'ikincil'
    ikon: ''
    yazi: ''
    size_hint_y: None
    height: dp(40)
    font_name: 'InterMedium'
    font_size: '14sp'
    markup: True
    halign: 'center'
    valign: 'middle'
    text_size: self.width - dp(20), None
    text: ('[font=Lucide][size=16sp]' + self.ikon + '[/size][/font]   ' if self.ikon else '') + self.yazi
    background_normal: ''
    background_down: ''
    background_disabled_normal: ''
    background_disabled_down: ''
    background_color: 0, 0, 0, 0
    opacity: .5 if self.disabled else 1
    color: app.t.primary_foreground if self.tur == 'birincil' else (app.t.muted_foreground if self.tur == 'hayalet' else app.t.foreground)
    canvas.before:
        Color:
            rgba: (app.t.primary_down if self.state == 'down' else app.t.primary) if self.tur == 'birincil' else ((app.t.secondary if self.state == 'down' else app.t.card) if self.tur == 'ikincil' else ((app.t.secondary) if self.state == 'down' else (0, 0, 0, 0)))
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
        Color:
            rgba: app.t.border if self.tur == 'ikincil' else (0, 0, 0, 0)
        Line:
            rounded_rectangle: self.x + .5, self.y + .5, self.width - 1, self.height - 1, dp(8)
            width: 1

# Input (Kivy'nin kendi arka planini birakip kendimiz ciziyoruz: '-' oneki)
<-Giris@TextInput>:
    size_hint_y: None
    height: dp(40)
    multiline: False
    write_tab: False
    font_size: '14sp'
    padding: dp(12), (self.height - self.line_height) / 2
    background_normal: ''
    background_active: ''
    background_disabled_normal: ''
    background_color: 0, 0, 0, 0
    foreground_color: app.t.muted_foreground if self.readonly else app.t.foreground
    disabled_foreground_color: app.t.muted_foreground
    hint_text_color: app.t.muted_foreground
    cursor_color: app.t.foreground
    selection_color: app.t.ring
    opacity: .55 if self.disabled else 1
    canvas.before:
        Color:
            rgba: app.t.muted if (self.readonly or self.disabled) else app.t.card
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
        Color:
            rgba: app.t.primary if self.focus else app.t.input
        Line:
            rounded_rectangle: self.x + .5, self.y + .5, self.width - 1, self.height - 1, dp(8)
            width: dp(1.3) if self.focus else 1
        Color:
            rgba: (self.cursor_color if self.focus and not self._cursor_blink and int(self.x + self.padding[0]) <= self._cursor_visual_pos[0] <= int(self.x + self.width - self.padding[2]) else (0, 0, 0, 0))
        Rectangle:
            pos: self._cursor_visual_pos
            size: self.cursor_width, -self._cursor_visual_height
        Color:
            rgba: self.disabled_foreground_color if self.disabled else (self.hint_text_color if not self.text else self.foreground_color)

<SayiGiris@Giris>:
    font_name: 'RobotoMono-Regular'
    font_size: '13sp'

# Select
<SecimListe@DropDown>:
    max_height: dp(320)
    bar_width: dp(4)
    bar_color: app.t.border
    canvas.before:
        Color:
            rgba: app.t.card
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
        Color:
            rgba: app.t.border
        Line:
            rounded_rectangle: self.x + .5, self.y + .5, self.width - 1, self.height - 1, dp(8)

<SecimSecenek@SpinnerOption>:
    size_hint_y: None
    height: dp(36)
    font_size: '14sp'
    halign: 'left'
    valign: 'middle'
    padding: dp(12), 0
    text_size: self.size
    shorten: True
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    color: app.t.foreground
    canvas.before:
        Color:
            rgba: app.t.secondary if self.state == 'down' else (0, 0, 0, 0)
        RoundedRectangle:
            pos: self.x + dp(4), self.y + dp(2)
            size: self.width - dp(8), self.height - dp(4)
            radius: [dp(6)]

<Secim@Spinner>:
    size_hint_y: None
    height: dp(40)
    font_size: '14sp'
    halign: 'left'
    valign: 'middle'
    padding: dp(12), 0, dp(36), 0
    text_size: self.size
    shorten: True
    shorten_from: 'right'
    option_cls: 'SecimSecenek'
    dropdown_cls: 'SecimListe'
    background_normal: ''
    background_down: ''
    background_disabled_normal: ''
    background_color: 0, 0, 0, 0
    color: app.t.foreground
    disabled_color: app.t.muted_foreground
    opacity: .55 if self.disabled else 1
    canvas.before:
        Color:
            rgba: app.t.muted if self.disabled else app.t.card
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(8)]
        Color:
            rgba: app.t.primary if self.is_open else app.t.input
        Line:
            rounded_rectangle: self.x + .5, self.y + .5, self.width - 1, self.height - 1, dp(8)
            width: dp(1.3) if self.is_open else 1
    canvas.after:
        Color:
            rgba: app.t.muted_foreground
        Line:
            points: self.right - dp(24), self.center_y + dp(2.5), self.right - dp(19), self.center_y - dp(2.5), self.right - dp(14), self.center_y + dp(2.5)
            width: dp(1.2)
            cap: 'round'
            joint: 'round'

# Checkbox (Kivy'nin resimli cizimini birakip kendi cizimimiz)
<-Onay@CheckBox>:
    size_hint: None, None
    size: dp(18), dp(18)
    opacity: .5 if self.disabled else 1
    canvas:
        Color:
            rgba: app.t.primary if self.active else app.t.card
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(4)]
        Color:
            rgba: app.t.primary if self.active else app.t.input
        Line:
            rounded_rectangle: self.x + .5, self.y + .5, self.width - 1, self.height - 1, dp(4)
        Color:
            rgba: app.t.primary_foreground if self.active else (0, 0, 0, 0)
        Line:
            points: self.x + dp(4.5), self.center_y, self.x + dp(7.5), self.y + dp(5), self.right - dp(4), self.top - dp(5)
            width: dp(1.5)
            cap: 'round'
            joint: 'round'

<OnaySatir@BoxLayout>:
    size_hint_y: None
    height: dp(28)
    spacing: dp(10)

# Alan: ustte etiket, altta kutu
<Alan@BoxLayout>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    spacing: dp(6)

<Izgara@GridLayout>:
    size_hint_y: None
    height: self.minimum_height
    spacing: dp(12), dp(14)

# Rapor kutusu (salt okunur, es aralikli)
<-Sonuc@TextInput>:
    readonly: True
    font_name: 'RobotoMono-Regular'
    font_size: '12.5sp'
    line_spacing: dp(3)
    size_hint_y: None
    height: max(dp(300), self.minimum_height)
    padding: dp(18), dp(16)
    background_normal: ''
    background_active: ''
    background_color: 0, 0, 0, 0
    foreground_color: app.t.foreground
    cursor_color: 0, 0, 0, 0
    selection_color: app.t.ring
    canvas.before:
        Color:
            rgba: app.t.rapor_bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [0, 0, dp(14), dp(14)]
        Color:
            rgba: (self.cursor_color if self.focus and not self._cursor_blink and int(self.x + self.padding[0]) <= self._cursor_visual_pos[0] <= int(self.x + self.width - self.padding[2]) else (0, 0, 0, 0))
        Rectangle:
            pos: self._cursor_visual_pos
            size: self.cursor_width, -self._cursor_visual_height
        Color:
            rgba: self.disabled_foreground_color if self.disabled else (self.hint_text_color if not self.text else self.foreground_color)

<RaporKart@BoxLayout>:
    hedef: None
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    pos_hint: {'top': 1}
    canvas.before:
        Color:
            rgba: app.t.card
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
    canvas.after:
        Color:
            rgba: app.t.border
        Line:
            rounded_rectangle: self.x + .5, self.y + .5, self.width - 1, self.height - 1, dp(14)
        Line:
            points: self.x, self.top - dp(48), self.right, self.top - dp(48)
    BoxLayout:
        size_hint_y: None
        height: dp(48)
        padding: dp(18), 0, dp(10), 0
        spacing: dp(8)
        Ikon:
            text: main.IKON['terminal']
            pos_hint: {'center_y': .5}
        Label:
            text: 'Hesap raporu'
            font_name: 'InterSemiBold'
            font_size: '14sp'
            color: app.t.foreground
            halign: 'left'
            valign: 'middle'
            text_size: self.size
        Dugme:
            id: kopyala
            tur: 'hayalet'
            ikon: main.IKON['copy']
            yazi: 'Kopyala'
            size_hint_x: None
            width: dp(112)
            height: dp(32)
            font_size: '13sp'
            pos_hint: {'center_y': .5}
            on_release: app.root.kopyala(root.hedef, self)

<PanelBas@BoxLayout>:
    baslik: ''
    aciklama: ''
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    spacing: dp(6)
    padding: 0, 0, 0, dp(6)
    Yazi:
        text: root.baslik
        font_name: 'InterSemiBold'
        font_size: '22sp'
    Soluk:
        text: root.aciklama
        font_size: '14sp'

# Sayfa: ortalanmis, en fazla 1200 dp genislik
<Sayfa@BoxLayout>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    spacing: dp(18)
    padding: max(dp(16), (self.width - dp(1200)) / 2), dp(24), max(dp(16), (self.width - dp(1200)) / 2), dp(32)

<Kaydirma@ScrollView>:
    bar_width: dp(6)
    bar_color: app.t.border
    bar_inactive_color: app.t.border[:3] + [.4]
    scroll_type: ['bars', 'content']
    do_scroll_x: False

<Kolon@BoxLayout>:
    orientation: 'vertical'
    size_hint_y: None
    height: self.minimum_height
    spacing: dp(16)
    pos_hint: {'top': 1}

# Sekme dugmesi (shadcn TabsTrigger)
<SekmeDugme@ToggleButton>:
    ikon: ''
    yazi: ''
    ekran: ''
    group: 'sekme'
    allow_no_selection: False
    markup: True
    font_name: 'InterMedium'
    font_size: '14sp'
    text: ('[font=Lucide][size=15sp]' + self.ikon + '[/size][/font]  ' if self.ikon else '') + self.yazi
    width: self.texture_size[0] + dp(28)
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    color: app.t.foreground if self.state == 'down' else app.t.muted_foreground
    on_state: if self.state == 'down' and app.root: app.root.sekme_sec(self.ekran)
    canvas.before:
        Color:
            rgba: app.t.card if self.state == 'down' else (0, 0, 0, 0)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(7)]
        Color:
            rgba: app.t.border if self.state == 'down' else (0, 0, 0, 0)
        Line:
            rounded_rectangle: self.x + .5, self.y + .5, self.width - 1, self.height - 1, dp(7)

<TemaDugme@ToggleButton>:
    tema: ''
    group: 'tema'
    allow_no_selection: False
    font_name: 'Lucide'
    font_size: '15sp'
    size_hint_x: None
    width: dp(32)
    background_normal: ''
    background_down: ''
    background_color: 0, 0, 0, 0
    color: app.t.foreground if self.state == 'down' else app.t.muted_foreground
    on_state: if self.state == 'down': app.tema_sec(self.tema)
    canvas.before:
        Color:
            rgba: app.t.card if self.state == 'down' else (0, 0, 0, 0)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(7)]

<Logo@Widget>:
    size_hint: None, None
    size: dp(26), dp(26)
    canvas:
        Color:
            rgba: main.hx('#1F6B57')
        Ellipse:
            pos: self.x + self.width * 2 / 32, self.y + self.height * 2 / 32
            size: self.width * 28 / 32, self.height * 28 / 32
        Color:
            rgba: main.hx('#F0BE2E')
        Line:
            bezier: self.x + self.width * 4 / 32, self.y + self.height * 14 / 32, self.x + self.width * 10 / 32, self.y + self.height * 19 / 32, self.x + self.width * 22 / 32, self.y + self.height * 19 / 32, self.x + self.width * 28 / 32, self.y + self.height * 14 / 32
            width: dp(1.4)
        Color:
            rgba: 1, 1, 1, 1
        Ellipse:
            pos: self.x + self.width * 13 / 32, self.y + self.height * 18 / 32
            size: self.width * 6 / 32, self.height * 6 / 32

# ======================= Ana panel =======================
<AnaPanel>:
    orientation: 'vertical'
    canvas.before:
        Color:
            rgba: app.t.background
        Rectangle:
            pos: self.pos
            size: self.size

    # ---------- ust cubuk ----------
    BoxLayout:
        orientation: 'vertical'
        size_hint_y: None
        height: self.minimum_height
        padding: max(dp(16), (root.width - dp(1200)) / 2), dp(10), max(dp(16), (root.width - dp(1200)) / 2), dp(12)
        spacing: dp(10)
        canvas.before:
            Color:
                rgba: app.t.background
            Rectangle:
                pos: self.pos
                size: self.size
            Color:
                rgba: app.t.border
            Line:
                points: self.x, self.y, self.right, self.y
        BoxLayout:
            size_hint_y: None
            height: dp(38)
            spacing: dp(10)
            Logo:
                pos_hint: {'center_y': .5}
            Label:
                text: 'Koordinat Dönüşümü'
                font_name: 'InterSemiBold'
                font_size: '16sp'
                color: app.t.foreground
                halign: 'left'
                valign: 'middle'
                text_size: self.size
                shorten: True
            BoxLayout:
                size_hint: None, None
                size: dp(3 * 32 + 2 * 2 + 6), dp(34)
                pos_hint: {'center_y': .5}
                padding: dp(3)
                spacing: dp(2)
                canvas.before:
                    Color:
                        rgba: app.t.muted
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(9)]
                TemaDugme:
                    id: tema_sistem
                    tema: 'sistem'
                    text: main.IKON['monitor']
                TemaDugme:
                    id: tema_acik
                    tema: 'light'
                    text: main.IKON['sun']
                TemaDugme:
                    id: tema_koyu
                    tema: 'dark'
                    text: main.IKON['moon']
        # sekmeler (TabsList)
        BoxLayout:
            size_hint: (None, None) if root.genis else (1, None)
            width: self.minimum_width
            height: dp(38)
            padding: dp(3)
            spacing: dp(2)
            canvas.before:
                Color:
                    rgba: app.t.muted
                RoundedRectangle:
                    pos: self.pos
                    size: self.size
                    radius: [dp(9)]
            SekmeDugme:
                id: sekme_cografi
                size_hint_x: None if root.genis else 1
                ekran: 'cografi'
                ikon: main.IKON['globe'] if root.genis else ''
                yazi: 'Coğrafi ↔ Kartezyen' if root.genis else 'Coğrafi ↔ XYZ'
                state: 'down'
            SekmeDugme:
                id: sekme_datum
                size_hint_x: None if root.genis else 1
                ekran: 'datum'
                ikon: main.IKON['layers'] if root.genis else ''
                yazi: 'Datum ve çerçeve' if root.genis else 'Datum'
            SekmeDugme:
                id: sekme_bilgi
                size_hint_x: None if root.genis else 1
                ekran: 'bilgi'
                ikon: main.IKON['info'] if root.genis else ''
                yazi: 'Bilgi'

    ScreenManager:
        id: ekranlar
        transition: FadeTransition(duration=.12)

        # ================= COGRAFI <-> KARTEZYEN =================
        Screen:
            name: 'cografi'
            Kaydirma:
                Sayfa:
                    PanelBas:
                        baslik: 'Coğrafi ↔ Kartezyen'
                        aciklama: 'Aynı noktanın φ, λ, h ve X, Y, Z gösterimleri arasında seçilen elipsoitte dönüşüm. Rapor her adımın formülünü ve ara değerlerini gösterir.'
                    BoxLayout:
                        orientation: 'horizontal' if root.genis else 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(20)
                        Kolon:
                            Kart:
                                Izgara:
                                    cols: 2 if root.width > dp(600) else 1
                                    Alan:
                                        Etiket:
                                            text: 'Elipsoit'
                                        Secim:
                                            id: t1_elips
                                            text: 'GRS80'
                                            values: list(jz.ELIPSOITLER)
                                    Alan:
                                        Etiket:
                                            text: 'Ters çözüm yöntemi'
                                        Secim:
                                            id: t1_yontem
                                            text: 'iteratif'
                                            values: ['iteratif', 'bowring']
                            Kart:
                                KartBaslik:
                                    baslik: 'Coğrafi koordinatlar'
                                    aciklama: 'φ ve λ ondalık derece ya da derece dakika saniye.'
                                Izgara:
                                    cols: 3 if root.width > dp(600) else 1
                                    Alan:
                                        Etiket:
                                            text: 'Enlem φ'
                                        SayiGiris:
                                            id: t1_phi
                                            hint_text: '39.925'
                                            text: '39 55 30.0'
                                    Alan:
                                        Etiket:
                                            text: 'Boylam λ'
                                        SayiGiris:
                                            id: t1_lam
                                            hint_text: '32.8369'
                                            text: '32 50 12.84'
                                    Alan:
                                        Etiket:
                                            text: 'h (m)'
                                        SayiGiris:
                                            id: t1_h
                                            text: '938.000'
                                Dugme:
                                    tur: 'birincil'
                                    ikon: main.IKON['arrow-down']
                                    yazi: 'Coğrafi → Kartezyen'
                                    on_release: root.t1_geo2cart()
                            Kart:
                                KartBaslik:
                                    baslik: 'Kartezyen koordinatlar'
                                    aciklama: 'Yer merkezli X, Y, Z (m).'
                                Izgara:
                                    cols: 3 if root.width > dp(600) else 1
                                    Alan:
                                        Etiket:
                                            text: 'X (m)'
                                        SayiGiris:
                                            id: t1_x
                                    Alan:
                                        Etiket:
                                            text: 'Y (m)'
                                        SayiGiris:
                                            id: t1_y
                                    Alan:
                                        Etiket:
                                            text: 'Z (m)'
                                        SayiGiris:
                                            id: t1_z
                                Dugme:
                                    tur: 'birincil'
                                    ikon: main.IKON['arrow-up']
                                    yazi: 'Kartezyen → Coğrafi'
                                    on_release: root.t1_cart2geo()
                        RaporKart:
                            hedef: t1_out
                            Sonuc:
                                id: t1_out
                                text: 'Bir dönüşüm seçin; formüller ve ara değerler burada görünür.'

        # ================= DATUM VE CERCEVE (+ model parametreleri) =================
        Screen:
            name: 'datum'
            Kaydirma:
                Sayfa:
                    PanelBas:
                        baslik: 'Datum ve çerçeve dönüşümü'
                        aciklama: 'ITRF, ETRF, WGS84 ve ED50 arasında Helmert dönüşümleri. Parametreler kaynak, hedef ve model üçlüsüne göre kayıtlı setlerden otomatik seçilir.'
                    BoxLayout:
                        orientation: 'horizontal' if root.genis else 'vertical'
                        size_hint_y: None
                        height: self.minimum_height
                        spacing: dp(20)
                        Kolon:
                            Kart:
                                KartBaslik:
                                    baslik: 'Sistemler ve model'
                                Izgara:
                                    cols: 2 if root.width > dp(600) else 1
                                    Alan:
                                        Etiket:
                                            text: 'Kaynak sistem'
                                        Secim:
                                            id: t2_kaynak
                                            text: 'WGS84 (G2139)'
                                            values: list(jz.SISTEMLER)
                                            on_text: root.parametreleri_guncelle()
                                    Alan:
                                        Etiket:
                                            text: 'Hedef sistem'
                                        Secim:
                                            id: t2_hedef
                                            text: 'ITRF96 (TUREF)'
                                            values: list(jz.SISTEMLER)
                                            on_text: root.parametreleri_guncelle()
                                Alan:
                                    Etiket:
                                        text: 'Dönüşüm modeli'
                                    Secim:
                                        id: t2_model
                                        text: main.M_IERS
                                        values: main.MODELLER
                                        on_text: root.parametreleri_guncelle()
                                Izgara:
                                    cols: 2 if root.width > dp(600) else 1
                                    Alan:
                                        Etiket:
                                            text: 'Ölçü epoğu t (yıl)'
                                        SayiGiris:
                                            id: t2_epok
                                            text: '2025.0'
                                            disabled: t2_model.text != main.M_IERS
                                            on_text: root.parametreleri_guncelle()
                                    Alan:
                                        Etiket:
                                            text: 'Giriş koordinat türü'
                                        Secim:
                                            id: t2_tip
                                            text: 'Kartezyen'
                                            values: ['Kartezyen', 'Coğrafi']
                            Kart:
                                KartBaslik:
                                    baslik: 'Giriş koordinatları'
                                    aciklama: 'Kaynak sistemde. Coğrafi girişte kaynak sistemin elipsoidi kullanılır.'
                                Izgara:
                                    cols: 3 if root.width > dp(600) else 1
                                    Alan:
                                        Etiket:
                                            text: 'Enlem φ' if main.cografi_mi(t2_tip.text) else 'X (m)'
                                        SayiGiris:
                                            id: t2_a
                                            text: '4116037.2588'
                                    Alan:
                                        Etiket:
                                            text: 'Boylam λ' if main.cografi_mi(t2_tip.text) else 'Y (m)'
                                        SayiGiris:
                                            id: t2_b
                                            text: '2656358.3524'
                                    Alan:
                                        Etiket:
                                            text: 'h (m)' if main.cografi_mi(t2_tip.text) else 'Z (m)'
                                        SayiGiris:
                                            id: t2_c
                                            text: '4072204.7958'
                                BoxLayout:
                                    size_hint_y: None
                                    height: dp(40)
                                    spacing: dp(8)
                                    Dugme:
                                        tur: 'birincil'
                                        yazi: 'Dönüştür'
                                        on_release: root.t2_donustur()
                                    Dugme:
                                        ikon: main.IKON['swap'] if root.width > dp(600) else ''
                                        yazi: 'Kaynak ↔ Hedef'
                                        on_release: root.t2_yer_degistir()

                            # ---- Model parametreleri (acilir kapanir kart) ----
                            Kart:
                                id: param_kart
                                padding: 0
                                spacing: 0
                                Dugme:
                                    tur: 'hayalet'
                                    height: dp(54)
                                    halign: 'left'
                                    text_size: self.width - dp(44), None
                                    color: app.t.foreground
                                    font_name: 'InterSemiBold'
                                    font_size: '15sp'
                                    yazi: 'Model parametreleri'
                                    on_release: root.param_ac_kapa()
                                    canvas.after:
                                        Color:
                                            rgba: app.t.muted_foreground
                                        Line:
                                            points: (self.right - dp(27), self.center_y - dp(2.5), self.right - dp(22), self.center_y + dp(2.5), self.right - dp(17), self.center_y - dp(2.5)) if root.param_acik else (self.right - dp(27), self.center_y + dp(2.5), self.right - dp(22), self.center_y - dp(2.5), self.right - dp(17), self.center_y + dp(2.5))
                                            width: dp(1.2)
                                            cap: 'round'
                                            joint: 'round'
                                BoxLayout:
                                    id: param_icerik
                                    orientation: 'vertical'
                                    size_hint_y: None
                                    height: self.minimum_height
                                    padding: dp(20), dp(14), dp(20), dp(20)
                                    spacing: dp(12)
                                    canvas.before:
                                        Color:
                                            rgba: app.t.border
                                        Line:
                                            points: self.x, self.top, self.right, self.top
                                    Soluk:
                                        id: p_baslik
                                        text: ''
                                    Izgara:
                                        cols: 3 if root.width > dp(600) else 1
                                        Alan:
                                            Etiket:
                                                text: 'Tx (m)'
                                            SayiGiris:
                                                id: p_tx
                                                readonly: not root.manuel_aktif
                                        Alan:
                                            Etiket:
                                                text: 'Ty (m)'
                                            SayiGiris:
                                                id: p_ty
                                                readonly: not root.manuel_aktif
                                        Alan:
                                            Etiket:
                                                text: 'Tz (m)'
                                            SayiGiris:
                                                id: p_tz
                                                readonly: not root.manuel_aktif
                                        Alan:
                                            Etiket:
                                                text: 'Rx (″)'
                                            SayiGiris:
                                                id: p_rx
                                                readonly: not root.manuel_aktif
                                        Alan:
                                            Etiket:
                                                text: 'Ry (″)'
                                            SayiGiris:
                                                id: p_ry
                                                readonly: not root.manuel_aktif
                                        Alan:
                                            Etiket:
                                                text: 'Rz (″)'
                                            SayiGiris:
                                                id: p_rz
                                                readonly: not root.manuel_aktif
                                        Alan:
                                            Etiket:
                                                text: 'Ölçek D (ppm)'
                                            SayiGiris:
                                                id: p_d
                                                readonly: not root.manuel_aktif
                                    Alan:
                                        Etiket:
                                            text: 'Dönüklük konvansiyonu'
                                        Secim:
                                            id: p_konv
                                            text: 'PV (Position Vector)'
                                            values: ['PV (Position Vector)', 'CF (Coordinate Frame)']
                                            disabled: not root.manuel_aktif
                                    Izgara:
                                        cols: 3 if root.width > dp(600) else 1
                                        Alan:
                                            Etiket:
                                                text: 'Xm (m), M-B'
                                            SayiGiris:
                                                id: p_xm
                                                disabled: t2_model.text != main.M_MB
                                                readonly: not root.manuel_aktif
                                        Alan:
                                            Etiket:
                                                text: 'Ym (m), M-B'
                                            SayiGiris:
                                                id: p_ym
                                                disabled: t2_model.text != main.M_MB
                                                readonly: not root.manuel_aktif
                                        Alan:
                                            Etiket:
                                                text: 'Zm (m), M-B'
                                            SayiGiris:
                                                id: p_zm
                                                disabled: t2_model.text != main.M_MB
                                                readonly: not root.manuel_aktif
                                    OnaySatir:
                                        Onay:
                                            id: p_ters
                                            pos_hint: {'center_y': .5}
                                            disabled: not root.manuel_aktif
                                        Yazi:
                                            text: 'Ters yönde uygula'
                                            pos_hint: {'center_y': .5}
                                            color: app.t.muted_foreground if p_ters.disabled else app.t.foreground
                                    OnaySatir:
                                        Onay:
                                            id: p_manuel
                                            pos_hint: {'center_y': .5}
                                            disabled: t2_model.text not in (main.M_BW, main.M_MB)
                                            on_active: root.parametreleri_guncelle()
                                        Yazi:
                                            text: 'Manuel parametre girişi (Bursa-Wolf ve Molodensky-Badekas)'
                                            pos_hint: {'center_y': .5}
                                            color: app.t.muted_foreground if p_manuel.disabled else app.t.foreground
                                    # durum kutusu (Alert)
                                    BoxLayout:
                                        size_hint_y: None
                                        height: p_durum.height + dp(20) if p_durum.text else 0
                                        opacity: 1 if p_durum.text else 0
                                        padding: dp(12), dp(10)
                                        canvas.before:
                                            Color:
                                                rgba: list({'iyi': app.t.success, 'uyari': app.t.destructive, 'bilgi': app.t.info}.get(root.durum_tur, app.t.foreground))[:3] + [.08]
                                            RoundedRectangle:
                                                pos: self.pos
                                                size: self.size
                                                radius: [dp(8)]
                                            Color:
                                                rgba: list({'iyi': app.t.success, 'uyari': app.t.destructive, 'bilgi': app.t.info}.get(root.durum_tur, app.t.foreground))[:3] + [.35]
                                            Line:
                                                rounded_rectangle: self.x + .5, self.y + .5, self.width - 1, self.height - 1, dp(8)
                                        Yazi:
                                            id: p_durum
                                            font_name: 'InterMedium'
                                            font_size: '13sp'
                                            text: ''
                                            color: {'iyi': app.t.success, 'uyari': app.t.destructive, 'bilgi': app.t.info}.get(root.durum_tur, app.t.foreground)
                                    BoxLayout:
                                        size_hint_y: None
                                        height: p_ayrinti.height + dp(20) if p_ayrinti.text else 0
                                        opacity: 1 if p_ayrinti.text else 0
                                        padding: dp(12), dp(10)
                                        canvas.before:
                                            Color:
                                                rgba: app.t.muted
                                            RoundedRectangle:
                                                pos: self.pos
                                                size: self.size
                                                radius: [dp(8)]
                                        Yazi:
                                            id: p_ayrinti
                                            font_name: 'RobotoMono-Regular'
                                            font_size: '11.5sp'
                                            color: app.t.muted_foreground
                                            text: ''
                                    Dugme:
                                        ikon: main.IKON['flask']
                                        yazi: 'Test örneği: EPSG 7-2 (WGS72 → WGS84), gerçek dönüşüm değil'
                                        height: max(dp(40), self.texture_size[1] + dp(16))
                                        on_release: root.ornek_epsg()
                                    Soluk:
                                        text: main.PARAM_NOTU
                        RaporKart:
                            hedef: t2_out
                            Sonuc:
                                id: t2_out
                                text: "Kaynak, hedef ve modeli seçip Dönüştür'e basın."

        # ================= BILGI =================
        Screen:
            name: 'bilgi'
            Kaydirma:
                Sayfa:
                    Kart:
                        size_hint_x: None if root.width > dp(860) else 1
                        width: dp(780)
                        pos_hint: {'x': 0}
                        padding: dp(28), dp(26)
                        Yazi:
                            text: main.BILGI
                            line_height: 1.35
                            color: app.t.foreground
"""

PARAM_NOTU = ("Parametreler kaynak, hedef ve model üçlüsüne göre kayıtlı setten ya da IERS "
              "tablosundan otomatik seçilir ve salt okunurdur. Kayıt yoksa alanlar boş kalır; "
              "0 ya da örnek değer yazılmaz. Kayıtlı set ters yöndeyse parametreler "
              "değiştirilmeden kesin ters çözüm uygulanır. Manuel girişte konvansiyonu ve yönü "
              "siz seçersiniz: PV ve CF aynı sayılarla farklı sonuç verir (IERS ve EPSG:1033 PV, "
              "EPSG:1032 CF).")

BILGI = """[size=17sp][b]Ne neyi belirler?[/b][/size]
[b]Çerçeve ya da datum[/b] (ITRF2020, WGS84 (G2139), ETRF2000, ED50) noktanın [b]X, Y, Z[/b] değerini belirler. [b]Elipsoit[/b] (GRS80, WGS84, Hayford) ise aynı X, Y, Z'nin [b]φ, λ, h[/b] olarak nasıl ifade edileceğini belirler.

[b]WGS84 ve GRS80[/b]: iki elipsoidin a değeri aynıdır, yalnız 1/f farklıdır (b'de yaklaşık 0.105 mm). Aynı çerçevede X, Y, Z hiç değişmez; φ aynı kalır, h en fazla 0.1 mm değişir. Bunu "Yalnız elipsoit değişimi" modeliyle görebilirsiniz.

[size=17sp][b]ITRF'ler arası dönüşüm[/b][/size]
IERS 14 parametre yayınlar: 7 parametre ve bunların yıllık hızları.
    P(t) = P(t0) + (dP/dt) (t − t0)
    X2 = X1 + T + D X1 + R X1
Hızları ihmal etmek (7 parametre, t0'da sabit) yıllar ilerledikçe santimetre düzeyinde hata yapar; iki modeli karşılaştırarak farkı görün.

[b]WGS84 gerçekleştirmeleri[/b]: G1762 ≈ ITRF2008, G2139 ≈ ITRF2014, G2296 ≈ ITRF2020 (santimetre düzeyinde örtüşür, sıfır parametre kabul edilir). [b]WGS84 (EPSG ensemble)[/b]: EPSG'deki WGS 84 topluluğu (yaklaşık 2 m). ED50 → WGS 84 (EPSG:1784) bu sisteme tanımlıdır.

[size=17sp][b]Datum dönüşüm modelleri[/b][/size]
[b]Bursa-Wolf[/b]: X2 = T + (1 + D) R X1, dönüklük dünya merkezi etrafında.
[b]Molodensky-Badekas[/b]: X2 = Xm + T + (1 + D) R (X1 − Xm), dönüklük ağırlık merkezi etrafında.
[b]Otomatik parametre[/b]: Datum sekmesindeki "Model parametreleri" kartı (kaynak, hedef, model) üçlüsüne göre kayıtlı seti doldurur. Kayıt yoksa alanlar boş kalır ve dönüşüm yapılmaz; Bursa-Wolf ve Molodensky-Badekas için manuel giriş yapabilirsiniz.

[size=17sp][b]Coğrafi ve kartezyen koordinatlar[/b][/size]
    N = a / √(1 − e² sin² φ)
    X = (N + h) cos φ cos λ
    Y = (N + h) cos φ sin λ
    Z = (N (1 − e²) + h) sin φ
Ters çözüm iteratif (10⁻¹² rad) ya da Bowring yöntemiyle yapılır.

[color=d97706][b]Uyarı[/b]: Programdaki IERS, EUREF ve EPSG parametreleri ders amaçlıdır; resmî işlerde güncel tablolarla (itrf.ign.fr, epsg.org) karşılaştırın. "ITRF96 (TUREF)" etiketi sadeleştirilmiştir: TUREF'in referans epoğu 2005.0'dır ve program noktayı bu epoğa taşımaz.[/color]"""


def sayi(metin):
    """'1.234' veya '1,234' -> float"""
    return float(metin.strip().replace(",", "."))


def hata_metni(e):
    return f"HATA: {e}\n\n(Ayrinti)\n{traceback.format_exc(limit=2)}"


class AnaPanel(BoxLayout):
    # Manuel parametre girisi acik VE model BW/MB ise True; KV'de kutularin salt-okunurlugu buna bagli
    manuel_aktif = BooleanProperty(False)
    genis = BooleanProperty(True)          # pencere genis mi (iki sutun)? on_size'da guncellenir
    param_acik = BooleanProperty(True)     # 'Model parametreleri' karti acik mi
    durum_tur = StringProperty("")         # p_durum rengi: 'iyi' | 'uyari' | 'bilgi'
    _eslesme = None                        # son jz.parametre_bul sonucu

    def on_size(self, *_):
        self.genis = self.width >= 980

    # ---------------- gorunum yardimcilari ----------------
    def sekme_sec(self, ad):
        """'cografi' | 'datum' | 'bilgi' ekranina gecer ve ilgili sekme dugmesini secili yapar."""
        ekranlar = self.ids.ekranlar
        if ekranlar.current != ad:
            ekranlar.current = ad
        # Toggle grubunu elle esitle: state'i koddan degistirmek digerlerini birakmaz
        for e in ("cografi", "datum", "bilgi"):
            dugme = self.ids.get("sekme_" + e)
            yeni = "down" if e == ad else "normal"
            if dugme is not None and dugme.state != yeni:
                dugme.state = yeni

    def param_ac_kapa(self):
        """Model parametreleri kartinin govdesini gizler / gosterir (widget referansi korunur)."""
        kart, icerik = self.ids.param_kart, self.ids.param_icerik
        self._param_icerik = icerik
        if self.param_acik:
            kart.remove_widget(icerik)
        else:
            kart.add_widget(icerik)
        self.param_acik = not self.param_acik

    def kopyala(self, kutu, dugme):
        if kutu is None:
            return
        try:
            from kivy.core.clipboard import Clipboard   # gerektiginde yukle
            Clipboard.copy(kutu.text)
            dugme.ikon, dugme.yazi = IKON["check"], "Kopyalandı"
        except Exception:
            dugme.yazi = "Kopyalanamadı"

        def geri(_dt):
            dugme.ikon, dugme.yazi = IKON["copy"], "Kopyala"
        Clock.schedule_once(geri, 1.6)

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
    def t2_yer_degistir(self):
        """Kaynak <-> Hedef.  Otomatik modda parametre_bul yeni yonu kendisi cozer
        (kayitli set ters yondeyse kesin ters cozum).  Manuel modda kutulardaki
        parametreler ESKI yon icin girildiginden 'Ters yonde uygula' tersine cevrilir."""
        i = self.ids
        if self.manuel_aktif:
            i.p_ters.active = not i.p_ters.active
        i.t2_kaynak.text, i.t2_hedef.text = i.t2_hedef.text, i.t2_kaynak.text
        self.parametreleri_guncelle()

    def _kullanici_param(self, mb=False):
        i = self.ids
        try:
            p = [sayi(w.text) for w in (i.p_tx, i.p_ty, i.p_tz, i.p_d, i.p_rx, i.p_ry, i.p_rz)]
            merkez = ((sayi(i.p_xm.text), sayi(i.p_ym.text), sayi(i.p_zm.text)) if mb
                      else (0.0, 0.0, 0.0))
        except ValueError:
            raise ValueError("Manuel parametre girisi eksik/hatali: Tx, Ty, Tz, D, Rx, Ry, Rz"
                             + (", Xm, Ym, Zm" if mb else "") + " alanlarini doldurun.")
        konv = "CF" if i.p_konv.text.startswith("CF") else "PV"
        return p, merkez, konv, i.p_ters.active

    def t2_donustur(self):
        i = self.ids
        try:
            self.parametreleri_guncelle()
            e = self._eslesme
            kay, hed, model = i.t2_kaynak.text, i.t2_hedef.text, i.t2_model.text
            kod = MODEL_KODU[model]
            el_k, el_h = jz.SISTEMLER[kay], jz.SISTEMLER[hed]
            a, b, c = i.t2_a.text, i.t2_b.text, i.t2_c.text
            o = [f"MODEL : {model}", f"YON   : {kay} [{el_k}]  ->  {hed} [{el_h}]",
                 "=" * 56]

            # 1) Girisi Kartezyen'e getir (kaynak sistemin elipsoidi ile)
            if cografi_mi(i.t2_tip.text):
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
            if model in (M_BW, M_MB) and self.manuel_aktif:
                p, merkez, konv, ters = self._kullanici_param(model == M_MB)
                if model == M_BW:
                    f, args = jz.bursa_wolf, p
                else:
                    f, args = jz.molodensky_badekas, p + [merkez]
                X2 = (jz.ters_cevir_7(X1, f, *args, konvansiyon=konv) if ters
                      else f(X1, *args, konvansiyon=konv))
                o += ["   Parametre kaynagi: Manuel giris (kullanici)",
                      f"   T[m] = {p[0]:.4f} {p[1]:.4f} {p[2]:.4f}   D = {p[3]:.4f} ppm",
                      f"   R[\"] = {p[4]:.5f} {p[5]:.5f} {p[6]:.5f}   konvansiyon = {konv}"
                      + ("   (TERS, kesin iteratif cozum)" if ters else "")]
                if model == M_MB:
                    o.append(f"   Xm  = {merkez[0]:.3f} {merkez[1]:.3f} {merkez[2]:.3f}")
            else:
                if not e.bulundu:
                    o += ["   " + (MANUEL_YOK if model in (M_BW, M_MB) else e.mesaj),
                          "   Donusum YAPILMADI (ornek/0 parametre kullanilmaz)."]
                    i.t2_out.text = "\n".join(o)
                    return
                try:
                    epok = sayi(i.t2_epok.text)
                except ValueError:
                    epok = None
                X2, e, rapor = jz.donustur(X1, kay, hed, kod, epok)
                o.append(f"   Parametre kaynagi: {e.kurum}" + (f"  [{e.kod}]" if e.kod else ""))
                if model in (M_IERS, M_SABIT):
                    if not rapor:
                        o.append("   Kaynak = hedef, donusum yok.")
                    for r in rapor:
                        T, D, R = r["T_mm"], r["D_ppb"], r["R_mas"]
                        o += [f"   * {r['adim']}   (t = {r['epok']:.2f})",
                              f"     T[mm] = {T[0]:8.3f} {T[1]:8.3f} {T[2]:8.3f}   D[ppb] = {D:7.3f}",
                              f"     R[mas]= {R[0]:8.4f} {R[1]:8.4f} {R[2]:8.4f}",
                              "     dX[mm]= " + " ".join(f"{v*1000:8.2f}" for v in r["fark_m"])]
                elif model in (M_BW, M_MB):
                    if e.yon == "ozdes":
                        o.append("   " + e.mesaj)
                    else:
                        o += [f"   T[m] = {e.T[0]:.4f} {e.T[1]:.4f} {e.T[2]:.4f}   D = {e.D:.4f} ppm",
                              f"   R[\"] = {e.R[0]:.5f} {e.R[1]:.5f} {e.R[2]:.5f}   "
                              f"konvansiyon = {e.konvansiyon} (kayitli)"]
                        if e.merkez:
                            o.append(f"   Xm  = {e.merkez[0]:.3f} {e.merkez[1]:.3f} {e.merkez[2]:.3f}")
                        if e.ters:
                            o.append(f"   Kayitli yon {e.set.kaynak} -> {e.set.hedef}; "
                                     "kesin ters cozum (ters_cevir_7) uygulandi.")
                else:  # yalniz elipsoit
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

    # ---------------- Model parametreleri ----------------
    def parametreleri_guncelle(self, *_):
        """Kaynak / hedef / model / epok degisince cagrilir: (kaynak, hedef, model) icin
        kayitli parametreyi bulur ve 'Model parametreleri' kartini doldurur."""
        i = self.ids
        if "p_manuel" not in i or "t2_epok" not in i:     # KV henuz tamamlanmadi
            return
        kay, hed, model = i.t2_kaynak.text, i.t2_hedef.text, i.t2_model.text
        kod = MODEL_KODU.get(model)
        try:
            epok = sayi(i.t2_epok.text)
        except ValueError:
            epok = None
        e = jz.parametre_bul(kay, hed, kod, epok)
        self._eslesme = e
        self.manuel_aktif = bool(i.p_manuel.active and kod in (jz.MODEL_BW, jz.MODEL_MB))

        yon = {"ileri": "kayitli yonde (ileri)",
               "ters": "kayitli setin TERSI (kesin ters cozum)",
               "zincir": f"zincir ({len(e.zincir)} adim)",
               "ozdes": "ozdeslik / parametresiz", "yok": "-"}[e.yon]
        baslik = [f"Kaynak: {kay}", f"Hedef: {hed}", f"Model: {model}",
                  f"Kaynak -> Hedef:  {kay}  ->  {hed}"]
        if self.manuel_aktif:
            baslik.append("Parametre kaynagi: Manuel giris (kullanici)")
        elif e.bulundu:
            baslik.append(f"Parametre kaynagi: {e.kurum}" + (f"  [{e.kod}]" if e.kod else ""))
            baslik.append(f"Yon: {yon}" + (f"   Konvansiyon: {e.konvansiyon}"
                                          if e.konvansiyon else "")
                          + (f"   Epok t = {e.epok:.2f}" if e.epok is not None else ""))
        else:
            baslik.append("Parametre kaynagi: - (kayit yok)")
        i.p_baslik.text = "\n".join(baslik)

        alanlar = (i.p_tx, i.p_ty, i.p_tz, i.p_d, i.p_rx, i.p_ry, i.p_rz)
        merkez_alan = (i.p_xm, i.p_ym, i.p_zm)
        if self.manuel_aktif:
            self.durum_tur = "bilgi"
            i.p_durum.text = ("Manuel parametre girisi aktif: hesapta kutulardaki degerler "
                              "kullanilir (kaynak -> hedef yonunde; gerekirse 'Ters yonde uygula').")
            i.p_ayrinti.text = ("Kayitli set mevcut; manuel girisi kapatinca otomatik degerler geri "
                                "gelir." if e.bulundu and e.T is not None else "")
            return

        if e.bulundu and e.T is not None:
            for w, v in zip(alanlar, (*e.T, e.D, *e.R)):
                w.text = _yaz(v)
            for w, v in zip(merkez_alan, e.merkez or ("", "", "")):
                w.text = f"{v:.3f}" if v != "" else ""
            i.p_konv.text = KONV_ADI[e.konvansiyon]
            i.p_ters.active = e.ters
            self.durum_tur = "iyi"
            i.p_durum.text = e.mesaj
        else:
            for w in alanlar + merkez_alan:       # BOS birak: 0 / ornek deger YAZMA
                w.text = ""
            i.p_ters.active = False
            if e.bulundu:                         # parametresiz model (yalniz elipsoit)
                self.durum_tur = "iyi"
                i.p_durum.text = e.mesaj
            else:
                self.durum_tur = "uyari"
                i.p_durum.text = (MANUEL_YOK if kod in (jz.MODEL_BW, jz.MODEL_MB) else
                                  e.mesaj + ("" if e.mesaj != jz.BULUNAMADI else
                                             "  (Manuel giris yalniz Bursa-Wolf / "
                                             "Molodensky-Badekas modellerinde yapilabilir.)"))
        i.p_ayrinti.text = "\n".join(e.ayrinti)

    def ornek_epsg(self):
        """EPSG Guidance Note 7-2 ornegi (Position Vector):
        WGS72 (3657660.66, 255768.55, 5201382.11) -> WGS84 (3657660.78, 255778.43, 5201387.75)
        Yalnizca TEST ornegidir: manuel giris olarak doldurulur, hicbir gercek
        kaynak-hedef dönüşümüne otomatik atanmaz."""
        i = self.ids
        i.t2_model.text, i.t2_tip.text = M_BW, "Kartezyen"
        i.t2_kaynak.text = i.t2_hedef.text = "WGS84 (G2139)"
        i.p_manuel.active = True
        self.parametreleri_guncelle()
        for w, v in zip((i.p_tx, i.p_ty, i.p_tz, i.p_d, i.p_rx, i.p_ry, i.p_rz),
                        ("0", "0", "4.5", "0.219", "0", "0", "0.554")):
            w.text = v
        i.p_konv.text = "PV (Position Vector)"
        i.p_ters.active = False
        i.t2_a.text, i.t2_b.text, i.t2_c.text = "3657660.66", "255768.55", "5201382.11"
        self.sekme_sec("datum")
        self.t2_donustur()
        i.p_durum.text = ("TEST ORNEGI (EPSG GN 7-2, WGS72 -> WGS84): manuel giris olarak "
                          "dolduruldu; gercek bir kaynak-hedef donusumu degildir.")


def _yaz(v):
    """Parametreyi kutuya yazmak icin: gereksiz sifirlar olmadan, -0 olmadan."""
    if abs(v) < 5e-10:
        return "0"
    return f"{v:.9f}".rstrip("0").rstrip(".")


class KoordinatApp(App):
    title = "Koordinat Dönüşümü"
    t = Tema()                         # renk token'lari; KV'de app.t.<ad>
    tema_secimi = StringProperty("sistem")

    # ---- tema: 'sistem' | 'light' | 'dark'; secim user_data_dir/tema.json'da hatirlanir ----
    def _tema_dosyasi(self):
        return os.path.join(self.user_data_dir, "tema.json")

    def tema_sec(self, secim):
        self.tema_secimi = secim
        koyu = sistem_koyu_mu() if secim == "sistem" else secim == "dark"
        self.t.uygula(koyu)
        Window.clearcolor = self.t.background
        try:
            with open(self._tema_dosyasi(), "w", encoding="utf-8") as f:
                json.dump({"tema": secim}, f)
        except OSError:
            pass

    def build(self):
        Window.softinput_mode = "below_target"   # Android'de klavye kutuyu ortmesin
        secim = os.environ.get("KOORD_TEMA")     # test / ekran goruntusu icin zorla
        if not secim:
            try:
                with open(self._tema_dosyasi(), encoding="utf-8") as f:
                    secim = json.load(f).get("tema", "sistem")
            except (OSError, ValueError):
                secim = "sistem"
        self.t.uygula(sistem_koyu_mu() if secim == "sistem" else secim == "dark")
        Window.clearcolor = self.t.background
        Builder.load_string(KV)
        kok = AnaPanel()
        kok.ids["tema_" + {"light": "acik", "dark": "koyu"}.get(secim, "sistem")].state = "down"
        self.tema_secimi = secim
        kok.parametreleri_guncelle()             # varsayilan secim icin parametreleri doldur
        # Test/ekran goruntusu icin: KOORD_SCREENSHOT=dosya.png verilirse kaydedip kapanir
        yol = os.environ.get("KOORD_SCREENSHOT")
        if yol:
            adimlar = [
                lambda: kok.t1_geo2cart(),
                lambda: (kok.sekme_sec("datum"), kok.t2_donustur()),
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


# KV icinde main.hx(...) olarak kullanilir
hx = hx

if __name__ == "__main__":
    KoordinatApp().run()
