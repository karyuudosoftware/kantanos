# KantanOS: runs once, at the first sign-in of the Windows virtual machine.
# Turns on what KantanOS needs to show Windows programs as its own windows, trims the
# preinstalled extras and ads, removes the stored setup password, then shuts Windows down
# so KantanOS knows setup is finished.
$ErrorActionPreference = 'Continue'
$src = Split-Path -Parent $MyInvocation.MyCommand.Path
New-Item -ItemType Directory -Force C:\kantanos | Out-Null
Start-Transcript C:\kantanos\firstlogon.log
Copy-Item "$src\scan.ps1" C:\kantanos\ -Force

function Set-Reg($path, $name, $value) {
    if (-not (Test-Path $path)) { New-Item -Path $path -Force | Out-Null }
    Set-ItemProperty -Path $path -Name $name -Value $value -Type DWord
}

# Remote Desktop (only reachable from this PC: the VM's network is private to it)
Set-Reg 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server' fDenyTSConnections 0
Get-NetFirewallRule -Group '@FirewallAPI.dll,-28752' | Enable-NetFirewallRule
# Let KantanOS open single programs in their own windows (RemoteApp)
Set-Reg 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Terminal Server\TSAppAllowList' fDisabledAllowList 1
Set-Reg 'HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\Terminal Services' fAllowUnlistedRemotePrograms 1

# Never sleep or hibernate: KantanOS pauses the whole virtual machine when it is not used
powercfg /change standby-timeout-ac 0
powercfg /change monitor-timeout-ac 0
powercfg /hibernate off

# Fewer ads, suggestions and silently installed apps
$cdm = 'HKCU:\Software\Microsoft\Windows\CurrentVersion\ContentDeliveryManager'
foreach ($v in 'ContentDeliveryAllowed', 'OemPreInstalledAppsEnabled', 'PreInstalledAppsEnabled',
               'SilentInstalledAppsEnabled', 'SoftLandingEnabled', 'SystemPaneSuggestionsEnabled',
               'SubscribedContent-338388Enabled', 'SubscribedContent-338389Enabled',
               'SubscribedContent-353694Enabled', 'SubscribedContent-353696Enabled') {
    Set-Reg $cdm $v 0
}
Set-Reg 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\CloudContent' DisableWindowsConsumerFeatures 1
Set-Reg 'HKCU:\Software\Policies\Microsoft\Windows\Explorer' DisableSearchBoxSuggestions 1
Set-Reg 'HKCU:\Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo' Enabled 0

# Preinstalled extras nobody asked for (the Store can bring any of them back)
$extras = 'Clipchamp.Clipchamp', 'Microsoft.BingNews', 'Microsoft.BingSearch', 'Microsoft.BingWeather',
          'Microsoft.Copilot', 'Microsoft.GetHelp', 'Microsoft.Getstarted', 'Microsoft.MicrosoftOfficeHub',
          'Microsoft.MicrosoftSolitaireCollection', 'Microsoft.OutlookForWindows', 'Microsoft.People',
          'Microsoft.PowerAutomateDesktop', 'Microsoft.Todos', 'Microsoft.WindowsFeedbackHub',
          'Microsoft.WindowsMaps', 'Microsoft.YourPhone', 'MicrosoftCorporationII.QuickAssist', 'MSTeams'
Get-AppxProvisionedPackage -Online | Where-Object { $extras -contains $_.DisplayName } |
    ForEach-Object { Remove-AppxProvisionedPackage -Online -PackageName $_.PackageName | Out-Null }
Get-AppxPackage | Where-Object { $extras -contains $_.Name } | Remove-AppxPackage -ErrorAction SilentlyContinue

# The setup answers held the sign-in password: remove every copy Windows kept
Remove-Item 'C:\Windows\Panther\unattend.xml', 'C:\Windows\Panther\Unattend\unattend.xml' -Force -ErrorAction SilentlyContinue
$wl = 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon'
Remove-ItemProperty -Path $wl -Name DefaultPassword -ErrorAction SilentlyContinue
Set-ItemProperty -Path $wl -Name AutoAdminLogon -Value '0'

'ready' | Set-Content C:\kantanos\ready.txt
Stop-Transcript
shutdown /s /t 10 /c "KantanOS: Windows is set up."
