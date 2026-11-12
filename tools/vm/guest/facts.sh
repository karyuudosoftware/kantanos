export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
echo "== plymouth this boot"
journalctl -b --no-pager -o cat -u plymouth-start.service -u plymouth-quit.service 2>/dev/null | tail -5
journalctl -b --no-pager -o short-monotonic | grep -i plymouth | head -12
plymouth-set-default-theme
echo "== cmdline"; cat /proc/cmdline
echo "== panel opacity"; grep -n -i -E "opacity|floating|PlasmaViews" ~/.config/plasmashellrc
echo "== flatpaks"; flatpak list --app --columns=application 2>/dev/null | head -20
systemctl status bazzite-flatpak-manager.service --no-pager 2>/dev/null | head -6
echo "== plasma theme panel svg"; ls -la /usr/share/plasma/desktoptheme/default/widgets/panel-background.svgz /usr/share/plasma/desktoptheme/default/translucent/widgets/panel-background.svgz /usr/share/plasma/desktoptheme/default/opaque/widgets/panel-background.svgz 2>&1
ls /usr/share/plasma/desktoptheme/
echo "== kwin compositing"; qdbus6 org.kde.KWin /KWin supportInformation 2>/dev/null | grep -i -E "^OpenGL renderer|compositing type|blur|GL version" | head -8
echo "== fcitx"; pgrep -a fcitx5 | head -3; cat ~/.config/fcitx5/profile 2>/dev/null | head -12
