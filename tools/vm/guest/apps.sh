systemctl is-active kantanos-flatpak-setup.service
journalctl -b --no-pager -o cat -u kantanos-flatpak-setup.service | grep -v -E "^$|%|\.\.\.$" | tail -12
echo "== installed apps"; flatpak list --system --app --columns=application 2>/dev/null
ls /var/lib/kantanos 2>/dev/null
echo "== locale/ime"; locale -a | grep -i -c ja_JP; pgrep -c fcitx5
echo "== ujust"; ujust kantan-version 2>&1 | tail -1
