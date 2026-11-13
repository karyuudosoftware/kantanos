#!/bin/bash
# Shows the installer's artwork hooks (uses the files extracted by inspect-installer2.sh).
cd /root/instx || exit 1
echo "== fedora.css"; cat usr/share/anaconda/pixmaps/fedora.css
echo "== anaconda-gtk.css 85-125"; sed -n 85,125p usr/share/anaconda/anaconda-gtk.css
echo "== fedora.conf"; cat etc/anaconda/profile.d/fedora.conf
echo "== sizes"; file usr/share/anaconda/pixmaps/*.png
mkdir -p /mnt/d/CLAUDE_Projects/kantanos/output/anaconda-ref
cp usr/share/anaconda/pixmaps/*.png usr/share/anaconda/pixmaps/fedora.css usr/share/anaconda/anaconda-gtk.css /mnt/d/CLAUDE_Projects/kantanos/output/anaconda-ref/
