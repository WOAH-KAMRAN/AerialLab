"""Rev 2 CF plates: outlines, M3 holes and lightening windows.

Windows are straight-sided triangles / slots with small corner radii, so they can
be made by drilling the corners (6 mm) and joining the holes with a cut-off disc.
Geometry only (pure Python); model.py turns it into CadQuery solids.
"""
import math

import params as P

CORNER_R = 3.0      # window corner radius: drill 6 mm at each corner
WEB = 7.0           # minimum CF web between windows
HOLE_CLEAR = 5.0    # min CF from a window to any bolt hole edge


# ------------------------------------------------------------------ helpers
def _incentre(tri):
    (ax, ay), (bx, by), (cx, cy) = tri
    a = math.dist((bx, by), (cx, cy))
    b = math.dist((ax, ay), (cx, cy))
    c = math.dist((ax, ay), (bx, by))
    p = a + b + c
    ix, iy = (a * ax + b * bx + c * cx) / p, (a * ay + b * by + c * cy) / p
    s = p / 2
    area = abs((bx - ax) * (cy - ay) - (cx - ax) * (by - ay)) / 2
    return (ix, iy), area / s


def inset_triangle(tri, d):
    (ix, iy), r = _incentre(tri)
    if r - d < CORNER_R + 1.0:
        return None
    k = (r - d) / r
    return [(ix + (x - ix) * k, iy + (y - iy) * k) for x, y in tri]


def _seg_dist(px, py, a, b):
    (x1, y1), (x2, y2) = a, b
    dx, dy = x2 - x1, y2 - y1
    t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - x1 - t * dx, py - y1 - t * dy)


def _inside(px, py, poly):
    inside = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > py) != (y2 > py) and px < x1 + (py - y1) * (x2 - x1) / (y2 - y1):
            inside = not inside
    return inside


def poly_hole_clear(poly, holes):
    for x, y, d, _ in holes:
        if _inside(x, y, poly):
            return False
        if min(_seg_dist(x, y, a, b) for a, b in zip(poly, poly[1:] + poly[:1])) < d / 2 + HOLE_CLEAR:
            return False
    return True


def poly_in_outline(poly, outline, margin):
    return all(_inside(x, y, outline) and
               min(_seg_dist(x, y, a, b) for a, b in zip(outline, outline[1:] + outline[:1])) >= margin
               for x, y in poly)


def truss_band(x0, x1, z0, z1, pitch, holes, outline, margin=6):
    """Warren-truss row of alternating triangles between z0 and z1."""
    n = max(1, round((x1 - x0) / pitch))
    p = (x1 - x0) / n
    out = []
    for k in range(n):
        xa, xb = x0 + k * p, x0 + (k + 1) * p
        tris = [[(xa, z0), (xb, z0), ((xa + xb) / 2, z1)]]                 # apex up
        if k < n - 1:
            tris.append([((xa + xb) / 2, z1), ((xb + xb + p) / 2, z1), (xb, z0)])  # apex down
        for t in tris:
            w = inset_triangle(t, WEB / 2)
            if w and poly_hole_clear(w, holes) and poly_in_outline(w, outline, margin):
                out.append(w)
    return out


def xbrace(x0, x1, z0, z1, holes, outline, margin=6):
    """Rectangle panel split by both diagonals into 4 triangles (X-brace)."""
    c = ((x0 + x1) / 2, (z0 + z1) / 2)
    corners = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    out = []
    for i in range(4):
        t = inset_triangle([corners[i], corners[(i + 1) % 4], c], WEB / 2)
        if t and poly_hole_clear(t, holes) and poly_in_outline(t, outline, margin):
            out.append(t)
    return out


def slots_row(x0, x1, y0, y1, length, holes, outline, margin=6):
    """Row of rectangular slots between y0..y1, keeping only those clear of holes."""
    out = []
    x = x0
    while x + length <= x1:
        r = [(x, y0), (x + length, y0), (x + length, y1), (x, y1)]
        if poly_hole_clear(r, holes) and poly_in_outline(r, outline, margin):
            out.append(r)
            x += length + WEB
        else:
            x += 4
    return out


def rounded(poly, r=CORNER_R, seg=6):
    """Sampled rounded polygon (for drawings only)."""
    pts = []
    n = len(poly)
    for i in range(n):
        p0, p1, p2 = poly[i - 1], poly[i], poly[(i + 1) % n]
        v1 = (p0[0] - p1[0], p0[1] - p1[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        l1, l2 = math.hypot(*v1), math.hypot(*v2)
        u1, u2 = (v1[0] / l1, v1[1] / l1), (v2[0] / l2, v2[1] / l2)
        ang = math.acos(max(-1, min(1, u1[0] * u2[0] + u1[1] * u2[1])))
        t = r / math.tan(ang / 2)
        a = (p1[0] + u1[0] * t, p1[1] + u1[1] * t)
        b = (p1[0] + u2[0] * t, p1[1] + u2[1] * t)
        bis = (u1[0] + u2[0], u1[1] + u2[1])
        bl = math.hypot(*bis)
        c = (p1[0] + bis[0] / bl * r / math.sin(ang / 2), p1[1] + bis[1] / bl * r / math.sin(ang / 2))
        a0 = math.atan2(a[1] - c[1], a[0] - c[0])
        a1 = math.atan2(b[1] - c[1], b[0] - c[0])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for j in range(seg + 1):
            th = a0 + da * j / seg
            pts.append((c[0] + r * math.cos(th), c[1] + r * math.sin(th)))
    return pts


# ------------------------------------------------------------------ plates
def round_rect(x0, x1, y0, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def side_plate():
    L, H = P.L, P.H
    outline = [(0, 18), (22, 0), (L, 0), (L, H), (P.X_TOP_BREAK, H), (0, P.H_FRONT)]
    holes = []
    for z in P.FW_SIDE_HOLE_Z:
        holes.append((P.FW_SIDE_HOLE_X, z, P.M3, "nose frame"))
    for x in P.FRAMES:
        for z in P.FRAME_SIDE_Z:
            holes.append((x, z, P.M3, "frame"))
    for z in P.BULKHEAD_SIDE_Z:
        holes.append((P.BULKHEAD_X, z, P.M3, "rear bulkhead"))
    for s, b in ((P.SPAR_FRONT, P.SPAR_BLOCK_FRONT), (P.SPAR_REAR, P.SPAR_BLOCK_REAR)):
        holes.append((s["x"], s["z"], s["hole"], "spar %g" % s["d"]))
        holes.append((s["x"] - b["bolt_dx"], s["z"], P.M3, "spar block"))
        holes.append((s["x"] + b["bolt_dx"], s["z"], P.M3, "spar block"))
    # one window per bay between frames: 4 straight cuts + 4 corner drills each
    z0 = P.FRAME_SIDE_Z[0] + P.M3 / 2 + HOLE_CLEAR + 1
    z1 = P.FRAME_SIDE_Z[-1] - P.M3 / 2 - HOLE_CLEAR - 1
    posts = [P.FW_DEPTH - 2] + P.FRAMES + [P.BOOM_BULKHEAD_X[0]]
    windows = []
    for a, b in zip(posts, posts[1:]):
        w = round_rect(a + 10, b - 10, z0, z1)
        if P.CUT_WINDOWS and poly_hole_clear(w, holes) and poly_in_outline(w, outline, 6):
            windows.append(w)
    return outline, holes, windows


def bottom_plate():
    w = P.W + 2 * P.T_SIDE
    outline = [(0, -w / 2 + 8), (8, -w / 2), (P.L, -w / 2), (P.L, w / 2), (8, w / 2), (0, w / 2 - 8)]
    holes = []
    fx, fy = P.FW_BOTTOM_HOLE
    holes += [(fx, s * fy, P.M3, "nose frame") for s in (-1, 1)]
    for x in P.FRAMES:
        holes += [(x, s * P.FRAME_BOTTOM_Y, P.M3, "frame") for s in (-1, 1)]
    holes += [(P.BULKHEAD_X, s * P.BULKHEAD_BOTTOM_Y, P.M3, "rear bulkhead") for s in (-1, 1)]
    for name, pts in (("trike nose", P.GEAR_TRIKE_NOSE), ("trike main", P.GEAR_TRIKE_MAIN),
                      ("taildragger main", P.GEAR_TAILDRAGGER_MAIN), ("battery tray", P.BATTERY_TRAY_HOLES)):
        for x, y in pts:
            for s in (-1, 1):
                holes.append((x, s * y, name == "battery tray" and P.M3 or P.M3, name))
    # two long slots only, under the open battery bay
    windows = []
    for a, b in ((P.FRAMES[0], P.FRAMES[1]), (P.FRAMES[2], P.FRAMES[3])):
        r = round_rect(a + 12, b - 12, -12, 12)
        if P.CUT_WINDOWS and poly_hole_clear(r, holes):
            windows.append(r)
    return outline, holes, windows


def _rect_pattern(xc, a, b, label):
    return [(xc + sx * a / 2, sy * b / 2, P.M3, label) for sx in (-1, 1) for sy in (-1, 1)]


def deck(which):
    w = P.DECK_W
    x0 = P.MID_DECK_X0 if which == "middle" else 0
    outline = [(x0, -w / 2), (P.L, -w / 2), (P.L, w / 2), (x0, w / 2)]
    holes = []
    fx, fy = P.FW_MID_DECK_HOLE if which == "middle" else P.FW_UP_DECK_HOLE
    holes += [(fx, s * fy, P.M3, "nose frame") for s in (-1, 1)]
    for x in P.FRAMES + ([P.BULKHEAD_X] if which == "upper" else []):
        holes += [(x, s * P.DECK_HOLE_Y, P.M3, "frame" if x in P.FRAMES else "rear bulkhead") for s in (-1, 1)]
    if which == "middle":
        holes += _rect_pattern(P.FC_X, 30.5, 30.5, "FC 30.5")
        holes += _rect_pattern(P.FC_X, 20, 20, "FC 20")
        holes += _rect_pattern(P.PI_X, 58, 23, "Pi Zero 2")
    else:
        for s in (P.SPAR_FRONT, P.SPAR_REAR):
            holes += [(s["x"], sy * P.SPAR_DECK_Y, P.M3, "spar block") for sy in (-1, 1)]
        holes += _rect_pattern(P.VTX_X, 20, 20, "VTX 20x20")
        for name, pts in (("camera", P.CAM_HOLES), ("GPS", P.GPS_HOLES), ("antenna", P.ANT_HOLES)):
            for x, y in pts:
                holes += [(x, s * y, P.M3, name) for s in (-1, 1)]
        holes += [(x, 0, P.M3, "boom pin") for x in (P.FRAME_BOOM, P.BULKHEAD_X)]
    return outline, holes, []


PLATES = {
    "side_plate": (side_plate, lambda: P.T_SIDE, 2),
    "bottom_plate": (bottom_plate, lambda: P.T_BOT, 1),
    "upper_deck": (lambda: deck("upper"), lambda: P.T_DECK, 1),
}


def check_all(min_gap=2.5, min_edge=2.5):
    """Print hole-to-hole and hole-to-edge problems for every plate."""
    bad = 0
    for name, (f, _, _) in PLATES.items():
        outline, holes, windows = f()
        for i, (x1, y1, d1, l1) in enumerate(holes):
            for x2, y2, d2, l2 in holes[i + 1:]:
                if (abs(x1 - x2) > 1e-6 or abs(y1 - y2) > 1e-6) and math.hypot(x1 - x2, y1 - y2) - (d1 + d2) / 2 < min_gap:
                    print("  %s: %s (%.1f,%.1f) too close to %s (%.1f,%.1f)" % (name, l1, x1, y1, l2, x2, y2))
                    bad += 1
            e = min(_seg_dist(x1, y1, a, b) for a, b in zip(outline, outline[1:] + outline[:1])) - d1 / 2
            if e < min_edge or not _inside(x1, y1, outline):
                print("  %s: %s (%.1f,%.1f) edge distance %.1f" % (name, l1, x1, y1, e))
                bad += 1
    return bad
