"""Animation: Drehen durch die 8 Rastpositionen + Drücken (Fire), Taster leuchten rot bei Betätigung.

    python scripts/animate_rotary.py   -> exports/rotary_stick/animation.gif
"""

import math
import sys
from pathlib import Path

import numpy as np
import pyvista as pv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "models"))
import rotary_stick as rs  # noqa: E402
from build123d import Pos, Rot, extrude  # noqa: E402

FPS = 20
OFF, ON = "#3a3a3a", "#e02020"
NAMES = ["Rechts", "Oben", "Links", "Unten"]   # Taster 0..3 von oben gesehen


def pv_mesh(shape, tol=0.12):
    v, t = shape.tessellate(tol, 0.25)
    pts = np.array([(p.X, p.Y, p.Z) for p in v])
    faces = np.hstack([np.full((len(t), 1), 3), np.array(t)]).ravel()
    return pv.PolyData(pts, faces).compute_normals(split_vertices=True, feature_angle=35)


def matrix(theta_deg, dz):
    c, s = math.cos(math.radians(theta_deg)), math.sin(math.radians(theta_deg))
    m = np.eye(4)
    m[:2, :2] = [[c, -s], [s, c]]
    m[2, 3] = dz
    return m


# --- Ablauf (Keyframes: theta, push) --------------------------------------------
def ease(u):
    return 0.5 - 0.5 * math.cos(math.pi * u)


timeline = []            # (theta, push)
theta = 0.0


def hold(n):
    timeline.extend([(theta, 0.0)] * n)


def turn(dst, n=12):
    global theta
    src = theta
    for i in range(1, n + 1):
        u = i / n
        # Rastgefühl: erst zäh, dann schnappt es in die Kerbe
        timeline.append((src + (dst - src) * ease(u ** 1.6), 0.0))
    theta = dst


def fire(n=6):
    for i in range(1, n + 1):
        timeline.append((theta, rs.PUSH_TRAVEL * ease(i / n)))
    timeline.extend([(theta, rs.PUSH_TRAVEL)] * 6)
    for i in range(1, n + 1):
        timeline.append((theta, rs.PUSH_TRAVEL * (1 - ease(i / n))))


hold(12)
for step in range(1, 9):
    turn(step * 45)
    hold(8)
    if step in (2, 5, 8):
        fire()
        hold(4)
turn(270, 16); hold(4); turn(360, 16); hold(10)   # zurückdrehen
fire(); hold(12)

# --- Szene ----------------------------------------------------------------------
pl = pv.Plotter(off_screen=True, window_size=(900, 640))
pl.set_background("white")
pl.enable_depth_peeling()

moving, static = {}, {}
style = {"grundplatte": ("#8a9099", 0.18), "schalterdeck": ("#7d8590", 0.30), "rotor": ("#e8892b", 1),
         "knopf": ("#c9ccd1", 1), "inlay": ("#c0392b", 1), "scheibe": ("#333333", 0.5),
         "achse": ("#aab8c8", 1), "kugel": ("#dfe6ee", 1), "kugeldruckstueck": ("#d4ac2b", 1),
         "feder": ("#6fa8dc", 1)}
sw_actors = {}
for shape in rs.asm:
    lbl = shape.label
    if lbl.startswith("hebel"):
        continue
    if lbl.startswith("taster"):
        sw_actors[lbl] = pl.add_mesh(pv_mesh(shape), color=OFF, smooth_shading=True)
        continue
    col, op = next((v for k, v in style.items() if lbl.startswith(k)), ("#9a9a9a", 1))
    a = pl.add_mesh(pv_mesh(shape), color=col, opacity=op, smooth_shading=True, specular=0.3)
    if lbl.startswith(("rotor", "knopf", "inlay", "achse")):
        moving[lbl] = a

# Pfeil im Inlay weiß gefüllt; zeigt wie der Nocken nach +X (Rastkugel-Seite) in Stellung 1
arrow = Pos(0, 0, rs.z_knopf + rs.KNOB_H - 0.6) * Rot(0, 0, -90) * extrude(rs.arrow_sketch(), amount=0.7)
moving["pfeil"] = pl.add_mesh(pv_mesh(arrow), color="white")

lever_actors = []
pl.camera_position = [(170, -240, 110), (0, 0, -14), (0, 0, 1)]
pl.camera.zoom(1.15)
txt = None

out = rs.OUT / "animation.gif"
pl.open_gif(str(out), fps=FPS)
for th, push in timeline:
    for a in moving.values():
        a.user_matrix = matrix(th, -push)
    for a in lever_actors:
        pl.remove_actor(a)
    lever_actors.clear()

    states = []
    for k in range(4):
        h = rs.lever_height(90 * k, th)
        on = rs.SW_EDGE_R - h > rs.CAM_LOBE_R - 1.0
        states.append(on)
        body, lever = rs.make_switch(h)
        t = Pos(0, 0, rs.Z_SW_MID) * Rot(0, 0, 90 * k) * Pos(rs.SW_EDGE_R, 0, 0)
        lever_actors.append(pl.add_mesh(pv_mesh(t * lever), color="#f0f0f0"))
        sw_actors[f"taster_{k}"].prop.color = ON if on else OFF
    shaft_end = rs.Z_SHAFT_END - push
    fire_h = min(rs.LEVER_FREE, shaft_end - rs.FIRE_TOP)
    fire_on = push > 1.5
    lever_actors.append(pl.add_mesh(pv_mesh(rs.FIRE_LOC * rs.make_switch(fire_h)[1]), color="#f0f0f0"))
    sw_actors["taster_fire"].prop.color = ON if fire_on else OFF

    pos = int(round((th % 360) / 45)) % 8
    snapped = abs(th - round(th / 45) * 45) < 0.5
    dirs = " + ".join(n for n, s in zip(NAMES, states) if s) or "-"
    lines = [f"Stellung {pos + 1}/8  ({(pos * 45) % 360:3d} Grad)" if snapped else "dreht ...",
             f"Richtung: {dirs}",
             "FIRE: GEDRUECKT" if fire_on else ("FIRE: -" if push < 0.05 else "Knopf wird gedrueckt ...")]
    if txt is not None:
        pl.remove_actor(txt)
    txt = pl.add_text("\n".join(lines), position="upper_left", font_size=13, color="black")
    pl.write_frame()
pl.close()
print(f"{len(timeline)} Frames -> {out}")
