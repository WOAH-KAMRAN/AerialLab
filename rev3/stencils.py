#!/usr/bin/env python3
"""1:1 A4 stencils for the CF plates (needs reportlab).

Each plate is longer than an A4 page, so it is split into two landscape pages
that overlap by 16 mm. Print at 100 % / "Actual size", check the 100 mm bar,
trim page 1 on the dashed join line and lay it over page 2 so the line and the
holes match, then tape and spray-glue to the plate.

  python3 stencils.py   ->  stencils/plates_A4_stencil.pdf
"""
import os

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

import params as P
import plates as PL

HERE = os.path.dirname(os.path.abspath(__file__))
PW, PH = (v / mm for v in landscape(A4))      # 297 x 210
M = 8                                         # page margin
OVERLAP = 8                                   # each side of the join line
GAP = 5                                       # between plates on one page

# pages: list of plates stacked top to bottom
SHEETS = [["side_plate"], ["bottom_plate", "upper_deck"]]
TITLES = {"side_plate": "SIDE PLATE  x2 (stack both, drill together)  CF %.1f" % P.T_SIDE,
          "bottom_plate": "BOTTOM PLATE  x1  CF %.1f" % P.T_BOT,
          "upper_deck": "UPPER DECK  x1  CF %.1f" % P.T_DECK}


def bounds(poly):
    xs, ys = [p[0] for p in poly], [p[1] for p in poly]
    return min(xs), max(xs), min(ys), max(ys)


def draw_plate(c, name, ox, oy, x0, x1):
    """Plate with its min corner at page (ox, oy) mm, showing plate x in [x0, x1]."""
    outline, holes, windows = PL.PLATES[name][0]()
    bx0, bx1, by0, by1 = bounds(outline)

    def X(x):
        return (ox + x - bx0) * mm

    def Y(y):
        return (oy + y - by0) * mm

    c.saveState()
    p = c.beginPath()
    p.rect(X(x0), 0, (x1 - x0) * mm, PH * mm)
    c.clipPath(p, stroke=0, fill=0)
    # outline = cut line
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0, 0, 0)
    path = c.beginPath()
    path.moveTo(X(outline[0][0]), Y(outline[0][1]))
    for x, y in outline[1:]:
        path.lineTo(X(x), Y(y))
    path.close()
    c.drawPath(path, stroke=1, fill=0)
    for w in windows:
        wp = PL.rounded(w)
        path = c.beginPath()
        path.moveTo(X(wp[0][0]), Y(wp[0][1]))
        for x, y in wp[1:]:
            path.lineTo(X(x), Y(y))
        path.close()
        c.setDash(3, 1.5)
        c.drawPath(path, stroke=1, fill=0)
        c.setDash()
    # holes: true-size circle + centre-punch cross
    for x, y, d, lab in holes:
        big = d > P.M3 + 0.01
        c.setStrokeColorRGB(0.8, 0, 0) if big else c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(0.25)
        c.circle(X(x), Y(y), d / 2 * mm, stroke=1, fill=0)
        k = d / 2 + 1.5
        c.setLineWidth(0.15)
        c.line(X(x - k), Y(y), X(x + k), Y(y))
        c.line(X(x), Y(y - k), X(x), Y(y + k))
        if big:
            c.setFillColorRGB(0.8, 0, 0)
            c.setFont("Helvetica", 5)
            c.drawString(X(x + d / 2 + 0.8), Y(y + d / 2 + 0.3), "%.1f" % d)
    c.setStrokeColorRGB(0, 0, 0)
    c.setFillColorRGB(0.45, 0.45, 0.45)
    c.setFont("Helvetica-Bold", 7)
    tx = max(x0, bx0) + 22
    c.drawString(X(tx), Y(by1) - 9 * mm if name != "side_plate" else Y(by0 + P.FRAME_SIDE_Z[1] - 12), TITLES[name])
    c.restoreState()
    return by1 - by0


def join_marks(c, x_page, y0, y1, label):
    c.saveState()
    c.setStrokeColorRGB(0, 0.35, 0.8)
    c.setLineWidth(0.35)
    c.setDash(4, 2)
    c.line(x_page * mm, (y0 - 3) * mm, x_page * mm, (y1 + 3) * mm)
    c.setDash()
    for yy in (y0 - 3, y1 + 3):
        c.line((x_page - 3) * mm, yy * mm, (x_page + 3) * mm, yy * mm)
    c.setFillColorRGB(0, 0.35, 0.8)
    c.setFont("Helvetica", 6)
    c.drawCentredString(x_page * mm, (y1 + 4.5) * mm, label)
    c.restoreState()


def scale_bar(c, x, y):
    c.saveState()
    c.setLineWidth(0.4)
    c.line(x * mm, y * mm, (x + 100) * mm, y * mm)
    for i in range(0, 101, 10):
        h = 3 if i % 50 == 0 else 1.5
        c.line((x + i) * mm, y * mm, (x + i) * mm, (y + h) * mm)
    c.setFont("Helvetica", 6)
    c.drawString(x * mm, (y - 3.5) * mm, "100 mm: measure this. If it is not exactly 100, reprint at 100 % / Actual size")
    c.restoreState()


def build(path):
    c = canvas.Canvas(path, pagesize=landscape(A4))
    c.setTitle("CF wing rev 3 plate stencils (1:1, A4)")
    L = P.L
    join = L / 2
    tiles = [(0, join + OVERLAP), (join - OVERLAP, L)]
    page_no, n_pages = 0, len(SHEETS) * len(tiles)
    for sheet in SHEETS:
        heights = []
        for n in sheet:
            o = PL.PLATES[n][0]()[0]
            b = bounds(o)
            heights.append(b[3] - b[2])
        total = sum(heights) + GAP * (len(sheet) - 1)
        top = min((PH + total) / 2 + 4, PH - 20)
        for ti, (x0, x1) in enumerate(tiles):
            page_no += 1
            ox = M - x0 if ti == 0 else PW - M - (x1 - x0) - x0
            y = top
            for n, h in zip(sheet, heights):
                y -= h
                draw_plate(c, n, ox, y, x0, x1)
                y -= GAP
            jx = ox + join
            join_marks(c, jx, top - total, top,
                       "JOIN: trim page %d here, lay it over page %d" % (page_no if ti == 0 else page_no - 1,
                                                                          page_no + 1 if ti == 0 else page_no))
            c.setFont("Helvetica-Bold", 9)
            c.drawString(M * mm, (PH - 6) * mm, "CF wing rev 3 (1.2 m) plate stencil, 1:1   page %d of %d   (%s, %s half)" %
                         (page_no, n_pages, " + ".join(sheet), "front" if ti == 0 else "rear"))
            c.setFont("Helvetica", 6.5)
            c.drawString(M * mm, (PH - 10) * mm, "Black circles M3 (3.2 mm), red circles spar holes. Centre-punch at each cross. "
                         "Nose is on the %s." % ("left" if ti == 0 else "left, off this page"))
            scale_bar(c, M + 2 if ti == 1 else PW - M - 104, 9)
            c.showPage()
    c.save()


if __name__ == "__main__":
    d = os.path.join(HERE, "stencils")
    os.makedirs(d, exist_ok=True)
    out = os.path.join(d, "plates_A4_stencil.pdf")
    build(out)
    print(out)
