#!/bin/bash
# Prints the key settings in the newest installer ISO's kickstart.
ISO=$(ls -t /mnt/d/CLAUDE_Projects/kantanos/output/iso/*.iso | head -1)
M=/root/isomnt; mkdir -p $M; umount $M 2>/dev/null
mount -o loop,ro "$ISO" $M || exit 1
grep -h -E "^(rootpw|keyboard|bootloader)|bootc switch" $M/osbuild.ks $M/osbuild-base.ks
echo "rootpw lines: $(grep -c '^rootpw' $M/osbuild.ks)"
umount $M
