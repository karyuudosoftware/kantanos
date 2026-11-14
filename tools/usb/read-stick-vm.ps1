# Starts the KantanOS test VM with a USB stick attached READ-ONLY as a second disk, so the
# logs of a failed real-hardware boot can be read from inside the VM.
# Must be run from an administrator PowerShell (opening a physical drive needs admin).
#   read-stick-vm.ps1 [-DiskNumber N]     default: the only USB disk under 64 GB
param([int]$DiskNumber = -1)
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { 'Please run this from an administrator PowerShell window.'; exit 1 }

$usb = @(Get-Disk | Where-Object { $_.BusType -eq 'USB' -and $_.Size -lt 64GB })
if ($DiskNumber -ge 0) { $usb = @($usb | Where-Object Number -eq $DiskNumber) }
if ($usb.Count -ne 1) { "Expected exactly one USB stick under 64 GB, found $($usb.Count). Nothing started."; $usb | Format-Table Number, FriendlyName, Size; exit 1 }
$stick = "\\.\PhysicalDrive$($usb[0].Number)"
"Using $stick ($($usb[0].FriendlyName), $([math]::Round($usb[0].Size/1GB,1)) GB), read-only"

$q = 'C:\Program Files\qemu'
$root = Split-Path (Split-Path $PSScriptRoot)
$d = "$root\output\vm"
Get-Process qemu* -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2
if (-not (Test-Path "$d\vars.fd")) { Copy-Item "$q\share\edk2-i386-vars.fd" "$d\vars.fd" }
Remove-Item "$d\serial.log", "$d\qemu-err.txt" -ErrorAction SilentlyContinue
$a = @(
    '-machine q35', '-accel whpx,kernel-irqchip=off', '-cpu max', '-smp 8', '-m 8G',
    "-drive `"if=pflash,format=raw,readonly=on,file=$q\share\edk2-x86_64-code.fd`"",
    "-drive if=pflash,format=raw,file=$d\vars.fd",
    "-drive file=$d\disk.qcow2,if=virtio",
    "-drive `"file=$stick,format=raw,if=virtio,readonly=on`"",
    '-device virtio-vga,xres=1920,yres=1080',
    '-device qemu-xhci', '-device usb-tablet', '-device usb-kbd',
    '-netdev user,id=n0', '-device virtio-net-pci,netdev=n0', '-device virtio-rng-pci',
    '-display none',
    '-qmp tcp:127.0.0.1:4444,server=on,wait=off',
    "-chardev socket,id=ser0,host=127.0.0.1,port=4445,server=on,wait=off,logfile=$d\serial.log",
    '-serial chardev:ser0'
) -join ' '
$p = Start-Process -FilePath "$q\qemu-system-x86_64.exe" -ArgumentList $a -PassThru -WindowStyle Hidden -RedirectStandardError "$d\qemu-err.txt"
$p.Id | Out-File -Encoding ascii "$d\qemu.pid"
Start-Sleep -Seconds 6
if ($p.HasExited) { 'The VM did not start:'; Get-Content "$d\qemu-err.txt"; exit 1 }
"VM started (pid $($p.Id)) with the stick attached read-only. You can leave this window; tell Claude it is running."
