# KantanOS (簡単)

A family desktop OS built on [Universal Blue / Bazzite](https://bazzite.gg) (Fedora atomic, KDE Plasma).
Built with Claude.

## Layout

| Path | What it is |
|---|---|
| `Containerfile` | The image definition. Base: `bazzite-nvidia-open:stable` |
| `build_files/build.sh` | Runs inside the base image: packages, identity, desktop defaults, boot splash |
| `system_files/` | Copied onto `/` in the image (theme, layout, wallpaper, icons, welcome app, services) |
| `branding/` | Logo, icon and wallpaper sources (SVG) |
| `tools/` | Build, check, ISO and VM scripts |
| `output/` | Generated: test disks, ISO, screenshots (not in git) |

## Build and test

Everything is driven from Windows PowerShell. Builds run inside the `kantan-build` WSL distro;
test VMs run in QEMU for Windows with hypervisor acceleration.

```powershell
powershell -ExecutionPolicy Bypass -File tools\vm\cycle.ps1
```

That one command rebuilds the image, runs the static checks, makes a test disk, boots it and
leaves it at the login screen. Then:

```powershell
powershell -ExecutionPolicy Bypass -File tools\vm\login.ps1 mydesktop 30   # log in + screenshot
python tools\vm\qmp.py click 960 540                                       # click in the VM
python tools\vm\serial.py --script tools\vm\guest\facts.sh                 # run a script in the VM
```

Screenshots land in `output\shots\`. The test disk has a throwaway account from
`tools/vm/config.toml`; never use that file for a real machine.

Installer ISO (15-25 minutes), written to `output\iso\`:

```powershell
wsl -d kantan-build -u root -- bash /mnt/d/CLAUDE_Projects/kantanos/tools/iso/make-iso.sh
```

## Updates

Installed PCs check their update address once a day (the base's `uupd.timer`, 4 am or at the
next start), download only what changed, and switch to the new version at the next restart.
Starter apps (Flatpaks) update in the same run. By hand: `ujust kantan-update`; to go back to
the version before the last update: `ujust kantan-undo-update`.

- `tools/registry.conf` holds the update address (`ghcr.io/<github-name>/kantanos`). It is
  built into the image, and the ISO installs PCs that follow it. Empty = no updates.
- `signing/cosign.key` is the private signing key (not in git; **back it up**). Its public
  half is in every image, and PCs refuse images from the update address that are not signed
  with it. `tools/signing/make-key.sh` created the pair.
- `tools/publish.sh` signs and pushes the built image by hand.
- `.github/workflows/build.yml` does build + sign + publish on GitHub every day and on each
  push to `main`. It needs the repository secret `SIGNING_SECRET` (contents of
  `signing/cosign.key`) and the published package set to public. Not run yet.
- The number in `VERSION` is the KantanOS version; each build also gets a date stamp.

`tools/update-test/` proves the whole path in the VM against a throwaway local registry:
`publish-build.sh 0.1.0 disk`, boot, `guest-prepare.sh`, `publish-build.sh 0.1.1 unsigned`
(must be refused), `sign-current.sh`, `guest-upgrade.sh`, `restart-vm.ps1`, `cleanup.sh`.
Tested 2026-11-12: unsigned refused, signed 0.1.0 → 0.1.1 (385 MB download), undo back to
0.1.0, and the automatic service staged 0.1.1 again.

## What is in the image

- KantanOS identity: name, logo, boot splash, login and lock wallpaper, hostname
- Glass desktop: floating pill dock, slim top bar, Kantan Glass panel theme, indigo colours, Inter font
- Japanese input (fcitx5 + Mozc) and Japanese locale
- Starter apps installed on first boot: Firefox, Gwenview, Okular, KCalc, VLC
- KantanOS Welcome: one-click installs for office, creative, media and chat apps; HDR and 7.1 helpers
- Explorer-style file manager ("Files", which is Dolphin configured, not a new program):
  two-row toolbar (Back/Forward/Up/Refresh + address bar; New/Cut/Copy/Paste/Rename/Delete/
  Sort/View), "Home > Documents" address bar, coloured folders in a details list, sidebar with
  Home, Desktop, Downloads, Documents, Pictures, Music, Videos, Programs, Trash.
  Sources: `tools/make-file-manager.py` (toolbar, from `tools/dolphin/dolphinui-upstream.rc`),
  `system_files/etc/xdg/dolphinrc`, `kwinrulesrc` (opening size), `/etc/skel/.local/state/dolphinstaterc`
  (sidebar width), `/usr/libexec/kantanos/files-setup` (sidebar, once per user).
  Try changes live with `tools/vm/push-files.py`. Not done: a `C:\` view (planned to be the
  Windows-apps drive once Wine is set up), the window title still says "Dolphin".
- Mode chooser (`/usr/libexec/kantanos/modes`, Python + QML): a full-screen "What would you
  like to do?" overlay after login and from the Modes dock icon. Tiles are `*.mode` files in
  `/usr/share/kantanos/modes` (Desktop, Game Mode = Steam Big Picture, Retro Games = RetroDECK
  installed on first use; Watch TV is hidden until the custom TV app exists; no Kodi) plus the
  user's own web shortcuts in `~/.config/kantanos/modes`. Arrow keys, Enter, Esc, or mouse.
- Looks: seven colour styles from one table in `tools/looks.py` (Light is the default; Sakura,
  Graphite, Ocean, Forest, Ember, Aurora). Each has a wallpaper, colour scheme, logo tint and
  tile icons under `/usr/share/kantanos/looks/<id>`. Switch from the swatches in the mode
  chooser, the Look tab in Welcome, or `kantan-look set <id>`. Boot splash, installer and
  login screen always use the default look's colours.
- Full codecs from the base (H.264, HEVC, AV1, AC-3, E-AC-3, DTS, TrueHD) and mpv
- `ujust kantan-hdr-on`, `ujust kantan-hdr-off`, `ujust kantan-audio-71`, `ujust kantan-version`

## Not done yet

- Updates are live (first GitHub build 2026-11-12; a test VM updated itself from
  `ghcr.io/karyuudosoftware/kantanos`). `tools/check-published.sh` re-checks access and signature;
  `tools/ci-wait.sh` waits for the newest GitHub build. Old dated tags are never cleaned up yet.
- Installer: KantanOS logo and colours, plus language, keyboard and time zone pages, come from
  `tools/iso/make-iso-config.sh` (the artwork rides in the kickstart's `%pre`). Still stock:
  the title says "KantanOS 45" (the Fedora release number), and the time zone page needs one visit.
- Nothing has been tested on real hardware (NVIDIA, HDR, 7.1 audio).
