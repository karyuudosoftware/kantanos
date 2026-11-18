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
    ("com.github.IsmaelMartinez.teams_for_linux", "Microsoft Teams", "Teams for work or school, in its own window (the community Teams for Linux app)."),
    ("com.discordapp.Discord", "Discord", "Voice, video and text chat for friends and gaming groups."),
    ("com.rtosta.zapzap", "WhatsApp (ZapZap)", "WhatsApp in its own window, with notifications. Link it to your phone once by scanning the code with WhatsApp (Settings → Linked devices)."),
]
GAMES = [
    ("com.heroicgameslauncher.hgl", "Heroic Games Launcher", "Epic Games Store, GOG and Amazon Prime Gaming. In Heroic, open a game's menu and choose \"Add to Steam\" to see it in Game Mode."),
    ("net.retrodeck.retrodeck", "RetroDECK", "Classic consoles in one app (the Retro Games tile). You supply your own game files; it can read them from the NAS."),
]
TOOLS = [
    ("com.github.shundhammer.qdirstat", "QDirStat", "See which folders use the most space, as a sorted list (like TreeSize on Windows)."),
    ("com.jeffser.Alpaca", "Alpaca (AI chat on this PC)", "Chat with an AI that runs on this PC: recipes, letters, checking documents, questions. Private and free. To share the Helper's AI, add the instance http://127.0.0.1:11434 in Alpaca's settings."),
    ("org.gnome.DejaDup", "Déjà Dup Backups", "Automatic backups of your files to Google Drive, OneDrive, the NAS or a USB drive, and getting them back. The simplest choice."),
    ("org.gnome.World.PikaBackup", "Pika Backup", "Backups as often as every hour to the NAS or a USB drive, with older versions of every file to go back to."),
]

PAUSE = 'echo; echo "Press Enter to close..."; read -r _'


def q(text):
    return json.dumps(text, ensure_ascii=False)     # JSON strings are valid YAML strings


# The Welcome engine highlights (and focuses) the option whose id equals the status token,
# and words the status chip from the token: "uninstall" -> "Not installed", "install" ->
# "Installed". So the Install button gets the id "uninstall": it is the suggested button
# while the app is missing. "Remove" never matches, so nothing is pushed once installed.
def app(fid, name, desc):
    slug = fid.split(".")[-1].lower()
    return f"""      - id: {q(slug)}
        title: {q(name)}
        description: {q(desc)}
        default: false
        status_script: {q(f"kantan-app status {fid}")}
        options:
          - id: "uninstall"
            label: {q(f"Install {name}")}
            script: {q(f"kantan-app install {fid}")}
          - id: "remove-app"
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
    action("phone", "Connect your Android phone", "See phone notifications on the PC, share files and the clipboard, use the phone as a remote. Install KDE Connect on the phone from the Play Store, then pair it here.",
           "nohup setsid kdeconnect-app >&/dev/null"),
    action("nas", "Connect your NAS", "Make the shared folders on your NAS (for example a TrueNAS box) work like normal folders in every app. Asks for the NAS user name and password once.",
           f"ujust kantan-nas-connect; {PAUSE}"),
    action("wake", "Wake this PC from another device", "Shows the details a wake-up app needs to switch this PC on over the network (Wake-on-LAN).",
           f"ujust kantan-wake-info; {PAUSE}"),
    action("update", "Check for updates", "Update KantanOS and your apps. A restart applies system updates; the previous version stays available as a fallback.",
           f"ujust update; {PAUSE}"),
    action("about", "About this PC", "Show the KantanOS version and system details.",
           "nohup setsid kinfocenter >&/dev/null"),
]), hidden=True)
import looks as _looks  # tools/looks.py: the table of colour styles

doc += screen("Look", "Pick a colour style. It changes the wallpaper, colours and icons straight away.", "".join(
    action(f"look-{look_id}", label,
           ("Dark" if dark else "Light") + " style." + (" This is the one KantanOS starts with." if look_id == _looks.DEFAULT else ""),
           f"kantan-look set {look_id}")
    for look_id, (label, _ja, dark, *_rest) in _looks.LOOKS.items()))
doc += screen("Office", "Documents, notes and email", "".join(app(*a) for a in OFFICE))
doc += screen("Creative", "Photos, drawing, video and audio", "".join(app(*a) for a in CREATIVE) + action(
    "artcraft", "ArtCraft", "Free creative and office apps (still in development). Opens the ArtCraft website, where you can get its launcher.",
    "xdg-open https://getartcraft.com/"))
doc += screen("Media & Chat", "Players and messaging", "".join(app(*a) for a in MEDIA + CHAT))
doc += screen("Windows", "Windows programs", "".join([
    action("notepadpp", "Notepad++", "The Windows Notepad++ text editor, downloaded from its official page and installed in your Windows programs.",
           f"kantan-windows install-notepadpp; {PAUSE}"),
    action("cdrive", "Open the C: drive", "Program Files and the other folders your Windows programs use. It is also in the Files sidebar as \"C: (Windows)\".",
           "nohup setsid kantan-windows c-drive >&/dev/null"),
    action("winhow", "Install any Windows program", "Download its installer (.exe or .msi) and double-click it in Files. It then appears in the app menu and in search (Win+Space). Most programs work; the rest need the Windows virtual machine below.",
           "nohup setsid xdg-open \"$HOME/Downloads\" >&/dev/null"),
    action("winvm", "Windows virtual machine", "Real Windows 11 inside KantanOS, for programs that don't work otherwise; they open as normal windows. Needs the Windows 11 ISO from Microsoft and a Windows 11 Pro licence. Once set up, this opens Windows or lets you manage it.",
           "nohup setsid kantan-windows vm setup >&/dev/null"),
    action("winecfg", "Windows settings", "Advanced: Windows version, drives and graphics settings for your Windows programs (Wine settings).",
           "nohup setsid kantan-windows settings >&/dev/null"),
]))
doc += screen("Games", "Game stores and classic consoles", "".join(app(*a) for a in GAMES) + "".join([
    action("lutris", "EA app, Ubisoft Connect, Battle.net", "Lutris is already installed. Search for the store in Lutris and choose Install; it then adds its games to your library. Games with anti-cheat may not run on Linux.",
           "nohup setsid lutris >&/dev/null"),
    action("gamemode", "Open Game Mode", "Your whole library, full screen, for a controller (Steam Big Picture).",
           "nohup setsid steam steam://open/bigpicture >&/dev/null"),
    action("restartwin", "Restart into Windows", "For games whose anti-cheat only works on real Windows (when Windows is installed on this PC). Windows starts once; the next restart is KantanOS again. Also a tile on the \"What would you like to do?\" screen.",
           "nohup setsid /usr/libexec/kantanos/restart-windows >&/dev/null"),
]))
doc += screen("Tools", "Disk space and system helpers", "".join([
    action("filelight", "Show folder sizes", "See what is filling your drive as a ring chart (Filelight). In Files you can also right-click any folder and choose Show Folder Sizes.",
           "nohup setsid filelight \"$HOME\" >&/dev/null"),
    action("forcequit", "Force quit an app", "End an app that has stopped responding. Shortcut: Ctrl+Alt+Esc.",
           "nohup setsid /usr/libexec/kantanos/force-quit >&/dev/null"),
    action("helper", "Something not working? Ask the KantanOS Helper", "Looks at what went wrong, explains it in plain words and offers safe fixes, asking before each one. Its AI runs on this PC (set it up once in AI settings) or, if you choose, an online service.",
           "nohup setsid /usr/libexec/kantanos/helper >&/dev/null"),
    action("kanchan", "Meet Kan-chan, your PC companion", "Chat with Kan-chan by talking or typing. She remembers what you tell her (you can see, change or delete it all in \"What I remember\"), suggests what to cook and keeps you company. Everything stays on this PC. Adds her to the app menu.",
           "nohup setsid /usr/libexec/kantanos/kanchan --enable >&/dev/null"),
    action("claudecode", "Install Claude Code", "Claude's coding assistant for the terminal, from Anthropic's official installer. Needs a Claude account. It goes into your home folder, so updates to KantanOS don't affect it.",
           f"curl -fsSL https://claude.ai/install.sh | bash; {PAUSE}"),
    action("virusscan", "Scan Downloads for viruses", "Checks your Downloads folder with ClamAV. To check anything else, right-click it in Files and choose Scan for viruses.",
           "nohup setsid /usr/libexec/kantanos/virus-scan >&/dev/null"),
    action("fixdock", "Dock or screen missing?", "Puts the dock back, and lists the screens KantanOS sees (an AV receiver on HDMI can count as a screen). To pick the main screen, run: ujust kantan-main-screen",
           f"ujust kantan-reset-dock; ujust kantan-display-info; {PAUSE}"),
]) + "".join(app(*a) for a in TOOLS))
doc += screen("Display & Sound", "HDR and surround sound", "".join([
    action("hdr-on", "Turn HDR on", "Enables HDR and wide colour on every connected display that supports it.",
           f"ujust kantan-hdr-on; {PAUSE}"),
    action("hdr-off", "Turn HDR off", "Switches every display back to standard colour.",
           f"ujust kantan-hdr-off; {PAUSE}"),
    action("audio-71", "Use 7.1 surround over HDMI", "For an AV receiver. Turn the receiver on first. Heights are added by the receiver's upmixer.",
           f"ujust kantan-audio-71; {PAUSE}"),
    action("atmos", "Films with Dolby Atmos", "Open films with \"Movie Player (Dolby Atmos)\" (right-click a film → Open With). It sends Dolby Atmos, TrueHD and DTS sound untouched to the receiver, like PotPlayer's pass-through on Windows.",
           "nohup setsid xdg-open \"$HOME/Videos\" >&/dev/null"),
]))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
    fh.write(doc)
print("welcome definition written:", os.path.normpath(OUT))
