#!/bin/bash
# Renders the branding SVGs into the image assets under system_files/.
# Run inside the Fedora build environment (needs rsvg-convert, Inter and Noto Sans CJK JP).
# tools/looks.py must have run first: it writes branding/default/ and branding/looks/.
set -euo pipefail
cd "$(dirname "$0")/.."
B=branding/default          # base artwork in the default look's colours
S=system_files/usr/share
DEFAULT_LOOK=$(cat "$S/kantanos/looks/default")

# Boot splash watermark (stacked logo on dark; the splash and installer stay dark in every look)
rsvg-convert -w 560 "$B/kantanos-logo-stacked-on-dark.svg" -o "$S/plymouth/themes/kantanos/watermark.png"

# App / launcher icon in the standard sizes
for s in 16 22 24 32 48 64 128 256 512; do
  d="$S/icons/hicolor/${s}x${s}/apps"
  mkdir -p "$d"
  rsvg-convert -w "$s" -h "$s" "$B/kantanos-icon.svg" -o "$d/kantanos.png"
done

# Logos for About pages and the installer
mkdir -p "$S/kantanos/logos"
rsvg-convert -w 940 "$B/kantanos-logo-horizontal-on-dark.svg"  -o "$S/kantanos/logos/horizontal-on-dark.png"
rsvg-convert -w 940 "$B/kantanos-logo-horizontal-on-light.svg" -o "$S/kantanos/logos/horizontal-on-light.png"
rsvg-convert -w 720 "$B/kantanos-logo-stacked-on-dark.svg"     -o "$S/kantanos/logos/stacked-on-dark.png"
rsvg-convert -w 720 "$B/kantanos-logo-stacked-on-light.svg"    -o "$S/kantanos/logos/stacked-on-light.png"

# One wallpaper and one logo per look
for dir in branding/looks/*/; do
  id=$(basename "$dir")
  out="$S/kantanos/looks/$id"
  mkdir -p "$out"
  rsvg-convert -w 2560 -h 1440 "$dir/wallpaper.svg" -o "$out/wallpaper.png"
  rsvg-convert -w 720 "$dir/logo.svg" -o "$out/logo.png"
done

# The default look's wallpaper is also the system wallpaper (new users, login and lock screen)
rsvg-convert -w 3840 -h 2160 "branding/looks/$DEFAULT_LOOK/wallpaper.svg" -o "$S/wallpapers/KantanOS/contents/images/3840x2160.png"

du -sh "$S/kantanos/looks" "$S/wallpapers/KantanOS"
