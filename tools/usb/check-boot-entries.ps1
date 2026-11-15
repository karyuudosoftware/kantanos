# Read-only check of why a KantanOS disk does not appear in the PC's boot menu.
# Lists the firmware's boot entries and the boot files on the KantanOS disk.
# Must be run from an administrator PowerShell. Changes nothing except giving the disk's
# small EFI partition a temporary drive letter, which it removes again at the end.
param([string]$Model = 'Samsung SSD 850')
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { 'Please run this from an administrator PowerShell window.'; exit 1 }

'===== Firmware boot entries ====='
bcdedit /enum firmware | Select-String -Pattern '^identifier|^description|^path|^device|^displayorder|^\s+\{' | ForEach-Object { $_.Line }

$disk = @(Get-Disk | Where-Object { $_.FriendlyName -like "*$Model*" })
if ($disk.Count -ne 1) { "Expected one disk matching '$Model', found $($disk.Count)."; Get-Disk | Format-Table Number, FriendlyName; exit 1 }
$disk = $disk[0]
if ($disk.IsBoot -or $disk.IsSystem) { 'That disk is the Windows disk. Stopping.'; exit 1 }
"===== Disk $($disk.Number): $($disk.FriendlyName), $([math]::Round($disk.Size/1GB,1)) GB, $($disk.PartitionStyle) ====="
Get-Partition -DiskNumber $disk.Number | Format-Table PartitionNumber, @{n='GB';e={[math]::Round($_.Size/1GB,2)}}, GptType -AutoSize | Out-String | Write-Output

$esp = Get-Partition -DiskNumber $disk.Number | Where-Object GptType -eq '{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}'
if (-not $esp) { 'No EFI partition on that disk.'; exit 1 }
$letter = (68..90 | ForEach-Object { [char]$_ } | Where-Object { -not (Test-Path "$($_):\") } | Select-Object -Last 1)
Add-PartitionAccessPath -DiskNumber $disk.Number -PartitionNumber $esp.PartitionNumber -AccessPath "$($letter):\"
Start-Sleep 2
try {
    "===== Boot files on the KantanOS disk ($($letter):) ====="
    Get-ChildItem "$($letter):\EFI" -Recurse -File -ErrorAction Stop | ForEach-Object { "{0,10}  {1}" -f $_.Length, $_.FullName.Substring(3) }
} catch { "Could not read the EFI partition: $($_.Exception.Message)" }
finally {
    Remove-PartitionAccessPath -DiskNumber $disk.Number -PartitionNumber $esp.PartitionNumber -AccessPath "$($letter):\"
}
'===== Done (nothing was changed) ====='
