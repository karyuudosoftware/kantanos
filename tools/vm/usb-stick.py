#!/usr/bin/env python3
"""Plug a pretend USB stick into the test VM, or pull it out (for testing Backups and the like).

  usb-stick.py plug   [image]    creates output/vm/usb-stick.img (2 GB, empty) if needed
  usb-stick.py unplug

The first time, format it in the VM (as root): mkfs.exfat -L BACKUP /dev/sdX
"""
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qmp import Qmp  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
IMG = os.path.join(ROOT, "output", "vm", "usb-stick.img")
QEMU_IMG = r"C:\Program Files\qemu\qemu-img.exe" if os.name == "nt" else "qemu-img"


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else "plug"
    q = Qmp()
    if what == "plug":
        img = sys.argv[2] if len(sys.argv) > 2 else IMG
        if not os.path.exists(img):
            subprocess.run([QEMU_IMG, "create", "-f", "raw", img, "2G"], check=True)
        q.cmd("blockdev-add", driver="raw", **{"node-name": "usbstick"},
              file={"driver": "file", "filename": img.replace("\\", "/")})
        q.cmd("device_add", driver="usb-storage", drive="usbstick", id="usbstick", removable=True)
        print("plugged in")
    else:
        q.cmd("device_del", id="usbstick")
        import time
        time.sleep(2)
        q.cmd("blockdev-del", **{"node-name": "usbstick"})
        print("pulled out")


if __name__ == "__main__":
    main()
