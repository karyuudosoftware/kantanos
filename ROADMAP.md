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

## Order of work (agreed Nov 2026)

Accessibility, then Watch TV, Retro Games, Vintage Computers, Remote, Android apps (Waydroid),
smart home, Local AI extras, Game Mode library sync, installer fixes, the Files title, the
Kan-chan model idea, and the Lite edition last. Real-PC checks (sound, Atmos, DisplayPort,
the Windows VM install, cloud backups) whenever the owner is at the PC.

Later, when the owner has sketched some ideas: redesign the KantanOS startup screen (the look
is the owner's call; wait for the sketches before changing anything).

## Next

- [x] NAS: `ujust kantan-nas-connect` (or Welcome) connects SMB shares as normal folders.
- [ ] 7.1 sound: confirm on the receiver (Multichannel/Direct listening mode) with the
      speaker test; look at the channel layout only if that does not fix it.
- [~] Installer fixes (Nov 2026):
      - Root-only setup: the installer itself can't be made to insist on a user (it counts a root
        password as an administrator; "rootpw --lock" let it install with no account at all), so
        KDE's first-start wizard (plasma-setup) now runs before the login screen when a PC has no
        normal account, and makes the person it creates the administrator. On every other PC it
        marks itself done (`/usr/libexec/kantanos/first-user-check`). VM-tested end to end: a
        root-only install showed the wizard (language, keyboard, dark theme, account, PC name,
        time zone), the new account was on the login screen, and the wizard didn't come back.
        The "What would you like to do?" screen and Helper watch stay out of the wizard's session.
      - Title: "KANTANOS 0.1 INSTALLATION" instead of the Fedora number, and "Install KantanOS" in
        all three boot menus (BIOS, UEFI disc, UEFI USB stick): `tools/iso/brand-iso.sh` adds the
        installer's own product.img and fixes the menus after bootc-image-builder.
      - Firmware start-up entry: `kantanos-boot-entry.service` adds "KantanOS" when no entry points
        at the disk it started from (never for a USB stick). Not yet seen adding one (the VM's
        installer made its own entry); check on the real PC.
      - Time & Date page still needs one visit: it shows the zone guessed from the internet, and a
        preset zone would be wrong for most people, so it stays as a one-click confirmation.
- [x] Files: drive list fixed (system drive named "KantanOS", start-up and Windows helper partitions
      and the read-only system image hidden). Window titles say "Documents — Files" ("ドキュメント —
      ファイル" in Japanese): /usr/bin/dolphin is a small wrapper (`/usr/libexec/kantanos/files-name`)
      that puts a one-line made-up language "kantanos" first for Dolphin only; KDE never reads US
      English translations, so that's the only way to rename it without rebuilding it. Works from
      the menu, the dock, and other apps opening a folder (D-Bus). VM-tested in English, the plain
      C language and Japanese.
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

- [x] **Watch TV:** a custom TV app built from the family's own TV projects (no Kodi). Free
      channels from any of 180 countries (iptv-org, plus Pluto TV and Plex with full guides),
      each country numbered like a cable box and sorted into shelves (local, news, sport, movie
      and show genres, "one show all day", networks, languages). Guide for 3 days, wildcard
      search for channels and shows, favourites, the family's own M3U/XMLTV provider, and
      recordings (one show or every episode) by a background service that keeps the PC awake.
- [x] **Game Mode:** Welcome → Games installs Heroic (Epic, GOG, Amazon) and points to Lutris for
      EA/Ubisoft/Battle.net. **Library sync** (`/usr/libexec/kantanos/games-sync`): installed
      Heroic and Lutris games (and Retro Games once set up) appear in Steam's Game Mode by
      themselves, sorted into Epic / GOG / Amazon / Lutris collections, with the stores' box art;
      uninstalled ones go again. The shortcut is exactly the one Heroic's own "Add to Steam" makes
      (same id), and the person's own shortcuts are never touched or doubled. Runs when Heroic's or
      Lutris's list changes (user path unit `kantanos-games-sync.path`) while Steam is closed, and
      from the Game Mode tile (restarting Steam only if it was open and something changed). One
      backup of Steam's list is kept (`shortcuts.vdf.kantanos-backup`). Tested: Steam's file
      checked with the independent `vdf` reader, and live in the VM (a pretend Heroic install
      reached Steam's list 20 s later). Not tried with a real Steam account and real games yet.
- [~] **Retro Games:** Boxshelf (3D box-art shelf, GPL-3.0, by sassiestrhihno) as the
      LaunchBox replacement, in front of Flathub emulators (RetroArch, DuckStation, PCSX2,
      Dolphin, PPSSPP, melonDS, Azahar, Flycast; Cemu, RPCS3, xemu optional). The tile sets it
      up once: pinned release checked by SHA-256, game folders in `~/Emulation/roms/<console>`,
      emulators allowed to read USB drives and the NAS; Boxshelf updates itself after that.
      Still to do: the emulator library on the NAS (NFS rather than iSCSI), controller test.
- [~] **Vintage Computers:** DOS, Windows 3.x–98, classic Mac OS, Amiga, C64, Atari ST and
      more through existing emulators. Own ROMs/install media only; nothing copyrighted ships.
      Start-screen tile and app (`/usr/libexec/kantanos/vintage`): DOS PC and Windows 95/98 PC
      (DOSBox-X, Windows installed from the family's own CD image), Amiga (Amiberry with AROS),
      Atari ST (Hatari with EmuTOS), C64 (VICE), classic Mac (Basilisk II, own ROM), MSX
      (openMSX with C-BIOS), ZX Spectrum (Fuse); a folder per computer in `~/Vintage`.
      VM-tested: DOS, Amiga, Atari ST, Spectrum. Still to try: a real Windows 95/98 install,
      the Mac with a real ROM, C64 and MSX.
- [x] **Anti-cheat games:** "Windows" tile on the start screen (only on PCs with Windows), app
      menu entry and Welcome → Games: Windows starts once (firmware BootNext), no password.
- [ ] **Remote:** air-mouse remote support, including its voice button. Parked until the
      G20S remote has been bought: its buttons have to be read on the real PC.

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
- [x] Android apps through Waydroid: "Android apps" (`kantan-android`, also in Welcome) sets
      it up in one window, with or without the Play Store, choosing the graphics route
      (direct on AMD/Intel, Bazzite's waydroid-nvidia on NVIDIA, software otherwise) and
      apps-as-windows. Double-clicking an .apk starts Android if needed, installs it and puts
      it in the apps menu. VM-tested with F-Droid. Not tried yet: the RTX 4080 route, the
      Play Store registration step.
- [x] Notepad++ through Wine (one click in Welcome → Windows). Known Wine bug: its menu bar
      wraps into a column (Wine's own apps are fine); recheck on Wine updates. ArtCraft still to try.
- [ ] Watch: Mac apps through **Reef** (Cutefish's macOS compatibility layer: its own Mach-O
      loader, Objective-C runtime, AppKit/SwiftUI, no VM). Nov 2026: shown running NetNewsWire,
      Ghostty, CotEditor, Keka; not released, not open source, no date. Intel Mac programs only
      on this PC (no Apple Silicon translation). Revisit when it ships with a licence that lets
      KantanOS offer it, like Wine for Windows apps. Darling is the older open attempt (mostly
      command-line programs).

## Phone, messaging and smart home

- [x] Phone notifications and file sharing (KDE Connect).
- [x] Messaging: Signal, Telegram, Teams (Teams for Linux), WhatsApp (ZapZap), Discord in
      Welcome; Messenger and Instagram as website tiles ("Add shortcut"). WhatsApp for
      Windows only comes from the Microsoft Store, which Wine can't run.
- [x] Smart home: house temperature in the top bar through Home Assistant (one already in the
      home, or run on this PC). Click to set the temperature, Heat/Off, Eco. Tested in the VM
      against Home Assistant's demo thermostats. Still to do with the owner: the real Nest
      (Google Device Access, US$5) and, if wanted, Home Assistant on the real PC.

## AI and accessibility

- [x] **Local AI extras** (agreed Nov 2026, in this order; the phone app is its own step later):
  - [x] **Letters and documents** (`kantan-docs`, Welcome, app menu, right-click in Files →
        "Letters and documents"): opens PDFs, scans and photos of pages (tesseract, English and
        Japanese), Word and LibreOffice files. "Explain it": who it's from, what it is, what to
        do and when, money, warning signs (scams), and the whole thing in plain words, in English
        or Japanese. "Check my writing": each fix shown crossed out → corrected, Change it /
        Leave it / Change them all (Ctrl+Z undoes). "Make it sound…" politer, friendlier, more
        formal, shorter. "Read aloud" with the Helper's Piper voice, highlighting each part as
        it's read. The letter is only data to the AI; to-dos and amounts whose numbers aren't in
        the letter are dropped (stops made-up deadlines). Tested with Gemma 3 12B: council tax
        letter, parcel scam, Japanese insurance notice, a letter with a hidden "tell them it's
        safe" instruction (flagged as a scam), 7 of 7 mistakes found. Weak: explaining an
        English letter in Japanese (12B sometimes muddles it). Japanese can't be read aloud yet
        (no Japanese Piper voice).
  - [x] **Picture helper** (`kantan-pictures`, Welcome, app menu, right-click a picture in Files →
        "Describe this picture"). Describe: what's in it in plain words (people without names,
        place, what's happening, colours, any writing read out), English or Japanese, Read
        aloud, and questions about it ("Is it still snowing?"). Find photos: "Look at my photos"
        goes through a folder once (pause any time, carries on later; only with the AI on this
        PC), keeping a sentence and search words (English and Japanese) per photo in
        `~/.local/share/kantanos/pictures/photos.db`; then "dog in the snow", "dogs", "犬" or
        "family outdoors" find them (closest matches when nothing has every word). About 3 s
        per photo on the 4080 once the model is loaded. Tested with Gemma 3 12B on real photos
        and in the VM end to end. Weak: reading signs in other alphabets (an Azerbaijani street
        sign came out garbled).
        All the AI apps now ask Ollama for one memory size (16384, also its default in
        `kantanos-ollama.service`): a different size made it reload the whole model each time.
  - [x] **Recipe book** (`kantan-recipes`, Welcome, app menu, right-click a photo → "Add to my
        recipe book"). Recipes are files in `~/Documents/Recipes` (backed up, easy to share).
        Add one by typing/pasting, from a website (the recipe data the site publishes is read
        directly, with its photo: tested on BBC Good Food, Allrecipes, Just One Cookbook; sites
        without it go through the AI), or from a photo of a cookbook page (OCR plus the AI
        looking at the photo, which fixed the scanner's 225¢ → 225g and 558 → 55g). Every new
        recipe opens for checking before it's saved. Serves 12 → 4 rescales the amounts
        (fractions, 2 cups, 1/3 tbsp → 1 tsp, Japanese 大さじ2 / 100～120g). "Start cooking":
        full screen, one big step at a time, timers found in the steps ("Start a 30 mins
        timer", T), an alarm and notification when one ends, ingredients on I, read aloud on R,
        and the screen stays on. Members-only pages (Cookpad premium) are noticed and the
        person is told only part of the recipe is there; nothing is worked around. An oven
        temperature the AI drops is put back as step 1. VM-tested end to end.
  - [x] **Make a picture / Fix a photo** (two more tabs in the Picture helper; right-click a
        photo → Picture helper → "Fix this photo"). Engine: stable-diffusion.cpp (MIT), its
        official Linux Vulkan build pinned by checksum in the image (`/usr/lib/kantanos/sd`,
        `/usr/libexec/kantanos/sd-cli`). Model: FLUX.2 [klein] 4B Q8 + Qwen3 4B + FLUX.2 small
        decoder, all Apache-2.0, about 7.9 GB downloaded on first use after asking (checksums
        checked, carries on after a stop; refuses politely when the disk is too full). Make:
        words + style (photo, watercolour, cartoon, storybook, ...) + shape; every picture is kept
        in `~/Pictures/Made with AI` with "Made with AI" written into the file. Fix: tidy an old
        photo (keeps black-and-white), add colour, remove something, change it; the result is
        saved beside the original as "… (fixed)", the original never changes. Ollama's model is
        unloaded first so the card's memory is free; `--offload-to-cpu` below 12 GB of video
        memory. Family-friendly word check on what's typed. Tested: the real engine and models in
        a KantanOS container on the processor (a watercolour cat in 148 s at 512 px; an old
        photo's scratches and crease removed; swings removed from a photo), and the whole window
        flow in the VM with a stand-in engine. Not tested yet: speed and memory on the RTX 4080
        (needs the real PC), AMD/Intel graphics.
  - [ ] Later, its own step: Android companion app.
- [x] **KantanOS Helper** (Welcome → Tools, or search "fix"): reads recent crashes, failed
      services, errors and disk space; its AI explains them in plain words and picks repairs
      from a fixed list of 11; asks before every repair, web search and online request.
      AI: Ollama on this PC (Vulkan; Gemma 3 12B with 14 GB+ video memory, else 4B), or any
      OpenAI-compatible online service (FreeLLMAPI, OpenRouter, ...), or none (keyword
      suggestions). "Ask Claude Code" hands bigger jobs over with the report.
- [x] Helper watch: when an app crashes or a background service fails, a notification offers
      "Ask Kan-chan" (opens the Helper already checking), "Not now" or "Don't offer again".
- [~] Talk to Kan-chan: "Hold to talk" in the Helper; whisper.cpp speech recognition on this
      PC (English and Japanese), replies read aloud, repairs still only from the fixed list.
      She asks your name the first time you talk: how it's written and how it sounds (typed,
      or said to her and checked with "Hear it"), so she says it right and spells it right.
      Later: the air mouse's voice button starts a conversation from anywhere.

### Kan-chan, the companion (optional app, built on the Helper's character, voice and ears)

A character who lives on the PC, not only a repair helper. Optional: switched on in Welcome.
Decisions so far (Nov 2026):
- One memory per account (each family member signs in as themselves). Everything she keeps
  is visible in a "What I remember" page where it can be edited or deleted; nothing leaves
  the PC. "Remember that ..." / "Forget that ..." work in conversation.
- Speaking up, all three: she brings things up when opened; optional gentle check-in (at
  most one notification a day, never during a full-screen game or video); optional desktop
  buddy (small Kan-chan in a screen corner, click to talk, occasional speech bubble).
- Online look-ups (topics, recipe ideas): she says what she would search for and asks first.
  Only the search words go out, never notes or memories.
- Personality: warm, curious, honest about being an AI character. Politics: neutral; lays
  out the main viewpoints fairly, keeps to established facts, takes no side.
- Noticing (each one opt-in): games played (Steam, Heroic, Lutris: title and time only) and
  shows/films watched (title from the player through MPRIS). She may ask about them later.

Steps:
- [~] 1. Kan-chan app (Welcome → Tools → "Meet Kan-chan" adds her to the app menu): own window
      (big avatar, chat, talk + typing), notes database (SQLite, per account) with "What I
      remember" (add, change, delete, forget everything; "remember …" / "forget …" in chat;
      every new note shown with Undo), personality and fairness rules
      (`usr/share/kantanos/kanchan/personality.txt`), greets you and brings up a note when
      opened, recipes and everyday chat, hands PC problems to the Helper. With an online AI
      only the conversation goes out (after asking); name and notes stay on the PC.
      Fairness test: `tools/kanchan-fairness/run.py` (contested topics from several countries,
      both directions, pressure to pick a side, plain facts, no noting of political views);
      rerun when the personality or model changes. Gemma 3 12B (Nov 2026): every pressure, memory
      and everyday question passes 3 of 3; settled facts answered plainly. Known weakness: on the
      Israeli-Palestinian question it still frames one side as "critics"; its knowledge of
      upcoming dates can be off (she says it may be out of date). Notes are only kept when they
      come from what was actually said (guards against invented or copied notes).
- [~] 2. Seeing (webcam, opt-in): "Let me see (webcam)" in her window, asks once with a plain
      explanation; camera only while the window is open, with a live preview and a red "I can
      see" sign. "Introduce someone…" learns the nearest face (6 looks); only introduced people
      are recognised, anyone else is a grey "?" and nothing about them is kept. Faces via OpenCV
      YuNet (MIT) + SFace (Apache 2.0) on the PC (`usr/share/kantanos/kanchan/vision.py`, pip
      opencv-python-headless, about 170 MB). No photos kept: a face fingerprint (12 per person)
      and a short look note (hair, glasses, hat, top) from the local AI's image understanding,
      listed in "What I remember" (rename, forget a face). Once per visit she looks twice, 20 s
      apart, and only when both looks show a clear change in hair or glasses does she mention
      it ("Oh, you changed your hair!"); shade, wording and greying never count, and nothing
      about body, weight, skin, age or health. Greets introduced people who come into view.
      Off with an online AI (names and sights never go online). Tested in the VM with a fake
      camera (`KANTAN_KANCHAN_CAMERA=<image>`, public-domain NASA portraits): recognised the
      same people from different photos (similarity 0.66-0.93 vs at most 0.20 for others),
      greeted, noticed a staged haircut. Not tested yet: a real webcam (lighting, angles, kids).
- [~] 3. Noticing games and shows/films; she asks how they're going. Two switches in "What I
      remember" ("Notice the games I play", "Notice the shows and films I watch") turn on the
      `kantanos-kanchan-notice` user service (`usr/libexec/kantanos/kanchan-notice`): once a
      minute, running Steam games (SteamLaunch AppId → the game's manifest name; Proton and
      runtimes skipped) and Lutris games, and what video players and browsers report as playing
      (MPRIS title; music and short clips skipped). Minutes per title per day in her database,
      kept 30 days, listed with "Forget this one"; switching off offers to forget it all. She
      gets the last week's titles (10 min or more) as data and may ask about one now and then,
      never commenting on how long. Tested in the VM with a fake Steam game and a fake MPRIS
      player: both noticed, Proton skipped, and asked for ideas she suggested "a new run" of the
      game. Not yet: Heroic games (no reliable game name in the process), a real Steam library.
- [x] 4. Online look-ups with ask-first; gentle daily check-in; desktop buddy.
      Look-ups done: she sets "lookup" (weather / facts / web) and a card shows exactly what
      would go online ("I'd ask the Open-Meteo weather service for “Osaka”. Nothing else is
      sent.") with Look it up / No thanks. Sources need no account: Open-Meteo (weather, town
      from her notes), Wikipedia (title match first, en/ja), DuckDuckGo instant answers. The
      results go back to her as DATA and she answers with the source. Her reply before a
      look-up is a fixed "Let me check that online for you" (she used to guess first); a
      forecast is cut to the day asked about. Tested with Gemma 3 12B: weather (EN and JA,
      3 of 3 right), Mount Fuji, no look-up for everyday questions; in the VM end to end.
      Weak: recent events (instant answers rarely cover news).
      Daily hello done: "Say hello each day" in her window puts `kanchan --check-in` in the
      person's autostart; once a day at login a notification (30 s) says hello, with a
      reminder when a plan note is dated today or tomorrow ("19 November", "November 19th",
      "11月19日"), and "Talk to Kan-chan" opens her window carrying on from it. No AI needed.
      Tested in the VM.
      Desktop buddy done: "Sit on my desktop" adds the `org.kantanos.kanchan` Plasma widget
      (bottom right, above the dock) through a desktop script; she blinks and sways, smiles
      when the mouse is over her, shows her daily hello in a speech bubble for a minute, and
      opens her window when clicked (kstart, so the window is its own app). Unticking removes
      her. Tested in the VM.
- [~] 5. Make your own character: design, personality, voice (character packs already work).
      "Make a character…" in her window (`usr/share/kantanos/kanchan/maker.py`): a name;
      Kan-chan's drawing recoloured (hair, hoodie, eyes, skin tone; live preview) or your own
      picture; a personality (5 manners, short or longer answers, one free line such as
      "loves trains"); one of five Piper voices whose licences allow family use, with "Hear
      it". Saved as the pack `my-character` in the home folder, used by the Helper, her window
      and the desktop buddy; "Back to Kan-chan" switches back. The style goes after her rules
      with a guard (style only; never sides or opinions). Fairness test `--style` option: with a
      deliberately provocative style ("cheeky, has strong opinions about everything") 30/35,
      slips even-handed (both parties explained alike). Tested in the VM (Pochi). Not tested:
      own picture, "Hear it" (no sound in the VM).

- [x] **Kan-chan's new look** (2D, Nov 2026): the owner's own design (pen sketches, finished with
      Gemini into full-size drawings, one per outfit, in `tools/kanchan-art/source/`).
      25 outfits live in `characters/kan-chan/looks/<name>/` and `when.json` picks one (first
      rule that fits): doctor while the Helper is fixing something, pyjamas 22:00-06:00, the
      raincoat when it's raining (Open-Meteo for the Weather widget's town, every 30 min), the
      winter coat in snow, swimwear (the briefs version) on hot weekends (28 °C+); on weekdays
      a suit, blazer or jacket; at weekends a seasonal pick; "choose" means a different outfit
      each day (`/usr/share/kantanos/helper/looks.py`).
      Frames: `tools/kanchan-art/make_pack.py` cuts the drawing out and asks the FLUX.2 picture
      model to change only her face; blink pastes back only the eyes and talking only the mouth,
      so nothing else flickers. 8 frames per outfit, saved as 256-colour PNGs (12 MB in all).
      A designer-style monogram on one bag was painted plain before shipping. Shown in her
      window, the Helper and the desktop buddy. The old drawn SVG frames stay as the fallback
      and for "Make a character".

- [ ] Idea, later: a "Kan-chan model". Fine-tune an open model (LoRA on Gemma/Qwen/Mistral,
      overnight on the RTX 4080) with reviewed example conversations: each side in its own
      terms, same words for every side, facts stated plainly, and how different parts of the
      world see each contested topic. A region setting only picks which local context comes
      first (laws, elections, examples), never which side she leans to. Checked with the
      fairness test (plus a "several parts of the world, each fairly" check) before shipping.

- [x] AI-made shortcuts on the "What would you like to do?" screen: "Add shortcut" → "Tell me
      what it's for" ("watch Netflix", "play Portal", "homework in Google Docs", Japanese too).
      The AI only *chooses* (an installed app, a Steam game, one of ~30 well-known sites, one of
      ~27 family-safe Flathub apps installed on first use, or another site's official https
      address); the command is always built by `shortcut_ai.py`, never written by the AI. A
      second AI check rejects picks that don't really fit (no calculator for "Roblox"), apps keep
      their real name, and the tile is shown (icon, name, "Opens …") before "Add it". Works
      without an AI by matching words; with an online AI it says so first (only the words typed
      and app names are sent). Typing a web address yourself still works.
- [x] Accessibility: **Easier to see and hear** (Welcome → "Make the PC easier to see and
      hear", app menu): Orca screen reader on/off (Meta+Alt+S), size of everything, text size,
      big mouse pointer, magnifier (Meta and +/-), inverted colours. Kan-chan reads and handles
      email through Thunderbird (Flathub `org.mozilla.thunderbird`, so Outlook, Gmail and any
      other account it opens): a KantanOS add-on in Thunderbird talks only to Kan-chan on this
      PC (127.0.0.1, per-person token). "Any new emails?", "read it", "next", "reply saying
      ...", "send an email to Bob saying ...", "bin it". Words are matched without an AI, and
      email text never reaches an AI, so instructions inside an email are only read out. Replies
      go only to the sender; new emails only to someone in the address book or who emailed her;
      every send and bin waits for big Yes/No buttons (or saying yes/no), and an old card can't
      answer a newer question. Calendar reminders from private calendar links (Outlook
      "Publish a calendar" ICS, Google "Secret address in iCal format", any https .ics): "what's
      on today/tomorrow/Friday?", a morning summary, then an hour and 15 minutes before each
      appointment (notification plus her voice, user timer `kantanos-kanchan-remind.timer`).
      Meta+K brings her forward to listen from anywhere, even when minimised. VM-tested with a
      pretend account and mail server (`tools/vm/mail-test/`). Still to try on the real PC: a
      real Outlook account and calendar link.

## Storage, safety and system

- [x] Backups: KantanOS **Backups** app (Welcome → Tools → "Back up your files", app menu
      "Backups"): pick a USB drive, a NAS share, Google Drive or OneDrive; tick folders (sizes
      shown, free-space warning for the cloud); write down a 30-letter backup key. Then restic
      backs up every 30 minutes (user timer `kantanos-backup.timer`), waits quietly while the
      drive is unplugged (a reminder after 3 days), keeps half-hourly versions for a day, then
      daily/weekly/monthly. "Get files back" opens the backups in Files by date, or puts
      everything back on a new PC (type the key). Everything is locked before it leaves the PC.
      Déjà Dup and Pika stay in Welcome → Tools as alternatives. Not tested: Google Drive and
      OneDrive sign-in (needs real accounts).
- [x] Security: strict KantanOS firewall zone (only phone link, game streaming, device
      discovery and file sharing reachable; `ujust kantan-firewall`), ClamAV with "Scan for
      viruses" in Files and Welcome → Tools.
- [ ] Lite edition for small PCs (Azulle Access 3 class). Last in the order of work.

## Working setup

- [x] Claude Code inside KantanOS: "Install Claude Code" in Welcome → Tools, and `CLAUDE.md`
      in this repository as the handoff file for sessions on either PC.
