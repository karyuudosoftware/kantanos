#!/usr/bin/env python3
"""KantanOS looks: one table of colour styles, and everything generated from it.

A "look" is a wallpaper, a desktop colour scheme, a logo tint and the mode chooser's
colours and icons. Users switch with `kantan-look set <id>` (the mode chooser and the
Welcome app call that). DEFAULT is the look a new user starts with; it also colours the
things that exist only once per PC: boot splash, installer, launcher icon, login screen.

Run:  python tools/looks.py      (then tools/render-branding.sh turns the SVGs into PNGs)

Writes:
  branding/looks/<id>/wallpaper.svg, logo.svg           sources for the renderer
  branding/default/*.svg                                 base artwork in the DEFAULT palette
  system_files/usr/share/kantanos/looks/<id>/look.conf   settings read at run time
  system_files/usr/share/kantanos/looks/<id>/icons/*.svg mode chooser tile icons
  system_files/usr/share/kantanos/looks/default          text file naming the DEFAULT look
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT = "light"

# id: label, Japanese label, dark?, logo/icon gradient (3), wallpaper base (3), wallpaper glows (4)
LOOKS = {
    "light":    ("Light",    "ライト",       False, ("#3cc4f5", "#3b82f6", "#2f5fe0"), ("#f6f9fd", "#eaf0f8", "#dde7f5"), ("#a9d8ff", "#b9cdfa", "#c9d6ff", "#ffffff")),
    "sakura":   ("Sakura",   "さくら",       False, ("#ff9ec4", "#f472a8", "#d9558f"), ("#fdf7f9", "#f8ecf1", "#f3e1ea"), ("#ffc9dd", "#f9d3e6", "#ffe0ea", "#ffffff")),
    "graphite": ("Graphite", "グラファイト", True,  ("#f1f4f8", "#aeb8c6", "#7c8796"), ("#17191d", "#101114", "#1b1d22"), ("#5b6370", "#3d434d", "#737c8a", "#2a2e35")),
    "ocean":    ("Ocean",    "オーシャン",   True,  ("#6fd6ff", "#3b9dff", "#2b6fe6"), ("#0a1728", "#07101c", "#0c1d36"), ("#1c8fd6", "#2463c9", "#1aa3c9", "#173a7a")),
    "forest":   ("Forest",   "フォレスト",   True,  ("#b7f08a", "#4fcf7a", "#1fa37a"), ("#0f1a14", "#0a120e", "#12231a"), ("#2f9e62", "#1f7f6b", "#7fbf4a", "#1c4a36")),
    "ember":    ("Ember",    "エンバー",     True,  ("#ffd36b", "#ff9a3c", "#f0603a"), ("#1d1410", "#130d0a", "#24150e"), ("#d9772b", "#c2452d", "#e0a23a", "#6b2f1c")),
    "aurora":   ("Aurora",   "オーロラ",     True,  ("#38d9f5", "#6c7bff", "#a55cff"), ("#0d1326", "#0b0e17", "#140f2a"), ("#1fb7e0", "#5a63e8", "#9a4dff", "#2b3a8c")),
}


def rgb(hex_colour):
    h = hex_colour.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    """Colour t of the way from a to b, as #rrggbb."""
    ra, rb = rgb(a), rgb(b)
    return "#%02x%02x%02x" % tuple(round(x + (y - x) * t) for x, y in zip(ra, rb))


def wallpaper_svg(look_id):
    _label, _ja, dark, grad, base, glow = LOOKS[look_id]
    veil = base[1] if dark else "#ffffff"
    g = (0.50, 0.55, 0.48, 0.45) if dark else (0.75, 0.70, 0.65, 0.80)
    ribbon = (0.55, 0.60) if dark else (0.45, 0.50)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3840 2160" width="3840" height="2160">
  <title>KantanOS wallpaper - {look_id}</title>
  <defs>
    <linearGradient id="base" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="{base[0]}"/>
      <stop offset="0.55" stop-color="{base[1]}"/>
      <stop offset="1" stop-color="{base[2]}"/>
    </linearGradient>
    <filter id="blur" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="170"/></filter>
    <filter id="blurSoft" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="90"/></filter>
    <linearGradient id="ribbon" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{grad[0]}" stop-opacity="0"/>
      <stop offset="0.3" stop-color="{grad[0]}" stop-opacity="{ribbon[0]}"/>
      <stop offset="0.6" stop-color="{grad[1]}" stop-opacity="{ribbon[1]}"/>
      <stop offset="1" stop-color="{grad[2]}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="3840" height="2160" fill="url(#base)"/>
  <g filter="url(#blur)">
    <ellipse cx="820" cy="1500" rx="900" ry="520" fill="{glow[0]}" opacity="{g[0]}"/>
    <ellipse cx="2050" cy="1250" rx="950" ry="520" fill="{glow[1]}" opacity="{g[1]}"/>
    <ellipse cx="3150" cy="820" rx="820" ry="560" fill="{glow[2]}" opacity="{g[2]}"/>
    <ellipse cx="1500" cy="300" rx="700" ry="300" fill="{glow[3]}" opacity="{g[3]}"/>
  </g>
  <g filter="url(#blurSoft)" fill="none" stroke="url(#ribbon)" stroke-linecap="round">
    <path d="M -200 1750 C 900 1250, 1700 1900, 2500 1250 S 3700 600, 4100 760" stroke-width="150"/>
    <path d="M -200 1380 C 800 980, 1900 1500, 2700 900 S 3800 380, 4100 420" stroke-width="70" opacity="0.6"/>
  </g>
  <rect width="3840" height="2160" fill="{veil}" opacity="0.18"/>
</svg>
'''


def recolour(svg_text, look_id):
    """Swap the original artwork's cyan-indigo-purple for a look's gradient."""
    grad = LOOKS[look_id][3]
    swaps = {
        "#38d9f5": grad[0], "#6c7bff": grad[1], "#a55cff": grad[2],
        "#5a63e8": grad[1], "#7f9bff": mix(grad[1], "#ffffff", 0.25), "#2a1f6b": mix(grad[2], "#000000", 0.55),
    }
    for old, new in swaps.items():
        svg_text = svg_text.replace(old, new)
    return svg_text


ICONS = {
    "desktop": '<rect x="6" y="8" width="36" height="24" rx="3.5"/><path d="M24 32v7M15 39h18"/>',
    "tv": '<rect x="6" y="15" width="36" height="23" rx="3.5"/><path d="M24 15l-8-8M24 15l8-8M15 42h18"/>',
    "game": '<rect x="5" y="15" width="38" height="20" rx="10"/><path d="M15 21v8M11 25h8"/>'
            '<circle cx="31" cy="22.5" r="1.6"/><circle cx="35.5" cy="27.5" r="1.6"/>',
    "retro": '<rect x="8" y="31" width="32" height="9" rx="3"/><path d="M22 31V17"/><circle cx="22" cy="12" r="5"/>'
             '<circle cx="33" cy="26.5" r="2.2"/>',
    "web": '<circle cx="24" cy="24" r="17"/><ellipse cx="24" cy="24" rx="7.5" ry="17"/><path d="M7 24h34M10 15h28M10 33h28"/>',
    "add": '<circle cx="24" cy="24" r="17"/><path d="M24 15v18M15 24h18"/>',
}


def icon_svg(body, look_id):
    _label, _ja, dark, grad, _base, _glow = LOOKS[look_id]
    stops = [mix(c, "#ffffff", 0.35) for c in grad] if dark else list(grad)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="192" height="192">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{stops[0]}"/><stop offset="0.5" stop-color="{stops[1]}"/><stop offset="1" stop-color="{stops[2]}"/>
  </linearGradient></defs>
  <g fill="none" stroke="url(#g)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">{body}</g>
</svg>
'''


def look_conf(look_id):
    label, ja, dark, grad, base, _glow = LOOKS[look_id]
    accent = rgb(grad[1])
    hover = rgb(mix(grad[1], "#ffffff", 0.2))
    if dark:
        colours = dict(TEXT="#ffffff", OVERLAY=base[1], OVERLAY_OPACITY="0.62", TILE="#1affffff",
                       TILE_SELECTED="#33ffffff", TILE_BORDER="#40ffffff", DIALOG="#eb" + base[0].lstrip("#"),
                       SHADE="#c0" + base[1].lstrip("#"))
    else:
        colours = dict(TEXT="#1b2330", OVERLAY="#ffffff", OVERLAY_OPACITY="0.45", TILE="#b3ffffff",
                       TILE_SELECTED="#f2ffffff", TILE_BORDER="#2e1b2330", DIALOG="#f7ffffff",
                       SHADE="#b0" + base[1].lstrip("#"))
    lines = {
        "ID": look_id, "LABEL": label, "LABEL_JA": ja, "DARK": "1" if dark else "0",
        "SCHEME": "Kantan" + look_id.capitalize(), "BASE_SCHEME": "BreezeDark" if dark else "BreezeLight",
        "ICON_THEME": "breeze-dark" if dark else "breeze",
        "ACCENT": "%d,%d,%d" % accent, "ACCENT_HOVER": "%d,%d,%d" % hover,
        "ACCENT_HEX": grad[1], "SWATCH_A": grad[0], "SWATCH_B": grad[2], "SWATCH_BG": base[1],
        **colours,
    }
    return "".join(f'{key}="{value}"\n' for key, value in lines.items())


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main():
    branding = ROOT / "branding"
    share = ROOT / "system_files/usr/share/kantanos/looks"
    for look_id, (_label, _ja, dark, *_rest) in LOOKS.items():
        write(branding / "looks" / look_id / "wallpaper.svg", wallpaper_svg(look_id))
        logo = (branding / f"kantanos-logo-stacked-on-{'dark' if dark else 'light'}.svg").read_text(encoding="utf-8")
        write(branding / "looks" / look_id / "logo.svg", recolour(logo, look_id))
        write(share / look_id / "look.conf", look_conf(look_id))
        for name, body in ICONS.items():
            write(share / look_id / "icons" / f"{name}.svg", icon_svg(body, look_id))
    write(share / "default", DEFAULT + "\n")
    write(share / "order", " ".join(LOOKS) + "\n")
    # Base artwork in the default look's colours, for the boot splash, installer and icons.
    for svg in sorted(branding.glob("kantanos-*.svg")):
        if svg.name != "kantanos-wallpaper.svg":
            write(branding / "default" / svg.name, recolour(svg.read_text(encoding="utf-8"), DEFAULT))
    print(f"wrote {len(LOOKS)} looks (default: {DEFAULT})")


if __name__ == "__main__":
    main()
