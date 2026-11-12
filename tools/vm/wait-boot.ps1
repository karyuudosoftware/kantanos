# Waits until the serial console shows the login prompt (fresh boot finished), then screenshots.
param([int]$Max = 400, [string]$Name = 'booted')
$log = 'D:\CLAUDE_Projects\kantanos\output\vm\serial.log'
$sw = [Diagnostics.Stopwatch]::StartNew()
while ($sw.Elapsed.TotalSeconds -lt $Max) {
    if ((Test-Path $log) -and (Select-String -Path $log -Pattern 'kantanos login:' -Quiet)) { "login prompt after $([int]$sw.Elapsed.TotalSeconds)s of waiting"; break }
    Start-Sleep -Seconds 5
}
Start-Sleep -Seconds 15
& "$PSScriptRoot\shot.ps1" $Name 0 | Select-Object -First 1
