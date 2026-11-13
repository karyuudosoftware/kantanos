#!/bin/bash
# Looks inside the installer ISO: kickstarts, boot menu, and the installer's own system
# (Anaconda version, product name, artwork, enabled pages).
ISO=$(ls -t /mnt/d/CLAUDE_Projects/kantanos/output/iso/*.iso | head -1)
M=/root/isomnt; R=/root/instroot
umount $R 2>/dev/null; umount $M 2>/dev/null; mkdir -p $M $R
mount -o loop,ro "$ISO" $M || exit 1
echo "== ISO tree"; (cd $M && find . -maxdepth 2 -not -path './container/*' | sort | head -60)
echo "== volume id"; blkid -o value -s LABEL "$ISO"
for f in $M/*.ks; do echo "== $f"; cat "$f"; done
echo "== grub.cfg"; cat $M/EFI/BOOT/grub.cfg 2>/dev/null | head -50
echo "== .discinfo / .treeinfo"; cat $M/.discinfo 2>/dev/null; cat $M/.treeinfo 2>/dev/null | head -30
echo "== install.img"; ls -la $M/images/; file -L $M/images/install.img
mount -o loop,ro $M/images/install.img $R 2>&1 || echo "mount failed"
ls $R | head -30
if [ -f $R/LiveOS/rootfs.img ]; then mkdir -p /root/instroot2; mount -o loop,ro $R/LiveOS/rootfs.img /root/instroot2; R=/root/instroot2; fi
echo "== installer os-release"; cat $R/etc/os-release 2>/dev/null | head -12
echo "== buildstamp"; cat $R/.buildstamp 2>/dev/null
echo "== anaconda"; ls $R/usr/lib/python3*/site-packages/ | grep -i -E "pyanaconda|anaconda" ; ls $R/usr/share/anaconda/ 2>/dev/null
ls $R/usr/share/cockpit 2>/dev/null | head; ls $R/usr/libexec/anaconda 2>/dev/null | head -20
echo "== conf"; ls $R/etc/anaconda/ $R/etc/anaconda/conf.d $R/etc/anaconda/profile.d $R/etc/anaconda/product.d 2>/dev/null
cat $R/etc/anaconda/conf.d/*.conf 2>/dev/null
echo "== pixmaps"; ls -la $R/usr/share/anaconda/pixmaps/ 2>/dev/null; ls -la $R/usr/share/pixmaps 2>/dev/null | head -20
echo "== product.img support"; grep -rn "product.img" $R/usr/lib/dracut 2>/dev/null | head; grep -rln "product.img\|updates.img" $R/usr/lib/python3*/site-packages/pyanaconda 2>/dev/null | head; ls $R/usr/lib/dracut/modules.d 2>/dev/null | grep -i anaconda
umount /root/instroot2 2>/dev/null; umount /root/instroot 2>/dev/null; umount $M
