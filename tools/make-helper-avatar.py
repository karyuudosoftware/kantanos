#!/usr/bin/env python3
"""Draws Kan-chan, the KantanOS Helper's character: a chibi girl with a light-blue bob, a
簡単 hair clip and a KantanOS-blue hoodie with a wrench badge (she fixes things).

Writes one SVG per expression into the character pack folder the Helper reads:
  idle, blink, talk1, talk2, think, happy, worried  (+ character.json)
A character pack is just that folder; any other pack with the same file names (SVG or PNG)
works too.  Run from anywhere:  python tools/make-helper-avatar.py
"""
import json
import os

OUT = os.path.join(os.path.dirname(__file__), "..", "system_files", "usr", "share", "kantanos",
                   "helper", "characters", "kan-chan")

SKIN, SKIN_SHADE = "#ffe6d8", "#f6c9b6"
HAIR, HAIR_DARK, HAIR_LIGHT = "#8ccfff", "#4b9fe6", "#d9f1ff"
HOODIE, HOODIE_DARK = "#3d8bfd", "#2a6ad1"
LINE = "#2b3a5c"
IRIS_TOP, IRIS_BOTTOM = "#5bc0ff", "#1f4fc2"

DEFS = f"""<defs>
  <linearGradient id="iris" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{IRIS_BOTTOM}"/><stop offset="0.55" stop-color="{IRIS_TOP}"/><stop offset="1" stop-color="#a8e4ff"/>
  </linearGradient>
  <linearGradient id="hair" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{HAIR}"/><stop offset="1" stop-color="{HAIR_DARK}"/>
  </linearGradient>
  <linearGradient id="hoodie" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{HOODIE}"/><stop offset="1" stop-color="{HOODIE_DARK}"/>
  </linearGradient>
</defs>"""


def back():
    return f"""
  <!-- hood and back hair -->
  <ellipse cx="120" cy="196" rx="74" ry="34" fill="{HOODIE_DARK}"/>
  <path d="M30,118 C24,22 216,22 210,118 C214,160 204,196 186,206 L54,206 C36,196 26,160 30,118 Z" fill="url(#hair)"/>
  <!-- body: hoodie -->
  <rect x="108" y="180" width="24" height="26" rx="8" fill="{SKIN_SHADE}"/>
  <path d="M52,300 C50,236 78,204 120,204 C162,204 190,236 188,300 Z" fill="url(#hoodie)" stroke="{LINE}" stroke-width="2.5"/>
  <path d="M96,206 C104,222 136,222 144,206" fill="none" stroke="{HOODIE_DARK}" stroke-width="5" stroke-linecap="round"/>
  <path d="M110,216 L107,252" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
  <path d="M130,216 L133,252" stroke="#ffffff" stroke-width="3" stroke-linecap="round"/>
  <circle cx="107" cy="255" r="4" fill="#ffffff"/><circle cx="133" cy="255" r="4" fill="#ffffff"/>
  <!-- wrench badge -->
  <circle cx="158" cy="262" r="14" fill="#ffffff" stroke="{LINE}" stroke-width="2"/>
  <g transform="translate(158,262) rotate(-45)" fill="{HOODIE}">
    <rect x="-2.6" y="-2" width="5.2" height="12" rx="2.4"/>
    <path d="M-6,-4 A6.5,6.5 0 1 1 6,-4 L2.6,-4 L2.6,-9 L-2.6,-9 L-2.6,-4 Z"/>
  </g>
  <!-- face -->
  <ellipse cx="120" cy="124" rx="76" ry="70" fill="{SKIN}" stroke="{LINE}" stroke-width="2.5"/>
  <ellipse cx="78" cy="154" rx="11" ry="5.5" fill="#ff98ad" opacity="0.55"/>
  <ellipse cx="162" cy="154" rx="11" ry="5.5" fill="#ff98ad" opacity="0.55"/>"""


def front_hair():
    return f"""
  <!-- bangs and side locks -->
  <path d="M42,116 C38,28 202,28 198,116 L186,100 L174,118 L160,92 L146,116 L132,90 L118,116 L104,92 L90,118 L76,94 L62,116 L52,102 Z"
        fill="url(#hair)" stroke="{LINE}" stroke-width="2.5" stroke-linejoin="round"/>
  <path d="M44,104 C34,146 38,184 58,198 C60,168 58,136 66,112 Z" fill="url(#hair)" stroke="{LINE}" stroke-width="2.5" stroke-linejoin="round"/>
  <path d="M196,104 C206,146 202,184 182,198 C180,168 182,136 174,112 Z" fill="url(#hair)" stroke="{LINE}" stroke-width="2.5" stroke-linejoin="round"/>
  <path d="M74,66 C96,52 126,50 150,58" fill="none" stroke="{HAIR_LIGHT}" stroke-width="6" stroke-linecap="round" opacity="0.8"/>
  <!-- cowlick -->
  <path d="M118,52 C112,28 132,18 140,30 C130,26 124,36 126,52" fill="url(#hair)" stroke="{LINE}" stroke-width="2.5" stroke-linejoin="round"/>
  <!-- 簡単 hair clip -->
  <g transform="translate(166,74) rotate(18)">
    <rect x="-21" y="-10" width="42" height="20" rx="8" fill="#ffffff" stroke="{HOODIE}" stroke-width="2.5"/>
    <text x="0" y="5" text-anchor="middle" font-family="Noto Sans CJK JP, Noto Sans JP, sans-serif" font-weight="700"
          font-size="13" fill="{HOODIE_DARK}">簡単</text>
  </g>"""


def eye_open(cx, cy, look=(0, 0), scale=1.0):
    lx, ly = look
    rx, ry = 13 * scale, 17 * scale
    return f"""
  <g>
    <ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="{LINE}"/>
    <ellipse cx="{cx + lx * 0.4}" cy="{cy + 1 + ly * 0.4}" rx="{rx - 2.5}" ry="{ry - 3}" fill="url(#iris)"/>
    <ellipse cx="{cx + lx}" cy="{cy + 2 + ly}" rx="{5 * scale}" ry="{7 * scale}" fill="#13265a"/>
    <circle cx="{cx - 4 + lx}" cy="{cy - 6 + ly}" r="{4.4 * scale}" fill="#ffffff"/>
    <circle cx="{cx + 4.5 + lx}" cy="{cy + 6 + ly}" r="{2 * scale}" fill="#ffffff" opacity="0.9"/>
    <path d="M{cx - rx - 3},{cy - ry + 5} Q{cx},{cy - ry - 7} {cx + rx + 3},{cy - ry + 5}" fill="none" stroke="{LINE}" stroke-width="3.2" stroke-linecap="round"/>
  </g>"""


def eyes(kind):
    L, R, Y = 92, 148, 134
    if kind == "open":
        return eye_open(L, Y) + eye_open(R, Y)
    if kind == "blink":
        return "".join(f'<path d="M{x - 13},{Y + 2} Q{x},{Y + 9} {x + 13},{Y + 2}" fill="none" stroke="{LINE}" stroke-width="3.5" stroke-linecap="round"/>' for x in (L, R))
    if kind == "happy":
        return "".join(f'<path d="M{x - 13},{Y + 6} Q{x},{Y - 12} {x + 13},{Y + 6}" fill="none" stroke="{LINE}" stroke-width="4" stroke-linecap="round"/>' for x in (L, R))
    if kind == "think":
        brow = f'<path d="M136,104 Q148,96 160,102" fill="none" stroke="{HAIR_DARK}" stroke-width="3.5" stroke-linecap="round"/>'
        return eye_open(L, Y, look=(3, -4)) + eye_open(R, Y, look=(3, -4)) + brow
    if kind == "worried":
        brows = (f'<path d="M80,112 L103,104" stroke="{HAIR_DARK}" stroke-width="3.5" stroke-linecap="round"/>'
                 f'<path d="M160,112 L137,104" stroke="{HAIR_DARK}" stroke-width="3.5" stroke-linecap="round"/>')
        return eye_open(L, Y + 2, scale=0.92) + eye_open(R, Y + 2, scale=0.92) + brows
    raise ValueError(kind)


def mouth(kind):
    c = "#9b2f43"
    if kind == "smile":
        return f'<path d="M111,165 Q120,172 129,165" fill="none" stroke="{c}" stroke-width="3" stroke-linecap="round"/>'
    if kind == "talk1":
        return f'<ellipse cx="120" cy="167" rx="5.5" ry="4" fill="{c}"/><ellipse cx="120" cy="169" rx="3.5" ry="1.6" fill="#ff8a98"/>'
    if kind == "talk2":
        return f'<ellipse cx="120" cy="168" rx="7.5" ry="8" fill="{c}"/><ellipse cx="120" cy="172" rx="5" ry="2.6" fill="#ff8a98"/>'
    if kind == "happy":
        return f'<path d="M108,162 Q120,182 132,162 Z" fill="{c}" stroke="{c}" stroke-width="2" stroke-linejoin="round"/><path d="M113,170 Q120,176 127,170" fill="#ff8a98"/>'
    if kind == "worried":
        return f'<path d="M111,169 Q115.5,164 120,169 Q124.5,174 129,169" fill="none" stroke="{c}" stroke-width="3" stroke-linecap="round"/>'
    if kind == "think":
        return f'<path d="M114,168 L127,166" stroke="{c}" stroke-width="3" stroke-linecap="round"/>'
    raise ValueError(kind)


def extras(kind):
    if kind == "think":
        return ('<circle cx="200" cy="66" r="4" fill="#cfe3ff" stroke="#8cb7f0" stroke-width="1.5"/>'
                '<circle cx="212" cy="50" r="6" fill="#cfe3ff" stroke="#8cb7f0" stroke-width="1.5"/>'
                '<circle cx="226" cy="30" r="9" fill="#cfe3ff" stroke="#8cb7f0" stroke-width="1.5"/>')
    if kind == "happy":
        star = '<path d="M0,-9 L2.4,-2.4 L9,0 L2.4,2.4 L0,9 L-2.4,2.4 L-9,0 L-2.4,-2.4 Z" fill="#ffd34d" stroke="#e8a600" stroke-width="1"/>'
        return f'<g transform="translate(204,98)">{star}</g><g transform="translate(34,84) scale(0.7)">{star}</g>'
    if kind == "worried":
        return '<path d="M196,92 C192,100 192,106 197,108 C202,106 202,100 196,92 Z" fill="#9fd8ff" stroke="#4b9fe6" stroke-width="1.5"/>'
    if kind == "listen":
        # sound coming in towards her ear: three arcs on the left, a little note on the right
        arcs = "".join(f'<path d="M{24 - 7 * i},{118 - 9 * i} Q{12 - 9 * i},{140} {24 - 7 * i},{162 + 9 * i}" fill="none" '
                       f'stroke="#3d8bfd" stroke-width="3.2" stroke-linecap="round" opacity="{0.9 - 0.25 * i}"/>' for i in range(3))
        note = ('<g transform="translate(206,96)" fill="#3d8bfd"><ellipse cx="0" cy="14" rx="6" ry="4.5"/>'
                '<rect x="4.2" y="-6" width="2.6" height="20" rx="1.2"/><path d="M6.8,-6 Q16,-2 14,8 Q12,0 6.8,0 Z"/></g>')
        return arcs + note
    return ""


FRAMES = {
    "idle": ("open", "smile", ""),
    "blink": ("blink", "smile", ""),
    "talk1": ("open", "talk1", ""),
    "talk2": ("open", "talk2", ""),
    "think": ("think", "think", "think"),
    "happy": ("happy", "happy", "happy"),
    "worried": ("worried", "worried", "worried"),
    "listen": ("open", "smile", "listen"),
}


def frame(e, m, x):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 300" width="240" height="300">\n'
            f'<!-- Kan-chan, the KantanOS Helper (KantanOS, built with Claude; GPL-2.0-or-later) -->\n'
            f'{DEFS}{back()}\n  {eyes(e)}\n  {mouth(m)}{front_hair()}\n  {extras(x)}\n</svg>\n')


def main():
    os.makedirs(OUT, exist_ok=True)
    for name, (e, m, x) in FRAMES.items():
        with open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8") as f:
            f.write(frame(e, m, x))
    with open(os.path.join(OUT, "character.json"), "w", encoding="utf-8") as f:
        json.dump({"name": "Kan-chan", "voice": "en_US-hfc_female-medium",
                   "greeting": "Hi! I'm Kan-chan. Tell me what's wrong, and I'll take a look."}, f, indent=1, ensure_ascii=False)
    print("wrote", len(FRAMES), "frames to", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
