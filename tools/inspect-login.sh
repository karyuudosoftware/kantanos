#!/bin/bash
podman run --rm --entrypoint bash localhost/kantanos:latest -c '
echo "== plasma-login-manager files"; rpm -ql plasma-login-manager | grep -v -E "locale|/doc/|licenses" | head -60
echo "== wallpaper strings in greeter"; for f in $(rpm -ql plasma-login-manager | grep -E "/(bin|libexec)/|\.so$"); do strings "$f" 2>/dev/null | grep -i -E "wallpaper|plasmaloginrc|kscreenlockerrc|\.conf" | sort -u | sed "s|^|$f: |" | head -12; done
echo "== sysconfig"; cat /etc/sysconfig/plasmalogin 2>/dev/null
echo "== defaults.conf"; cat /usr/lib/plasmalogin/defaults.conf 2>/dev/null
echo "== any plasmalogin rc"; find / -xdev \( -name "plasmaloginrc" -o -name "*plasma-login*rc" \) 2>/dev/null
echo "== apps for the dock"; ls /usr/share/applications | grep -i -E "discover|bazaar|konsole|ptyxis|firefox|browser|dolphin|systemsettings|^steam|mpv|kate|kwrite"
echo "== bazzite flatpak list"; ls /usr/share/ublue-os/bazzite/flatpak 2>/dev/null; cat /usr/share/ublue-os/bazzite/flatpak/* 2>/dev/null | head -40
echo "== autostart bits"; cat /etc/xdg/autostart/bazzite-announcement.desktop | grep -E "Exec|Name="; cat /etc/skel/.config/autostart/bazzite-portal.desktop | grep -E "Exec|Name="
echo "== grub font / plymouth"; rpm -q grub2-common; ls /usr/share/plymouth/themes/kantanos | head -30
'
