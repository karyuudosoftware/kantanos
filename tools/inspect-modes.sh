#!/bin/bash
# What does the image already have for a mode chooser: UI runtimes, sessions, game/TV pieces.
podman run --rm --entrypoint bash localhost/kantanos:latest -c '
echo "== sessions"; ls /usr/share/wayland-sessions /usr/share/xsessions 2>/dev/null
echo "== qml runtimes"; ls /usr/bin | grep -i -E "^qml|qmlscene|^qt6|kdialog|plasmawindowed|kioclient|kstart" | tr "\n" " "; ls /usr/lib64/qt6/bin 2>/dev/null | tr "\n" " "
echo; echo "== python ui"; python3 -c "import gi; gi.require_version(\"Gtk\",\"4.0\"); from gi.repository import Gtk; print(\"gtk4 ok\")" 2>&1 | tail -1; python3 -c "import PySide6; print(\"pyside6 ok\")" 2>&1 | tail -1; python3 -c "import PyQt6; print(\"pyqt6 ok\")" 2>&1 | tail -1
echo "== qml modules"; ls /usr/lib64/qt6/qml | tr "\n" " "; echo; ls /usr/lib64/qt6/qml/org/kde | tr "\n" " "
echo; echo "== game bits"; command -v steam gamescope gamescope-session-plus bazzite-steam mangohud lutris 2>&1; rpm -q steam gamescope 2>&1 | head -3
grep -l -i -E "gamepadui|bigpicture" /usr/share/applications/*.desktop 2>/dev/null | head; grep -h "^Exec" /usr/share/applications/steam.desktop | head -3
echo "== just recipes (emulation/tv)"; just --justfile /usr/share/ublue-os/justfile --list 2>/dev/null | grep -i -E "emu|retro|kodi|decky|steam|game" | head -20
echo "== plasma login manager"; rpm -qa | grep -i -E "plasma-login|sddm" ; ls /usr/lib/plasmalogin 2>/dev/null; grep -v "^#" /usr/lib/plasmalogin/defaults.conf 2>/dev/null | grep -v "^$" | head -40
echo "== autologin tools"; just --justfile /usr/share/ublue-os/justfile --list 2>/dev/null | grep -i -E "login|session" | head
'
