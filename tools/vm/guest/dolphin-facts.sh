# Runs in the test VM as the test user: dumps the file manager's current configuration.
echo "== dolphin version"; rpm -q dolphin kf6-kio
echo "== ui rc files"; find / -xdev -name "dolphinui.rc" 2>/dev/null; ls ~/.local/share/kxmlgui5/dolphin 2>/dev/null
echo "== user-places.xbel"; cat ~/.local/share/user-places.xbel 2>/dev/null || echo "(none yet)"
echo "== dolphinrc (user)"; cat ~/.config/dolphinrc 2>/dev/null
echo "== dolphinrc (system)"; cat /etc/xdg/dolphinrc
echo "== home"; ls -la ~ | head -30; echo; xdg-user-dir DOCUMENTS; readlink -f ~
echo "== kio protocols"; ls /usr/lib64/qt6/plugins/kf6/kio/ | tr '\n' ' '
echo; echo "== folder icons"; ls /usr/share/icons/breeze-dark/places/32/ | grep -E "^folder-(yellow|blue|windows)|^drive|^computer|^user-home" | tr '\n' ' '; ls /usr/share/icons/breeze-dark/devices/32/ | grep -E "drive|computer" | tr '\n' ' '
echo; echo "== servicemenus / templates"; ls /usr/share/templates 2>/dev/null | head; ls /usr/share/kio/servicemenus 2>/dev/null | head -20
