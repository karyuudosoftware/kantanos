# Boots a KantanOS install on a physical disk in the test VM, READ-ONLY: everything the VM
# changes goes to a throwaway file (QEMU snapshot), so the disk stays exactly as it was and
# its one-time first-boot setup still happens later on the real PC.
# Opens a normal window so you can log in with your own password.
# Must be run from an administrator PowerShell (opening a physical drive needs admin).
#   boot-disk-vm.ps1 -DiskNumber N
param([Parameter(Mandatory = $true)][int]$DiskNumber)
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { 'Please run this from an administrator PowerShell window.'; exit 1 }

$disk = Get-Disk -Number $DiskNumber -ErrorAction SilentlyContinue
if (-not $disk) { "There is no disk $DiskNumber."; exit 1 }
if ($disk.IsBoot -or $disk.IsSystem) { "Disk $DiskNumber is the disk Windows is running from. Refusing."; exit 1 }
$parts = @(Get-Partition -DiskNumber $DiskNumber -ErrorAction SilentlyContinue)
$efi = $parts | Where-Object { $_.GptType -eq '{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}' }
$linux = $parts | Where-Object { $_.GptType -eq '{0fc63daf-8483-4772-8e79-3d69d8477de4}' }
$lettered = $parts | Where-Object { $_.DriveLetter -and $_.GptType -ne '{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}' }
if (-not $efi -or -not $linux -or $lettered) {
    "Disk $DiskNumber does not look like a KantanOS install (needs an EFI and a Linux partition, and no Windows drive letters). Refusing."
    $parts | Format-Table PartitionNumber, Size, Type, DriveLetter; exit 1
}
"Booting disk $DiskNumber ($($disk.FriendlyName), $([math]::Round($disk.Size/1GB,1)) GB) read-only in a VM window."

$q = 'C:\Program Files\qemu'
$root = Split-Path (Split-Path $PSScriptRoot)
$d = "$root\output\vm"
Get-Process qemu* -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep 2
Copy-Item "$q\share\edk2-i386-vars.fd" "$d\disk-vars.fd" -Force
Remove-Item "$d\serial.log", "$d\qemu-err.txt" -ErrorAction SilentlyContinue
$a = @(
    '-machine q35', '-accel whpx,kernel-irqchip=off', '-cpu max', '-smp 8', '-m 8G',
    "-drive `"if=pflash,format=raw,readonly=on,file=$q\share\edk2-x86_64-code.fd`"",
    "-drive if=pflash,format=raw,file=$d\disk-vars.fd",
    "-drive `"file=\\.\PhysicalDrive$DiskNumber,format=raw,if=virtio,snapshot=on`"",
    '-device virtio-vga,xres=1920,yres=1080',
    '-device qemu-xhci', '-device usb-tablet', '-device usb-kbd',
    '-netdev user,id=n0', '-device virtio-net-pci,netdev=n0', '-device virtio-rng-pci',
    '-display sdl', '-name "KantanOS (read-only test of the installed SSD)"',
    '-qmp tcp:127.0.0.1:4444,server=on,wait=off',
    "-chardev socket,id=ser0,host=127.0.0.1,port=4445,server=on,wait=off,logfile=$d\serial.log",
    '-serial chardev:ser0'
) -join ' '
$p = Start-Process -FilePath "$q\qemu-system-x86_64.exe" -ArgumentList $a -PassThru -RedirectStandardError "$d\qemu-err.txt"
$p.Id | Out-File -Encoding ascii "$d\qemu.pid"
Start-Sleep -Seconds 6
if ($p.HasExited) { 'The VM did not start:'; Get-Content "$d\qemu-err.txt"; exit 1 }
"VM started (pid $($p.Id)). A window titled 'KantanOS (read-only test...)' should appear."
"Close that window when you are done; nothing it changed is kept."
