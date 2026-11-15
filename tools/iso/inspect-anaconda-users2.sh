#!/bin/bash
# Reads the installer's user and root pages' rules (uses files from inspect-anaconda-users.sh).
P=$(ls -d /root/instx/usr/lib64/python3*/site-packages/pyanaconda | head -1)
echo "== user.py mandatory/completed"; sed -n 450,530p "$P/ui/gui/spokes/user.py"
echo "== root_password.py"; sed -n 140,215p "$P/ui/gui/spokes/root_password.py"
echo "== ui config"; sed -n 30,70p "$P/core/configuration/ui.py"
echo "== hub: which spokes are shown"; grep -rn -E "can_change_root|can_change_users" "$P/ui" | head
