# Prints, for rows down a column, how much two screenshots differ (sum of R+G+B change).
param([string]$First, [string]$Second, [int]$X = 700, [int]$Y0 = 980, [int]$Y1 = 1078, [int]$Step = 6)
Add-Type -AssemblyName System.Drawing
$imgA = [System.Drawing.Bitmap]::FromFile((Resolve-Path $First))
$imgB = [System.Drawing.Bitmap]::FromFile((Resolve-Path $Second))
for ($y = $Y0; $y -le $Y1; $y += $Step) {
    $p = $imgA.GetPixel($X, $y); $q = $imgB.GetPixel($X, $y)
    "y={0,4}  diff={1}" -f $y, ([math]::Abs($p.R - $q.R) + [math]::Abs($p.G - $q.G) + [math]::Abs($p.B - $q.B))
}
$imgA.Dispose(); $imgB.Dispose()
