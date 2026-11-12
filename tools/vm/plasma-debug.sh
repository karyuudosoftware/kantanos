#!/bin/bash
HERE="$(cd "$(dirname "$0")" && pwd)"
python3 "$HERE/serial.py" --timeout 240 '
echo "== appletsrc"; ls -la ~/.config/plasma-org.kde.plasma.desktop-appletsrc ~/.config/plasmashellrc 2>&1; grep -c "^\[Containments\]\[[0-9]*\]$" ~/.config/plasma-org.kde.plasma.desktop-appletsrc 2>/dev/null; grep -E "^plugin=|^location=|^Image=" ~/.config/plasma-org.kde.plasma.desktop-appletsrc 2>/dev/null | sort | uniq -c;
echo "== kdedefaults"; ls ~/.config/kdedefaults 2>&1; cat ~/.config/kdedefaults/package 2>/dev/null; grep -E "ColorScheme|LookAndFeel" ~/.config/kdedefaults/kdeglobals ~/.config/kdeglobals 2>/dev/null;
echo "== plasmashell cpu"; ps -o pid,etimes,time,pcpu,rss,comm -C plasmashell;
echo "== plasmashell log"; journalctl -b --user --no-pager -o cat _COMM=plasmashell 2>/dev/null | grep -v -E "^$|qt.qpa|kf.svg" | tail -40'
