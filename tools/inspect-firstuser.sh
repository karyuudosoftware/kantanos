#!/bin/bash
# Does the image have a first-start "create your account" app for systems with no user?
podman run --rm --entrypoint bash localhost/kantanos:latest -c '
rpm -qa | grep -i -E "plasma-setup|initial-setup|gnome-initial|kiss|plasma-welcome" | sort
systemctl list-unit-files 2>/dev/null | grep -i -E "plasma-setup|initial-setup|kiss"
ls /usr/lib/systemd/system | grep -i -E "setup" | head -20
'
