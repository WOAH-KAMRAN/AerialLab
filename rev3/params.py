"""Single source of truth for the modular CF fixed wing.

All units mm / g unless noted. Coordinate system for the fuselage:
  x = aft from the front edge of the side plates
  y = lateral, 0 on the centreline, + = left
  z = up from the bottom edge of the side plates (= top face of bottom plate)

Revision 3: the 1.2 m variant of rev 2. Edit numbers here, then run:
  python3 model.py preview  -> build/ (STL stand-ins) ; python3 render.py -> PNGs
  python3 drawings.py       -> drawings/*.svg
  python3 sizing.py         -> sizing_report.md
"""

# ---------------- materials / hardware ----------------
CUT_WINDOWS = False  # True adds one lightening window per bay (about -75 g, harder to cut)
T_SIDE = 1.0        # side plate CF thickness (frames brace it every ~70 mm)
T_BOT = 1.5         # bottom plate CF thickness (takes gear + boom loads; 2.0 if you land on gear a lot)
T_DECK = 1.0        # upper deck CF thickness
T_MID_DECK = 2.0    # middle deck is printed (PLA/PETG), two halves with a lap joint
MID_DECK_SPLIT_X = 155   # the lap joint sits on this frame
MID_DECK_LAP = 5         # lap length each side of the frame centre
MID_DECK_RAIL = 6        # solid edge rail width
MID_DECK_SPINE = 6       # solid centre spine width
MID_DECK_BOSS_H = 5      # standoff height for the FC and Pi
M3 = 3.2            # clearance hole for M3
M3_NUT_AF = 5.5     # M3 nut across flats
CF_DENSITY = 1.55e-3  # g/mm^3

# ---------------- fuselage box ----------------
CHORD = 176         # wing chord (rectangular, easy to cut in foam)
X_LE = 150          # wing leading edge station; sets the balance, see sizing.py
L = X_LE + CHORD + 15  # side plate length: fuselage ends just behind the wing TE
W = 64              # internal width between side plates
H_FRONT = 100       # side plate height at the nose
H = 125             # side plate height from X_TOP_BREAK aft
X_TOP_BREAK = 90    # where the sloped nose top edge meets the flat top
DECK_W = W - 8      # decks are narrower: 4 mm wire channel each side, no cutting

Z_MID_DECK = 45     # underside of middle deck
Z_UP_DECK = 78      # underside of upper deck
DECK_HOLE_Y = 12    # deck screw offset from centreline

# One-piece printed frames replace the old cleats + deck spacers. Each frame
# is a full-height "goalpost": two legs against the side plates, a beam under
# each deck, and an open bottom so the battery slides through from the nose.
FRAMES = [80, 155, 228, 296]       # the last one is closed at the bottom and grips the boom
FRAME_BOOM = 296
FRAME_T = 10                       # frame thickness along x
FRAME_LEG = 10                     # leg width (y)
FRAME_BEAM = 12                    # beam height under each deck
FRAME_SIDE_Z = [6, Z_MID_DECK - 6, Z_UP_DECK - 6]   # M3 into each side plate
FRAME_BOTTOM_Y = W / 2 - FRAME_LEG / 2               # M3 up through the bottom plate
BATTERY_CLEAR_W = W - 2 * FRAME_LEG
BATTERY_CLEAR_H = Z_MID_DECK - FRAME_BEAM

# nose frame / tractor firewall: one part, full height, battery passes under it
FW_DEPTH = 20
FW_WALL = 4
FW_FRONT = 6
FW_SIDE_HOLE_X = 14
FW_SIDE_HOLE_Z = [20, Z_MID_DECK - 6, 55, 71]
FW_BOTTOM_HOLE = (14, 24)          # (x, +-y) into the bottom plate
FW_MID_DECK_HOLE = (13, 12)        # middle deck starts at x = FW_FRONT
FW_UP_DECK_HOLE = (13, 23)         # corner bosses, clear of the motor nuts
MID_DECK_X0 = FW_FRONT
TRACTOR_AXIS_Z = (Z_MID_DECK + T_MID_DECK + Z_UP_DECK) / 2

# motor: 2826 1400 kv. Cross mounts vary, so the printed mounts carry
# the common 16 mm / 19 mm pair and a 25 mm square. Check yours.
MOTOR_DIA = 35
MOTOR_LEN = 30
MOTOR_HOLES_16_19 = True
MOTOR_SQUARE = 25
MOTOR_SHAFT_CLEAR = 12

# ---------------- wing ----------------
SPAN = 1200
INCIDENCE_DEG = 2.0
SPAR_FRONT = dict(x=X_LE + 0.25 * CHORD, z=100.0, d=8.0, hole=8.4)    # 8x6 CF tube joiner
SPAR_REAR = dict(x=X_LE + 0.65 * CHORD, z=97.0, d=6.0, hole=6.4)      # 6 mm CF tube/rod joiner
# spar blocks stand on the upper deck and screw down into it
SPAR_BLOCK_FRONT = dict(depth=30, top=110, bolt_dx=10)
SPAR_BLOCK_REAR = dict(depth=24, top=105, bolt_dx=8)
SPAR_DECK_Y = 22
JOINER_FRONT_LEN = 400            # 8x6 CF tube
JOINER_REAR_LEN = 216             # 6 mm CF tube/rod                   # upper deck screws up into each spar block

# ---------------- pusher option ----------------
PUSHER_AXIS_Z = 134          # boom is inside now, so the prop sits higher to clear it
PUSHER_BASE_X = (L - 40, L)            # bracket footprint on the upper deck
PUSHER_DECK_HOLES_X = [L - 34, L - 6]     # L-6 shares the rear bulkhead nuts
PUSHER_SIDE_HOLES = [(L - 32, 100), (L - 18, 118)]

# ---------------- boom + tail ----------------
BOOM_OD, BOOM_ID = 16, 14
BOOM_Z = 12                   # boom centre height, inside the lower bay
BOOM_START_X = 280            # boom starts inside the fuselage, behind the tractor battery
# held in two places: the boom frame at FRAME_BOOM and the rear bulkhead
BULKHEAD_T = 12
BOOM_BULKHEAD_X = (L - BULKHEAD_T, L)
BULKHEAD_X = L - BULKHEAD_T / 2
BULKHEAD_SIDE_Z = [6, Z_MID_DECK - 6, Z_UP_DECK - 6]
BULKHEAD_BOTTOM_Y = 22
PINCH_HALF = 14                 # boom clamp bolts: M3 x 30, head at -14, nut at +14
PINCH_Z_FRAME = BOOM_Z + BOOM_OD / 2 + 5
PINCH_Z_BULKHEAD = BOOM_Z + 14
PINCH_ACCESS_D = 7.0            # drill in the side plates so a driver reaches the clamp bolt heads
TAIL_ARM = 580              # wing AC -> tail AC
VH = 0.45                   # horizontal tail volume
VV = 0.035                  # vertical tail volume
HS_SPAN = 360               # H-stab span
FIN_H = 152                 # fin height
FIN_TIP = 88                # fin tip chord

# ---------------- props ----------------
PROP_DIA = 8 * 25.4

# ---------------- landing gear (bottom plate, x, +-y) ----------------
GEAR_TRIKE_NOSE = [(12, 16), (28, 16)]
GEAR_TRIKE_MAIN = [(240, 22), (260, 22)]
GEAR_TAILDRAGGER_MAIN = [(125, 22), (145, 22)]
# battery tray: two bolt-down stations, chosen by sizing.py for balance
BATTERY_TRAY_PITCH = 60
BATTERY_TRAY_TRACTOR_X = 222
BATTERY_TRAY_PUSHER_X = 72
BATTERY_TRAY_Y = 8          # flat 2 mm tray, countersunk M3 from inside
BATTERY_TRAY_SHIFT = [-20, 0, 20]   # extra hole pairs so the tray can bolt 20 mm fore or aft for CG trim
BATTERY_TRAY_HOLES = sorted({(x + sh + d, BATTERY_TRAY_Y) for x in (BATTERY_TRAY_TRACTOR_X, BATTERY_TRAY_PUSHER_X)
                             for sh in BATTERY_TRAY_SHIFT for d in (-BATTERY_TRAY_PITCH / 2, BATTERY_TRAY_PITCH / 2)})

# ---------------- deck component patterns (x centre, pattern) ----------------
FC_X = 185                  # FC near the CG
PI_X = 245                  # Pi Zero 2 W, 58 x 23 mm (use M2.5 screws in the M3 holes)
VTX_X = 60                  # 20x20 pattern on the upper deck
CAM_HOLES = [(30, 10)]
CAM_W = 19                  # micro FPV camera width (use 14 for nano)
GPS_HOLES = [(105, 8)]
ANT_HOLES = [(285, 15)]
