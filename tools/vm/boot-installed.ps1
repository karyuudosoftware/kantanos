# Boots the disk that the ISO installed to, gets past the first-boot reboot, and screenshots.
$d = 'D:\CLAUDE_Projects\kantanos\output\vm'
$log = "$d\serial.log"
function Stop-Vm {
    $p = Get-Process -Id (Get-Content "$d\qemu.pid") -ErrorAction SilentlyContinue
    if ($p -and $p.ProcessName -like 'qemu*') { Stop-Process -Id $p.Id -Force; Start-Sleep 3 }
}
function Wait-Quiet([int]$max) {
    # The installed system has no serial console configured, so watch the screen instead:
    # wait until two screenshots 8 s apart are identical and not tiny (a settled graphical screen).
    $sw = [Diagnostics.Stopwatch]::StartNew(); $prev = ''
    while ($sw.Elapsed.TotalSeconds -lt $max) {
        Start-Sleep -Seconds 8
        python "$PSScriptRoot\qmp.py" shot "$d\probe.png" 2>$null
        if (Test-Path "$d\probe.png") {
            $h = (Get-FileHash "$d\probe.png").Hash; $len = (Get-Item "$d\probe.png").Length
            if ($h -eq $prev -and $len -gt 200000) { return [int]$sw.Elapsed.TotalSeconds }
            $prev = $h
        }
    }
    return -1
}
Stop-Vm
& "$PSScriptRoot\run-install-vm.ps1"
foreach ($t in 14, 18, 22, 26) { Start-Sleep -Seconds 4; python "$PSScriptRoot\qmp.py" shot "D:\CLAUDE_Projects\kantanos\output\shots\inst-boot-$t.png" 2>$null }
"settled after: $(Wait-Quiet 420) s"
& "$PSScriptRoot\shot.ps1" inst-first 0 | Select-Object -First 1
