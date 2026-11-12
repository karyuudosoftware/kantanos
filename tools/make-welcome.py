#!/usr/bin/env python3
"""Generates the KantanOS Welcome app definition (shown by the yafti GTK front end that the
Bazzite base already ships). Output replaces /usr/share/yafti/yafti.yml in the image.

Run from anywhere:  python tools/make-welcome.py
"""
import json, os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",
                   "system_files", "usr", "share", "yafti", "yafti.yml")

# (flatpak id, name, description)
OFFICE = [
    ("org.libreoffice.LibreOffice", "LibreOffice", "Word processor, spreadsheets and presentations. Opens and saves Microsoft Office files."),
    ("com.github.dail8859.NotepadNext", "NotepadNext", "A Notepad++ style text editor that runs natively."),
    ("org.mozilla.Thunderbird", "Thunderbird", "Email and calendar."),
]
CREATIVE = [
    ("org.kde.krita", "Krita", "Digital painting and drawing."),
    ("org.gimp.GIMP", "GIMP", "Photo editing."),
    ("org.inkscape.Inkscape", "Inkscape", "Vector illustration."),
    ("org.kde.kdenlive", "Kdenlive", "Video editing."),
    ("org.darktable.Darktable", "darktable", "Photo library and RAW developing."),
    ("org.audacityteam.Audacity", "Audacity", "Audio recording and editing."),
    ("org.blender.Blender", "Blender", "3D modelling and animation."),
]
MEDIA = [
    ("org.videolan.VLC", "VLC", "Plays almost any video or audio file."),
    ("org.kde.haruna", "Haruna", "A simple, modern video player."),
    ("org.kde.elisa", "Elisa", "Music player."),
]
CHAT = [
    ("org.signal.Signal", "Signal", "Private messaging."),
    ("org.telegram.desktop", "Telegram", "Messaging."),
]

PAUSE = 'echo; echo "Press Enter to close..."; read -r _'


def q(text):
    return json.dumps(text, ensure_ascii=False)     # JSON strings are valid YAML strings


def app(fid, name, desc):
    slug = fid.split(".")[-1].lower()
    return f"""      - id: {q(slug)}
        title: {q(name)}
        description: {q(desc)}
        default: false
        status_script: {q(f"kantan-app status {fid}")}
        options:
          - id: "install"
            label: {q(f"Install {name}")}
            script: {q(f"kantan-app install {fid}")}
          - id: "uninstall"
            label: {q(f"Remove {name}")}
            script: {q(f"kantan-app uninstall {fid}")}
"""


def action(aid, title, desc, script):
    return f"""      - id: {q(aid)}
        title: {q(title)}
        description: {q(desc)}
        default: false
        script: {q(script)}
"""


def screen(title, desc, body, hidden=False):
    head = f"  - title: {q(title)}\n    description: {q(desc)}\n"
    if hidden:
        head += "    hidden: true\n"
    return head + "    actions:\n" + body


doc = "title: KantanOS Welcome\nscreens:\n"
doc += screen("Welcome!", "Get started with KantanOS", "".join([
    action("store", "Open the app store", "Browse and install thousands of apps.",
           "nohup setsid gtk4-launch io.github.kolunmi.Bazaar >&/dev/null"),
    action("japanese", "Type in Japanese", "Japanese input is already installed. Press Ctrl+Space in any text box to switch between English and Japanese.",
           "nohup setsid fcitx5-configtool >&/dev/null"),
    action("update", "Check for updates", "Update KantanOS and your apps. A restart applies system updates; the previous version stays available as a fallback.",
           f"ujust update; {PAUSE}"),
    action("about", "About this PC", "Show the KantanOS version and system details.",
           "nohup setsid kinfocenter >&/dev/null"),
]), hidden=True)
doc += screen("Office", "Documents, notes and email", "".join(app(*a) for a in OFFICE))
doc += screen("Creative", "Photos, drawing, video and audio", "".join(app(*a) for a in CREATIVE) + action(
    "artcraft", "ArtCraft", "Free creative and office apps (still in development). Opens the ArtCraft website, where you can get its launcher.",
    "xdg-open https://getartcraft.com/"))
doc += screen("Media & Chat", "Players and messaging", "".join(app(*a) for a in MEDIA + CHAT))
doc += screen("Display & Sound", "HDR and surround sound", "".join([
    action("hdr-on", "Turn HDR on", "Enables HDR and wide colour on every connected display that supports it.",
           f"ujust kantan-hdr-on; {PAUSE}"),
    action("hdr-off", "Turn HDR off", "Switches every display back to standard colour.",
           f"ujust kantan-hdr-off; {PAUSE}"),
    action("audio-71", "Use 7.1 surround over HDMI", "For an AV receiver. Turn the receiver on first. Heights are added by the receiver's upmixer.",
           f"ujust kantan-audio-71; {PAUSE}"),
]))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(doc)
print("welcome definition written:", os.path.normpath(OUT))
