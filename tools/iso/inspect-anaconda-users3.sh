#!/bin/bash
# Whether a kickstart "rootpw --lock" stops the root page from being used instead of a user.
X=/root/instx
P=$(ls -d $X/usr/lib64/python3*/site-packages/pyanaconda | head -1)
sed -n 30,75p "$P/ui/lib/users.py"
ISO=$(ls -t /mnt/d/CLAUDE_Projects/kantanos/output/iso/*.iso | head -1)
M=/root/isomnt; mount -o loop,ro "$ISO" $M 2>/dev/null
unsquashfs -q -n -f -d $X $M/images/install.img etc/anaconda 2>/dev/null; umount $M
echo "== can_change_root / users settings"; grep -rn -E "can_change_root|can_change_users|hidden_spokes" $X/etc/anaconda/ | head
echo "== how the hub treats the user/root pair"; grep -rn -B2 -A12 "def _check_user_and_root\|CheckAdminUserExists\|users_spokes\|either" "$P/ui/gui/hubs/summary.py" "$P/ui/gui/hubs/__init__.py" 2>/dev/null | head -40
