# Boots a VM with a blank disk for testing the installer ISO (or the installed result).
#   run-install-vm.ps1 -Iso <path>   boot the installer
#   run-install-vm.ps1               boot the disk that was installed to
# Uses the same control ports as run-vm.ps1, so stop the other VM first.
param([string]$Iso = '', [switch]$Fresh, [string]$Cpu = 'max', [int]$Cpus = 8, [string]$Ram = '8G')
$q = 'C:\Program Files\qemu'
$d = 'D:\CLAUDE_Projects\kantanos\output\vm'
$disk = "$d\install.qcow2"
if ($Fresh) { Remove-Item $disk, "$d\install-vars.fd" -ErrorAction SilentlyContinue }
if (-not (Test-Path $disk)) { & "$q\qemu-img.exe" create -f qcow2 $disk 64G | Out-Null }
if (-not (Test-Path "$d\install-vars.fd")) { Copy-Item "$q\share\edk2-i386-vars.fd" "$d\install-vars.fd" }
Remove-Item "$d\serial.log", "$d\qemu-err.txt" -ErrorAction SilentlyContinue
$a = @(
    '-machine q35', '-accel whpx,kernel-irqchip=off', "-cpu $Cpu", "-smp $Cpus", "-m $Ram",
    "-drive `"if=pflash,format=raw,readonly=on,file=$q\share\edk2-x86_64-code.fd`"",
    "-drive if=pflash,format=raw,file=$d\install-vars.fd",
    "-drive file=$disk,if=virtio",
    '-device virtio-vga,xres=1920,yres=1080',
    '-device qemu-xhci', '-device usb-tablet', '-device usb-kbd',
    '-netdev user,id=n0', '-device virtio-net-pci,netdev=n0', '-device virtio-rng-pci',
    '-display none',
    '-qmp tcp:127.0.0.1:4444,server=on,wait=off',
    "-chardev socket,id=ser0,host=127.0.0.1,port=4445,server=on,wait=off,logfile=$d\serial.log",
    '-serial chardev:ser0'
)
if ($Iso) { $a += "-drive `"file=$Iso,media=cdrom,if=none,id=cd0,readonly=on`""; $a += '-device ide-cd,drive=cd0,bootindex=0' }
$p = Start-Process -FilePath "$q\qemu-system-x86_64.exe" -ArgumentList ($a -join ' ') -PassThru -WindowStyle Hidden -RedirectStandardError "$d\qemu-err.txt"
$p.Id | Out-File -Encoding ascii "$d\qemu.pid"
Start-Sleep -Seconds 4
if ($p.HasExited) { "QEMU exited:"; Get-Content "$d\qemu-err.txt"; exit 1 }
"install VM started, pid $($p.Id)"
