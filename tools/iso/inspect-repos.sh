#!/bin/bash
podman run --rm --entrypoint bash localhost/kantanos:latest -c '
echo "== repo files"; ls /etc/yum.repos.d
echo "== enabled flags"; grep -H -E "^\[|^enabled=" /etc/yum.repos.d/fedora*.repo 2>/dev/null | paste - - | head -20
echo "== repolist"; dnf5 repolist 2>&1 | head -20
echo "== bootc/grub pkgs"; rpm -q bootc grub2-efi-x64 shim-x64 2>&1
'
tail -5 /root/iso.log 2>/dev/null | cut -c1-200
