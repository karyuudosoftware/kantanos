# Runs as the test user in the VM: installs Notepad++ through the desktop session (the same
# security context as clicking it in the Welcome app), then reports the result.
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
rm -f /tmp/npp-run.log
systemd-run --user --collect --wait --unit npp-install -p StandardOutput=file:/tmp/npp-run.log -p StandardError=file:/tmp/npp-run.log \
    -E DISPLAY=:0 -E WAYLAND_DISPLAY=wayland-1 kantan-windows install-notepadpp >/dev/null 2>&1
grep -v -E 'fixme|^\s*#|%$' /tmp/npp-run.log | tail -4
echo "== context of a desktop process"; ps -eZ | grep -m1 plasmashell | cut -c1-60
echo "== menu shortcut"; find ~/.local/share/applications/wine -name '*.desktop' 2>/dev/null | head -5
find ~/.wine/drive_c -iname 'notepad++.exe'
