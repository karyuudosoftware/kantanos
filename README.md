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
- Explorer-style file manager defaults (details view, sidebar)
- Full codecs from the base (H.264, HEVC, AV1, AC-3, E-AC-3, DTS, TrueHD) and mpv
- `ujust kantan-hdr-on`, `ujust kantan-hdr-off`, `ujust kantan-audio-71`, `ujust kantan-version`

## Not done yet

- Updates work in the test VM but nothing is published: `tools/registry.conf` is empty, the
  project is not on GitHub, and the ISO in `output/iso` predates the update address (rebuild it).
- Installer still shows Fedora artwork and has no language, keyboard or time zone pages.
- Nothing has been tested on real hardware (NVIDIA, HDR, 7.1 audio).
