"""Bemaßte Baugruppenzeichnung (A2, M 1:1, Projektionsmethode 1) mit Stückliste.

    python scripts/drawing_rotary.py
    -> exports/rotary_stick/zeichnung_baugruppe.pdf / .png

Ansichten per HLR (verdeckte Kanten entfernt) aus dem build123d-Modell, Bemaßung in matplotlib
(Papierkoordinaten in mm, 1 Einheit = 1 mm auf dem Blatt).
"""

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.patches import Circle as MCircle, Polygon as MPolygon, Rectangle

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "models"))
import rotary_stick as rs  # noqa: E402
from build123d import Box, Compound, GeomType, Pos  # noqa: E402

SHEET_W, SHEET_H = 594.0, 420.0
PT = 72 / 25.4                      # mm -> pt
LW_THICK, LW_THIN = 0.5 * PT, 0.25 * PT
TXT = 3.5 * PT                      # Schrifthöhe 3,5 mm
FONT = "DejaVu Sans"

fig = plt.figure(figsize=(SHEET_W / 25.4, SHEET_H / 25.4))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, SHEET_W); ax.set_ylim(0, SHEET_H); ax.set_aspect("equal"); ax.axis("off")


def fmt(v):
    s = f"{v:.1f}".rstrip("0").rstrip(".")
    return s.replace(".", ",").replace("-", "−")


def text(x, y, s, size=TXT, **kw):
    kw.setdefault("ha", "center"); kw.setdefault("va", "center")
    ax.text(x, y, s, fontsize=size, family=FONT, **kw)


# =============================================================================
# Ansichten (HLR)
# =============================================================================
MODEL = Compound([s for s in rs.asm])


def hlr(origin, up):
    vis, _ = MODEL.project_to_viewport(origin, up, (0, 0, 0))
    segs = []
    for e in vis:
        if e.geom_type == GeomType.LINE:
            ts = [0.0, 1.0]
        else:
            ts = np.linspace(0, 1, max(8, int(e.length / 0.4)))
        pts = [e @ t for t in ts]
        segs.append([(p.X, p.Y) for p in pts])
    return segs


def draw_view(segs, ox, oy, lw=LW_THICK):
    ax.add_collection(LineCollection([[(x + ox, y + oy) for x, y in s] for s in segs],
                                     colors="black", linewidths=lw, capstyle="round"))


def centerline(p1, p2):
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="black", lw=LW_THIN, dashes=(12, 2, 1.5, 2))


def phantom_rect(x0, y0, w, h):
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, lw=LW_THIN, ls=(0, (12, 2, 1.5, 2, 1.5, 2))))


# =============================================================================
# Bemaßung
# =============================================================================
def arrowhead(tip, d):
    d = np.array(d, float) / np.linalg.norm(d)
    n = np.array([-d[1], d[0]])
    tip = np.array(tip, float)
    base = tip - 3.0 * d
    ax.add_patch(MPolygon([tip, base + 0.5 * n, base - 0.5 * n], closed=True, color="black", lw=0))


def line(p1, p2, lw=LW_THIN):
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color="black", lw=lw, solid_capstyle="butt")


def hdim(x1, y1, x2, y2, yd, label):
    """Horizontale Maßlinie bei yd zwischen den Punkten (x1,y1) und (x2,y2)."""
    for x, y in ((x1, y1), (x2, y2)):
        sgn = 1 if yd > y else -1
        line((x, y + sgn * 1.0), (x, yd + sgn * 2.0))
    if abs(x2 - x1) >= 12:
        line((x1, yd), (x2, yd))
        arrowhead((x1, yd), (-1, 0)); arrowhead((x2, yd), (1, 0))
    else:
        line((x1 - 8, yd), (x2 + 8, yd))
        arrowhead((x1, yd), (1, 0)); arrowhead((x2, yd), (-1, 0))
    text((x1 + x2) / 2, yd + 1.0, label, va="bottom")


def vdim(x1, y1, x2, y2, xd, label):
    for x, y in ((x1, y1), (x2, y2)):
        sgn = 1 if xd > x else -1
        line((x + sgn * 1.0, y), (xd + sgn * 2.0, y))
    if abs(y2 - y1) >= 12:
        line((xd, y1), (xd, y2))
        arrowhead((xd, y1), (0, -1 if y1 < y2 else 1)); arrowhead((xd, y2), (0, 1 if y2 > y1 else -1))
    else:
        lo, hi = min(y1, y2), max(y1, y2)
        line((xd, lo - 8), (xd, hi + 8))
        arrowhead((xd, lo), (0, 1)); arrowhead((xd, hi), (0, -1))
    text(xd - 1.0, (y1 + y2) / 2, label, rotation=90, ha="right")


def leader(p, q, label, ha="left"):
    """Hinweislinie vom Bauteil p zum Text bei q (mit Punkt am Bauteil)."""
    line(p, q); line(q, (q[0] + (12 if ha == "left" else -12), q[1]))
    ax.add_patch(MCircle(p, 0.6, color="black"))
    text(q[0] + (1 if ha == "left" else -1), q[1] + 0.8, label, ha=ha, va="bottom")


def ordinates(items, ox, oy, x_ext, x_txt):
    """Koordinatenbemaßung (Höhen) mit Nullpunkt; items = [(z, x_feature)], Text links."""
    items = sorted(items, key=lambda t: -t[0])
    ty, last = [], None
    for z, _ in items:
        y = oy + z
        if last is not None and y > last - 5.0:
            y = last - 5.0
        ty.append(y); last = y
    shift = (sum(oy + z for z, _ in items) - sum(ty)) / len(ty)       # Gruppe mittig halten
    ty = [y + shift for y in ty]
    for i in range(len(ty) - 2, -1, -1):
        ty[i] = max(ty[i], ty[i + 1] + 5.0)
    for (z, xf), y in zip(items, ty):
        yz = oy + z
        line((ox + xf - 1.0, yz), (x_ext, yz))
        line((x_ext, yz), (x_ext - 4, y)); line((x_ext - 4, y), (x_txt, y))
        if abs(z) < 1e-6:
            ax.add_patch(MCircle((x_ext, yz), 1.2, fill=False, lw=LW_THIN))
        text(x_txt - 1, y + 0.6, fmt(z), ha="right", va="bottom")


# =============================================================================
# Blatt: Rahmen
# =============================================================================
ax.add_patch(Rectangle((20, 10), SHEET_W - 30, SHEET_H - 20, fill=False, lw=0.7 * PT))

# --- Vorderansicht ---------------------------------------------------------------
FX, FY = 130.0, 300.0
print("HLR Vorderansicht …")
draw_view(hlr((0, -500, 0), (0, 0, 1)), FX, FY)
centerline((FX, FY + rs.z_knopf + rs.KNOB_H + 6), (FX, FY + rs.TAB_BOT - 6))
phantom_rect(FX - 75, FY, 150, rs.PANEL_T)
text(FX + 76, FY + 5.5, "Bedienpanel", ha="left", size=TXT * 0.8)
text(FX, FY + 70, "Vorderansicht", size=5 * PT, weight="bold")
k_top = rs.z_knopf + rs.KNOB_H
hdim(FX - 57.5, FY, FX + 57.5, FY, FY + 55, "115")
hdim(FX - 22.5, FY + k_top, FX + 22.5, FY + k_top, FY + k_top + 8, "Ø45")
hdim(FX - rs.COL_POS, FY + rs.Z_DECK_BOT, FX + rs.COL_POS, FY + rs.Z_DECK_BOT, FY + rs.TAB_BOT - 12,
     fmt(2 * rs.COL_POS))
hdim(FX - rs.DECK / 2, FY + rs.Z_DECK_BOT, FX + rs.DECK / 2, FY + rs.Z_DECK_BOT, FY + rs.TAB_BOT - 21,
     fmt(rs.DECK))
vdim(FX + 22.5, FY + rs.z_knopf, FX + 22.5, FY + k_top, FX + 34, fmt(rs.KNOB_H))
ordinates([(k_top, -22.5), (rs.z_knopf, -22.5), (rs.PANEL_T, -75), (0.0, -57.5), (-rs.PLATE_T, -57.5),
           (rs.Z_DECK_TOP, -rs.DECK / 2), (rs.Z_DECK_BOT, -rs.DECK / 2),
           (rs.TAB_BOT, rs.TAB_X0)],
          FX, FY, FX - 80, FX - 92)
leader((FX + 37, FY + rs.Z_BALL), (FX + 62, FY + rs.Z_BALL - 8), "Kugeldruckstück M8")
leader((FX + 2, FY + rs.Z_SHAFT_END + 3), (FX + 50, FY + rs.Z_SHAFT_END - 10), f"Achse Ø{fmt(rs.SHAFT_D)}")
leader((FX + 3, FY + rs.z_knopf + 4), (FX + 50, FY + rs.z_knopf + 30),
       f"Hub {fmt(rs.PUSH_TRAVEL)} bis Anschlag")

# --- Seitenansicht von links (rechts neben der Vorderansicht) ---------------------------
SX, SY = 305.0, 300.0
print("HLR Seitenansicht …")
draw_view(hlr((-500, 0, 0), (0, 0, 1)), SX, SY)
centerline((SX, SY + k_top + 6), (SX, SY + rs.TAB_BOT - 6))
phantom_rect(SX - 75, SY, 150, rs.PANEL_T)
text(SX, SY + 70, "Seitenansicht von links", size=5 * PT, weight="bold")
hdim(SX - rs.DECK / 2, SY + rs.Z_DECK_BOT, SX + rs.DECK / 2, SY + rs.Z_DECK_BOT, SY + rs.TAB_BOT - 21,
     fmt(rs.DECK))
y_tab_out = -(rs.FIRE_Y0 - rs.TAB_T)          # Papier-x = -Y
hdim(SX, SY + rs.TAB_BOT, SX + y_tab_out, SY + rs.TAB_BOT, SY + rs.TAB_BOT - 10, fmt(y_tab_out))
vdim(SX + 57.5, SY + rs.TAB_BOT, SX + 57.5, SY + k_top, SX + 72, fmt(k_top - rs.TAB_BOT))
vdim(SX - 4, SY + rs.Z_DECK_BOT, SX - 4, SY + rs.Z_SHAFT_END, SX - 22,
     fmt(rs.Z_DECK_BOT - rs.Z_SHAFT_END))
vdim(SX + 57.5, SY - rs.PLATE_T, SX + 57.5, SY, SX + 64, fmt(rs.PLATE_T))

# --- Draufsicht (unter der Vorderansicht) -------------------------------------------
TX, TY = 130.0, 120.0
print("HLR Draufsicht …")
draw_view(hlr((0, 0, 500), (0, 1, 0)), TX, TY)
centerline((TX - 65, TY), (TX + 65, TY)); centerline((TX, TY - 65), (TX, TY + 65))
for sx in (-1, 1):
    for sy in (-1, 1):
        cx, cy = TX + sx * rs.PLATE_HOLE_POS, TY + sy * rs.PLATE_HOLE_POS
        centerline((cx - 5, cy), (cx + 5, cy)); centerline((cx, cy - 5), (cx, cy + 5))
text(TX, TY - 88, "Draufsicht", size=5 * PT, weight="bold")
hp = rs.PLATE_HOLE_POS
hdim(TX - 57.5, TY - 57.5, TX + 57.5, TY - 57.5, TY - 75, "115")
hdim(TX - hp, TY - hp, TX + hp, TY - hp, TY - 66, fmt(2 * hp))
vdim(TX - 57.5, TY - 57.5, TX - 57.5, TY + 57.5, TX - 75, "115")
vdim(TX - hp, TY - hp, TX - hp, TY + hp, TX - 66, fmt(2 * hp))
a = math.radians(45)
leader((TX + hp + 2.5 * math.cos(a), TY + hp + 2.5 * math.sin(a)), (TX + 66, TY + 66),
       f"4× Ø{fmt(rs.PLATE_HOLE)}")
leader((TX + 57.5 - 1.76, TY - 57.5 + 1.76), (TX + 66, TY - 64), "R6")
ax.annotate("", xy=(TX + 78, TY), xytext=(TX + 62, TY),
            arrowprops=dict(arrowstyle="-|>", lw=LW_THIN, color="black"))
text(TX + 80, TY, "+X: Rastkugel,\nStellung 1 (0°)", ha="left", size=TXT * 0.8)

# --- Isometrie von unten -------------------------------------------------------------
IX, IY = 494.0, 292.0
ISO_O, ISO_UP = (1, -1, -1), (0, 0, 1)
print("HLR Isometrie …")
iso = hlr((500 * ISO_O[0], 500 * ISO_O[1], 500 * ISO_O[2]), ISO_UP)
pts = np.array([p for s in iso for p in s])
icx, icy = (pts.min(0) + pts.max(0)) / 2
draw_view(iso, IX - icx, IY - icy, lw=LW_THIN * 1.4)
text(IX, IY + 92, "Isometrie (von unten)", size=5 * PT, weight="bold")


def iso_xy(p):
    b = Pos(*p) * Box(0.01, 0.01, 0.01)
    v, h = b.project_to_viewport((500 * ISO_O[0], 500 * ISO_O[1], 500 * ISO_O[2]), ISO_UP, (0, 0, 0))
    c = Compound(list(v) + list(h)).bounding_box().center()
    return np.array([c.X + IX - icx, c.Y + IY - icy])


# Positionsnummern (Stückliste) -> sichtbare Stellen
hs = rs.switch_holes_s()
BALLOONS = [   # (Pos., 3D-Punkt, Balloon-Versatz in mm auf dem Blatt)
    (4, (48, -57.5, -2), (28, 18)),
    (6, (45, 0, -43), (32, -14)),
    (8, (40, 0, -16), (26, 14)),
    (12, (-11, -26, -31.5), (-40, 6)),
    (12, (-18, -5, -64), (-30, -16)),
    (13, (hs[0], -12.0, rs.FIRE_TOP - rs.SW_H + rs.SW_HOLE_FROM_BOTTOM), (22, -20)),
    (14, (rs.COL_POS, -rs.COL_POS, -46), (30, -18)),
    (15, (-rs.COL_POS - 3.4, -rs.COL_POS, rs.Z_DECK_BOT - 0.3), (-34, -8)),
    (16, (hs[1], -28.3, -45.5), (-34, -22)),
]
for nr, p, off in BALLOONS:
    a2 = iso_xy(p)
    b = a2 + np.array(off, float)
    d = (b - a2) / np.linalg.norm(b - a2)
    line(a2, b - d * 4)
    ax.add_patch(MCircle(a2, 0.6, color="black"))
    ax.add_patch(MCircle(b, 4, fill=True, fc="white", ec="black", lw=LW_THIN * 1.5))
    text(b[0], b[1], str(nr), weight="bold")
text(IX, IY - 88, "innenliegend: Pos. 5, 7, 9, 10, 11, 17 (siehe Längsschnitt)", size=TXT * 0.8)

# =============================================================================
# Stückliste + Schriftfeld
# =============================================================================
BOM = [
    (1, 1, "Drehknopf", "Druckteil PETG", "1"),
    (2, 1, "Knopf-Inlay (Pfeil)", "Druckteil PETG", "31"),
    (3, 1, "Gleitscheibe", "Druckteil PETG", "3"),
    (4, 1, "Grundplatte mit Lager + Säulen", "Druckteil PETG", "32"),
    (5, 1, "Rotor (Rastrad + Nocke)", "Druckteil PETG, 100 %", "27, 12"),
    (6, 1, "Schalterdeck mit Fire-Halter", "Druckteil PETG", "26, 16"),
    (7, 1, f"Achse Ø{fmt(rs.SHAFT_D)} × {fmt(rs.shaft_len)}", "Stahl", ""),
    (8, 1, f"Kugeldruckstück M8, Kugel Ø{fmt(rs.BALL_D)}", "Stahl, Kaufteil", "5, 6, 7"),
    (9, 1, "Sechskantmutter M8", "ISO 4032 – M8", ""),
    (10, 1, "Druckfeder Da 11 × L0 20, d 0,8", "Federstahl", "10"),
    (11, 1, "Scheibe 8,4 × 16 × 1,6", "ISO 7089 – 8,4 (DIN 125-A)", "28"),
    (12, 5, "Mikroschalter (Omron V)", "Kaufteil", "19, 22"),
    (13, 10, "Linsenschraube M3 × 20", "ISO 7045 – M3×20 – 4.8", ""),
    (14, 4, "Linsenschraube M3 × 10", "ISO 7045 – M3×10 – 4.8", ""),
    (15, 24, "Scheibe 3,2 × 7 × 0,5", "ISO 7089 – 3,2 (DIN 125-A)", ""),
    (16, 13, "Sechskantmutter M3", "ISO 4032 – M3", "15"),
    (17, 3, "Gewindestift M3 × 10", "ISO 4026 – M3×10", ""),
]
BX0, BX1 = 404.0, 584.0
cols = [BX0, BX0 + 10, BX0 + 22, BX0 + 88, BX0 + 158, BX1]
heads = ["Pos.", "Menge", "Benennung", "Norm / Werkstoff", "Taito"]
RH = 5.6
TB_TOP = 52.0                       # Oberkante Schriftfeld
y0 = TB_TOP
rows = [heads] + [[str(a), str(b), c, d, e] for a, b, c, d, e in BOM][::-1]
# Tabelle von unten nach oben (Kopf direkt über dem Schriftfeld, wie DIN EN ISO 7200)
for i, r in enumerate(rows):
    yb = y0 + i * RH
    ax.add_patch(Rectangle((BX0, yb), BX1 - BX0, RH, fill=False, lw=LW_THIN if i else LW_THICK))
    for j, c in enumerate(r):
        if j:
            line((cols[j], yb), (cols[j], yb + RH))
        ha = "center" if j in (0, 1, 4) else "left"
        x = (cols[j] + cols[j + 1]) / 2 if ha == "center" else cols[j] + 1.2
        text(x, yb + RH / 2, c, size=TXT * (0.78 if i else 0.8), ha=ha, weight="bold" if i == 0 else None)
ax.add_patch(Rectangle((BX0, y0), BX1 - BX0, RH * len(rows), fill=False, lw=LW_THICK))

# Schriftfeld
ax.add_patch(Rectangle((BX0, 10), BX1 - BX0, TB_TOP - 10, fill=False, lw=LW_THICK))
for yy in (24, 38):
    line((BX0, yy), (BX1, yy), LW_THIN)
for xx, y_a, y_b in ((BX0 + 45, 10, 24), (BX0 + 90, 10, 24), (BX0 + 135, 10, 38), (BX0 + 45, 24, 38),
                     (BX0 + 90, 24, 38)):
    line((xx, y_a), (xx, y_b), LW_THIN)


def cell(x, y, label, value, size=TXT * 0.8):
    text(x + 1.2, y + 10.5, label, ha="left", size=TXT * 0.55, color="#444444")
    text(x + 1.2, y + 4.5, value, ha="left", size=size)


cell(BX0, 10, "Maßstab", "1:1 (A2)")
cell(BX0 + 45, 10, "Allgemeintoleranz", "ISO 2768-m")
cell(BX0 + 90, 10, "Datum", "30.09.2026")
cell(BX0 + 135, 10, "Blatt", "1 / 1")
cell(BX0, 24, "Einheit", "mm")
cell(BX0 + 45, 24, "Werkstoff", "s. Stückliste")
cell(BX0 + 90, 24, "Zeichnungs-Nr.", "RS-001")
text(BX0 + 1.2, 48, "Benennung", ha="left", size=TXT * 0.55, color="#444444")
text(BX0 + 1.2, 42.5, "Aim-n-Fire Rotary Stick – Baugruppe", ha="left", size=TXT * 1.25, weight="bold")
# Projektionsmethode 1 (Symbol: Kegelstumpf links, Kreise rechts)
px, py = BX0 + 150, 31
ax.add_patch(MPolygon([(px - 7, py - 3.5), (px + 1, py - 2), (px + 1, py + 2), (px - 7, py + 3.5)],
                      closed=True, fill=False, lw=LW_THIN * 1.5))
ax.add_patch(MCircle((px + 9, py), 3.5, fill=False, lw=LW_THIN * 1.5))
ax.add_patch(MCircle((px + 9, py), 2.0, fill=False, lw=LW_THIN * 1.5))
line((px - 9, py), (px + 14, py), LW_THIN * 0.6)
text(BX0 + 136, 36, "Projektion", ha="left", size=TXT * 0.55, color="#444444")

# Hinweise
notes = [
    "Hinweise",
    "1  Maße in mm. Bezugsebene 0 = Oberseite Grundplatte (Anlage am Panel).",
    "2  Darstellung in Ruhestellung, Rastposition 1 (0°).",
    f"3  Knopfhub {fmt(rs.PUSH_TRAVEL)} mm bis Anschlag, Fire löst bei ca. 1,5 mm aus.",
    "4  Taster in Langlöchern ±4 mm justierbar (radial bzw. vertikal).",
    "5  Scheiben Pos. 15 je unter Schraubenkopf und Mutter.",
    "6  Scheibe Pos. 11 zwischen Rotor und Lagerbuchse (Gleitfläche).",
    "7  Druckteile PETG, 0,2 mm Schicht, 4 Wände; Rotor 100 % Infill.",
    "8  Panel strichpunktiert, nicht Lieferumfang.",
]
ny = 112.0
for i, n in enumerate(notes):
    text(250, ny - i * 5.2, n, ha="left", size=TXT * (0.95 if i == 0 else 0.78), weight="bold" if i == 0 else None)

out = rs.OUT / "zeichnung_baugruppe"
fig.savefig(str(out) + ".pdf")
fig.savefig(str(out) + ".png", dpi=150)
print("->", str(out) + ".pdf / .png")
