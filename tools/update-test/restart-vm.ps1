# Shuts the test VM down cleanly (so a staged update or rollback is finalised), boots it again
# and waits for the login prompt. Guest restarts hang under WHPX, hence power off + start.
param([string]$Before = '')
$root = Split-Path (Split-Path $PSScriptRoot)
$d = "$root\output\vm"
if ($Before) { python "$root\tools\vm\serial.py" --timeout 300 --root-script $Before }
$off = "$env:TEMP\kantan-poweroff.sh"; [IO.File]::WriteAllText($off, "systemctl poweroff`n")
python "$root\tools\vm\serial.py" --timeout 5 --root-script $off | Out-Null
$p = Get-Process -Id (Get-Content "$d\qemu.pid") -ErrorAction SilentlyContinue
if ($p) { if (-not $p.WaitForExit(120000)) { 'VM did not power off by itself; stopping it'; Stop-Process -Id $p.Id -Force } }
Start-Sleep 2
& "$root\tools\vm\run-vm.ps1"
$sw = [Diagnostics.Stopwatch]::StartNew()
while ($sw.Elapsed.TotalSeconds -lt 300) {
    if ((Test-Path "$d\serial.log") -and (Select-String -Path "$d\serial.log" -Pattern 'kantanos login:' -Quiet)) { break }
    Start-Sleep 4
}
"login prompt after $([int]$sw.Elapsed.TotalSeconds) s"
Start-Sleep 5
python "$root\tools\vm\serial.py" --timeout 120 --root-script "$PSScriptRoot\guest-after.sh" | Select-Object -Last 12
