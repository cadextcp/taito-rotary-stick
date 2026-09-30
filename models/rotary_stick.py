"""Taito "Aim n Fire" Rotary-Stick — druckbarer Nachbau (build123d, parametrisch).

Ausführen (aus dem CAD-Ordner):
    python models/rotary_stick.py

Aufbau nach Explosionszeichnung "Revolving Control Assembly (WWK00003)", von oben nach unten:

    Taito-Pos.  Nachbau (Druckteil / Kaufteil)
    1, 31       knopf + knopf_inlay         (Druck)   Drehknopf Ø45 mit Pfeil-Inlay
    3           scheibe                     (Druck)   Gleitscheibe auf dem Panel
    32 (+5/6/7) grundplatte                 (Druck)   Montageplatte, Lagerbuchse, Halter für
                                                      die Schnappkugel (Kugeldruckstück, radial)
    27 + 12     rotor                       (Druck)   Rastrad (8 Kerben) + Nocke in einem Teil,
                                                      mit 2 Madenschrauben auf der Achse geklemmt
    10          Druckfeder                  (Kauf)    drückt Rotor/Achse nach oben (Fire-Rückstellung)
    26 + 19     schalterdeck                (Druck)   4 Microtaster radial um die Nocke
    16 + 22     (am schalterdeck)                     Halter + Microtaster "Fire" unter dem Achsende

Funktion:
  * 8 Klicks: Kugeldruckstück rastet in 8 senkrechte Kerben (45°). Die Kerben laufen axial,
    daher darf die Achse zum Feuern ~2,5 mm nach unten gleiten, ohne dass die Rastung stört.
  * 8 Richtungen mit 4 Tastern: Die Nocke hat einen ~96°-Nocken. In den Hauptrichtungen
    drückt sie 1 Taster, in den Diagonalen 2 benachbarte (wie ein 8-Wege-Joystick).
  * Fire: Knopf drücken -> Achse gleitet runter -> Achsende drückt den Fire-Taster.
    Druckfeder im Rotor schiebt zurück; Anschlag oben = Lagerbuchse, unten = Schalterdeck.

Koordinaten: Z=0 ist die Oberseite der Grundplatte (liegt unter dem Panel). Mechanik hängt
nach unten (-Z). Rastkugel zeigt aus +X, Taster 0/1/2/3 liegen bei 0°/90°/180°/270°.
"""

import math
from pathlib import Path

from build123d import *

OUT = Path(__file__).resolve().parent.parent / "exports" / "rotary_stick"
OUT.mkdir(parents=True, exist_ok=True)

# =============================================================================
# Parameter (mm) — VOR DEM DRUCK AN DIE VORHANDENEN TEILE ANPASSEN
# =============================================================================
SHAFT_D = 8.0           # Achsdurchmesser (nachmessen!)
BORE_CLR = 0.3          # Spiel Achse <-> Lagerbohrung / Rotorbohrung

# Schnappkugel / Kugeldruckstück (Gewinde-Ausführung mit Mutter)
PLUNGER_M = 8.0         # Gewinde-Nenndurchmesser
PLUNGER_NUT_AF = 13.0   # Schlüsselweite der Mutter (M8 = 13)
PLUNGER_NUT_H = 6.5     # Mutterhöhe (M8 = 6,5)
BALL_D = 5.0            # Kugeldurchmesser
NOTCH_DEPTH = 1.5       # Tiefe der Rastkerben (mehr = härterer Klick)

# Microtaster (Omron V / Standardgröße, wie V-16539-3A5 / V10FL22)
SW_L, SW_H, SW_T = 27.8, 15.9, 10.3   # Länge, Höhe (Hebel->Anschlüsse), Dicke
SW_HOLE_PITCH = 22.2
SW_HOLE_FROM_BOTTOM = 5.1             # Lochmitte ab Anschlussseite
SW_SCREW = 3.2                        # Langloch-Breite (M3; bei M2.5 -> 2.8)
SLOT_TRAVEL = 4.0                     # +/- Justierweg der Taster
LEVER_TIP_OFF = 11.0                  # Hebelspitze liegt so weit vor der Gehäusemitte

# Panel / Knopf
PANEL_T = 3.0           # Dicke Bedienpanel (nur für Achslängen-Rechnung + Ansicht)
PUSH_TRAVEL = 3.0       # Weg bis zum Endanschlag (Fire löst bei ~1,5–2 mm aus)
KNOB_D, KNOB_H, KNOB_BORE_DEPTH = 45.0, 24.0, 18.0

# Grundplatte / Deck
PLATE, PLATE_T = 115.0, 4.0
PLATE_HOLE, PLATE_HOLE_POS = 5.0, 50.0   # Befestigung am Panel (M4/M5)
COL_POS, COL_R = 38.0, 5.0              # Säulen Grundplatte -> Deck
DECK = 90.0

# Abgeleitete Höhen (Ruhestellung)
Z_BOSS = -10.0                     # Unterkante Lagerbuchse = oberer Anschlag Rotor
Z_BALL = -16.0                     # Höhe der Rastkugel
DET_H, CAM_H = 14.0, 12.0
Z_DET_BOT = Z_BOSS - DET_H         # -24
Z_CAM_BOT = Z_DET_BOT - CAM_H      # -36
Z_DECK_TOP = Z_CAM_BOT - PUSH_TRAVEL   # -39
DECK_T = 4.0
Z_DECK_BOT = Z_DECK_TOP - DECK_T   # -43
Z_SHAFT_END = Z_DECK_BOT - 9.0     # -52

# Rastrad / Nocke
DET_R = 14.0
CAM_BASE_R, CAM_LOBE_R = 10.0, 16.0
CAM_FULL_HALF = 48.0     # Nocke voll über +/-48°
CAM_RAMP = 25.0          # dann 25° Rampe auf Grundkreis
SW_EDGE_R = 17.5         # Abstand Achse -> Hebelseite der Taster (nominal)
SW_PAD = 2.4             # Sockel unter den Tastern: Hebelmitte = Mitte des Nocken-Überdeckungsbereichs
Z_SW_MID = Z_DECK_TOP + SW_PAD + SW_T / 2
SPRING_POCKET_D, SPRING_POCKET_DEPTH = 12.3, 8.0

M3_NUT_AF, M3_NUT_H = 5.5, 2.4
M8_NUT_AF, M8_NUT_H = 13.0, 6.5
W28 = (8.4, 16.0, 1.6)             # Scheibe ISO 7089 8,4 zw. Rotor und Lagerbuchse (Taito Pos. 28)
W_M3 = (3.2, 7.0, 0.5)             # Scheibe ISO 7089 3,2
M3_HEAD_D, M3_HEAD_K = 5.6, 2.4    # Linsenkopf ISO 7045 M3

C, MIN, MAX = Align.CENTER, Align.MIN, Align.MAX


# =============================================================================
# Helfer
# =============================================================================
def polar_face(rfun, n=360, z=0.0):
    """Polares Profil als geschlossener Spline (glatte Fläche, keine Facettenkanten)."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = rfun(math.degrees(a))
        pts.append((r * math.cos(a), r * math.sin(a)))
    return Plane.XY.offset(z) * make_face(Wire([Spline(*pts, periodic=True)]))


def wrap(deg):
    return (deg + 180.0) % 360.0 - 180.0


def cam_r(deg):
    a = abs(wrap(deg))
    if a <= CAM_FULL_HALF:
        return CAM_LOBE_R
    if a >= CAM_FULL_HALF + CAM_RAMP:
        return CAM_BASE_R
    u = (a - CAM_FULL_HALF) / CAM_RAMP
    return CAM_BASE_R + (CAM_LOBE_R - CAM_BASE_R) * 0.5 * (1 + math.cos(math.pi * u))


NOTCH_W = BALL_D * 0.6   # halbe Kerbbreite (Bogenlänge)


def det_r(deg):
    a = abs(((deg + 22.5) % 45.0) - 22.5)          # Abstand zur nächsten Kerbe (°)
    u = math.radians(a) * DET_R                     # als Bogenlänge
    if u >= NOTCH_W:
        return DET_R
    return DET_R - NOTCH_DEPTH * math.cos(math.pi * u / (2 * NOTCH_W)) ** 2


def hole_x_teardrop(r, x0, x1, y, z, tip=-1):
    """Waagrechte Bohrung entlang X als Tropfen (Spitze in Druckrichtung 'oben')."""
    k = 0.7071 * r
    sk = Circle(r) + Polygon((k, tip * k), (0, tip * 1.4142 * r), (-k, tip * k), (0, 0), align=None)
    return Pos(0, y, z) * extrude(Plane.YZ.offset(x0) * sk, amount=x1 - x0)


def radial(phi_deg, d, s):
    """Punkt bei Radius d und tangentialem Versatz s für Richtung phi."""
    p = math.radians(phi_deg)
    return (d * math.cos(p) - s * math.sin(p), d * math.sin(p) + s * math.cos(p))


# =============================================================================
# 32  Grundplatte mit Lagerbuchse, Säulen und Kugeldruckstück-Halter
# =============================================================================
def make_grundplatte():
    p = Box(PLATE, PLATE, PLATE_T, align=(C, C, MAX))
    p = fillet(p.edges().filter_by(Axis.Z), 6)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p -= Pos(sx * PLATE_HOLE_POS, sy * PLATE_HOLE_POS, 0) * Cylinder(PLATE_HOLE / 2, 20)
    # Lagerbuchse
    p += Pos(0, 0, Z_BOSS + W28[2]) * Cylinder(11, -PLATE_T - Z_BOSS - W28[2], align=(C, C, MIN))
    # Säulen zum Schalterdeck
    col_h = -PLATE_T - Z_DECK_TOP
    for sx in (-1, 1):
        for sy in (-1, 1):
            col = Pos(sx * COL_POS, sy * COL_POS, Z_DECK_TOP) * Cylinder(COL_R, col_h, align=(C, C, MIN))
            col -= Pos(sx * COL_POS, sy * COL_POS, Z_DECK_TOP) * Cylinder(1.25, 14, align=(C, C, MIN))
            p += col
    # Halteblock für das Kugeldruckstück (radial aus +X, wie Taito Pos. 5/6/7)
    blk_bot = Z_DET_BOT + 1.0
    p += Pos(DET_R + 1.5, 0, blk_bot) * Box(17, 20, -PLATE_T - blk_bot, align=(MIN, C, MIN))
    # Gewindebohrung (Spiel) als Tropfen, Spitze zeigt beim Druck nach oben (= -Z)
    p -= hole_x_teardrop((PLUNGER_M + 0.4) / 2, DET_R - 2, 60, 0, Z_BALL, tip=-1)
    # Mutterschlitz von unten eingeschoben (Mutter = Kontermutter/Halter innen)
    nut_x = DET_R + 1.5 + 8.5
    nut_ac = PLUNGER_NUT_AF / math.cos(math.radians(30)) + 0.4
    nut = extrude(Plane.YZ.offset(nut_x - (PLUNGER_NUT_H + 0.3) / 2)
                  * RegularPolygon(nut_ac / 2, 6, rotation=30), amount=PLUNGER_NUT_H + 0.3)
    nut = Pos(0, 0, Z_BALL) * nut
    nut += Pos(nut_x, 0, blk_bot - 1) * Box(PLUNGER_NUT_H + 0.3, PLUNGER_NUT_AF + 0.3,
                                            Z_BALL - blk_bot + 1, align=(C, C, MIN))
    p -= nut
    # Achsbohrung
    p -= Cylinder((SHAFT_D + BORE_CLR) / 2, 100)
    p -= Pos(0, 0, 0) * Cylinder((SHAFT_D + BORE_CLR) / 2 + 0.8, 1.6, align=(C, C, MAX))  # Fase-Ersatz
    return p


# =============================================================================
# 27 + 12  Rotor: Rastrad (8 Kerben) + Nocke, Federtasche unten
# =============================================================================
def make_rotor():
    r = extrude(polar_face(det_r, z=Z_DET_BOT), amount=DET_H)
    r += extrude(polar_face(cam_r, z=Z_CAM_BOT), amount=CAM_H)
    r -= Cylinder((SHAFT_D + BORE_CLR) / 2, 200)
    r -= Pos(0, 0, Z_CAM_BOT) * Cylinder(SPRING_POCKET_D / 2, SPRING_POCKET_DEPTH, align=(C, C, MIN))
    # 2 Madenschrauben M3 zwischen den Kerben, unterhalb der Kugelbahn, mit Mutterschlitz von oben
    z_ss = Z_DET_BOT + 3.0
    for ang in (22.5, 112.5):
        screw = Rot(0, 0, ang) * Pos(0, 0, z_ss) * Rot(0, 90, 0) * Cylinder(1.65, 30, align=(C, C, MIN))
        nut_r = SHAFT_D / 2 + 1.5 + M3_NUT_H / 2 + 0.5
        slot = Rot(0, 0, ang) * Pos(nut_r, 0, z_ss - 3.4) * Box(M3_NUT_H + 0.3, M3_NUT_AF + 0.3,
                                                              Z_BOSS - z_ss + 3.4, align=(C, C, MIN))
        r -= screw + slot
    return r


# =============================================================================
# 26 + 16  Schalterdeck mit 4 Richtungs-Tastern und Fire-Halter
# =============================================================================
FIRE_Y0 = -SW_T / 2            # Anlagefläche des Fire-Tasters
FIRE_TOP = Z_SHAFT_END - 4.5   # Oberkante Fire-Taster (Hebel ~4 mm darüber)
TAB_X0, TAB_X1, TAB_T = -29.0, 7.0, 4.0
TAB_BOT = FIRE_TOP - SW_H - 4.0


def switch_holes_s():
    c = -LEVER_TIP_OFF
    return (c + SW_HOLE_PITCH / 2, c - SW_HOLE_PITCH / 2)


def make_deck():
    d = Box(DECK, DECK, DECK_T, align=(C, C, MAX))
    d = Pos(0, 0, Z_DECK_TOP) * fillet(d.edges().filter_by(Axis.Z), 6)
    for sx in (-1, 1):
        for sy in (-1, 1):
            d -= Pos(sx * COL_POS, sy * COL_POS, 0) * Cylinder(1.7, 200)
    # Führungsbuchse unten
    d += Pos(0, 0, Z_DECK_BOT) * Cylinder(9, 5, align=(C, C, MAX))
    # Fire-Halter (senkrechte Lasche) + 2 Rippen
    d += Pos(TAB_X0, FIRE_Y0, TAB_BOT) * Box(TAB_X1 - TAB_X0, TAB_T, Z_DECK_BOT - TAB_BOT,
                                            align=(MIN, MAX, MIN))
    for gx in (TAB_X0 + 1.5, TAB_X1 - 1.5):
        tri = Polygon((0, 0), (-12, 0), (0, -16), align=None)   # (y, z) relativ
        g = extrude(Plane.YZ.offset(gx - 1.5) * tri, amount=3)
        d += Pos(0, FIRE_Y0 - TAB_T, Z_DECK_BOT) * g
    # Langlöcher Fire-Taster (senkrecht)
    z_holes = FIRE_TOP - SW_H + SW_HOLE_FROM_BOTTOM
    for s in switch_holes_s():
        slot = extrude(Plane.XZ.offset(0) * Pos(s, z_holes) *
                       SlotCenterToCenter(2 * SLOT_TRAVEL, SW_SCREW, rotation=90), amount=40, both=True)
        d -= slot
    # Sockel unter den 4 Richtungs-Tastern
    for k in range(4):
        pad = Pos(SW_EDGE_R + 1.0, -LEVER_TIP_OFF, Z_DECK_TOP) * Box(
            SW_H + SLOT_TRAVEL - 1.0, SW_L + 2, SW_PAD, align=(MIN, C, MIN))
        d += Rot(0, 0, 90 * k) * pad
    # Langlöcher 4 Richtungs-Taster (radial)
    d_hole = SW_EDGE_R + SW_H - SW_HOLE_FROM_BOTTOM
    for k in range(4):
        phi = 90 * k
        for s in switch_holes_s():
            x, y = radial(phi, d_hole, s)
            d -= Pos(x, y, Z_DECK_BOT - 1) * extrude(
                SlotCenterToCenter(2 * SLOT_TRAVEL, SW_SCREW, rotation=phi), amount=DECK_T + SW_PAD + 2)
    # Achsdurchgang + Federsitz
    d -= Cylinder((SHAFT_D + 0.5) / 2, 300)
    d -= Pos(0, 0, Z_DECK_TOP) * Cylinder(SPRING_POCKET_D / 2, 1.5, align=(C, C, MAX))
    return d


# =============================================================================
# 1 / 31 / 3  Knopf, Inlay, Gleitscheibe  (lokal: Z=0 Unterseite)
# =============================================================================
INLAY_D, INLAY_T = 36.0, 1.6


def arrow_sketch(scale=1.0):
    pts = [(0, 11), (-8, 2), (-3.5, 2), (-3.5, -10), (3.5, -10), (3.5, 2), (8, 2)]
    return Polygon(*[(x * scale, y * scale) for x, y in pts], align=None)


def make_knopf():
    k = Cylinder(KNOB_D / 2, KNOB_H, align=(C, C, MIN))
    k = chamfer(k.edges().group_by(Axis.Z)[-1], 1.2)
    k = chamfer(k.edges().group_by(Axis.Z)[0], 0.8)
    n = 60
    for i in range(n):
        a = 360 * i / n
        k -= Rot(0, 0, a) * Pos(KNOB_D / 2, 0, 5) * Rot(0, 0, 45) * Box(1.3, 1.3, KNOB_H, align=(C, C, MIN))
    k -= Pos(0, 0, KNOB_H) * Cylinder(INLAY_D / 2 + 0.2, INLAY_T, align=(C, C, MAX))
    k -= Cylinder((SHAFT_D + 0.15) / 2, KNOB_BORE_DEPTH, align=(C, C, MIN))
    # Madenschraube M3 + Mutterschlitz von unten
    zs = 7.0
    k -= Pos(0, 0, zs) * Rot(0, 90, 0) * Cylinder(1.65, 30, align=(C, C, MIN))
    k -= Pos(SHAFT_D / 2 + 3.2, 0, 0) * Box(M3_NUT_H + 0.3, M3_NUT_AF + 0.3, zs + 3.4, align=(C, C, MIN))
    # Hohlraum oben (spart Material, bleibt unter dem Inlay geschlossen)
    return k


def make_inlay():
    i = Cylinder(INLAY_D / 2, INLAY_T, align=(C, C, MIN))
    i -= Pos(0, 0, INLAY_T - 0.6) * extrude(arrow_sketch(), amount=1)
    return i


def make_scheibe():
    return Cylinder(20, 1.5, align=(C, C, MIN)) - Cylinder((SHAFT_D + 0.6) / 2, 5, align=(C, C, MIN))


# =============================================================================
# Kaufteile als Platzhalter (nur für Ansicht / Kollisionsprüfung)
# =============================================================================
def cam_support(phi, theta, s_min, s_max):
    """Wie weit ragt die Nocke (Rotorwinkel theta) in Richtung phi auf den Hebelbereich?"""
    best = 0.0
    for i in range(720):
        a = i * 0.5
        r = cam_r(a - theta)
        rel = math.radians(a - phi)
        x, y = r * math.cos(rel), r * math.sin(rel)
        if s_min <= y <= s_max:
            best = max(best, x)
    return best


LEVER_S0, LEVER_S1 = -LEVER_TIP_OFF - SW_L / 2 + 2, -LEVER_TIP_OFF + SW_L / 2 + 3  # Hebel-Bereich
LEVER_FREE = 5.0


def make_switch(lever_h):
    """Microtaster lokal: Hebelseite bei x=0 (zeigt -X), Körper x in [0,SW_H], s entlang Y."""
    c = -LEVER_TIP_OFF
    body = Pos(0, c, 0) * Box(SW_H, SW_L, SW_T, align=(MIN, C, C))
    for s in switch_holes_s():
        body -= Pos(SW_H - SW_HOLE_FROM_BOTTOM, s, 0) * Cylinder(1.55, 20)
    for s in (c - 10, c, c + 10):
        body += Pos(SW_H, s, 0) * Box(7, 4.8, 0.6, align=(MIN, C, C))
    h0, h1 = 0.8, lever_h
    s0, s1 = LEVER_S0, LEVER_S1
    ln = math.hypot(s1 - s0, h1 - h0)
    ang = math.degrees(math.atan2(h1 - h0, s1 - s0))
    lever = Pos(-h0, s0, 0) * Rot(0, 0, ang) * Box(0.5, ln, 4.8, align=(MAX, MIN, C))
    return body, lever


def lever_height(phi, theta):
    sup = cam_support(phi, theta, LEVER_S0, LEVER_S1)
    return max(0.8, min(LEVER_FREE, SW_EDGE_R - sup))


# =============================================================================
# Bauen
# =============================================================================
grund = make_grundplatte()
rotor = make_rotor()
deck = make_deck()
knopf = make_knopf()
inlay = make_inlay()
scheibe = make_scheibe()

z_scheibe = PANEL_T
z_knopf = PANEL_T + 1.5 + PUSH_TRAVEL + 0.5
shaft_top = z_knopf + KNOB_BORE_DEPTH
shaft_len = shaft_top - Z_SHAFT_END

# --- Plausibilitätsprüfungen ---------------------------------------------------
print("Wahrheitstabelle (Nocke -> Taster 0/90/180/270°), Hebel-Andrück-Maß in mm:")
table = {}
for pos in range(8):
    theta = pos * 45
    sups = [cam_support(90 * k, theta, LEVER_S0, LEVER_S1) for k in range(4)]
    pressed = [s > (CAM_LOBE_R - 1.0) for s in sups]
    table[pos] = pressed
    print(f"  {theta:3d}°: " + "  ".join(f"{'X' if p else '.'}({s:4.1f})" for p, s in zip(pressed, sups)))
worst_released = max(s for t in range(8) for k, s in enumerate(
    [cam_support(90 * k, t * 45, LEVER_S0, LEVER_S1) for k in range(4)]) if s <= CAM_LOBE_R - 1.0)
print(f"  gedrückt = {CAM_LOBE_R:.1f}, frei max = {worst_released:.1f}  -> Schaltfenster "
      f"{CAM_LOBE_R - worst_released:.1f} mm")
patterns = {tuple(v) for v in table.values()}
assert len(patterns) == 8, "8 Positionen müssen 8 verschiedene Schaltmuster ergeben"
assert all(1 <= sum(v) <= 2 for v in table.values())

for push in (0.0, PUSH_TRAVEL):
    rp = Pos(0, 0, -push) * rotor
    for name, other in (("grundplatte", grund), ("deck", deck)):
        v = (rp & other).volume
        assert v < 0.01, f"Kollision Rotor/{name} bei Hub {push}: {v:.2f} mm³"
for k in range(4):
    for pos in range(8):
        body, _ = make_switch(LEVER_FREE)
        body = Pos(0, 0, Z_SW_MID) * Rot(0, 0, 90 * k) * Pos(SW_EDGE_R, 0, 0) * body
        assert (body & (Rot(0, 0, pos * 45) * rotor)).volume < 0.01
        assert (body & grund).volume < 0.01
print("Kollisionsprüfung: OK (Rotor frei in Ruhe und gedrückt, Taster frei)")

# --- Axialer Hub darf Rastung und Abtastung nicht beeinflussen ---------------------
LEVER_W = 4.8
lever_lo = Z_SW_MID - LEVER_W / 2
lever_hi = Z_SW_MID + LEVER_W / 2
z_ss = Z_DET_BOT + 3.0
print(f"Hub-Prüfung (0 … {PUSH_TRAVEL} mm):")
for push in (0.0, PUSH_TRAVEL):
    cam_lo, cam_hi = Z_CAM_BOT - push, Z_DET_BOT - push
    det_lo, det_hi = Z_DET_BOT - push, Z_BOSS - push
    # Nocke überdeckt die ganze Hebelbreite -> gleiche Schaltmuster in jeder Hubstellung
    assert cam_lo <= lever_lo - 0.5 and cam_hi >= lever_hi + 0.5, f"Nocke verlässt Hebel bei Hub {push}"
    # Kugel läuft vollständig in der (senkrechten) Kerbe, nicht über Madenschrauben-Löcher
    assert det_lo + 0.5 <= Z_BALL - BALL_D / 2 and Z_BALL + BALL_D / 2 <= det_hi - 0.5, f"Kugel verlässt Rastrad bei Hub {push}"
    assert Z_BALL - BALL_D / 2 > z_ss + 1.65 - push + 0.5, f"Kugel läuft über Madenschraube bei Hub {push}"
    print(f"  Hub {push:3.1f}: Nocke Z[{cam_lo:.1f},{cam_hi:.1f}] deckt Hebel Z[{lever_lo:.1f},{lever_hi:.1f}], "
          f"Rastrad Z[{det_lo:.1f},{det_hi:.1f}] deckt Kugel Z[{Z_BALL - BALL_D / 2:.1f},{Z_BALL + BALL_D / 2:.1f}]")
spring_rest = (Z_CAM_BOT + SPRING_POCKET_DEPTH) - (Z_DECK_TOP - 1.5)
print(f"  Feder: Einbaulänge {spring_rest:.1f} mm (Ruhe) / {spring_rest - PUSH_TRAVEL:.1f} mm (gedrückt)")
print(f"  Fire: Achsende {Z_SHAFT_END:.1f} -> {Z_SHAFT_END - PUSH_TRAVEL:.1f}, Taster-Oberkante {FIRE_TOP:.1f}")


# --- Normteile: Unterlegscheiben, Schrauben, Muttern ------------------------------
def washer(w):
    di, do, t = w
    return Cylinder(do / 2, t, align=(C, C, MIN)) - Cylinder(di / 2, 3 * t)


def hexnut(af, h, d):
    n = extrude(RegularPolygon(af / math.cos(math.radians(30)) / 2, 6), amount=h)
    return chamfer(n.edges().filter_by(Axis.Z, reverse=True), 0.3) - Cylinder(d / 2, 3 * h)


def pan_screw(length, d=3.0):
    """Auflagefläche bei z=0, Kopf nach +Z, Schaft nach -Z."""
    head = fillet(Cylinder(M3_HEAD_D / 2, M3_HEAD_K, align=(C, C, MIN)).edges().group_by(Axis.Z)[-1], 1.0)
    head -= Pos(0, 0, M3_HEAD_K) * (Box(3, 0.6, 2.4) + Box(0.6, 3, 2.4))
    return head + Cylinder(d / 2, length, align=(C, C, MAX))


hardware = []   # (label, shape, farbe)
hardware.append(("u_scheibe_28", Pos(0, 0, Z_BOSS) * washer(W28), "silver"))
z_sw_top = Z_DECK_TOP + SW_PAD + SW_T
d_hole = SW_EDGE_R + SW_H - SW_HOLE_FROM_BOTTOM
for k in range(4):
    for j, sv in enumerate(switch_holes_s()):
        x, y = radial(90 * k, d_hole, sv)
        n = f"{k}{j}"
        hardware += [
            (f"u_scheibe_m3_o{n}", Pos(x, y, z_sw_top) * washer(W_M3), "silver"),
            (f"schraube_m3x20_{n}", Pos(x, y, z_sw_top + W_M3[2]) * pan_screw(20), "dimgray"),
            (f"u_scheibe_m3_u{n}", Pos(x, y, Z_DECK_BOT - W_M3[2]) * washer(W_M3), "silver"),
            (f"mutter_m3_{n}", Pos(x, y, Z_DECK_BOT - W_M3[2] - M3_NUT_H) * hexnut(M3_NUT_AF, M3_NUT_H, 3.0), "dimgray"),
        ]
for sx in (-1, 1):
    for sy in (-1, 1):
        x, y = sx * COL_POS, sy * COL_POS
        hardware += [
            (f"u_scheibe_m3_d{sx}{sy}", Pos(x, y, Z_DECK_BOT - W_M3[2]) * washer(W_M3), "silver"),
            (f"schraube_m3x10_{sx}{sy}", Pos(x, y, Z_DECK_BOT - W_M3[2]) * Rot(180, 0, 0) * pan_screw(10), "dimgray"),
        ]
z_fh = FIRE_TOP - SW_H + SW_HOLE_FROM_BOTTOM
for j, sv in enumerate(switch_holes_s()):
    y_tab = FIRE_Y0 - TAB_T
    hardware += [
        (f"u_scheibe_m3_f{j}a", Pos(sv, y_tab, z_fh) * Rot(90, 0, 0) * washer(W_M3), "silver"),
        (f"schraube_m3x20_f{j}", Pos(sv, y_tab - W_M3[2], z_fh) * Rot(90, 0, 0) * pan_screw(20), "dimgray"),
        (f"u_scheibe_m3_f{j}b", Pos(sv, SW_T / 2, z_fh) * Rot(-90, 0, 0) * washer(W_M3), "silver"),
        (f"mutter_m3_f{j}", Pos(sv, SW_T / 2 + W_M3[2], z_fh) * Rot(-90, 0, 0)
         * hexnut(M3_NUT_AF, M3_NUT_H, 3.0), "dimgray"),
    ]
nut_x = DET_R + 1.5 + 8.5
hardware.append(("mutter_m8", Pos(nut_x, 0, Z_BALL) * Rot(0, 90, 0) * Pos(0, 0, -M8_NUT_H / 2)
                 * Rot(0, 0, 30) * hexnut(M8_NUT_AF, M8_NUT_H, PLUNGER_M), "dimgray"))
for lbl, hw_shape, _ in hardware:
    for other_name, other in (("grundplatte", grund), ("rotor", rotor), ("deck", deck)):
        if other_name == "grundplatte" and lbl.startswith(("mutter_m8", "schraube_m3x10")):
            continue   # M8-Mutter sitzt im Schlitz, M3x10 schneiden ins Kernloch der Säulen
        assert (hw_shape & other).volume < 0.01, f"Kollision {lbl} / {other_name}"
print(f"Normteile: {len(hardware)} Stück, kollisionsfrei")

# --- Druckteile exportieren (in Druckorientierung) -----------------------------
print_parts = {
    "grundplatte": Rot(180, 0, 0) * grund,            # Plattenoberseite aufs Bett
    "rotor": Rot(180, 0, 0) * rotor,                  # Oberseite aufs Bett
    "schalterdeck": Rot(180, 0, 0) * deck,            # Deckoberseite aufs Bett, Lasche nach oben
    "knopf": knopf,
    "knopf_inlay": inlay,
    "scheibe": scheibe,
}
for name, part in print_parts.items():
    bb = part.bounding_box()
    part = Pos(-bb.center().X, -bb.center().Y, -bb.min.Z) * part
    export_stl(part, str(OUT / f"{name}.stl"))
    export_step(part, str(OUT / f"{name}.step"))
    print(f"  {name:13s} {part.volume / 1000:6.1f} cm³  -> {name}.stl")

# --- Baugruppe (Ruhestellung, Position 0°) ---------------------------------------
def colored(shape, label, color):
    shape.label, shape.color = label, Color(color)
    return shape


asm = [
    colored(grund, "grundplatte", "gray"),
    colored(rotor, "rotor", "orange"),
    colored(deck, "schalterdeck", "gray"),
    colored(Pos(0, 0, z_knopf) * knopf, "knopf", "silver"),
    colored(Pos(0, 0, z_knopf + KNOB_H - INLAY_T) * Rot(0, 0, -90) * inlay, "inlay", "red"),  # Pfeil -> +X = Nocken
    colored(Pos(0, 0, z_scheibe) * scheibe, "scheibe", "black"),
    colored(Pos(0, 0, Z_SHAFT_END) * Cylinder(SHAFT_D / 2, shaft_len, align=(C, C, MIN)), "achse", "lightsteelblue"),
    colored(Pos(DET_R - NOTCH_DEPTH + BALL_D / 2, 0, Z_BALL) * Sphere(BALL_D / 2), "kugel", "lightsteelblue"),
    colored(Pos(DET_R - NOTCH_DEPTH + BALL_D / 2, 0, Z_BALL) * Rot(0, 90, 0)
            * Cylinder(PLUNGER_M / 2, 19, align=(C, C, MIN)), "kugeldruckstueck", "gold"),
    colored(Pos(0, 0, Z_DECK_TOP - 1.5) * (Cylinder(5.5, Z_CAM_BOT + SPRING_POCKET_DEPTH - Z_DECK_TOP + 1.5,
            align=(C, C, MIN)) - Cylinder(4.6, 100)), "feder", "lightsteelblue"),
]
for k in range(4):
    body, lever = make_switch(lever_height(90 * k, 0))
    t = Pos(0, 0, Z_SW_MID) * Rot(0, 0, 90 * k) * Pos(SW_EDGE_R, 0, 0)
    asm += [colored(t * body, f"taster_{k}", "dimgray"), colored(t * lever, f"hebel_{k}", "white")]
# Fire-Taster: Hebelseite oben (+Z), Länge entlang X, Dicke entlang Y, liegt an der Lasche an
FIRE_LOC = Plane((0, 0, FIRE_TOP), x_dir=(0, 0, -1), z_dir=(0, -1, 0)).location
body, lever = make_switch(Z_SHAFT_END - FIRE_TOP)
asm += [colored(FIRE_LOC * body, "taster_fire", "dimgray"), colored(FIRE_LOC * lever, "hebel_fire", "white")]
assert (FIRE_LOC * body & deck).volume < 0.01, "Fire-Taster kollidiert mit Lasche"
asm += [colored(shape, lbl, col) for lbl, shape, col in hardware]

export_step(Compound(children=asm), str(OUT / "baugruppe.step"))
print(f"\nBenötigte Achslänge (Panel {PANEL_T} mm): {shaft_len:.1f} mm "
      f"(Achsende {abs(Z_SHAFT_END):.0f} mm unter Plattenoberkante, "
      f"{shaft_top - PANEL_T:.1f} mm über Panel)")
