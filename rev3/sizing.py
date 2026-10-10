#!/usr/bin/env python3
"""Sizing, weight & balance, and static thrust / current estimate.
Writes sizing_report.md next to this file. Numbers are first-order estimates:
weigh real parts and check current with a wattmeter before flying."""
import math
import os

import params as P

RHO = 1.225
G = 9.81


def wing():
    S = P.SPAN * P.CHORD * 1e-6
    return dict(S=S, AR=P.SPAN ** 2 / (P.SPAN * P.CHORD), mac=P.CHORD, ac_x=P.X_LE + 0.25 * P.CHORD)


def tail_geometry():
    w = wing()
    S, c, b = w["S"], w["mac"] / 1000, P.SPAN / 1000
    lt = P.TAIL_ARM / 1000
    sh = P.VH * S * c / lt * 1e6
    sv = P.VV * S * b / lt * 1e6
    hs_span = P.HS_SPAN
    hs_chord = round(sh / hs_span)
    fin_h = P.FIN_H
    fin_tip = P.FIN_TIP
    fin_root = round(2 * sv / fin_h - fin_tip)
    tail_ac = w["ac_x"] + P.TAIL_ARM
    hs_le = tail_ac - 0.25 * hs_chord
    return dict(sh=sh, sv=sv, hs_span=hs_span, hs_chord=hs_chord, fin_h=fin_h, fin_root=fin_root,
                fin_tip=fin_tip, hs_le=hs_le, tail_ac=tail_ac, boom_end=round(hs_le + hs_chord + 5))


def _area(poly):
    return abs(sum(x1 * y2 - x2 * y1 for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]))) / 2


def plate_area(name):
    """Net area of a plate: outline minus windows and holes."""
    import plates as PL
    f, _, _ = PL.PLATES[name]
    outline, holes, windows = f()
    corner_loss = (4 - math.pi) * PL.CORNER_R ** 2
    return (_area(outline) - sum(_area(w) - len(w) * corner_loss / 4 for w in windows)
            - sum(math.pi * d * d / 4 for _, _, d, _ in holes))


def cf_plate_mass():
    side = plate_area("side_plate") * P.T_SIDE * P.CF_DENSITY
    bot = plate_area("bottom_plate") * P.T_BOT * P.CF_DENSITY
    deck = plate_area("upper_deck") * P.T_DECK * P.CF_DENSITY
    return side, bot, deck


_MID_DECK = {}


def mid_deck_mass(density=1.24e-3):
    """Printed middle deck at 100% (a 2 mm part is all perimeters)."""
    if "g" not in _MID_DECK:
        import parts as PT
        _MID_DECK["g"] = PT.middle_deck().val().Volume() * density
    return _MID_DECK["g"]


def tube_mass(od, id_, length):
    return math.pi / 4 * (od ** 2 - id_ ** 2) * length * P.CF_DENSITY


def mass_items(config, battery_x):
    tg = tail_geometry()
    side, bot, deck = cf_plate_mass()
    boom_len = tg["boom_end"] - P.BOOM_START_X
    fx = P.L / 2
    items = [
        ("Side plates x2 (CF %.1f)" % P.T_SIDE, 2 * side, fx),
        ("Bottom plate (CF %.1f)" % P.T_BOT, bot, fx),
        ("Upper deck (CF %.1f)" % P.T_DECK, deck, fx),
        ("Middle deck, printed %.0f mm, 2 halves" % P.T_MID_DECK, mid_deck_mass(), fx),
        ("Printed nose frame, 4 frames, rear bulkhead, spar blocks", 145, 0.56 * P.L),
        ("M3 hardware + nuts", 40, P.L / 2),
        ("Boom %dx%d, %d mm" % (P.BOOM_OD, P.BOOM_ID, boom_len), tube_mass(P.BOOM_OD, P.BOOM_ID, boom_len), (P.BOOM_START_X + tg["boom_end"]) / 2),
        ("Tail surfaces (6 mm Depron) + tail mount", 45 * (P.SPAN / 1500) ** 2, tg["tail_ac"]),
        ("Wing panels (foam, sleeves, 2 servos, covering)", 300 * (P.SPAN / 1500) ** 2, P.X_LE + 0.40 * P.CHORD),
        ("Joiners: 8x6x%d + 6x4x%d" % (P.JOINER_FRONT_LEN, P.JOINER_REAR_LEN), tube_mass(8, 6, P.JOINER_FRONT_LEN) + tube_mass(6, 4, P.JOINER_REAR_LEN), P.X_LE + 0.4 * P.CHORD),
        ("Elevator + rudder servos (9 g, middle bay) + pushrods", 18 + 15, 150),
        ("ESC 30-40 A (stays at the nose in both configs)", 30, 70),
        ("Flight controller", 10, P.FC_X),
        ("Receiver", 6, P.L - 80),
        ("FPV camera + VTX + antenna", 30, 50),
        ("GPS", 15, 105),
        ("Nose cover (Depron/coro)", 20, 45),
        ("Wiring, connectors, velcro", 40, P.L / 2),
        ("Battery 3S 2200 mAh + tray", 195, battery_x),
    ]
    if config == "tractor":
        items += [("Motor 2826 1400 kv + prop adapter", 60, -18), ("Prop 8in", 12, -45)]
    else:
        items += [("Motor 2826 1400 kv + prop adapter", 60, P.L + 22), ("Prop 8in", 12, P.L + 45),
                  ("Pusher mount", 14, P.L - 20)]
    return items


def cg(items):
    m = sum(i[1] for i in items)
    return m, sum(i[1] * i[2] for i in items) / m


def solve_battery(config, target):
    lo, hi = -100, 400
    for _ in range(60):
        mid = (lo + hi) / 2
        if cg(mass_items(config, mid))[1] < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ------------------------------------------------ motor + prop (static)
MOTOR = dict(kv=1400, rm=0.09, i0=1.2)          # typical 2826 1400 kv; check your datasheet
PROPS = {"8x4": (0.105, 0.042), "8x5": (0.110, 0.052), "8x6": (0.115, 0.065)}   # static Ct, Cp (APC-E class)


def static_point(ct, cp, v_batt=11.1, r_batt=0.03, r_esc=0.005):
    D = P.PROP_DIA / 1000
    kt = 60 / (2 * math.pi * MOTOR["kv"])
    rpm = 1000
    for _ in range(200):
        n = rpm / 60
        q = cp * RHO * n ** 2 * D ** 5 / (2 * math.pi)
        i = q / kt + MOTOR["i0"]
        v = v_batt - i * (r_batt + r_esc)
        rpm_new = (v - i * MOTOR["rm"]) * MOTOR["kv"]
        rpm = 0.7 * rpm + 0.3 * rpm_new
    n = rpm / 60
    t = ct * RHO * n ** 2 * D ** 4
    pshaft = cp * RHO * n ** 3 * D ** 5
    return dict(rpm=rpm, thrust_g=t / G * 1000, amps=i, watts=v * i, pshaft=pshaft)


def pitch_speed(pitch_in, rpm):
    return pitch_in * 0.0254 * rpm / 60


def main():
    w = wing()
    tg = tail_geometry()
    cg_target = P.X_LE + 0.27 * P.CHORD
    out = []
    o = out.append
    o("# Sizing report (generated by sizing.py)\n")
    o("All x stations are mm aft of the side plate front edge. Estimates, so weigh the real parts.\n")
    o("## Wing\n")
    o("| item | value |\n|---|---|")
    o("| span | %d mm |" % P.SPAN)
    o("| chord (rectangular) | %d mm |" % P.CHORD)
    o("| area | %.3f m² (%.1f dm²) |" % (w["S"], w["S"] * 100))
    o("| aspect ratio | %.1f |" % w["AR"])
    o("| airfoil | Clark Y or similar flat-bottom section, ~11%% thick (%.0f mm) |" % (0.11 * P.CHORD))
    o("| incidence | %.1f° to the deck line |" % P.INCIDENCE_DEG)
    o("| leading edge at root | x = %d |" % P.X_LE)
    o("| front spar (25%% chord) | x = %.0f, z = %.0f, %g mm tube |" % (P.SPAR_FRONT["x"], P.SPAR_FRONT["z"], P.SPAR_FRONT["d"]))
    o("| rear spar (65%% chord) | x = %.0f, z = %.0f, %g mm tube |" % (P.SPAR_REAR["x"], P.SPAR_REAR["z"], P.SPAR_REAR["d"]))
    o("| panel span each side | %.0f mm (fuselage is %.0f wide) |" % ((P.SPAN - P.W - 2 * P.T_SIDE) / 2, P.W + 2 * P.T_SIDE))
    o("| ailerons | outer 45%% of each panel, 25%% chord (%.0f mm) |" % (0.25 * P.CHORD) + "")
    o("")
    o("## Tail\n")
    o("| item | value |\n|---|---|")
    o("| tail arm (wing AC to tail AC) | %d mm |" % P.TAIL_ARM)
    o("| H-stab: Vh %.2f | %.0f cm², %d x %d mm, elevator 40 mm |" % (P.VH, tg["sh"] / 100, tg["hs_span"], tg["hs_chord"]))
    o("| fin: Vv %.3f | %.0f cm², root %d, tip %d, height %d, rudder 50 mm |" % (P.VV, tg["sv"] / 100, tg["fin_root"], tg["fin_tip"], tg["fin_h"]))
    o("| H-stab leading edge | x = %.0f |" % tg["hs_le"])
    o("| boom | %dx%d CF tube, x = %d to %d (%d mm long, cut from 1000) |" % (P.BOOM_OD, P.BOOM_ID, P.BOOM_START_X, tg["boom_end"], tg["boom_end"] - P.BOOM_START_X))
    o("| boom held by | frame at x = %d and rear bulkhead at x = %d |" % (P.FRAME_BOOM, P.BULKHEAD_X))
    o("")
    o("## Weight and balance\n")
    o("CG target: **x = %.0f mm** (27%% chord, %.0f mm behind the wing leading edge). First flights anywhere from 25 to 30%% (x = %.0f to %.0f).\n" %
      (cg_target, cg_target - P.X_LE, P.X_LE + 0.25 * P.CHORD, P.X_LE + 0.30 * P.CHORD))
    for config in ("tractor", "pusher"):
        bx = solve_battery(config, cg_target)
        items = mass_items(config, bx)
        m, x = cg(items)
        o("### %s\n" % config.capitalize())
        o("| item | g | x |\n|---|---:|---:|")
        for name, g, xi in items:
            o("| %s | %.0f | %.0f |" % (name, g, xi))
        o("| **AUW** | **%.0f** | CG %.0f |" % (m, x))
        o("")
        fits = 0 <= bx - 52 and bx + 52 <= P.L
        tray = P.BATTERY_TRAY_TRACTOR_X if config == "tractor" else P.BATTERY_TRAY_PUSHER_X
        o("Battery centre for balance: **x = %.0f mm** (a 105 mm pack spans %.0f to %.0f). %s "
          "The battery tray station for this layout is x = %d; slide the pack on the tray to fine-tune.\n" %
          (bx, bx - 52, bx + 52, "Fits in the lower bay." if fits else "**Outside the bay: add nose weight or move parts.**", tray))
    m_t, _ = cg(mass_items("tractor", solve_battery("tractor", cg_target)))
    W_N = m_t / 1000 * G
    o("## Performance (tractor AUW)\n")
    o("| item | value |\n|---|---|")
    o("| wing loading | %.1f g/dm² |" % (m_t / (w["S"] * 100)))
    for clmax in (1.0, 1.2):
        o("| stall speed (CLmax %.1f) | %.1f m/s |" % (clmax, math.sqrt(2 * W_N / (RHO * w["S"] * clmax))))
    vc = math.sqrt(2 * W_N / (RHO * w["S"] * 0.45))
    o("| cruise at CL 0.45 | %.1f m/s (%.0f km/h) |" % (vc, vc * 3.6))
    o("| Reynolds number at cruise | %.0f k |" % (vc * P.CHORD / 1000 / 1.5e-5 / 1000))
    p_cruise = W_N / 8.0 * vc / 0.45          # L/D 8, prop x motor efficiency 0.45
    i_cruise = p_cruise / 11.1
    o("| cruise power, L/D 8, 45%% propulsive eff. | %.0f W, %.1f A |" % (p_cruise, i_cruise))
    o("| flight time, 2200 mAh to 80%% | about %.0f min cruising |" % (2.2 * 0.8 / i_cruise * 60))
    o("")
    o("## Motor + prop, static, 3S\n")
    o("Model: 2826 1400 kv, Rm %.2f Ω, I0 %.1f A, 3S at 11.1 V under load. Ct/Cp are typical static values for APC-E style props.\n" % (MOTOR["rm"], MOTOR["i0"]))
    o("| prop | rpm | thrust g | current A | power W | thrust/weight | pitch speed m/s |\n|---|---:|---:|---:|---:|---:|---:|")
    for name, (ct, cp) in PROPS.items():
        r = static_point(ct, cp)
        o("| %s | %.0f | %.0f | %.1f | %.0f | %.2f | %.1f |" % (name, r["rpm"], r["thrust_g"], r["amps"], r["watts"], r["thrust_g"] / m_t, pitch_speed(int(name[2]), r["rpm"])))
    o("")
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "sizing_report.md"), "w") as f:
        f.write("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
