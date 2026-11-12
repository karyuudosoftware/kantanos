# shot.ps1 <name> [wait-seconds] — waits, then saves a VM screenshot to output\shots\<name>.png
param([string]$Name = 'shot', [int]$Wait = 0)
$shots = 'D:\CLAUDE_Projects\kantanos\output\shots'
New-Item -ItemType Directory -Force $shots | Out-Null
if ($Wait -gt 0) { Start-Sleep -Seconds $Wait }
python "$PSScriptRoot\qmp.py" shot "$shots\$Name.png"
"saved $Name.png"
$log = 'D:\CLAUDE_Projects\kantanos\output\vm\serial.log'
if (Test-Path $log) { (Get-Content $log -Tail 4) -replace "`e\[[0-9;]*[A-Za-z]", '' }
