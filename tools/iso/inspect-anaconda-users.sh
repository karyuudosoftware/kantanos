#!/bin/bash
# How the installer (Anaconda) decides whether the user page is required, and what names it refuses.
X=/root/instx
ISO=$(ls -t /mnt/d/CLAUDE_Projects/kantanos/output/iso/*.iso | head -1)
M=/root/isomnt; umount $M 2>/dev/null; mkdir -p $M; mount -o loop,ro "$ISO" $M || exit 1
rm -rf $X; unsquashfs -q -n -d $X $M/images/install.img 'usr/lib64/python3*' 2>/dev/null | tail -1
umount $M
P=$(ls -d $X/usr/lib64/python3*/site-packages/pyanaconda | head -1)
echo "pyanaconda: $P"
echo "== root/user requirement"
grep -rn -E "def (completed|mandatory|status)|root_password_is_set|is_root_password_set|can_change_root|check_user_creation|admin_user|can_login|lock" "$P/ui/gui/spokes/user.py" "$P/ui/gui/spokes/root_password.py" 2>/dev/null | head -40
echo "== reserved names"
grep -rn -E "reserved|\"root\"|'root'" "$P/core/users.py" "$P/core/regexes.py" 2>/dev/null | head -12
echo "== conf options"
grep -rn -E "can_change_root|can_change_users|root_account|user_creation" "$P/core/configuration" 2>/dev/null | head -12
