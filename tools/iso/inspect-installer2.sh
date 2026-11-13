#!/bin/bash
# Extracts the interesting parts of the installer system (install.img) for inspection.
command -v unsquashfs >/dev/null || dnf -y -q install squashfs-tools >/dev/null 2>&1
ISO=$(ls -t /mnt/d/CLAUDE_Projects/kantanos/output/iso/*.iso | head -1)
M=/root/isomnt; X=/root/instx
umount $M 2>/dev/null; mkdir -p $M; rm -rf $X
mount -o loop,ro "$ISO" $M || exit 1
echo "== top level"; unsquashfs -l -d '' $M/images/install.img 2>/dev/null | awk -F/ 'NF<=2' | head -30
unsquashfs -q -n -d $X $M/images/install.img \
    etc/os-release usr/lib/os-release .buildstamp etc/anaconda usr/share/anaconda/pixmaps usr/share/anaconda/boot \
    usr/share/pixmaps usr/lib/dracut/modules.d/80anaconda usr/share/anaconda/gnome usr/share/anaconda/interactive-defaults.ks \
    usr/share/anaconda/anaconda-gtk.css usr/share/anaconda/window-manager 2>&1 | tail -3
umount $M
cd $X
echo "== os-release"; cat usr/lib/os-release 2>/dev/null | head -14
echo "== buildstamp"; cat .buildstamp
echo "== etc/anaconda"; find etc/anaconda -type f | sort;
echo "== anaconda.conf (non-comment)"; grep -v -E "^\s*#|^\s*$" etc/anaconda/anaconda.conf | head -80
echo "== conf.d"; for f in etc/anaconda/conf.d/*; do echo "-- $f"; cat "$f"; done
echo "== profiles"; ls etc/anaconda/profile.d | tr '\n' ' '
echo; echo "== pixmaps"; ls -la usr/share/anaconda/pixmaps usr/share/pixmaps 2>/dev/null | head -50
echo "== interactive defaults"; cat usr/share/anaconda/interactive-defaults.ks 2>/dev/null
echo "== product.img in dracut"; grep -rn "product.img\|updates.img" usr/lib/dracut 2>/dev/null | head
echo "== css"; grep -n -i "logo\|sidebar" usr/share/anaconda/anaconda-gtk.css | head -20
