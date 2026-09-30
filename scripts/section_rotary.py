"""Längsschnitt durch die Achse (XZ-Ebene), Ruhestellung und gedrückt, mit Positionsnummern.

    python scripts/section_rotary.py   -> exports/rotary_stick/laengsschnitt.png
"""

import sys
from pathlib import Path

import numpy as np
import pyvista as pv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "models"))
import rotary_stick as rs  # noqa: E402
from build123d import Align, Box, Circle, Helix, Plane, Pos, sweep  # noqa: E402

WIRE_D, SPRING_DM, COILS = 0.8, 10.2, 7
SPRING_Z0 = rs.Z_DECK_TOP - 1.5                        # Federsitz im Deck
SPRING_Z1 = rs.Z_CAM_BOT + rs.SPRING_POCKET_DEPTH      # Taschenboden im Rotor (Ruhe)


def spring(length):
    pitch = (length - WIRE_D) / COILS
    path = Pos(0, 0, SPRING_Z0 + WIRE_D / 2) * Helix(pitch, length - WIRE_D, SPRING_DM / 2)
    prof = Plane(path @ 0, z_dir=path % 0) * Circle(WIRE_D / 2)
    return sweep(prof, path=path)


def pv_mesh(shape, tol=0.08):
    v, t = shape.tessellate(tol, 0.2)
    pts = np.array([(p.X, p.Y, p.Z) for p in v])
    faces = np.hstack([np.full((len(t), 1), 3), np.array(t)]).ravel()
    return pv.PolyData(pts, faces).compute_normals(split_vertices=True, feature_angle=35)


HALF = Box(400, 200, 400, align=(Align.CENTER, Align.MIN, Align.CENTER))   # behält y >= 0
COL = {"grundplatte": "#8a9099", "rotor": "#e8892b", "schalterdeck": "#7d8590", "knopf": "#c9ccd1",
       "inlay": "#c0392b", "scheibe": "#333333", "achse": "#9fb3c8", "kugel": "#dfe6ee",
       "kugeldruckstueck": "#d4ac2b", "feder": "#00a651", "taster": "#2b2b2b", "hebel": "#bbbbbb"}
MOVING = ("rotor", "knopf", "inlay", "achse")


def scene(pl, push):
    for s in rs.asm:
        lbl = s.label
        if lbl.endswith("_3"):
            continue                      # Taster vor der Schnittebene weglassen, verdeckt sonst die Feder
        if lbl == "feder":
            s = spring(SPRING_Z1 - push - SPRING_Z0)
        elif lbl == "hebel_fire":
            s = rs.FIRE_LOC * rs.make_switch(min(rs.LEVER_FREE, rs.Z_SHAFT_END - push - rs.FIRE_TOP))[1]
        if lbl.startswith(MOVING):
            s = Pos(0, 0, -push) * s
        if not lbl.endswith("_1"):        # Taster 1 liegt komplett hinter der Schnittebene
            s = s & HALF
        if s is None or s.volume < 1e-6:
            continue
        color = next((v for k, v in COL.items() if lbl.startswith(k)), "#9a9a9a")
        if lbl.startswith("taster_fire") and push > 1.5:
            color = "#e02020"
        pl.add_mesh(pv_mesh(s), color=color, smooth_shading=True, specular=0.2)


CX, CZ, SCALE, W, H = 0.0, -25.0, 57.0, 1100, 1045       # Ansicht in mm, parallel
HW = SCALE * W / H


def render(push, cz=None, scale=None, size=(W, H)):
    cz = CZ if cz is None else cz
    scale = SCALE if scale is None else scale
    pl = pv.Plotter(off_screen=True, window_size=size)
    pl.set_background("white")
    scene(pl, push)
    pl.enable_parallel_projection()
    pl.camera_position = [(CX, -500, cz), (CX, 0, cz), (0, 0, 1)]
    pl.camera.parallel_scale = scale
    img = pl.screenshot(return_img=True)
    pl.close()
    return img


# (Nr., Ziel am Bauteil (x, z), Balloon-Position (x, z)) — Nummern wie Taito Fig. 15
BALLOONS = [
    ("1", (-20, 18), (-78, 22)), ("3", (-16, 3.8), (-78, 8)), ("32", (-9, -7), (-78, -6)),
    ("27", (-12, -15), (-78, -17)), ("12", (-8.5, -26), (-78, -28)), ("10", (-5.1, -35.5), (-78, -40)),
    ("26", (-30, -41), (-78, -52)), ("22", (-12, -64), (-78, -66)),
    ("5-7", (22, -16), (78, -12)), ("11", (6, -21), (78, -24)), ("19", (26, -31.5), (78, -34)),
    ("A", (0, -47), (78, -50)),
]
LEGEND = ("1 Knopf   3 Gleitscheibe   32 Grundplatte mit Lager   27 Rastrad (8 Kerben)   12 Nocke   "
          "10 Rueckholfeder\n26 Schalterdeck   22 Fire-Taster   5-7 Kugeldruckstueck (Schnappkugel)   "
          "11 Madenschrauben M3   19 Richtungs-Taster   A Achse")

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

fig, axs = plt.subplots(1, 2, figsize=(20, 11), dpi=110)
titles = ["Ruhestellung\nFeder (10) drueckt Rotor + Achse nach oben gegen das Lager (32)",
          f"Gedrueckt ({rs.PUSH_TRAVEL:.0f} mm)\nFeder zusammengedrueckt, Achsende betaetigt Fire-Taster (22)"]
for ax, push, title in zip(axs, (0.0, rs.PUSH_TRAVEL), titles):
    ax.imshow(render(push), extent=[CX - HW, CX + HW, CZ - SCALE, CZ + SCALE])
    for nr, (tx, tz), (bx, bz) in BALLOONS:
        if nr in ("10", "A"):
            tz -= push if nr == "A" else push / 2
        green = nr == "10"
        ax.annotate(nr, xy=(tx, tz), xytext=(bx, bz), ha="center", va="center",
                    fontsize=15 if green else 12, fontweight="bold", color="#00a651" if green else "black",
                    bbox=dict(boxstyle="circle,pad=0.35", fc="white", ec="#00a651" if green else "black",
                              lw=2.5 if green else 1.2),
                    arrowprops=dict(arrowstyle="-|>", color="#00a651" if green else "black",
                                    lw=2.5 if green else 1.0, shrinkA=0, shrinkB=0))
    spring_len = SPRING_Z1 - push - SPRING_Z0
    ax.text(-78, -95, f"Federlaenge {spring_len:.1f} mm", color="#00a651", fontsize=12, fontweight="bold")
    # Detail: Federtasche vergrößert
    dz, ds = -34.0, 9.0
    ins = ax.inset_axes([0.60, 0.0, 0.40, 0.30])
    ins.imshow(render(push, dz, ds, (900, 900)), extent=[-ds, ds, dz - ds, dz + ds])
    ins.set_xticks([]); ins.set_yticks([])
    for sp in ins.spines.values():
        sp.set_edgecolor("#00a651"); sp.set_linewidth(2.5)
    ins.set_title("Detail Feder (10)", color="#00a651", fontsize=11, fontweight="bold")
    ax.add_patch(plt.Rectangle((-ds, dz - ds), 2 * ds, 2 * ds, fill=False, ec="#00a651", lw=1.5, ls="--"))
    ax.set_xlim(-88, 88); ax.set_ylim(CZ - SCALE - 45, CZ + SCALE); ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(title, fontsize=13)
fig.suptitle("Laengsschnitt durch die Achse (Nummern wie Taito Fig. 15)", fontsize=16, fontweight="bold")
fig.text(0.5, 0.03, LEGEND, ha="center", fontsize=12)
fig.tight_layout(rect=(0, 0.06, 1, 0.97))
out = rs.OUT / "laengsschnitt.png"
fig.savefig(out)
print("->", out)
