# AerialLab: modular CF fixed wing

A modular fixed wing built from flat carbon plates and printed frames, defined by parametric Python CAD (CadQuery).

| Folder | What it is |
|---|---|
| `rev2/` | 1.5 m span, tractor/pusher convertible, solid plates |
| `rev3/` | 1.2 m span, thinner plates (1.0 / 1.5 mm), printed middle deck, A4 stencils |
| `rev4/` | 1.2 m, tractor only, 20 mm boom high in the upper bay, two 8 mm spars, NACA 4412. **Current** |

Each folder has its own README, hardware list, CAD exports (`cad/`) and scripts. To regenerate a revision, edit its `params.py` and run `python3 export.py` (needs `pip install cadquery`).

STEP and STL files are committed directly. If the repo grows large, move them to Git LFS.
