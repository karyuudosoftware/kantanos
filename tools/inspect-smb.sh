#!/bin/bash
# SMB/NAS tools in the image.
podman run --rm --entrypoint bash localhost/kantanos:latest -c '
rpm -q cifs-utils samba-client nss-mdns avahi kio-fuse kio-extras 2>&1
grep -E "^hosts:" /etc/nsswitch.conf /usr/etc/nsswitch.conf 2>/dev/null
command -v smbclient mount.cifs
ls -ld /mnt /var/mnt 2>&1
'
