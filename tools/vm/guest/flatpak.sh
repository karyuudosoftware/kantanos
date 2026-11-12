echo "== manager log"; journalctl -b --no-pager -o cat -u bazzite-flatpak-manager.service | tail -25
echo "== manager script"; sed -n '1,80p' /usr/libexec/bazzite-flatpak-manager
echo "== remotes"; flatpak remotes --columns=name,url 2>&1
echo "== state"; ls -la /etc/bazzite 2>/dev/null; cat /etc/bazzite/flatpak_manager_version 2>/dev/null
echo "== net"; curl -s -m 8 -o /dev/null -w "flathub http %{http_code}\n" https://dl.flathub.org/repo/summary.idx
