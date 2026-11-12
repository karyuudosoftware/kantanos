# Collects facts from the running VM over the serial console.
python "$PSScriptRoot\serial.py" --timeout 90 @'
echo "== cmdline"; cat /proc/cmdline;
echo "== desktop files"; ls /usr/share/applications | grep -i -E "discover|bazaar|konsole|ptyxis|firefox|browser|dolphin|systemsettings|steam.desktop|mpv|fcitx"; ls /var/lib/flatpak/exports/share/applications 2>/dev/null | head -30;
echo "== plasmalogin cfg"; sudo -n true 2>/dev/null && echo sudo-ok; ls -la /var/lib/plasmalogin/.config 2>/dev/null | head; find /etc /usr/share /usr/lib -iname "*plasmalogin*" -maxdepth 3 2>/dev/null | head -20;
echo "== who references convergence"; grep -r -l convergence /usr/share/plasma /usr/lib64/qt6/qml/org/kde/plasma/login 2>/dev/null | head; rpm -ql plasma-login-manager | grep -v -E "locale|/doc/" | head -40;
echo "== announcements"; ls /usr/share/ublue-os/announcements 2>/dev/null; ls /etc/xdg/autostart | head -40
'@
