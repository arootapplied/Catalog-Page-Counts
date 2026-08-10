#!/usr/bin/env python3
"""Logo detector: group vector paths by fill color AND spatial proximity.

The SKILL.md example groups get_drawings() by fill color alone. That works when
a logo's color is unique on the page, but on a page where the logo shares a fill
with table rules or body art, the per-fill bounding box balloons to the whole
page and a size filter throws the logo away. Clustering spatially inside each
fill group fixes that: a logo is a tight cluster of same-fill paths.
"""
import sys
import fitz

HEADER_H, FOOTER_Y = 45.0, 750.0
GAP = 6.0            # rects within this many pt are treated as one cluster


def clusters(rects, gap=GAP):
    """Single-link cluster rects whose inflated boxes touch."""
    out = []
    for r in rects:
        box = [r.x0, r.y0, r.x1, r.y1]
        merged = []
        for c in out:
            if (box[0] - gap <= c[2] and c[0] - gap <= box[2] and
                    box[1] - gap <= c[3] and c[1] - gap <= box[3]):
                box = [min(box[0], c[0]), min(box[1], c[1]),
                       max(box[2], c[2]), max(box[3], c[3])]
                box.append(c[4] if len(c) > 4 else 0)
                box = box[:4] + [ (c[4] if len(c) > 4 else 0) ]
            else:
                merged.append(c)
        merged.append(box[:4] + [1])
        out = merged
    # second pass to settle transitively-connected clusters
    changed = True
    while changed:
        changed = False
        res = []
        for c in out:
            hit = None
            for d in res:
                if (c[0] - gap <= d[2] and d[0] - gap <= c[2] and
                        c[1] - gap <= d[3] and d[1] - gap <= c[3]):
                    hit = d
                    break
            if hit:
                hit[0] = min(hit[0], c[0]); hit[1] = min(hit[1], c[1])
                hit[2] = max(hit[2], c[2]); hit[3] = max(hit[3], c[3])
                changed = True
            else:
                res.append(list(c))
        out = res
    return out


def scan(path):
    doc = fitz.open(path)
    for i, page in enumerate(doc):
        by_fill = {}
        for dr in page.get_drawings():
            r, f = dr["rect"], dr.get("fill")
            if f in (None, (1.0, 1.0, 1.0)):
                continue
            if r.y0 < HEADER_H or r.y1 > FOOTER_Y:
                continue
            if r.width > 260 or r.height > 90:      # page furniture, not logo art
                continue
            by_fill.setdefault(tuple(round(c, 3) for c in f), []).append(r)
        print(f"\n=== p{i+1} ===")
        found = []
        for fill, rects in by_fill.items():
            for c in clusters(rects):
                w, h = c[2] - c[0], c[3] - c[1]
                if 35 < w < 230 and 6 < h < 60:
                    found.append((round(c[1], 1), round(c[0], 1), round(c[2], 1),
                                  round(c[3], 1), fill, w, h))
        for y0, x0, x1, y1, fill, w, h in sorted(found):
            print(f"   fill={fill} ({x0},{y0},{x1},{y1}) {w:.0f}x{h:.0f}")


if __name__ == "__main__":
    scan(sys.argv[1])
