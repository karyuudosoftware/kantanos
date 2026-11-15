#!/bin/bash
# Firewall, KDE Connect and Wake-on-LAN facts in the image.
podman run --rm --entrypoint bash localhost/kantanos:latest -c '
echo "== firewalld"; rpm -q firewalld; grep -E "^DefaultZone" /etc/firewalld/firewalld.conf /usr/lib/firewalld/firewalld.conf 2>/dev/null
Z=$(sed -n "s/^DefaultZone=//p" /etc/firewalld/firewalld.conf 2>/dev/null); Z=${Z:-FedoraWorkstation}
echo "zone $Z:"; cat /etc/firewalld/zones/$Z.xml 2>/dev/null || cat /usr/lib/firewalld/zones/$Z.xml
ls /usr/lib/firewalld/services | grep -i -E "kde|connect"
echo "== kdeconnect"; rpm -qa | grep -i kdeconnect; ls /usr/share/applications | grep -i kdeconnect
echo "== NetworkManager conf"; ls /etc/NetworkManager/conf.d /usr/lib/NetworkManager/conf.d 2>/dev/null
echo "== ethtool"; command -v ethtool
'
