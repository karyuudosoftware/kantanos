# Runs as the test user in the VM: applies the new animation, search and Force Quit settings
# to the running session without rebuilding the image (mirrors what the image ships).
export XDG_RUNTIME_DIR=/run/user/1000 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
kwriteconfig6 --file kwinrc --group Plugins --key magiclampEnabled true
kwriteconfig6 --file kwinrc --group Plugins --key squashEnabled false
kwriteconfig6 --file kwinrc --group Plugins --key maximizeEnabled true
kwriteconfig6 --file kwinrc --group Plugins --key scaleEnabled true
kwriteconfig6 --file krunnerrc --group General --key FreeFloating true
# Slow animations down 4x for screenshots (reset afterwards)
kwriteconfig6 --file kdeglobals --group KDE --key AnimationDurationFactor 4
busctl --user call org.kde.KWin /KWin org.kde.KWin reconfigure
busctl --user call org.kde.KWin /Effects org.kde.kwin.Effects loadEffect s magiclamp
mkdir -p ~/.local/share/kglobalaccel
cp /tmp/kantanos-force-quit.desktop ~/.local/share/kglobalaccel/
cp /tmp/kantanos-force-quit.desktop ~/.local/share/applications/ 2>/dev/null || { mkdir -p ~/.local/share/applications; cp /tmp/kantanos-force-quit.desktop ~/.local/share/applications/; }
sed 's|^X-KDE-Shortcuts=.*|X-KDE-Shortcuts=Meta+Space,Alt+Space,Alt+F2,Search|' /usr/share/kglobalaccel/org.kde.krunner.desktop > ~/.local/share/kglobalaccel/org.kde.krunner.desktop
systemctl --user restart plasma-kglobalaccel 2>/dev/null || true
echo "loaded: $(busctl --user call org.kde.KWin /Effects org.kde.kwin.Effects isEffectLoaded s magiclamp)"
