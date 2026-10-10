#!/usr/bin/env python3
"""Rev 2 3D model (CadQuery). Builds the CF plates with their windows and holes,
places them in the airframe with stand-in bodies for the printed parts and
equipment, and exports STL/STEP.

  python3 model.py preview   # plates + stand-ins -> build/*.stl for the PNG render
"""
import math
import os
import sys

import cadquery as cq

import params as P
import plates as PL

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, "build")


# ------------------------------------------------------------------ plates
def plate_solid(name):
    """Flat plate in its own XY frame (x along the fuselage), thickness along +Z."""
    f, t, _ = PL.PLATES[name]
    outline, holes, windows = f()
    th = t()
    body = cq.Workplane("XY").polyline(outline).close().extrude(th)
    for w in windows:
        cut = cq.Workplane("XY").polyline(w).close().extrude(th + 2).translate((0, 0, -1))
        cut = cut.edges("|Z").fillet(PL.CORNER_R)
        body = body.cut(cut)
    for x, y, d, _ in holes:
        body = body.cut(cq.Workplane("XY").center(x, y).circle(d / 2).extrude(th + 2).translate((0, 0, -1)))
    return body


def placed_plates():
    side = plate_solid("side_plate")
    # side plate drawn in x/z: rotate its XY frame into XZ, thickness along +Y
    left = side.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, P.W / 2 + P.T_SIDE, 0))
    right = side.rotate((0, 0, 0), (1, 0, 0), 90).translate((0, -P.W / 2, 0))
    bottom = plate_solid("bottom_plate").translate((0, 0, -P.T_BOT))
    mid = plate_solid("middle_deck").translate((0, 0, P.Z_MID_DECK))
    up = plate_solid("upper_deck").translate((0, 0, P.Z_UP_DECK))
    return {"cf_side_left": left, "cf_side_right": right, "cf_bottom": bottom, "cf_mid_deck": mid, "cf_up_deck": up}


# ------------------------------------------------------------------ stand-ins
def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl_x(x0, length, y, z, d, d_in=0):
    c = cq.Workplane("YZ").center(y, z).circle(d / 2)
    if d_in:
        c = c.circle(d_in / 2)
    return c.extrude(length).translate((x0, 0, 0))


def cyl_y(x, z, y0, length, d):
    return cq.Workplane("XZ").center(x, z).circle(d / 2).extrude(-length).translate((0, y0, 0))


def airfoil_pts(chord, n=40):
    """Clark-Y-like section: NACA 2412 mean line with 11.7% thickness."""
    m, p, t = 0.02, 0.4, 0.117
    up, lo = [], []
    for i in range(n + 1):
        b = math.pi * i / n
        x = (1 - math.cos(b)) / 2
        yt = 5 * t * (0.2969 * math.sqrt(x) - 0.126 * x - 0.3516 * x ** 2 + 0.2843 * x ** 3 - 0.1036 * x ** 4)
        yc = m / p ** 2 * (2 * p * x - x * x) if x < p else m / (1 - p) ** 2 * (1 - 2 * p + 2 * p * x - x * x)
        up.append((x * chord, (yc + yt) * chord))
        lo.append((x * chord, (yc - yt) * chord))
    return up[::-1] + lo[1:-1]


def wing_panel(side):
    a = math.radians(P.INCIDENCE_DEG)
    root_y = P.W / 2 + P.T_SIDE
    span = P.SPAN / 2 - root_y
    zc = P.SPAR_FRONT["z"] - 0.03 * P.CHORD      # chord line so the front spar sits inside the section
    pts = []
    for x, z in airfoil_pts(P.CHORD):
        xr = x * math.cos(a) + z * math.sin(a)
        zr = -x * math.sin(a) + z * math.cos(a)
        pts.append((P.X_LE + xr, zc + zr + (0.25 * P.CHORD) * math.sin(a)))
    w = cq.Workplane("XZ").polyline(pts).close().extrude(-span)
    w = w.translate((0, root_y, 0))
    return w if side > 0 else w.mirror("XZ")


def tail():
    from sizing import tail_geometry
    tg = tail_geometry()
    r = P.BOOM_OD / 2
    zp = P.BOOM_Z + r + 4
    hs = box(tg["hs_le"], tg["hs_le"] + tg["hs_chord"], -tg["hs_span"] / 2, tg["hs_span"] / 2, zp, zp + 6)
    te = tg["hs_le"] + tg["hs_chord"]
    fin = (cq.Workplane("XZ").polyline([(te - tg["fin_root"], zp + 6), (te, zp + 6), (te, zp + 6 + tg["fin_h"]),
                                       (te - tg["fin_tip"], zp + 6 + tg["fin_h"])]).close().extrude(3).translate((0, 3, 0)))
    mount = cyl_x(tg["boom_end"] - 45, 45, 0, P.BOOM_Z, P.BOOM_OD + 6)
    return hs, fin, mount, tg


def stand_ins(config="tractor"):
    import parts as PT
    hs, fin, mount, tg = tail()
    pla = list(PT.all_parts(config, tg["boom_end"]).values())
    eq = {}
    bt = P.BATTERY_TRAY_TRACTOR_X if config == "tractor" else P.BATTERY_TRAY_PUSHER_X
    eq["battery"] = box(bt - 52, bt + 52, -17, 17, 2.5, 2.5 + 27)
    eq["fc"] = box(P.FC_X - 18, P.FC_X + 18, -18, 18, P.Z_MID_DECK + 6, P.Z_MID_DECK + 14)
    eq["pi"] = box(P.PI_X - 32.5, P.PI_X + 32.5, -15, 15, P.Z_MID_DECK + 5, P.Z_MID_DECK + 9)
    eq["esc"] = box(40, 95, -13, 13, P.Z_MID_DECK + 1, P.Z_MID_DECK + 9)
    eq["vtx"] = box(P.VTX_X - 15, P.VTX_X + 15, -15, 15, P.Z_UP_DECK + 4, P.Z_UP_DECK + 10)
    eq["cam"] = box(18, 37, -9.5, 9.5, P.Z_UP_DECK + 5, P.Z_UP_DECK + 24)
    eq["gps"] = box(95, 120, -12.5, 12.5, P.Z_UP_DECK + 12, P.Z_UP_DECK + 20)
    if config == "tractor":
        eq["motor"] = cyl_x(-36, 30, 0, P.TRACTOR_AXIS_Z, P.MOTOR_DIA)
        prop = cyl_x(-46, 2, 0, P.TRACTOR_AXIS_Z, P.PROP_DIA)
    else:
        eq["motor"] = cyl_x(P.L + 2, 30, 0, P.PUSHER_AXIS_Z, P.MOTOR_DIA)
        prop = cyl_x(P.L + 40, 2, 0, P.PUSHER_AXIS_Z, P.PROP_DIA)
    boom = cyl_x(P.BOOM_START_X, tg["boom_end"] - P.BOOM_START_X, 0, P.BOOM_Z, P.BOOM_OD, P.BOOM_ID)
    joiners = [cyl_y(P.SPAR_FRONT["x"], P.SPAR_FRONT["z"], -250, 500, P.SPAR_FRONT["d"]),
               cyl_y(P.SPAR_REAR["x"], P.SPAR_REAR["z"], -135, 270, P.SPAR_REAR["d"])]
    return dict(pla=pla, eq=eq, prop=prop, boom=boom, joiners=joiners, hs=hs, fin=fin)


def union_all(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out.union(s)
    return out


def export_preview(config):
    d = os.path.join(BUILD, config)
    os.makedirs(d, exist_ok=True)
    tol = dict(tolerance=0.2, angularTolerance=0.3)
    for name, s in placed_plates().items():
        cq.exporters.export(s, os.path.join(d, name + ".stl"), **tol)
    si = stand_ins(config)
    cq.exporters.export(union_all(si["pla"]), os.path.join(d, "pla.stl"), **tol)
    for k, v in si["eq"].items():
        cq.exporters.export(v, os.path.join(d, "eq_" + k + ".stl"), **tol)
    for k in ("prop", "boom", "hs", "fin"):
        cq.exporters.export(si[k], os.path.join(d, k + ".stl"), **tol)
    cq.exporters.export(union_all(si["joiners"]), os.path.join(d, "joiners.stl"), **tol)
    if config == "tractor":
        cq.exporters.export(wing_panel(1).union(wing_panel(-1)), os.path.join(d, "wing.stl"), **tol)


if __name__ == "__main__":
    if "preview" in sys.argv:
        for c in ("tractor", "pusher"):
            export_preview(c)
            print("preview", c, "ok")
