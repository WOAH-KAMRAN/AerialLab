#!/usr/bin/env python3
"""Render preview PNGs of the rev 4 model with OpenSCAD (needs xvfb-run)."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
COL = {"cf_": "[0.18,0.19,0.22]", "pla": "[0.95,0.55,0.1]", "eq_battery": "[0.3,0.35,0.85]", "eq_fc": "[0.1,0.6,0.25]",
       "eq_pi": "[0.1,0.6,0.25]", "eq_esc": "[0.6,0.1,0.6]", "eq_vtx": "[0.1,0.6,0.25]", "eq_cam": "[0.1,0.1,0.1]",
       "eq_gps": "[0.85,0.85,0.85]", "eq_motor": "[0.7,0.7,0.75]", "prop": "[0.2,0.2,0.2,0.25]", "boom": "[0.1,0.1,0.1]",
       "joiners": "[0.1,0.1,0.1]", "hs": "[0.92,0.92,0.95]", "fin": "[0.92,0.92,0.95]", "tail_mount": "[0.95,0.55,0.1]",
       "wing": "[0.92,0.92,0.95,0.55]"}


def scad_for(config, skip=()):
    d = os.path.join(HERE, "build", config)
    lines = []
    for f in sorted(os.listdir(d)):
        if not f.endswith(".stl") or any(f.startswith(s) for s in skip):
            continue
        name = f[:-4]
        col = next((v for k, v in COL.items() if name.startswith(k)), "[0.5,0.5,0.5]")
        lines.append('color(%s) import("%s");' % (col, os.path.join(d, f)))
    return "\n".join(lines)


def render(config, out, camera, size=(1400, 1000), skip=(), proj="p"):
    p = os.path.join(HERE, "build", "_%s.scad" % os.path.basename(out))
    open(p, "w").write(scad_for(config, skip))
    subprocess.run(["xvfb-run", "-a", "openscad", "-o", out, "--imgsize=%d,%d" % size, "--colorscheme=Tomorrow",
                    "--camera=" + camera, "--projection=" + proj, p], capture_output=True)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "png")
    os.makedirs(out, exist_ok=True)
    # camera = translate x,y,z, rot x,y,z, distance
    render("tractor", os.path.join(out, "a_full_tractor.png"), "320,0,40,62,0,215,1900")
    render("tractor", os.path.join(out, "b_fuselage_tractor.png"), "170,0,55,62,0,220,780", skip=("wing", "hs", "fin", "joiners"))
    render("tractor", os.path.join(out, "c_fuselage_cutaway.png"), "170,0,55,75,0,180,720",
           skip=("wing", "hs", "fin", "joiners", "cf_side_left", "cf_up_deck"))
    render("tractor", os.path.join(out, "d_fuselage_rear.png"), "250,0,70,65,0,140,700", skip=("wing", "hs", "fin", "joiners"))
    render("tractor", os.path.join(out, "e_side.png"), "380,0,60,90,0,0,1250", size=(1800, 700), proj="o")
