# Full test cycle: stop VM, rebuild image, verify, rebuild disk, boot, get past the first-boot reboot.
param([switch]$SkipBuild)
$env:WSL_UTF8 = 1
$d = 'D:\CLAUDE_Projects\kantanos\output\vm'
$log = "$d\serial.log"

function Stop-Vm {
    if (Test-Path "$d\qemu.pid") {
        $p = Get-Process -Id (Get-Content "$d\qemu.pid") -ErrorAction SilentlyContinue
        if ($p -and $p.ProcessName -like 'qemu*') { Stop-Process -Id $p.Id -Force; Start-Sleep 3 }
    }
}
function Wait-Log([string]$pattern, [int]$max) {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    while ($sw.Elapsed.TotalSeconds -lt $max) {
        if ((Test-Path $log) -and (Select-String -Path $log -Pattern $pattern -Quiet)) { return $true }
        Start-Sleep -Seconds 4
    }
    return $false
}

Stop-Vm
if (-not $SkipBuild) {
    wsl -d kantan-build -u root -- bash -c "bash /mnt/d/CLAUDE_Projects/kantanos/tools/build-image.sh > /root/build.log 2>&1 || { tail -30 /root/build.log; exit 1; }"
    if ($LASTEXITCODE -ne 0) { 'BUILD FAILED'; exit 1 }
    wsl -d kantan-build -u root -- bash /mnt/d/CLAUDE_Projects/kantanos/tools/verify-image.sh | Select-String -Pattern 'FAIL|initramfs:' | ForEach-Object { $_.Line }
    'verify done (only FAIL lines are listed above)'
    wsl -d kantan-build -u root -- bash /mnt/d/CLAUDE_Projects/kantanos/tools/vm/export-disk.sh | Select-Object -Last 2
    if ($LASTEXITCODE -ne 0) { 'DISK FAILED'; exit 1 }
    Remove-Item "$d\vars.fd" -ErrorAction SilentlyContinue
}

& "$PSScriptRoot\run-vm.ps1"
& "$PSScriptRoot\shot.ps1" cycle-boot1-splash 14 | Select-Object -First 1
if (Wait-Log 'reboot: Restarting system|kantanos login:' 420) {
    if (Select-String -Path $log -Pattern 'reboot: Restarting system' -Quiet) {
        'first-boot setup asked for a reboot; restarting the VM'
        Stop-Vm
        & "$PSScriptRoot\run-vm.ps1"
        & "$PSScriptRoot\shot.ps1" cycle-boot2-splash 9 | Select-Object -First 1
        & "$PSScriptRoot\shot.ps1" cycle-boot2-splash-b 6 | Select-Object -First 1
        if (-not (Wait-Log 'kantanos login:' 300)) { 'second boot never reached login' }
    }
} else { 'boot timed out' }
Start-Sleep -Seconds 12
& "$PSScriptRoot\shot.ps1" cycle-greeter 0 | Select-Object -First 1
'CYCLE DONE'
