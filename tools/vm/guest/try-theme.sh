# Applies the theme files pushed to /tmp/KantanGlass.b64 (tar.gz, base64) for the logged-in test user.
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export XDG_RUNTIME_DIR=/run/user/1000 QT_QPA_PLATFORM=offscreen
D=~/.local/share/plasma/desktoptheme
mkdir -p $D && rm -rf $D/KantanGlass
base64 -d /tmp/KantanGlass.b64 | tar xz -C $D
find $D/KantanGlass -type f | wc -l
plasma-apply-desktoptheme KantanGlass 2>&1 | tail -1
# Plasma caches rendered theme pieces per theme version; clear them so edits show up.
rm -f ~/.cache/plasma_theme_* ~/.cache/plasma-svgelements* 2>/dev/null
systemctl --user restart plasma-plasmashell.service
sleep 6
systemctl --user is-active plasma-plasmashell.service
