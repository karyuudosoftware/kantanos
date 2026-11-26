# Boots the KantanOS test disk in QEMU for Windows with hypervisor (WHPX) acceleration.
# Headless: control it with qmp.py (tcp 4444) and serial.py (tcp 4445).
#   -Audio   add a sound card (silent: its sound goes nowhere) for audio-setting tests
#   -Screen 2560x1440   the virtual screen reports this as its best picture (safe-picture tests;
#                       QEMU puts 4K in a DisplayID block, so 2560x1440 is the useful test;
#                       virtio-gpu ignores Linux's EDID override, so only the program's
#                       own logic can be tested here, not the picture change)
param([string]$Cpu = 'max', [int]$Cpus = 8, [string]$Ram = '8G', [switch]$Audio, [string]$Screen = '')
$q = 'C:\Program Files\qemu'
$d = 'D:\CLAUDE_Projects\kantanos\output\vm'
if (-not (Test-Path "$d\vars.fd")) { Copy-Item "$q\share\edk2-i386-vars.fd" "$d\vars.fd" }
Remove-Item "$d\serial.log", "$d\qemu-err.txt" -ErrorAction SilentlyContinue
$a = @(
    '-machine q35', '-accel whpx,kernel-irqchip=off', "-cpu $Cpu", "-smp $Cpus", "-m $Ram",
    "-drive `"if=pflash,format=raw,readonly=on,file=$q\share\edk2-x86_64-code.fd`"",
    "-drive if=pflash,format=raw,file=$d\vars.fd",
    "-drive file=$d\disk.qcow2,if=virtio",
    '-device virtio-vga,xres=1920,yres=1080',
    '-device qemu-xhci', '-device usb-tablet', '-device usb-kbd',
    '-netdev user,id=n0', '-device virtio-net-pci,netdev=n0', '-device virtio-rng-pci',
    '-display none',
    '-qmp tcp:127.0.0.1:4444,server=on,wait=off',
    "-chardev socket,id=ser0,host=127.0.0.1,port=4445,server=on,wait=off,logfile=$d\serial.log",
    '-serial chardev:ser0'
)
if ($Screen) { $w, $h = $Screen -split 'x'; $a = $a -replace 'virtio-vga,xres=1920,yres=1080', "virtio-vga,edid=on,xres=$w,yres=$h" }
if ($Audio) { $a += '-audiodev none,id=snd0'; $a += '-device ich9-intel-hda'; $a += '-device hda-output,audiodev=snd0' }
$a = $a -join ' '
$p = Start-Process -FilePath "$q\qemu-system-x86_64.exe" -ArgumentList $a -PassThru -WindowStyle Hidden -RedirectStandardError "$d\qemu-err.txt"
$p.Id | Out-File -Encoding ascii "$d\qemu.pid"
Start-Sleep -Seconds 4
if ($p.HasExited) { "QEMU exited:"; Get-Content "$d\qemu-err.txt"; exit 1 }
"VM started, pid $($p.Id)"
