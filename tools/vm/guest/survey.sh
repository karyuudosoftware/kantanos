echo "== yafti files"; rpm -qf /usr/bin/yafti_gtk.py 2>/dev/null; ls -la /usr/share/yafti/ /usr/bin/yafti* 2>/dev/null
echo "== yafti.yml (first 120 lines)"; sed -n '1,120p' /usr/share/yafti/yafti.yml
echo "== yml line count"; wc -l /usr/share/yafti/yafti.yml
echo "== portal desktop"; cat /usr/share/applications/*portal*.desktop 2>/dev/null | head -20; ls /usr/share/applications | grep -i -E "portal|yafti"
echo "== firewall"; systemctl is-active firewalld; firewall-cmd --get-default-zone 2>/dev/null
echo "== snapper"; systemctl is-enabled snapper-timeline.timer snapper-cleanup.timer 2>&1 | tr "\n" " "; ls /etc/snapper/configs 2>/dev/null; findmnt -n -o FSTYPE /var/home
echo "== selinux"; getenforce
echo "== dolphinrc"; cat /etc/xdg/dolphinrc 2>/dev/null | head -20
