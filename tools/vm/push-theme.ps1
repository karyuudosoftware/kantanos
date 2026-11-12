# Regenerates the Kantan Glass theme and applies it live in the running VM (no image rebuild).
$root = 'D:\CLAUDE_Projects\kantanos'
python "$root\tools\make-plasma-theme.py" | Out-Null
$tmp = "$env:TEMP\kg.tar.gz"
tar -czf $tmp -C "$root\system_files\usr\share\plasma\desktoptheme" KantanGlass
$b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($tmp))
$push = "$env:TEMP\kg-push.sh"
"cat > /tmp/KantanGlass.b64 <<'EOF'`n$b64`nEOF`n" | Out-File -Encoding ascii $push
python "$PSScriptRoot\serial.py" --timeout 60 --script $push | Out-Null
python "$PSScriptRoot\serial.py" --timeout 60 --script "$PSScriptRoot\guest\try-theme.sh"
