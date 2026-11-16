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

**Windows virtual machine (planned design).** For programs Wine cannot run (some Office
versions, drivers, apps with copy protection):

1. A one-click "Set up Windows" step: turns on the virtual-machine service the base already
   has, and asks you to download the official Windows 11 ISO from Microsoft yourself (your
   own licence; KantanOS never ships or fetches Windows for you).
2. An unattended install with a slimmed-down setup (no ads, no extra apps), sized for the PC
   it runs on, with a shared folder to your home folder.
3. Programs inside it appear as normal windows on the KantanOS desktop, with their own app
   menu shortcuts (RDP "RemoteApp", the method WinApps uses; the RDP client is already in
   the image). The VM starts on first use and pauses when idle.
4. Not for anti-cheat games: those detect virtual machines; they get "restart into Windows".

- [x] Windows programs through Wine: double-click any .exe or .msi to install or run it;
      installed programs land in the app menu and search. One shared Windows space
      (`~/.wine`), Windows 11 mode, Japanese fonts. Welcome → Windows tab.
- [ ] Windows programs Wine cannot run: the built-in Windows VM above.
- [x] `C:\` in the Files sidebar ("C: (Windows)").
- [ ] Android apps through Waydroid.
- [x] Notepad++ through Wine (one click in Welcome → Windows). Known Wine bug: its menu bar
      wraps into a column (Wine's own apps are fine); recheck on Wine updates. ArtCraft still to try.

## Phone, messaging and smart home

- [x] Phone notifications and file sharing (KDE Connect).
- [ ] Messaging: Teams, WhatsApp, Signal, Telegram, Messenger, Instagram.
- [ ] Smart home: house temperature widget for a Nest thermostat through Home Assistant.

## AI and accessibility

- [ ] **Local AI:** images, document checking, recipes, and an Android companion app.
- [ ] **KantanOS Helper:** explains what just crashed (crash reports and logs, in plain
      words), offers a fix from a fixed list of safe repairs, and can look online for a
      solution. Asks before every action and every web search; everything can be undone;
      never takes instructions from what it reads.
- [ ] AI-made shortcuts on the "What would you like to do?" screen.
- [ ] Accessibility: screen reader plus an AI voice helper that reads and handles email and
      the day's agenda, always asking before it sends or deletes anything.

## Storage, safety and system

- [ ] Backups every 30 minutes to OneDrive, Google Drive, Dropbox or the NAS; file snapshots
      to undo changes to documents.
- [ ] Security: tighten the firewall (the base allows all high ports) and add virus scanning.
- [ ] Lite edition for small PCs (Azulle Access 3 class).

## Working setup

- [ ] Claude Code inside KantanOS, with a handoff file so a session there can continue.
