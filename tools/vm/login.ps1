# Logs the test user in (or unlocks) at the graphical login screen, then screenshots.
param([string]$Name = 'desktop', [int]$Wait = 30)
$q = "$PSScriptRoot\qmp.py"
$env:KANTAN_KEY_DELAY = '0.15'
python $q key shift
Start-Sleep -Seconds 3
python $q type kantan
& "$PSScriptRoot\shot.ps1" login-prompt 1 | Select-Object -First 1
python $q key ret
& "$PSScriptRoot\shot.ps1" $Name $Wait | Select-Object -First 1
