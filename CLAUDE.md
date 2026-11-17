# KantanOS: notes for Claude Code

This file is the handoff between Claude Code sessions, whether they run on the Windows build
PC or on KantanOS itself. Claude Code reads it at the start of every session in this folder.
Keep it short and current.

## What this is

KantanOS (簡単, "easy") is a family desktop OS: a bootc/ostree image built on Bazzite
(Fedora atomic, KDE Plasma 6), published signed to `ghcr.io/karyuudosoftware/kantanos` by
GitHub Actions on every push to `main`. Installed PCs update themselves daily (uupd) and can
roll back (`ujust kantan-undo-update`). `README.md` explains the layout and the build;
`ROADMAP.md` is the to-do list: done, next and ideas.

The owner is moving their main PC from Windows 11 to KantanOS (Ryzen 9 3900X, RTX 4080,
Sony TV through an Onkyo AV receiver). Family members of all ages use it: plain words in
everything a person sees, no jargon.

## Where things are

- `build_files/build.sh`: packages and changes made inside the image
- `system_files/`: copied onto `/` (KantanOS programs are in `usr/libexec/kantanos/`,
  `usr/bin/kantan-*`; helper commands in `usr/share/ublue-os/just/60-custom.just`)
- `tools/make-welcome.py`: generates the KantanOS Welcome app (`yafti.yml`) at build time
- `tools/verify-image.sh`: static checks on the built image. The whole check list sits inside
  one single-quoted string: **never use single quotes in a check**
- `tools/vm/`: test VM scripts (Windows build PC only: QEMU + WHPX, `cycle.ps1`, `qmp.py`)

## Working on KantanOS itself

You can't rebuild the image on KantanOS the way the Windows PC does, but you can:
- read and change this repository, then commit and push (GitHub builds the image);
- try a change to one file live, e.g. copy a script to `~/.local/bin` or a Plasma widget to
  `~/.local/share/plasma/plasmoids/`, before committing it;
- look at the running system: `journalctl`, `systemctl --user`, `ujust kantan-display-info`,
  `rpm-ostree status` / `bootc status`.
`/usr` is read-only on the running system; `/etc` and `/var` are writable.

## Rules

- Ask before anything hard to undo, and before sending anything from this PC to an outside
  service. Never put personal details (names, the home network, NAS addresses, e-mail) in
  this public repository.
- Secrets never go in git: `signing/cosign.key`, `output/usb/LOGIN.txt`, API keys.
- Windows, ROMs and other copyrighted material are never shipped or downloaded by KantanOS;
  the user brings their own. No anti-cheat evasion.
- The KantanOS Helper's AI may only pick repairs from its fixed list (`FIXES` in
  `usr/libexec/kantanos/helper`); keep it that way.
- Credit is a plain-text "Built with Claude".
