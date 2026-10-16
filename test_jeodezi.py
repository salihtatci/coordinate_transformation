"""
test_jeodezi.py - cekirdegin dogrulugunu bilinen orneklerle kontrol eder.
Calistirma:  python test_jeodezi.py
"""
import math
import jeodezi as jz


def yakin(a, b, tol):
    return all(abs(x - y) <= tol for x, y in zip(a, b))


def test_gidis_donus():
    """Cografi -> Kartezyen -> Cografi kapanmasi (her iki ters yontem)."""
    for el in jz.ELIPSOITLER:
        for phi, lam, h in [(0, 0, 0), (39.925, 32.8369, 938), (-33.9, 151.2, 50),
                            (89.9999, -120, 3000), (-45, -179.9, -30)]:
            X = jz.geo_to_cart(phi, lam, h, el)
            for yon in ("iteratif", "bowring"):
                p2, l2, h2, _ = jz.cart_to_geo(*X, el, yon)
                assert abs(p2 - phi) < 1e-9 and abs(l2 - lam) < 1e-9 and abs(h2 - h) < 1e-4, (el, yon, phi)
    print("OK  gidis-donus (tum elipsoitler, iki yontem)")


def test_epsg_bursa_wolf():
    """EPSG Guidance Note 7-2: Position Vector ve Coordinate Frame ornekleri."""
    X1 = (3657660.66, 255768.55, 5201382.11)
    beklenen = (3657660.78, 255778.43, 5201387.75)
    pv = jz.bursa_wolf(X1, 0, 0, 4.5, 0.219, 0, 0, 0.554, "PV")
    cf = jz.bursa_wolf(X1, 0, 0, 4.5, 0.219, 0, 0, -0.554, "CF")
    assert yakin(pv, beklenen, 0.01) and yakin(cf, beklenen, 0.01), (pv, cf)
    geri = jz.ters_cevir_7(pv, jz.bursa_wolf, 0, 0, 4.5, 0.219, 0, 0, 0.554, konvansiyon="PV")
    assert yakin(geri, X1, 1e-6)
    print("OK  EPSG 7-2 Bursa-Wolf (PV/CF) + kesin ters")


def test_mb_bw_esdegerligi():
    """Merkez = 0 iken Molodensky-Badekas == Bursa-Wolf olmali."""
    X = (4116037.2588, 2656358.3524, 4072204.7958)
    p = (12.3, -45.6, 7.8, 1.5, 0.3, -0.7, 1.1)
    assert yakin(jz.bursa_wolf(X, *p), jz.molodensky_badekas(X, *p, (0, 0, 0)), 1e-9)
    print("OK  Molodensky-Badekas(merkez=0) == Bursa-Wolf")


def test_wgs84_grs80():
    """Ayni XYZ: WGS84 ve GRS80 cografi koordinatlari mm-alti farkli olmali."""
    X = jz.geo_to_cart(45, 30, 100, "GRS80")
    p1, l1, h1, _ = jz.cart_to_geo(*X, "GRS80")
    p2, l2, h2, _ = jz.cart_to_geo(*X, "WGS84")
    assert abs(h1 - h2) < 0.0002 and abs(p1 - p2) * 3600 < 1e-4
    print(f"OK  WGS84-GRS80 farki: dh = {(h2-h1)*1000:.4f} mm, dphi = {(p2-p1)*3600*1e6:.2f} mikro-sn")


def test_itrf_zincir_kapanmasi():
    """A -> B -> A gidis-donusu ~0 olmali; t0'da hizlarin etkisi olmamali."""
    X = (4116037.2588, 2656358.3524, 4072204.7958)
    for a, b in [("ITRF2020", "ITRF96 (TUREF)"), ("WGS84 (G1762)", "ETRF2000 (ETRS89)"),
                 ("ITRF2014", "ITRF2005")]:
        Y, _ = jz.sistemler_arasi(X, a, b, 2025.0)
        Z, _ = jz.sistemler_arasi(Y, b, a, 2025.0)
        assert yakin(X, Z, 1e-4), (a, b)
    h = jz.DONUSUMLER[("ITRF2014", "ITRF2008")]
    assert yakin(h.uygula(X, h.t0, True), h.uygula(X, 0, False), 1e-12)
    print("OK  ITRF zincir gidis-donus ve t0 kontrolu")


if __name__ == "__main__":
    test_gidis_donus()
    test_epsg_bursa_wolf()
    test_mb_bw_esdegerligi()
    test_wgs84_grs80()
    test_itrf_zincir_kapanmasi()
    print("\nTum testler gecti.")
