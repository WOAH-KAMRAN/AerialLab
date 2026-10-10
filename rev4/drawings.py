"""1:1 SVG drawings + DXF for the rev 4 plates, plus a combined sheet.
Run from model.py or on its own."""
import os

import params as P
import plates as PL

HERE = os.path.dirname(os.path.abspath(__file__))


def _svg_plate(name, title, outline, holes, windows, t, qty, ox=0.0, oy=0.0, label2="z", table=True):
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)

    def X(x):
        return ox + x - minx

    def Y(y):
        return oy + maxy - y

    s = ['<text x="%g" y="%g" font-size="5" font-weight="bold">%s</text>' % (X(minx), Y(maxy) - 12, title),
         '<text x="%g" y="%g" font-size="3">CF %.1f mm, qty %d. Holes 3.2 mm (M3) unless red. Windows: drill 6 mm at each corner, '
         'join with a cut-off disc.</text>' % (X(minx), Y(maxy) - 6, t, qty)]
    s.append('<polygon points="%s" fill="#e4e6ef" stroke="#000" stroke-width="0.35"/>' % " ".join("%.2f,%.2f" % (X(x), Y(y)) for x, y in outline))
    for w in windows:
        s.append('<polygon points="%s" fill="#fff" stroke="#000" stroke-width="0.3"/>' %
                 " ".join("%.2f,%.2f" % (X(x), Y(y)) for x, y in PL.rounded(w)))
        for x, y in PL.rounded(w, PL.CORNER_R, 1)[::2]:
            pass
    for i, (x, y, d, lab) in enumerate(holes):
        col = "#c00" if d > P.M3 + 0.01 else "#000"
        s.append('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="#fff" stroke="%s" stroke-width="0.25"/>' % (X(x), Y(y), d / 2, col))
        s.append('<text x="%.2f" y="%.2f" font-size="1.9" fill="#555">%d</text>' % (X(x) + d / 2 + 0.3, Y(y) - d / 2 - 0.2, i + 1))
    yb = Y(miny) + 7
    s.append('<path d="M%.2f %.2fH%.2f" stroke="#06c" stroke-width="0.25"/>' % (X(minx), yb, X(maxx)))
    s.append('<text x="%.2f" y="%.2f" font-size="3.2" fill="#06c" text-anchor="middle">%g</text>' % ((X(minx) + X(maxx)) / 2, yb + 4, maxx - minx))
    s.append('<text x="%.2f" y="%.2f" font-size="3.2" fill="#06c" text-anchor="end">%g</text>' % (X(minx) - 2, (Y(miny) + Y(maxy)) / 2, maxy - miny))
    h = maxy - miny + 30
    if table:
        cols = 2
        per = (len(holes) + cols - 1) // cols
        for i, (x, y, d, lab) in enumerate(holes):
            c, r = divmod(i, per)
            s.append('<text x="%g" y="%.1f" font-size="2.6">%d: x %.1f, %s %.1f, d %.1f, %s</text>' %
                     (X(maxx) + 8 + c * 62, Y(maxy) + 3 + 3.3 * r, i + 1, x, label2, y, d, lab))
        h = max(h, 3.3 * per + 20)
    return s, maxx - minx, h


def write_plate_svg(name, path):
    f, t, qty = PL.PLATES[name]
    outline, holes, windows = f()
    label2 = "z" if name == "side_plate" else "y"
    body, w, h = _svg_plate(name, name.replace("_", " ").title() + " (rev 4)", outline, holes, windows, t(), qty, 20, 30, label2)
    W, H = w + 175, h + 40
    with open(path, "w") as fh:
        fh.write('<svg xmlns="http://www.w3.org/2000/svg" width="%gmm" height="%gmm" viewBox="0 0 %g %g" font-family="Helvetica,Arial,sans-serif">\n'
                 '<rect width="100%%" height="100%%" fill="#fff"/>\n%s\n</svg>' % (W, H, W, H, "\n".join(body)))


def write_sheet(path):
    """All four plates on one sheet, no tables (for the preview PNG)."""
    parts, y = [], 25
    W = 0
    for name in PL.PLATES:
        f, t, qty = PL.PLATES[name]
        outline, holes, windows = f()
        body, w, h = _svg_plate(name, name.replace("_", " ").title(), outline, holes, windows, t(), qty, 20, y, table=False)
        parts += body
        y += h + 4
        W = max(W, w + 40)
    with open(path, "w") as fh:
        fh.write('<svg xmlns="http://www.w3.org/2000/svg" width="%gmm" height="%gmm" viewBox="0 0 %g %g" font-family="Helvetica,Arial,sans-serif">\n'
                 '<rect width="100%%" height="100%%" fill="#fff"/>\n%s\n</svg>' % (W, y, W, y, "\n".join(parts)))


if __name__ == "__main__":
    d = os.path.join(HERE, "drawings")
    os.makedirs(d, exist_ok=True)
    for n in PL.PLATES:
        write_plate_svg(n, os.path.join(d, n + ".svg"))
    write_sheet(os.path.join(d, "plates_sheet.svg"))
