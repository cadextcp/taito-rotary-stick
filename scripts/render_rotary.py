"""Vorschaubilder für models/rotary_stick.py (matplotlib, ohne OpenGL).

    python scripts/render_rotary.py
"""

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "models"))
import rotary_stick as rs  # noqa: E402  (baut das Modell)
from build123d import Pos  # noqa: E402
from matplotlib.colors import to_rgb  # noqa: E402

COLORS = {"grundplatte": "#8a9099", "rotor": "#e8892b", "schalterdeck": "#7d8590", "knopf": "#c9ccd1",
          "inlay": "#c0392b", "scheibe": "#333333", "achse": "#aab8c8", "kugel": "#dfe6ee",
          "kugeldruckstueck": "#d4ac2b", "feder": "#6fa8dc", "taster": "#2b2b2b", "hebel": "#e6e6e6"}


def color_for(label):
    for k, v in COLORS.items():
        if label.startswith(k):
            return v
    return "#999999"


def mesh(shape, tol=0.15):
    v, t = shape.tessellate(tol, 0.3)
    v = np.array([(p.X, p.Y, p.Z) for p in v])
    return v[np.array(t)]


def draw(ax, items, elev, azim):
    light = np.array([0.4, -0.5, 0.8])
    light /= np.linalg.norm(light)
    for shape, label, dz in items:
        tris = mesh(Pos(0, 0, dz) * shape)
        n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
        shade = 0.45 + 0.55 * np.abs(n @ light)
        base = np.array(to_rgb(color_for(label)))
        fc = np.clip(base[None, :] * shade[:, None], 0, 1)
        ax.add_collection3d(Poly3DCollection(tris, facecolors=fc, edgecolors="none"))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()


def fit(ax, lo, hi):
    c, r = (np.array(lo) + hi) / 2, max(np.array(hi) - lo) / 2
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1))


asm = [(s, s.label, 0.0) for s in rs.asm]

import pyvista as pv  # noqa: E402


def pv_mesh(shape, tol=0.1):
    v, t = shape.tessellate(tol, 0.25)
    pts = np.array([(p.X, p.Y, p.Z) for p in v])
    faces = np.hstack([np.full((len(t), 1), 3), np.array(t)]).ravel()
    return pv.PolyData(pts, faces).compute_normals(split_vertices=True, feature_angle=35)


def shot(items, path, views, clip=False, size=(1600, 900), focus=(0, 0, -25), zoom=1.35):
    shape = (1, len(views))
    pl = pv.Plotter(off_screen=True, shape=shape, window_size=size, border=False)
    meshes = [(pv_mesh(Pos(0, 0, dz) * s), lbl) for s, lbl, dz in items]
    for i, (pos, up, title) in enumerate(views):
        pl.subplot(0, i)
        pl.set_background("white")
        for m, lbl in meshes:
            if clip:
                m = m.clip(normal=(0, 1, 0), origin=(0, 0.01, 0), invert=False)
                if m.n_points == 0:
                    continue
            pl.add_mesh(m, color=color_for(lbl), smooth_shading=True, specular=0.25,
                        show_edges=False)
        pl.add_text(title, font_size=11, color="black")
        pl.camera_position = [pos, focus, up]
        pl.camera.zoom(zoom)
    pl.screenshot(str(path))
    pl.close()


# 1) Baugruppe
shot(asm, rs.OUT / "vorschau_baugruppe.png",
     [((180, -220, -170), (0, 0, 1), "von unten"), ((170, -230, 190), (0, 0, 1), "von oben")])

# 1b) Schnitt durch die Achse (XZ-Ebene)
moving = ("achse", "rotor", "knopf", "inlay")
pushed = [(s, lbl, -rs.PUSH_TRAVEL if lbl.startswith(moving) else 0.0) for s, lbl, _ in asm
          if lbl != "hebel_fire"]
pushed.append((rs.FIRE_LOC * rs.make_switch(rs.Z_SHAFT_END - rs.PUSH_TRAVEL - rs.FIRE_TOP)[1], "hebel_fire", 0.0))
shot(asm, rs.OUT / "vorschau_schnitt.png",
     [((0, -380, -20), (0, 0, 1), "Schnitt: Ruhestellung")], clip=True, size=(1100, 1000))
shot(pushed, rs.OUT / "vorschau_schnitt_gedrueckt.png",
     [((0, -380, -20), (0, 0, 1), f"Schnitt: gedrueckt ({rs.PUSH_TRAVEL} mm, Fire)")], clip=True, size=(1100, 1000))

# 2) Explosionsansicht wie Taito Fig. 15
offs = {"knopf": 110, "inlay": 135, "scheibe": 75, "achse": 0, "grundplatte": 35, "kugel": 35,
        "kugeldruckstueck": 35, "rotor": 0, "feder": -25, "schalterdeck": -65, "taster": -65, "hebel": -65}
exp = []
for s, label, _ in asm:
    dz = next(v for k, v in offs.items() if label.startswith(k))
    if label.startswith("kugel"):
        s = Pos(30, 0, 0) * s
    exp.append((s, label, dz))
pl_items = exp
shot(pl_items, rs.OUT / "vorschau_explosion.png",
     [((330, -420, 160), (0, 0, 1), "Explosionsansicht (Reihenfolge wie Taito Fig. 15)")], size=(1000, 1300),
     focus=(0, 0, 10), zoom=0.95)

# 3) Schaltebene: Nocke + Hebel für alle 8 Positionen
fig, axs = plt.subplots(2, 4, figsize=(16, 8.5), dpi=100)
th = np.radians(np.arange(0, 360.5, 0.5))
for pos, ax in enumerate(axs.flat):
    theta = pos * 45
    r = np.array([rs.cam_r(np.degrees(a) - theta) for a in th])
    ax.fill(r * np.cos(th), r * np.sin(th), color="#e8892b")
    ax.add_patch(plt.Circle((0, 0), rs.SHAFT_D / 2, color="#aab8c8"))
    for k in range(4):
        phi = np.radians(90 * k)
        R = np.array([[np.cos(phi), -np.sin(phi)], [np.sin(phi), np.cos(phi)]])
        c = -rs.LEVER_TIP_OFF
        box = np.array([[rs.SW_EDGE_R, c - rs.SW_L / 2], [rs.SW_EDGE_R + rs.SW_H, c - rs.SW_L / 2],
                        [rs.SW_EDGE_R + rs.SW_H, c + rs.SW_L / 2], [rs.SW_EDGE_R, c + rs.SW_L / 2]])
        h = rs.lever_height(90 * k, theta)
        on = h < rs.SW_EDGE_R - (rs.CAM_LOBE_R - 1.0) + 0.01
        ax.fill(*(box @ R.T).T, color="#c0392b" if on else "#555555")
        lev = np.array([[rs.SW_EDGE_R - 0.8, rs.LEVER_S0], [rs.SW_EDGE_R - h, rs.LEVER_S1]])
        ax.plot(*(lev @ R.T).T, color="k", lw=2)
    ax.annotate("", xy=(30 * np.cos(np.radians(theta)), 30 * np.sin(np.radians(theta))), xytext=(0, 0),
                arrowprops=dict(arrowstyle="->", lw=1.5, color="#1f77b4"))
    ax.set_title(f"Position {pos + 1}: {theta}°")
    ax.set_aspect("equal"); ax.set_xlim(-38, 38); ax.set_ylim(-38, 38); ax.axis("off")
fig.suptitle("Schaltebene von oben — rot = Taster betätigt (Rastkugel sitzt bei +X)")
fig.tight_layout()
fig.savefig(rs.OUT / "vorschau_schaltlogik.png")
print("Bilder geschrieben nach", rs.OUT)
