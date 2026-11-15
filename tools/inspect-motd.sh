#!/bin/bash
# Where the terminal welcome banner comes from, and the image label it shows.
podman run --rm --entrypoint bash localhost/kantanos:latest -c '
ls /etc/profile.d | grep -i -E "motd|ublue|bazzite"
ls -d /usr/share/ublue-os/motd* 2>/dev/null; ls /usr/share/ublue-os/motd 2>/dev/null
grep -rl "Welcome to" /usr/share/ublue-os /etc/profile.d /usr/libexec /usr/bin 2>/dev/null | head
echo "== image-info"; jq -c . /usr/share/ublue-os/image-info.json
for f in $(grep -rl "Welcome to" /usr/share/ublue-os /usr/libexec 2>/dev/null | head -3); do echo "== $f"; head -40 "$f"; done
'
