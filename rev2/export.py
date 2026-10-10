#!/usr/bin/env python3
"""Export the rev 2 CAD: STEP + STL for every CF plate and printed part,
plus full assemblies (tractor and pusher) as STEP and STL, and plate DXFs.

  python3 export.py            # writes ./cad/...
"""
import math
import os
import shutil

import cadquery as cq

import params as P
import parts as PT
import plates as PL
from model import cyl_x, cyl_y, placed_plates, plate_solid, tail, wing_panel

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "cad")
TOL = dict(tolerance=0.05, angularTolerance=0.2)

CF = cq.Color(0.15, 0.15, 0.17)
PLA = cq.Color(0.95, 0.55, 0.10)
FOAM = cq.Color(0.92, 0.92, 0.95)
TUBE = cq.Color(0.08, 0.08, 0.08)
METAL = cq.Color(0.7, 0.7, 0.75)


def to_origin(wp):
    bb = wp.val().BoundingBox()
    return wp.translate((-bb.xmin, -bb.ymin, -bb.zmin))


def lay_flat_x(wp):
    """Parts that are thin along x (frames, bulkheads): put that face on the bed."""
    return to_origin(wp.rotate((0, 0, 0), (0, 1, 0), -90))


def flip(wp):
    return to_origin(wp.rotate((0, 0, 0), (1, 0, 0), 180))


def write(wp, folder, name):
    os.makedirs(os.path.join(OUT, "step", folder), exist_ok=True)
    os.makedirs(os.path.join(OUT, "stl", folder), exist_ok=True)
    cq.exporters.export(wp, os.path.join(OUT, "step", folder, name + ".step"))
    cq.exporters.export(wp, os.path.join(OUT, "stl", folder, name + ".stl"), **TOL)


def write_dxf(name):
    f, _, _ = PL.PLATES[name]
    outline, holes, windows = f()
    e = []

    def ent(*pairs):
        e.extend("%d\n%s\n" % pv for pv in pairs)

    for poly, layer in [(outline, "CUT")] + [(PL.rounded(w), "CUT") for w in windows]:
        for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
            ent((0, "LINE"), (8, layer), (10, x1), (20, y1), (30, 0), (11, x2), (21, y2), (31, 0))
    for x, y, d, _ in holes:
        ent((0, "CIRCLE"), (8, "DRILL"), (10, x), (20, y), (30, 0), (40, d / 2))
    os.makedirs(os.path.join(OUT, "dxf"), exist_ok=True)
    with open(os.path.join(OUT, "dxf", name + ".dxf"), "w") as fh:
        fh.write("0\nSECTION\n2\nENTITIES\n" + "".join(e) + "0\nENDSEC\n0\nEOF\n")
    with open(os.path.join(OUT, "dxf", name + "_holes.csv"), "w") as fh:
        fh.write("n,x,%s,dia,use\n" % ("z" if name == "side_plate" else "y"))
        for i, (x, y, d, lab) in enumerate(holes):
            fh.write("%d,%.2f,%.2f,%.2f,%s\n" % (i + 1, x, y, d, lab))


def airframe(config):
    """name -> (workplane, colour) in airframe coordinates."""
    hs, fin, _, tg = tail()
    items = {}
    for n, s in placed_plates().items():
        items[n] = (s, CF)
    for n, s in PT.all_parts(config, tg["boom_end"]).items():
        items[n] = (s, PLA)
    items["boom_16x14"] = (cyl_x(P.BOOM_START_X, tg["boom_end"] - P.BOOM_START_X, 0, P.BOOM_Z, P.BOOM_OD)
                           .cut(cyl_x(P.BOOM_START_X - 1, tg["boom_end"] - P.BOOM_START_X + 2, 0, P.BOOM_Z, P.BOOM_ID)), TUBE)
    items["joiner_front_10x8"] = (cyl_y(P.SPAR_FRONT["x"], P.SPAR_FRONT["z"], -250, 500, P.SPAR_FRONT["d"]), TUBE)
    items["joiner_rear_6"] = (cyl_y(P.SPAR_REAR["x"], P.SPAR_REAR["z"], -135, 270, P.SPAR_REAR["d"]), TUBE)
    items["wing_left"] = (wing_panel(1), FOAM)
    items["wing_right"] = (wing_panel(-1), FOAM)
    items["h_stab"] = (hs, FOAM)
    items["fin"] = (fin, FOAM)
    if config == "tractor":
        items["motor_2826"] = (cyl_x(-36, 30, 0, P.TRACTOR_AXIS_Z, P.MOTOR_DIA), METAL)
    else:
        items["motor_2826"] = (cyl_x(P.L + 2, 30, 0, P.PUSHER_AXIS_Z, P.MOTOR_DIA), METAL)
    return items, tg


def export_assembly(config):
    items, _ = airframe(config)
    asm = cq.Assembly(name="cf_wing_rev2_" + config)
    for n, (s, c) in items.items():
        asm.add(s, name=n, color=c)
    suffix = "" if config == "tractor" else "_pusher"
    asm.save(os.path.join(OUT, "assembly" + suffix + ".step"))
    comp = cq.Compound.makeCompound([s.val() for s, _ in items.values()])
    cq.exporters.export(cq.Workplane().add(comp), os.path.join(OUT, "assembly" + suffix + ".stl"), **TOL)
    return items


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    # CF plates, flat, as cut
    for name in PL.PLATES:
        write(plate_solid(name), "cf_plates", name)
        write_dxf(name)
    # printed parts in print orientation
    _, _, _, tg = tail()
    pp = PT.all_parts("pusher", tg["boom_end"])
    printed = {
        "nose_frame_firewall": lay_flat_x(pp["nose_frame"]),
        "frame_x3": lay_flat_x(pp["frame_90"]),
        "frame_boom": lay_flat_x(pp["frame_%d" % P.FRAME_BOOM]),
        "rear_bulkhead": lay_flat_x(pp["rear_bulkhead"]),
        "spar_block_front": to_origin(pp["spar_block_front"]),
        "spar_block_rear": to_origin(pp["spar_block_rear"]),
        "battery_tray": to_origin(PT.battery_tray()),
        "camera_mount": to_origin(pp["camera_mount"]),
        "tail_mount": to_origin(pp["tail_mount"]),
        "pusher_mount_optional": to_origin(pp["pusher_mount"]),
        "gear_block_main_optional": flip(PT.gear_block_main(270)),
        "gear_block_nose_optional": flip(PT.gear_block_nose()),
    }
    for n, s in printed.items():
        write(s, "printed", n)
    for c in ("tractor", "pusher"):
        export_assembly(c)
    print("exported to", OUT)


if __name__ == "__main__":
    main()
