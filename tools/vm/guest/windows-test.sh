# Runs as the test user in the VM: sets up the Windows space, installs Notepad++ the way the
# Welcome app does, and checks C:, the menu shortcut and the Files sidebar entry.
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus WAYLAND_DISPLAY=wayland-0 DISPLAY=:0
start=$(date +%s)
kantan-windows setup 2>&1 | tail -2
echo "setup took $(( $(date +%s) - start )) s"
P=~/.wine
echo "== C: drive"; ls "$P/drive_c"
echo "== Windows version"; grep -m1 -i '"ProductName"' "$P/system.reg"
echo "== Japanese font mapping"; grep -c 'Noto Sans CJK JP' "$P/user.reg"
echo "== sidebar"; grep -c 'drive_c' ~/.local/share/user-places.xbel
echo "== Notepad++"
start=$(date +%s)
kantan-windows install-notepadpp </dev/null 2>&1 | grep -v -E '^\s*#|%' | tail -4
echo "install took $(( $(date +%s) - start )) s"
echo "== menu shortcut"; find ~/.local/share/applications/wine -name '*.desktop' 2>/dev/null | head -5
echo "== file association"; xdg-mime query default application/x-msi; xdg-mime query default application/x-ms-dos-executable
