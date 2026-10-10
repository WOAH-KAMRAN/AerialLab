"""Rev 2 printed parts (CadQuery), built in airframe coordinates.

Every part bolts to the CF plates with M3: clearance holes plus hex pockets
for captive nuts. export.py lays each one flat for printing.
"""
import cadquery as cq

import params as P

HOLE = 3.4                 # M3 clearance in PLA
NUT_AF = P.M3_NUT_AF + 0.3
NUT_T = 2.8
WI = P.W - 0.4             # printed width between the side plates
Y0, Y1 = -WI / 2, WI / 2


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl_x(x0, length, y, z, d):
    return cq.Workplane("YZ").center(y, z).circle(d / 2).extrude(length).translate((x0, 0, 0))


def cyl_y(x, z, y0, length, d):
    return cq.Workplane("XZ").center(x, z).circle(d / 2).extrude(-length).translate((0, y0, 0))


def cyl_z(x, y, z0, length, d):
    return cq.Workplane("XY").center(x, y).circle(d / 2).extrude(length).translate((0, 0, z0))


def hex_z(x, y, z0, t=NUT_T):
    return cq.Workplane("XY").center(x, y).polygon(6, NUT_AF / 0.866).extrude(t).translate((0, 0, z0))


def boom_pin(part, x):
    """Vertical M3 x 35 through the upper deck and the boom, into a captive nut just under the boom.
    The hole carries on through the middle deck into the mid beam so the screw tip has room.
    The nut pocket is open to the front face so the nut slides in."""
    zt = P.Z_UP_DECK
    zn = P.BOOM_PIN_NUT_Z
    part = part.cut(cyl_z(x, 0, zn - 8, zt - zn + 9, HOLE))
    part = part.cut(hex_z(x, 0, zn))
    part = part.cut(box(x - 20, x, -NUT_AF / 2, NUT_AF / 2, zn, zn + NUT_T))
    return part


def side_screw(part, x, z, depth=12, nut_at=7):
    """M3 from outside each side plate into the part, captive nut in a slot open at the bottom/top."""
    for s in (-1, 1):
        ye = s * WI / 2
        part = part.cut(cyl_y(x, z, ye - s * depth if s > 0 else ye, depth, HOLE))
        yn = ye - s * nut_at
        part = part.cut(box(x - NUT_AF / 2, x + NUT_AF / 2, yn - NUT_T / 2, yn + NUT_T / 2, z - 3.3, z + 3.3))
    return part


def vert_screw(part, x, y, z_face, up=True, depth=12, nut_at=6):
    """M3 entering a horizontal face (bottom face if up=True) with a hex pocket inside."""
    if up:
        part = part.cut(cyl_z(x, y, z_face - 0.1, depth, HOLE)).cut(hex_z(x, y, z_face + nut_at))
    else:
        part = part.cut(cyl_z(x, y, z_face - depth + 0.1, depth, HOLE)).cut(hex_z(x, y, z_face - nut_at - NUT_T))
    return part


# ------------------------------------------------------------------ frames
def frame(x, boom=False):
    t = P.FRAME_T / 2
    leg, beam = P.FRAME_LEG, P.FRAME_BEAM
    zm, zu = P.Z_MID_DECK, P.Z_UP_DECK
    f = box(x - t, x + t, Y0, Y0 + leg, 0, zu).union(box(x - t, x + t, Y1 - leg, Y1, 0, zu))
    f = f.union(box(x - t, x + t, Y0, Y1, zm - beam, zm)).union(box(x - t, x + t, Y0, Y1, zu - beam, zu))
    if boom:
        f = f.union(box(x - t, x + t, Y0, Y1, zm + P.T_MID_DECK + 0.3, zu - beam))        # fill the upper bay
        f = f.cut(cyl_x(x - t - 1, P.FRAME_T + 2, 0, P.BOOM_Z, P.BOOM_OD + 0.3))
        f = boom_pin(f, x)
    for z in P.FRAME_SIDE_Z:
        f = side_screw(f, x, z)
    for s in (-1, 1):
        f = vert_screw(f, x, s * P.FRAME_BOTTOM_Y, 0, up=True)
        f = vert_screw(f, x, s * P.DECK_HOLE_Y, zm, up=False)
        f = vert_screw(f, x, s * P.DECK_HOLE_Y, zu, up=False)
    return f


def motor_holes_x(part, x_face, z, depth=20):
    pts = [(0, 0)]
    pts += [(8, 0), (-8, 0), (0, 9.5), (0, -9.5)]
    pts += [(a * P.MOTOR_SQUARE / 2, b * P.MOTOR_SQUARE / 2) for a in (-1, 1) for b in (-1, 1)]
    for i, (y, dz) in enumerate(pts):
        d = P.MOTOR_SHAFT_CLEAR if i == 0 else HOLE
        part = part.cut(cyl_x(x_face - 1, depth, y, z + dz, d))
    return part


def nose_frame():
    """Tractor firewall + front frame in one: battery goes in under it."""
    d, wall, front = P.FW_DEPTH, 8, P.FW_FRONT
    zm, zu = P.Z_MID_DECK, P.Z_UP_DECK
    f = box(0, d, Y0, Y0 + wall, 0, zu).union(box(0, d, Y1 - wall, Y1, 0, zu))       # side walls
    f = f.union(box(0, front, Y0, Y1, zm, zu))                                          # motor wall
    f = f.union(box(front, d, Y0, Y1, zm - P.FRAME_BEAM, zm))                           # mid beam
    ux, uy = P.FW_UP_DECK_HOLE
    for s in (-1, 1):
        f = f.union(box(ux - 6, d, s * uy - 6, s * uy + 6, zm, zu))                     # upper deck bosses
    f = motor_holes_x(f, 0, P.TRACTOR_AXIS_Z)
    for z in P.FW_SIDE_HOLE_Z:
        f = side_screw(f, P.FW_SIDE_HOLE_X, z, depth=wall + 4, nut_at=wall - 2)
    bx, by = P.FW_BOTTOM_HOLE
    mx, my = P.FW_MID_DECK_HOLE
    for s in (-1, 1):
        f = vert_screw(f, bx, s * by, 0, up=True)
        f = vert_screw(f, mx, s * my, zm, up=False, nut_at=5)
        f = vert_screw(f, ux, s * uy, zu, up=False)
    return f


def rear_bulkhead():
    x0, x1 = P.BOOM_BULKHEAD_X
    zm, zu = P.Z_MID_DECK, P.Z_UP_DECK
    b = box(x0, x1, Y0, Y1, 0, zu)
    b = b.cut(box(x0 - 1, x1 + 1, -15, 15, 10, zm - 8).edges("|X").fillet(4))           # wire pass-through, lower bay
    b = b.cut(cyl_x(x0 - 1, P.BULKHEAD_T + 2, 0, P.BOOM_Z, P.BOOM_OD + 0.3))
    b = boom_pin(b, P.BULKHEAD_X)
    for z in P.BULKHEAD_SIDE_Z:
        b = side_screw(b, P.BULKHEAD_X, z)
    for s in (-1, 1):
        b = vert_screw(b, P.BULKHEAD_X, s * P.BULKHEAD_BOTTOM_Y, 0, up=True)
        b = vert_screw(b, P.BULKHEAD_X, s * P.DECK_HOLE_Y, zu, up=False)
    return b


def spar_block(s, b):
    zb = P.Z_UP_DECK + P.T_DECK
    x0, x1 = s["x"] - b["depth"] / 2, s["x"] + b["depth"] / 2
    blk = box(x0, x1, Y0, Y1, zb, b["top"])
    blk = blk.cut(box(x0 - 1, x1 + 1, -14, 14, zb - 1, s["z"] - s["d"] / 2 - 4))       # lighten under the bore
    blk = blk.cut(cyl_y(s["x"], s["z"], Y0 - 1, WI + 2, s["d"] + 0.3))
    for dx in (-b["bolt_dx"], b["bolt_dx"]):
        blk = side_screw(blk, s["x"] + dx, s["z"], nut_at=8)
    # deck screws come up from under the upper deck into the solid sides
    for sy in (-1, 1):
        blk = vert_screw(blk, s["x"], sy * P.SPAR_DECK_Y, zb, up=True, nut_at=5)
    blk = blk.cut(cyl_z(s["x"], 0, s["z"], b["top"] - s["z"] + 1, 2.8))                 # joiner lock screw, M3 self-taps
    return blk


def battery_tray():
    x = P.BATTERY_TRAY_TRACTOR_X
    w = P.BATTERY_CLEAR_W - 4
    t = box(x - 55, x + 55, -w / 2, w / 2, 0, 2.5)
    t = t.union(box(x - 55, x + 55, -w / 2, -w / 2 + 2, 0, 6)).union(box(x - 55, x + 55, w / 2 - 2, w / 2, 0, 6))
    for sx in (-1, 1):
        t = t.cut(box(x + sx * 12 - 11, x + sx * 12 + 11, -w / 2 - 1, -w / 2 + 5, -1, 10))
        t = t.cut(box(x + sx * 12 - 11, x + sx * 12 + 11, w / 2 - 5, w / 2 + 1, -1, 10))
        for sy in (-1, 1):
            c = cq.Workplane("XY").center(x + sx * P.BATTERY_TRAY_PITCH / 2, sy * P.BATTERY_TRAY_Y)
            t = t.cut(c.circle(HOLE / 2).extrude(5).translate((0, 0, -1)))
            t = t.cut(c.circle(3.2).workplane(offset=1.0).circle(1.7).loft().translate((0, 0, 1.5)))
    return t


def tail_mount(boom_end):
    r = P.BOOM_OD / 2
    l = 45
    x0 = boom_end - l + 5
    m = cyl_x(x0, l, 0, P.BOOM_Z, P.BOOM_OD + 6)
    m = m.union(box(x0, x0 + l + 15, -25, 25, P.BOOM_Z + r, P.BOOM_Z + r + 4))
    m = m.union(box(x0, x0 + l, -6, 6, P.BOOM_Z - r - 10, P.BOOM_Z))
    m = m.cut(cyl_x(x0 - 1, l - 4, 0, P.BOOM_Z, P.BOOM_OD + 0.3))
    m = m.cut(box(x0 - 1, x0 + l - 4, -0.75, 0.75, P.BOOM_Z - r - 11, P.BOOM_Z))
    for x in (x0 + 12, x0 + 32):
        m = m.cut(cyl_y(x, P.BOOM_Z - r - 5, -7, 14, HOLE))
    for x in (x0 + 15, x0 + l + 7):
        for s in (-1, 1):
            m = m.cut(cyl_z(x, s * 16, P.BOOM_Z + r - 1, 6, HOLE))
    return m


def camera_mount():
    x, dy = P.CAM_HOLES[0]
    z0 = P.Z_UP_DECK + P.T_DECK
    w = P.CAM_W / 2
    m = box(x - 10, x + 10, -w - 2.7, w + 2.7, z0, z0 + 3)
    m = m.union(box(x - 10, x + 10, -w - 2.7, -w - 0.2, z0, z0 + 22)).union(box(x - 10, x + 10, w + 0.2, w + 2.7, z0, z0 + 22))
    for s in (-1, 1):
        m = m.cut(cyl_z(x, s * dy, z0 - 1, 5, HOLE))
    return m.cut(cyl_y(x, z0 + 14, -w - 4, 2 * w + 8, 2.2))


def gear_block_main(xc):
    """Under the bottom plate on the trike or taildragger pattern; takes a bow gear on 2x M3."""
    zb = -P.T_BOT
    g = box(xc - 16, xc + 16, -30, 30, zb - 14, zb)
    g = g.cut(box(xc - 17, xc + 17, -12, 12, zb - 15, zb - 6))                          # lighten
    for sx in (-1, 1):
        for sy in (-1, 1):
            g = vert_screw(g, xc + sx * 10, sy * 22, zb, up=False, nut_at=6)
    for sy in (-1, 1):
        g = vert_screw(g, xc, sy * 22, zb - 14, up=True, nut_at=5)                          # bow gear bolts
    return g


def gear_block_nose():
    (x0, y), (x1, _) = P.GEAR_TRIKE_NOSE
    xc = (x0 + x1) / 2
    zb = -P.T_BOT
    g = box(x0 - 7, x1 + 7, -y - 7, y + 7, zb - 22, zb)
    for x in (x0, x1):
        for s in (-1, 1):
            g = vert_screw(g, x, s * y, zb, up=False, nut_at=6)
    g = g.cut(cyl_z(xc, 0, zb - 23, 19, 3.3))                                              # 3 mm wire leg
    return g.cut(cyl_y(xc, zb - 16, -y - 8, 2 * y + 16, 2.8))                              # lock screw


def middle_deck(half=None):
    """Printed middle deck with windows and FC / Pi standoffs. half = None, "front" or "rear"."""
    from plates import deck
    w, t = P.DECK_W, P.T_MID_DECK
    x0, x1 = P.MID_DECK_X0, P.BOOM_BULKHEAD_X[0] - P.MID_DECK_X1_GAP
    zb = P.Z_MID_DECK
    d = box(x0, x1, -w / 2, w / 2, zb, zb + t)

    # windows: two per bay either side of a centre spine, clear of the screw rows
    posts = [P.FW_MID_DECK_HOLE[0]] + P.FRAMES + [x1 + 6]
    yi, yo = P.MID_DECK_SPINE / 2, w / 2 - P.MID_DECK_RAIL
    for a, b in zip(posts, posts[1:]):
        for s in (-1, 1):
            win = box(a + 9, b - 9, min(s * yi, s * yo), max(s * yi, s * yo), zb - 1, zb + t + 1)
            d = d.cut(win.edges("|Z").fillet(3))
    # solid cross pads under the FC and the Pi, with standoffs on top
    pads = [(P.FC_X, 30.5 + 10, [(30.5, 30.5, 2.8), (20, 20, 2.8)]), (P.PI_X, 58 + 10, [(58, 23, 2.2)])]
    for xc, lx, pats in pads:
        d = d.union(box(xc - lx / 2, xc + lx / 2, -w / 2, w / 2, zb, zb + t))
        for a, bb, hd in pats:
            for sx in (-1, 1):
                for sy in (-1, 1):
                    d = d.union(cyl_z(xc + sx * a / 2, sy * bb / 2, zb + t, P.MID_DECK_BOSS_H, 6))
    for xc, lx, pats in pads:
        for a, bb, hd in pats:
            for sx in (-1, 1):
                for sy in (-1, 1):
                    d = d.cut(cyl_z(xc + sx * a / 2, sy * bb / 2, zb - 1, t + P.MID_DECK_BOSS_H + 2, hd))
    # notches: frame legs run full height past the deck, and so do the nose frame walls and bosses
    ny = WI / 2 - P.FRAME_LEG - 0.3
    for x in P.FRAMES:
        for s in (-1, 1):
            d = d.cut(box(x - P.FRAME_T / 2 - 0.3, x + P.FRAME_T / 2 + 0.3, min(s * ny, s * w), max(s * ny, s * w), zb - 1, zb + t + 1))
    ux, uy = P.FW_UP_DECK_HOLE
    for s in (-1, 1):
        d = d.cut(box(x0 - 1, P.FW_DEPTH + 0.3, min(s * (uy - 6.3), s * w), max(s * (uy - 6.3), s * w), zb - 1, zb + t + 1))
    d = d.cut(cyl_z(P.FRAME_BOOM, 0, zb - 1, t + 2, HOLE))                               # boom pin tip
    # frame / nose frame / bulkhead screws
    _, holes, _ = deck("middle")
    for x, y, _, lab in holes:
        if lab in ("nose frame", "frame"):
            d = d.cut(cyl_z(x, y, zb - 1, t + 2, HOLE))
    if half is None:
        return d
    j, lap = P.MID_DECK_SPLIT_X, P.MID_DECK_LAP
    # front half carries the upper lap (print it flipped), rear half the lower lap (prints as-is, standoffs up)
    if half == "front":
        keep = box(x0 - 1, j - lap, -w, w, zb - 1, zb + 20).union(box(j - lap - 0.01, j + lap, -w, w, zb + t / 2, zb + t + 1))
    else:
        keep = box(j + lap, x1 + 1, -w, w, zb - 1, zb + 20).union(box(j - lap, j + lap + 0.01, -w, w, zb - 1, zb + t / 2))
    return d.intersect(keep)


def all_parts(config="tractor", boom_end=930):
    """name -> solid, in airframe coordinates (tractor only since rev 4)."""
    parts = {"nose_frame": nose_frame()}
    for i, x in enumerate(P.FRAMES):
        parts["frame_%d" % x] = frame(x, boom=(x == P.FRAME_BOOM))
    parts["rear_bulkhead"] = rear_bulkhead()
    parts["middle_deck_front"] = middle_deck("front")
    parts["middle_deck_rear"] = middle_deck("rear")
    parts["spar_block_front"] = spar_block(P.SPAR_FRONT, P.SPAR_BLOCK_FRONT)
    parts["spar_block_rear"] = spar_block(P.SPAR_REAR, P.SPAR_BLOCK_REAR)
    parts["battery_tray"] = battery_tray()
    parts["camera_mount"] = camera_mount()
    parts["tail_mount"] = tail_mount(boom_end)
    return parts
