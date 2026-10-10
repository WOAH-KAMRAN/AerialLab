# CF fixed wing: revision 4 (1.2 m, tractor only)

Rev 4 builds on rev 3 with these changes:
- Tractor only.
- The 20 mm boom runs high in the upper bay, so the whole lower bay is free for the battery.
- Two 8 mm spars.
- NACA 4412 wing at 0° incidence.
- Thinner plates: 1.0 mm sides and a 1.5 mm bottom.
- A printed middle deck.

## What's in this folder

| Path | Contents |
|---|---|
| `cad/assembly.step`, `cad/assembly.stl` | Full airframe: CF plates, printed parts, boom, joiners, wing, tail, motor |
| `cad/step/cf_plates/`, `cad/stl/cf_plates/` | The 3 CF plates, flat, as cut |
| `cad/step/printed/`, `cad/stl/printed/` | 13 printed parts, already laid flat for printing |
| `cad/dxf/` | Plate outlines (layer CUT) and holes (layer DRILL), plus hole tables as CSV |
| `stencils/plates_A4_stencil.pdf` | 1:1 paper stencils on 4 A4 landscape pages (each plate is split in two halves) |
| `drawings/*.svg` | 1:1 plate drawings with numbered holes |
| `hardware.md` | Every screw and nut: where it goes, length and count |
| `png/` | Renders |
| `sizing_report.md` | Weight and balance, tail sizing, thrust |
| `*.py` | The parametric model (see "Changing it") |

## Key numbers

- **Wing:** 1200 × 176 mm, NACA 4412 at 0°, leading edge at x = 150.
  - Front spar hole is 8.4 mm at x = 194, z = 100.
  - Rear spar hole is 8.4 mm at x = 264, z = 100.
- **Joiners:** two 8×6 CF tubes, 400 mm (front) and 216 mm (rear).
- **Fuselage:** 341 × 66 × 125 mm. The middle deck underside is at z = 45 and the upper deck underside at z = 78.
- **Boom:** 20×18 CF tube from x = 250 to 752 (502 mm, cut from a 1 m tube). Its centre is at z = 62, in the upper bay.
- **Tail:**
  - H-stab is 360 × 97 mm and sits on top of the boom.
  - Fin is 152 mm high, with a 155 mm root and 88 mm tip.
  - Tail arm is 480 mm.
- **CG:** x = 198 mm, which is 27% of chord, 48 mm behind the wing leading edge.
- **Battery tray:** x = 242, with ±20 mm of trim holes.
- **All-up weight:** about 1.18 kg (estimate).
  - Wing loading is 56 g/dm².
  - Stall is about 8.6–9.5 m/s.
  - Static thrust on an 8x4 is about 940 g, so thrust/weight is about 0.8.

x is measured aft from the nose edge of the side plates. z is measured up from the top of the bottom plate.

## CF plates (all straight cuts, all holes M3 except the spar holes)

| Plate | Qty | Size | Thickness |
|---|---|---|---|
| side_plate | 2 (identical) | 341 × 125 | 1.0 mm |
| bottom_plate | 1 | 341 × 66 | 1.5 mm |
| upper_deck | 1 | 341 × 56 | 1.0 mm |

Clamp the two side plates together and drill them as a pair.

## Printed parts

| File | Qty | Notes |
|---|---|---|
| nose_frame_firewall | 1 | Motor wall and front frame in one part. The battery slides in underneath it |
| frame_x3 | 3 | x = 80, 155, 228. Open bottom for the battery |
| frame_boom | 1 | x = 296. Bottom open, upper bay filled around the boom, with a boom pin |
| rear_bulkhead | 1 | Holds the boom end with the second boom pin. Wire pass-through in the lower bay |
| middle_deck_front / rear | 1 + 1 | Printed 2 mm deck with windows, plus FC (30.5 and 20 mm) and Pi standoffs. The two halves lap-join on the frame at x = 155. Print the front half as exported (flipped) and the rear half with the standoffs up |
| spar_block_front / rear | 1 + 1 | Stand on the upper deck. Each has a top screw that locks its joiner |
| battery_tray | 1 | Bolts down with 4 countersunk M3, and moves ±20 mm for trim |
| camera_mount | 1 | 19 mm micro camera |
| tail_mount | 1 | Pinch-clamps the boom end. Flat top for the H-stab |
| gear_block_main_optional / nose_optional | 1 + 1 | Trike or taildragger |

Print in PLA or PETG with 4 perimeters and 30–40% infill; print the middle deck solid. Every screw hole has a hex pocket for a captive M3 nut.

## Boom

The boom slides in from the back, through the rear bulkhead and the boom frame, and ends at x = 250, behind the FC.
1. With the boom in place, drill it 3.2 mm straight down at x = 296 and at x = 335, through both walls. Use the upper deck holes as a guide.
2. Drop an M3 nut into the slot at the front of each pin pocket.
3. Fit an M3×35 from the top of the upper deck at each point.

## Battery

The battery loads through the nose and slides back under the frames, all of which are open at the bottom. It sits on the tray at x = 242 and is held by a velcro strap through the tray rails. With the boom out of the lower bay, the pack can go anywhere from the nose frame to the bulkhead.

**Trimming the CG**
- **Fine:** slide the pack on the velcro.
- **Coarse:** bolt the tray at the hole pairs 20 mm forward or aft.

## Layout on the decks

- **Middle deck:** ESC at the front (x ≈ 26–81), Pi Zero 2 at x = 116, FC at x = 185. The boom takes the upper bay behind x = 250.
- **Upper deck:** camera, VTX and GPS at the front, then the spar blocks, then the two boom pins.

## Paper stencils

1. Print `stencils/plates_A4_stencil.pdf` at 100 % / Actual size, and check the 100 mm bar on each page.
2. Trim the first page of each plate on the blue dashed join line. Lay it over the second page so the line and the holes match, then tape the two pages together.
3. Spray-glue the stencil to the CF sheet.
4. Centre-punch every cross and drill.
5. Cut the outline with the grinder.

For the side plates, glue one stencil and drill both plates as a stack.

## Changing it

1. Edit `params.py`.
2. Run `python3 export.py`. It needs CadQuery (`pip install cadquery`).
3. Run `python3 stencils.py` for the paper stencils. It needs reportlab.
4. Run `python3 sizing.py` for weight and balance.
