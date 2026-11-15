# Adds a "KantanOS" entry to the PC's firmware boot menu, pointing at the boot files on the
# KantanOS disk. Windows stays first (the default); KantanOS is added at the end of the list
# and is picked from the boot menu (F12) or moved up in the BIOS.
# Must be run from an administrator PowerShell.
#   add-boot-entry.ps1             add the entry
#   add-boot-entry.ps1 -Remove     remove it again
param([switch]$Remove, [string]$Model = 'Samsung SSD 850', [string]$Name = 'KantanOS')
$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $admin) { 'Please run this from an administrator PowerShell window.'; exit 1 }

function Get-KantanEntries {
    $ids = @(); $id = $null
    foreach ($line in (bcdedit /enum firmware)) {
        if ($line -match '^identifier\s+(\{[^}]+\})') { $id = $Matches[1] }
        elseif ($line -match '^description\s+(.+)$' -and $Matches[1].Trim() -eq $Name) { $ids += $id }
    }
    return $ids
}

$existing = @(Get-KantanEntries)
if ($Remove) {
    if (-not $existing) { "There is no '$Name' boot entry."; exit 0 }
    foreach ($id in $existing) { bcdedit /delete $id | Out-Null; "Removed boot entry $id." }
    exit 0
}
if ($existing) { "A '$Name' boot entry already exists ($($existing -join ', ')). Nothing to do."; exit 0 }

$disk = @(Get-Disk | Where-Object { $_.FriendlyName -like "*$Model*" })
if ($disk.Count -ne 1) { "Expected one disk matching '$Model', found $($disk.Count). Nothing changed."; exit 1 }
$disk = $disk[0]
if ($disk.IsBoot -or $disk.IsSystem) { 'That disk is the Windows disk. Nothing changed.'; exit 1 }
$esp = Get-Partition -DiskNumber $disk.Number | Where-Object GptType -eq '{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}'
if (-not $esp) { 'No EFI partition on that disk. Nothing changed.'; exit 1 }

$letter = (68..90 | ForEach-Object { [char]$_ } | Where-Object { -not (Test-Path "$($_):\") } | Select-Object -Last 1)
Add-PartitionAccessPath -DiskNumber $disk.Number -PartitionNumber $esp.PartitionNumber -AccessPath "$($letter):\"
Start-Sleep 2
try {
    if (-not (Test-Path "$($letter):\EFI\fedora\shimx64.efi")) { 'The KantanOS boot loader was not found on that disk. Nothing changed.'; exit 1 }
    $out = bcdedit /copy '{bootmgr}' /d $Name
    if ($out -notmatch '(\{[0-9a-fA-F-]+\})') { "Could not create the entry: $out"; exit 1 }
    $id = $Matches[1]
    bcdedit /set $id device "partition=$($letter):" | Out-Null
    bcdedit /set $id path '\EFI\fedora\shimx64.efi' | Out-Null
    bcdedit /set '{fwbootmgr}' displayorder $id /addlast | Out-Null
    "Added boot entry '$Name' $id on disk $($disk.Number) ($($disk.FriendlyName))."
} finally {
    Remove-PartitionAccessPath -DiskNumber $disk.Number -PartitionNumber $esp.PartitionNumber -AccessPath "$($letter):\"
}
''
'Firmware boot entries now:'
bcdedit /enum firmware | Select-String -Pattern '^identifier|^description|^path' | ForEach-Object { $_.Line }
