# Hard-restarts the VM and takes a burst of screenshots during boot (to catch the splash).
$d = 'D:\CLAUDE_Projects\kantanos\output\vm'
$p = Get-Process -Id (Get-Content "$d\qemu.pid") -ErrorAction SilentlyContinue
if ($p -and $p.ProcessName -like 'qemu*') { python "$PSScriptRoot\qmp.py" quit; Start-Sleep 12; Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue; Start-Sleep 2 }
& "$PSScriptRoot\run-vm.ps1"
$sw = [Diagnostics.Stopwatch]::StartNew()
foreach ($t in 17, 20, 23, 26, 30) {
    $wait = $t - $sw.Elapsed.TotalSeconds
    if ($wait -gt 0) { Start-Sleep -Milliseconds ([int]($wait * 1000)) }
    python "$PSScriptRoot\qmp.py" shot "D:\CLAUDE_Projects\kantanos\output\shots\splash-$t.png"
}
'burst done'
