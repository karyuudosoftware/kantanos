# Runs as root in the test VM: mounts the attached USB stick read-only and summarises the
# logs of its boots on the real PC.
set -u
DEV=/dev/vdb     # the stick is the VM's second virtio disk
echo "stick: $DEV"; lsblk -o NAME,SIZE,FSTYPE,LABEL "$DEV"
PART=$(lsblk -rno NAME,FSTYPE "$DEV" | awk '$2=="btrfs" {print "/dev/"$1; exit}')
mkdir -p /mnt/stick
mountpoint -q /mnt/stick || mount -t btrfs -o ro,rescue=nologreplay "$PART" /mnt/stick || { echo "mount failed"; dmesg | tail -5; exit 1; }
VAR=$(ls -d /mnt/stick/ostree/deploy/*/var 2>/dev/null | head -1)
[ -n "$VAR" ] || VAR=$(find /mnt/stick -maxdepth 5 -type d -path '*/deploy/*/var' | head -1)
echo "var: $VAR"
J="$VAR/log/journal"
du -sh "$J" 2>/dev/null
echo "== boots"; journalctl -D "$J" --list-boots --no-pager 2>&1 | tail -12
echo "== deployments"; ls /mnt/stick/ostree/deploy/*/deploy/ 2>/dev/null
echo "== users / home"; ls "$VAR/home" 2>/dev/null
