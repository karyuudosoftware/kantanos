# KantanOS roadmap

What is done, what is next, and the ideas waiting their turn. Updated as work lands.

## Done

- **Identity and look:** 簡単 KantanOS branding, boot splash, login and lock screens, seven
  colour looks (Light by default; Sakura, Graphite, Ocean, Forest, Ember, Aurora), glass
  theme, Inter font, Japanese input (Ctrl+Space).
- **KantanOS Dock:** macOS-style magnification, running dots, hop while starting, right-click
  menu (new window, keep/remove, close, force quit), launcher button and Trash.
- **Window animations:** genie minimize into the dock (Magic Lamp), smooth maximize, open and
  close. *Only checked as settings; the test VM cannot draw these effects.*
- **Spotlight-style search:** Win+Space opens a centred search for apps, files, settings and
  calculations.
- **Force Quit:** Ctrl+Alt+Esc lists open apps and ends a frozen one after a confirmation.
- **What would you like to do?** screen after login: Desktop, Game Mode, Retro Games, your
  own web shortcuts, look picker, restart and shut down. Warns and offers "Create your
  account" when someone signs in as root.
- **Files:** Explorer-style toolbar and sidebar, folder-size tools (Filelight, QDirStat,
  "Show Folder Sizes" on right-click).
- **KantanOS Welcome:** one-click installs (office, creative, media, chat, tools), looks,
  HDR, 7.1, phone link, Wake-on-LAN details.
- **Sound:** HDMI audio kept awake for AV receivers; per-speaker test
  (`ujust kantan-speaker-test`).
- **System:** signed daily updates from GitHub with one-step undo, Windows-friendly clock,
  Wake-on-LAN on wired ports, installer ISO and run-from-USB image.

## Next

- [x] NAS: `ujust kantan-nas-connect` (or Welcome) connects SMB shares as normal folders.
- [ ] 7.1 sound: confirm on the receiver (Multichannel/Direct listening mode) with the
      speaker test; look at the channel layout only if that does not fix it.
- [ ] Installer: stop a root-only setup (the warning after login is the safety net for now);
      title shows the Fedora release number; firmware boot entry not always created.
- [ ] Files: window title still says "Dolphin"; drive list shows raw names like "root".
- [x] Fixes from the first weeks on the real PC (Nov 2026): Windows ISOs not recognised
      (UDF), "What would you like to do?" and Force Quit missing Qt for Python, Windows-drive
      notice reworded, `ujust kantan-reset-dock` / `kantan-display-info` /
      `kantan-main-screen` / `kantan-login-screen-sync` for the dock and login screen with a
      receiver on HDMI, `ujust kantan-admin-password off`, `ujust kantan-waydroid-text-size`.
- [ ] Dock missing and login screen not full-size over DisplayPort: confirm the cause on the
      real PC with `ujust kantan-display-info`.
- [x] Weather: KantanOS Weather in the top bar (Open-Meteo, any town worldwide; replaces
      KDE's widget). Apps may ask for the location; `ujust kantan-set-location` fixes the
      PC's location by town name. Without a set town it now finds the area by itself (GeoClue).
- [x] KantanOS Stats in the top bar (like the Mac "Stats" app): small graphs, bars or numbers
      for processor, graphics card, memory, drive, network and temperature; click for gauges,
      per-thread bars, history, busiest apps, every drive. Settings pick what's shown.
- [~] Dolby Atmos: HDMI pass-through allowed for TrueHD/E-AC-3/DTS-HD, plus "Movie Player
      (Dolby Atmos)" (mpv). To confirm on the receiver.

## Entertainment and games

- [ ] **Watch TV:** a custom TV app built from the family's own TV projects (no Kodi).
- [~] **Game Mode:** Welcome → Games installs Heroic (Epic, GOG, Amazon → "Add to Steam") and points to Lutris for EA/Ubisoft; automatic library sync still to do.
- [ ] **Retro Games:** RetroDECK set up as a LaunchBox replacement, emulator library on the
      NAS (NFS rather than iSCSI).
- [ ] **Vintage Computers:** DOS, Windows 3.x–98, classic Mac OS, Amiga, C64, Atari ST and
      more through existing emulators. Own ROMs/install media only; nothing copyrighted ships.
- [ ] **Anti-cheat games:** one-click "restart into Windows".
- [ ] **Remote:** air-mouse remote support, including its voice button.

## Windows and Android apps

**Windows virtual machine** (`kantan-windows vm`, Welcome → Windows → Windows virtual
machine). For programs Wine cannot run (some Office versions, apps with copy protection):

1. Guided setup: checks the PC (virtualisation on, 8 GB memory, 45 GB free), opens
   Microsoft's download page for the Windows 11 ISO (your own download and licence; KantanOS
   never ships or fetches Windows), and takes an optional product key.
   Reads the disc itself to pick the edition: Pro from the regular Windows 11 disc, or a
   Windows 10/11 (IoT) Enterprise LTSC disc with no key needed; warns about Windows 10
   editions without security updates. Activate later in Windows.
2. Unattended install of Windows in a VM owned by your account (QEMU, Secure Boot,
   TPM 2.0; no admin rights), sized for the PC. A first-sign-in script removes ads and
   extras, turns on Remote Desktop for this PC only, and removes the setup password.
3. Windows programs get their own app menu entries and open as normal windows (FreeRDP
   RemoteApp); your home folder is `\\tsclient\home` inside Windows. The VM starts on first
   use, pauses after 10 idle minutes and shuts Windows down cleanly on logout.
4. Not for anti-cheat games: those detect virtual machines; they get "restart into Windows".

*Tested without Windows: firmware, TPM, setup disc, commands, and edition choice with
sample discs (`tools/vm/make-test-isos.sh`). The first full install is still to be tried
on the real PC.*

- [x] Windows programs through Wine: double-click any .exe or .msi to install or run it;
      installed programs land in the app menu and search. One shared Windows space
      (`~/.wine`), Windows 11 mode, Japanese fonts. Welcome → Windows tab.
- [~] Windows programs Wine cannot run: the Windows VM above (built; first real install to do).
- [x] `C:\` in the Files sidebar ("C: (Windows)").
- [ ] Android apps through Waydroid.
- [x] Notepad++ through Wine (one click in Welcome → Windows). Known Wine bug: its menu bar
      wraps into a column (Wine's own apps are fine); recheck on Wine updates. ArtCraft still to try.

## Phone, messaging and smart home

- [x] Phone notifications and file sharing (KDE Connect).
- [x] Messaging: Signal, Telegram, Teams (Teams for Linux), WhatsApp (ZapZap), Discord in
      Welcome; Messenger and Instagram as website tiles ("Add shortcut"). WhatsApp for
      Windows only comes from the Microsoft Store, which Wine can't run.
- [ ] Smart home: house temperature widget for a Nest thermostat through Home Assistant.

## AI and accessibility

- [ ] **Local AI:** images, document checking, recipes, and an Android companion app.
- [x] **KantanOS Helper** (Welcome → Tools, or search "fix"): reads recent crashes, failed
      services, errors and disk space; its AI explains them in plain words and picks repairs
      from a fixed list of 11; asks before every repair, web search and online request.
      AI: Ollama on this PC (Vulkan; Gemma 3 12B with 14 GB+ video memory, else 4B), or any
      OpenAI-compatible online service (FreeLLMAPI, OpenRouter, ...), or none (keyword
      suggestions). "Ask Claude Code" hands bigger jobs over with the report.
- [ ] Helper: open automatically when an app crashes (DrKonqi) and when a service fails.
- [ ] AI-made shortcuts on the "What would you like to do?" screen.
- [ ] Accessibility: screen reader plus an AI voice helper that reads and handles email and
      the day's agenda, always asking before it sends or deletes anything.

## Storage, safety and system

- [~] Backups: Déjà Dup (Google Drive, OneDrive, NAS, USB) and Pika Backup (hourly, older
      versions of each file) in Welcome → Tools. Still to do: a KantanOS one-step setup and
      every-30-minutes schedule.
- [x] Security: strict KantanOS firewall zone (only phone link, game streaming, device
      discovery and file sharing reachable; `ujust kantan-firewall`), ClamAV with "Scan for
      viruses" in Files and Welcome → Tools.
- [ ] Lite edition for small PCs (Azulle Access 3 class).

## Working setup

- [x] Claude Code inside KantanOS: "Install Claude Code" in Welcome → Tools, and `CLAUDE.md`
      in this repository as the handoff file for sessions on either PC.
