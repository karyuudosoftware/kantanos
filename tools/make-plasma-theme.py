#!/usr/bin/env python3
"""Generates the Kantan Glass Plasma theme (panel background with large rounded corners,
a see-through fill and a thin light edge). Everything else falls back to Breeze.

Run from anywhere:  python tools/make-plasma-theme.py
"""
import json, os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                    "system_files", "usr", "share", "plasma", "desktoptheme", "KantanGlass")
R = 18          # corner radius / edge thickness in px
C = 36          # centre tile size
MARGIN = 5      # content margin hint in px
EDGE = "#ffffff"


def frame(prefix, x0, y0, fill_attr, edge_opacity):
    """One 9-slice frame. Elements are found by id; position is free.

    The light edge is drawn with filled shapes, never strokes: a stroke makes a piece half a
    pixel wider than its fill, and that sliver shows up as a gap once the piece is stretched.
    """
    a, b, c = x0, x0 + R, x0 + R + C          # x of left / centre / right columns
    d, e, f = y0, y0 + R, y0 + R + C          # y of top / centre / bottom rows
    r1 = R - 1                                # inner radius of the 1px edge ring
    out = []

    def group(name, body):
        out.append(f'<g id="{prefix}{name}">{body}</g>')

    def lit(shape):
        if edge_opacity <= 0:
            return ""
        return shape.replace("/>", f' fill="{EDGE}" fill-opacity="{edge_opacity}"/>')

    # corners: a quarter disc that fills its RxR box, plus a quarter ring for the edge
    group("topleft", f'<path d="M{a},{e} A{R},{R} 0 0 1 {b},{d} L{b},{e} Z" {fill_attr}/>'
          + lit(f'<path d="M{a},{e} A{R},{R} 0 0 1 {b},{d} L{b},{d + 1} A{r1},{r1} 0 0 0 {a + 1},{e} Z"/>'))
    group("topright", f'<path d="M{c},{d} A{R},{R} 0 0 1 {c + R},{e} L{c},{e} Z" {fill_attr}/>'
          + lit(f'<path d="M{c},{d} A{R},{R} 0 0 1 {c + R},{e} L{c + R - 1},{e} A{r1},{r1} 0 0 0 {c},{d + 1} Z"/>'))
    group("bottomleft", f'<path d="M{a},{f} A{R},{R} 0 0 0 {b},{f + R} L{b},{f} Z" {fill_attr}/>'
          + lit(f'<path d="M{a},{f} A{R},{R} 0 0 0 {b},{f + R} L{b},{f + R - 1} A{r1},{r1} 0 0 1 {a + 1},{f} Z"/>'))
    group("bottomright", f'<path d="M{c},{f + R} A{R},{R} 0 0 0 {c + R},{f} L{c},{f} Z" {fill_attr}/>'
          + lit(f'<path d="M{c},{f + R} A{R},{R} 0 0 0 {c + R},{f} L{c + R - 1},{f} A{r1},{r1} 0 0 1 {c},{f + R - 1} Z"/>'))
    # edges
    group("top", f'<rect x="{b}" y="{d}" width="{C}" height="{R}" {fill_attr}/>'
          + lit(f'<rect x="{b}" y="{d}" width="{C}" height="1"/>'))
    group("bottom", f'<rect x="{b}" y="{f}" width="{C}" height="{R}" {fill_attr}/>'
          + lit(f'<rect x="{b}" y="{f + R - 1}" width="{C}" height="1"/>'))
    group("left", f'<rect x="{a}" y="{e}" width="{R}" height="{C}" {fill_attr}/>'
          + lit(f'<rect x="{a}" y="{e}" width="1" height="{C}"/>'))
    group("right", f'<rect x="{c}" y="{e}" width="{R}" height="{C}" {fill_attr}/>'
          + lit(f'<rect x="{c + R - 1}" y="{e}" width="1" height="{C}"/>'))
    out.append(f'<rect id="{prefix}center" x="{b}" y="{e}" width="{C}" height="{C}" {fill_attr}/>')
    return "\n  ".join(out)


def svg(fill_opacity, edge_opacity):
    fill = f'class="ColorScheme-Background" fill="currentColor" fill-opacity="{fill_opacity}"'
    hints = "\n  ".join(
        f'<rect id="hint-{side}-margin" x="{200 + i * 12}" y="10" width="{MARGIN}" height="{MARGIN}" fill="#ff00ff" opacity="0"/>'
        for i, side in enumerate(("top", "bottom", "left", "right")))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="320" height="200" viewBox="0 0 320 200">
  <defs>
    <style id="current-color-scheme" type="text/css">
      .ColorScheme-Text {{ color:#fcfcfc; }}
      .ColorScheme-Background {{ color:#141618; }}
    </style>
  </defs>
  <!-- visible frame -->
  {frame("", 10, 10, fill, edge_opacity)}
  <!-- mask: the area that gets blurred behind the panel -->
  {frame("mask-", 110, 10, 'fill="#000000"', 0)}
  <!-- content margins -->
  {hints}
  <!-- stretch the edge pieces instead of tiling them (tiling shows seams) -->
  <rect id="hint-stretch-borders" x="200" y="30" width="4" height="4" fill="#ff00ff" opacity="0"/>
</svg>
'''


def write(rel, text):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


write("metadata.json", json.dumps({
    "KPlugin": {
        "Authors": [{"Name": "KantanOS"}],
        "Description": "Glass panels with large rounded corners; the rest follows Breeze",
        "Id": "KantanGlass",
        "License": "CC-BY-SA-4.0",
        "Name": "Kantan Glass",
        "Version": "0.1.0",
    },
    "X-Plasma-API": "5.0",
}, indent=4) + "\n")
write("translucent/widgets/panel-background.svg", svg(0.42, 0.16))   # used when blur is available
write("widgets/panel-background.svg", svg(0.72, 0.14))               # compositing without blur
write("opaque/widgets/panel-background.svg", svg(1.0, 0.10))         # no compositing
print("theme written to", os.path.normpath(ROOT))
