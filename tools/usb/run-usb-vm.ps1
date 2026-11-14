# Boots the run-from-USB image in a VM as an emulated USB drive, to prove it starts from USB.
# The image file itself is never written to (see the overlay below), so
# the file stays exactly as built for writing to a real USB drive.
#   -Fresh   start again from the image as built (throws away what earlier test boots changed)
param([switch]$Fresh, [string]$Cpu = 'max', [int]$Cpus = 8, [string]$Ram = '8G')
$q = 'C:\Program Files\qemu'
$root = Split-Path (Split-Path $PSScriptRoot)
$d = "$root\output\vm"
$img = (Get-ChildItem "$root\output\usb\KantanOS-*-usb.img" | Sort-Object LastWriteTime | Select-Object -Last 1).FullName
if (-not $img) { 'no USB image found in output\usb'; exit 1 }
# Test boots write to an overlay file next to the VM files, never to the image itself, and
# the overlay survives a VM restart (needed to get past the one-time first-boot restart).
$overlay = "$d\usb-overlay.qcow2"
if ($Fresh) { Remove-Item $overlay, "$d\usb-vars.fd" -ErrorAction SilentlyContinue }
if (-not (Test-Path $overlay)) { & "$q\qemu-img.exe" create -f qcow2 -b $img -F raw $overlay | Out-Null }
if (-not (Test-Path "$d\usb-vars.fd")) { Copy-Item "$q\share\edk2-i386-vars.fd" "$d\usb-vars.fd" }
Remove-Item "$d\serial.log", "$d\qemu-err.txt" -ErrorAction SilentlyContinue
$a = @(
    '-machine q35', '-accel whpx,kernel-irqchip=off', "-cpu $Cpu", "-smp $Cpus", "-m $Ram",
    "-drive `"if=pflash,format=raw,readonly=on,file=$q\share\edk2-x86_64-code.fd`"",
    "-drive if=pflash,format=raw,file=$d\usb-vars.fd",
    '-device qemu-xhci,id=xhci',
    "-drive `"file=$overlay,format=qcow2,if=none,id=usbdisk`"",
    '-device usb-storage,bus=xhci.0,drive=usbdisk,bootindex=0',
    '-device virtio-vga,xres=1920,yres=1080',
    '-device usb-tablet', '-device usb-kbd',
    '-netdev user,id=n0', '-device virtio-net-pci,netdev=n0', '-device virtio-rng-pci',
    '-display none',
    '-qmp tcp:127.0.0.1:4444,server=on,wait=off',
    "-chardev socket,id=ser0,host=127.0.0.1,port=4445,server=on,wait=off,logfile=$d\serial.log",
    '-serial chardev:ser0'
) -join ' '
$p = Start-Process -FilePath "$q\qemu-system-x86_64.exe" -ArgumentList $a -PassThru -WindowStyle Hidden -RedirectStandardError "$d\qemu-err.txt"
$p.Id | Out-File -Encoding ascii "$d\qemu.pid"
Start-Sleep -Seconds 4
if ($p.HasExited) { "QEMU exited:"; Get-Content "$d\qemu-err.txt"; exit 1 }
"USB VM started, pid $($p.Id), image $img"
