# CF fixed wing: revision 2

1.5 m span, tractor/pusher convertible, solid CF plates (no windows), one-piece printed frames, tail boom starting inside the fuselage.

## What's in this folder

| Path | Contents |
|---|---|
| `cad/assembly.step`, `cad/assembly.stl` | Full airframe, tractor setup: CF plates, printed parts, boom, joiners, wing, tail, motor |
| `cad/assembly_pusher.step`, `.stl` | Same with the pusher mount and the battery tray at the pusher station |
| `cad/step/cf_plates/`, `cad/stl/cf_plates/` | The 4 CF plates, flat, as cut |
| `cad/step/printed/`, `cad/stl/printed/` | 12 printed parts, already laid flat for printing |
| `cad/dxf/` | Plate outlines (layer CUT) and holes (layer DRILL), plus hole tables as CSV |
| `drawings/*.svg` | 1:1 plate drawings with numbered holes |
| `png/` | Renders |
| `sizing_report.md` | Weight and balance, tail sizing, thrust |
| `*.py` | The parametric model (see "Changing it") |

## Key numbers

- **Wing:** 1500 × 220 mm, LE at x = 180. Front spar hole is 10.4 mm at x = 235, z = 100. Rear spar hole is 6.4 mm at x = 323, z = 97.
- **Fuselage:** 415 × 67 × 125 mm. Middle deck underside is at z = 45 and upper deck underside at z = 78.
- **Tail:** boom is a 16×14 tube from x = 300 to 931. H-stab 450 × 121, fin 190 high, tail arm 600.
- **CG:** x = 239 mm, which is 59 mm behind the wing LE.
- **Battery tray:** x = 240 for tractor, x = 60 for pusher.
- **All-up weight:** about 1.46 kg tractor and 1.47 kg pusher (estimate). Static thrust on an 8x4 is about 940 g.

x is measured aft from the nose edge of the side plates. z is measured up from the top of the bottom plate.

## CF plates (all straight cuts, all holes M3 except the spar holes)

| Plate | Qty | Size | Thickness |
|---|---|---|---|
| side_plate | 2 (identical) | 415 × 125 | 1.5 mm |
| bottom_plate | 1 | 415 × 67 | 2 mm |
| middle_deck | 1 | 409 × 56 | 1 mm |
| upper_deck | 1 | 415 × 56 | 1 mm |

Clamp the two side plates together and drill them as a pair.

## Printed parts

| File | Qty | Notes |
|---|---|---|
| nose_frame_firewall | 1 | Tractor motor wall and front frame in one part. The battery slides in underneath it |
| frame_x3 | 3 | x = 90, 170, 250. Open bottom for the battery |
| frame_boom | 1 | x = 330. Closed bottom with a pinch clamp on the boom |
| rear_bulkhead | 1 | Boom exit with a pinch clamp, plus a wire pass-through |
| spar_block_front / rear | 1 + 1 | Stand on the upper deck. Each has a top screw that locks its joiner |
| battery_tray | 1 | Bolts up from under the bottom plate at either station |
| camera_mount | 1 | 19 mm micro camera |
| tail_mount | 1 | Pinch-clamps the boom end. Flat top for the H-stab |
| pusher_mount_optional | 1 | Pusher setup only |
| gear_block_main_optional / nose_optional | 1 + 1 | Trike or taildragger |

Print in PLA or PETG with 4 perimeters and 30-40% infill. Every screw hole has a hex pocket for a captive M3 nut.

## Changing it

Edit `params.py` and run `python3 export.py`. That needs CadQuery (`pip install cadquery`). Setting `CUT_WINDOWS = True` adds one lightening window per bay, which saves about 75 g.
