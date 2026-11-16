# KantanOS: lists the programs in the Windows Start menu, with their icons, so KantanOS can
# put them in its own app menu and search. Runs inside the Windows virtual machine; KantanOS
# passes a folder of its own as \\tsclient\kscan for the results.
param([string]$Out = '\\tsclient\kscan')
$ErrorActionPreference = 'SilentlyContinue'
Add-Type -AssemblyName System.Drawing
$shell = New-Object -ComObject WScript.Shell
$md5 = [Security.Cryptography.MD5]::Create()
$skip = 'uninstall|deinstall|readme|read me|help|manual|documentation|website|license|release notes|support'
$menus = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs",
         "$env:APPDATA\Microsoft\Windows\Start Menu\Programs"

New-Item -ItemType Directory -Force "$Out\icons" | Out-Null
$rows = New-Object System.Collections.Generic.List[string]
$seen = @{}
foreach ($menu in $menus) {
    Get-ChildItem $menu -Recurse -Filter *.lnk | ForEach-Object {
        $name = $_.BaseName
        if ($name -match $skip) { return }
        $target = $shell.CreateShortcut($_.FullName).TargetPath
        if (-not $target -or $target -notmatch '\.exe$' -or -not (Test-Path $target)) { return }
        if ($target -like "$env:windir\*") { return }   # Windows' own tools stay in Windows
        $key = $target.ToLowerInvariant()
        if ($seen.ContainsKey($key)) { return }
        $seen[$key] = $true
        $hash = $md5.ComputeHash([Text.Encoding]::UTF8.GetBytes($key))
        $id = ([BitConverter]::ToString($hash) -replace '-', '').Substring(0, 12).ToLowerInvariant()
        try {
            $icon = [Drawing.Icon]::ExtractAssociatedIcon($target)
            $icon.ToBitmap().Save("$Out\icons\$id.png", [Drawing.Imaging.ImageFormat]::Png)
        } catch { }
        $rows.Add("$id`t$name`t$target")
    }
}
[IO.File]::WriteAllLines("$Out\apps.tsv", $rows, (New-Object Text.UTF8Encoding $false))
