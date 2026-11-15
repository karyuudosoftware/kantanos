#!/bin/bash
# NTFS / BitLocker support in the image, and how the Welcome app (yafti) runs its scripts.
podman run --rm --entrypoint bash localhost/kantanos:latest -c '
echo "== ntfs"; K=$(ls /usr/lib/modules | head -1); find /usr/lib/modules/$K -name "ntfs*" | head; rpm -q ntfs-3g ntfs-3g-system-compression ntfsprogs 2>&1 | head -3
echo "== bitlocker"; cryptsetup --version; cryptsetup --help 2>/dev/null | grep -i -o bitlk | head -1; rpm -q udisks2 2>&1
echo "== exfat"; find /usr/lib/modules/$K -name "exfat*" | head -2
echo "== iscsi"; rpm -q iscsi-initiator-utils 2>&1
echo "== adjtime"; cat /etc/adjtime 2>&1; ls -la /usr/etc/adjtime 2>&1
echo "== yafti run code"; grep -n -E "subprocess|Popen|run\(|Vte|vte|konsole|terminal|spawn|script" /usr/bin/yafti_gtk.py | head -60
echo "== konsole default profile"; ls /etc/xdg/konsolerc /usr/share/konsole /etc/skel/.config/konsolerc /etc/skel/.local/share/konsole 2>&1; cat /etc/xdg/konsolerc 2>/dev/null; cat /etc/skel/.config/konsolerc 2>/dev/null; grep -rl -i distrobox /usr/share/konsole /etc/skel/.local/share/konsole /etc/xdg 2>/dev/null | head
'
