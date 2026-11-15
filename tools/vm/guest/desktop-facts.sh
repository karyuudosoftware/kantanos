# Runs as the test user in the VM: facts needed for animations, Spotlight-style search and Force Quit.
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
echo "== effects loaded"; busctl --user call org.kde.KWin /Effects org.freedesktop.DBus.Properties Get ss org.kde.kwin.Effects loadedEffects | tr ' ' '\n' | grep -E '"' | tr -d '"' | tr '\n' ' '; echo
echo "== effects available (minimize/maximize/open)"; busctl --user call org.kde.KWin /Effects org.freedesktop.DBus.Properties Get ss org.kde.kwin.Effects listOfEffects | tr ' ' '\n' | grep -i -E 'lamp|squash|minim|maxim|scale|glide|fade|zoom' | tr -d '"' | tr '\n' ' '; echo
echo "== kwinrc plugins"; sed -n '/\[Plugins\]/,/^\[/p' ~/.config/kwinrc /etc/xdg/kwinrc 2>/dev/null
echo "== krunner"; grep -E "^X-KDE-Shortcuts|^Exec" /usr/share/applications/org.kde.krunner.desktop; cat ~/.config/krunnerrc 2>/dev/null
echo "== file search (baloo)"; balooctl6 status 2>&1 | head -3; cat ~/.config/baloofilerc 2>/dev/null | head
echo "== app scopes"; systemctl --user list-units --type=scope --no-legend 'app-*' | head -8
echo "== kill window shortcut"; grep -n -i "kill" ~/.config/kglobalshortcutsrc 2>/dev/null | head -3
