# Runs as root in the test VM (via serial.py --root-script, so SUDO_USER is the test user):
# exercises nas-connect with a stand-in smbclient that "lists" three shares, then checks
# the mount units, the credentials file and the Files sidebar entries, then removes it all.
mkdir -p /tmp/stub
cat > /tmp/stub/smbclient <<'EOF'
#!/bin/bash
printf 'Disk|media|\nDisk|storage|\nDisk|FTP Uploads|\nIPC|IPC$|IPC Service\nDisk|admin$|\n'
EOF
chmod +x /tmp/stub/smbclient
install -m 0755 /tmp/nas-connect /tmp/nas-connect-run
export SUDO_USER=kantan
printf 'localhost\nnasuser\nsecret-test-pw\n\n' | PATH=/tmp/stub:$PATH /tmp/nas-connect-run 2>&1 | tail -6
echo "== units"; ls /etc/systemd/system | grep -E 'nas.*\.(mount|automount)$'
echo "== verify"; for u in /etc/systemd/system/*nas*.mount; do systemd-analyze verify "$u" 2>&1 | grep -v -i "is not executable\|Unknown key" | head -3; done; echo "(no lines above = valid)"
echo "== a unit"; cat "/etc/systemd/system/var-mnt-nas-FTP\\x20Uploads.mount" | sed -n '1,14p'
echo "== automounts"; systemctl is-enabled 'var-mnt-nas-media.automount' "var-mnt-nas-FTP\\x20Uploads.automount"; systemctl is-active 'var-mnt-nas-media.automount'
echo "== credentials"; stat -c '%a %U %n' /etc/kantanos/nas/localhost.cred
echo "== sidebar"; grep -c 'var/mnt/nas' /var/home/kantan/.local/share/user-places.xbel
echo "== list"; /tmp/nas-connect-run list
echo "== remove"; /tmp/nas-connect-run remove; ls /etc/systemd/system | grep -c nas
