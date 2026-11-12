#!/bin/bash
# Renders the branding SVGs into the image assets under system_files/.
# Run inside the Fedora build environment (needs rsvg-convert, Inter and Noto Sans CJK JP).
set -euo pipefail
cd "$(dirname "$0")/.."
B=branding
S=system_files/usr/share

# Boot splash watermark (stacked logo on dark)
rsvg-convert -w 560 "$B/kantanos-logo-stacked-on-dark.svg" -o "$S/plymouth/themes/kantanos/watermark.png"

# Wallpaper
rsvg-convert -w 3840 -h 2160 "$B/kantanos-wallpaper.svg" -o "$S/wallpapers/KantanOS/contents/images/3840x2160.png"

# App / launcher icon in the standard sizes
for s in 16 22 24 32 48 64 128 256 512; do
  d="$S/icons/hicolor/${s}x${s}/apps"
  mkdir -p "$d"
  rsvg-convert -w "$s" -h "$s" "$B/kantanos-icon.svg" -o "$d/kantanos.png"
done

# Logos for About pages, the installer and the login screen
mkdir -p "$S/kantanos/logos"
rsvg-convert -w 940 "$B/kantanos-logo-horizontal-on-dark.svg"  -o "$S/kantanos/logos/horizontal-on-dark.png"
rsvg-convert -w 940 "$B/kantanos-logo-horizontal-on-light.svg" -o "$S/kantanos/logos/horizontal-on-light.png"
rsvg-convert -w 720 "$B/kantanos-logo-stacked-on-dark.svg"     -o "$S/kantanos/logos/stacked-on-dark.png"
rsvg-convert -w 720 "$B/kantanos-logo-stacked-on-light.svg"    -o "$S/kantanos/logos/stacked-on-light.png"
ls -la "$S/plymouth/themes/kantanos" "$S/wallpapers/KantanOS/contents/images" "$S/kantanos/logos"
