# CF fixed wing: revision 3 (1.2 m)

The 1.2 m variant of rev 2. Same parts, same deck heights and cross-section, shorter fuselage and smaller wing and tail. 1.2 m span, tractor/pusher convertible, solid CF plates (no windows), one-piece printed frames, tail boom starting inside the fuselage.

## What's in this folder

| Path | Contents |
|---|---|
| `cad/assembly.step`, `cad/assembly.stl` | Full airframe, tractor setup: CF plates, printed parts, boom, joiners, wing, tail, motor |
| `cad/assembly_pusher.step`, `.stl` | Same with the pusher mount and the battery tray at the pusher station |
| `cad/step/cf_plates/`, `cad/stl/cf_plates/` | The 4 CF plates, flat, as cut |
| `cad/step/printed/`, `cad/stl/printed/` | 12 printed parts, already laid flat for printing |
| `cad/dxf/` | Plate outlines (layer CUT) and holes (layer DRILL), plus hole tables as CSV |
| `stencils/plates_A4_stencil.pdf` | 1:1 paper stencils for all 4 plates, 6 A4 landscape pages (each plate is split in two halves) |
| `drawings/*.svg` | 1:1 plate drawings with numbered holes |
| `png/` | Renders |
| `hardware.md` | Every screw and nut: where it goes, length and count (117 screws for tractor + trike) |
| `sizing_report.md` | Weight and balance, tail sizing, thrust |
| `*.py` | The parametric model (see "Changing it") |

## Why the tail arm is 580, not 480

With a 480 mm arm the tractor battery has to sit at x = 258 to balance, which is where the boom starts. Stretching the arm to 580 lets the battery sit at x = 222, ahead of the boom, while keeping the fuselage at 341 mm. Both setups balance with no nose weight.

## Key numbers

- **Wing:** 1200 × 176 mm, LE at x = 150. Front spar hole is 10.4 mm at x = 194, z = 100. Rear spar hole is 6.4 mm at x = 264, z = 97. Joiners are 10×8 × 400 and 6 mm × 216.
- **Fuselage:** 341 × 67 × 125 mm. Middle deck underside is at z = 45 and upper deck underside at z = 78.
- **Tail:** boom is a 16×14 tube from x = 280 to 839 (559 mm, cut from 1000). H-stab 360 × 80, fin 152 high (root 113, tip 88), tail arm 580.
- **CG:** x = 198 mm, which is 48 mm behind the wing LE.
- **Battery tray:** x = 222 for tractor, x = 72 for pusher.
- **All-up weight:** about 1.24 kg tractor and 1.25 kg pusher (estimate). Static thrust on an 8x4 is about 940 g, so thrust/weight is about 0.76. Wing loading is 59 g/dm², stall about 9 m/s.

x is measured aft from the nose edge of the side plates. z is measured up from the top of the bottom plate.

## CF plates (all straight cuts, all holes M3 except the spar holes)

| Plate | Qty | Size | Thickness |
|---|---|---|---|
| side_plate | 2 (identical) | 341 × 125 | 1.5 mm |
| bottom_plate | 1 | 341 × 67 | 2 mm |
| middle_deck | 1 | 335 × 56 | 1 mm |
| upper_deck | 1 | 341 × 56 | 1 mm |

Clamp the two side plates together and drill them as a pair.

## Printed parts

| File | Qty | Notes |
|---|---|---|
| nose_frame_firewall | 1 | Tractor motor wall and front frame in one part. The battery slides in underneath it |
| frame_x3 | 3 | x = 80, 155, 228. Open bottom for the battery |
| frame_boom | 1 | x = 296. Closed bottom with a pinch clamp on the boom |
| rear_bulkhead | 1 | Boom exit with a pinch clamp, plus a wire pass-through |
| spar_block_front / rear | 1 + 1 | Stand on the upper deck. Each has a top screw that locks its joiner |
| battery_tray | 1 | Bolts down at either station, ±20 mm for trim. Strap slots in the side rails |
| camera_mount | 1 | 19 mm micro camera |
| tail_mount | 1 | Pinch-clamps the boom end. Flat top for the H-stab |
| pusher_mount_optional | 1 | Pusher setup only |
| gear_block_main_optional / nose_optional | 1 + 1 | Trike or taildragger |

Print in PLA or PETG with 4 perimeters and 30-40% infill. Every screw hole has a hex pocket for a captive M3 nut.

## Battery: in, out and trimming

The battery goes in through the nose, underneath the nose frame. Every frame except the boom frame is open at the bottom, so the pack slides straight back along the bottom plate.

1. Take off the nose cover. In tractor setup, the prop and motor stay on.
2. Slide the pack in, plug-end first, until it sits on the tray. The tray is at x = 222 for tractor and x = 72 for pusher.
3. Pass a velcro strap through the two slots in each tray side rail and pull it over the pack.
4. To take the pack out, release the strap, unplug, and slide it forward out of the nose.

**Trimming the CG**
- **Fine:** slide the pack on the velcro before you strap it. About ±15 mm of battery travel moves the CG about ±2.5 mm.
- **Coarse:** the tray bolts down with 4 countersunk M3 screws. The bottom plate has hole pairs 20 mm forward and 20 mm aft of each station, so you can move the tray ±20 mm. That moves the CG about ±3 mm.
- **Switching to pusher:** move the tray to the pusher station.

## Paper stencils

1. Print `stencils/plates_A4_stencil.pdf` at 100 % / Actual size, and check the 100 mm bar on each page.
2. Trim the first page of each plate on the blue dashed join line. Lay it over the second page so the line and the holes match, then tape the two pages together.
3. Spray-glue the stencil to the CF sheet.
4. Centre-punch every cross and drill.
5. Cut the outline with the grinder.

For the side plates, glue one stencil and drill both plates as a stack.

## Changing it

Edit `params.py` and run `python3 export.py`. Run `python3 stencils.py` for the paper stencils (needs reportlab). That needs CadQuery (`pip install cadquery`). Setting `CUT_WINDOWS = True` adds one lightening window per bay, which saves about 60 g.
