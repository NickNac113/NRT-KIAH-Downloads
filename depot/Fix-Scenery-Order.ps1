param([switch]$CheckOnly)
$ErrorActionPreference = 'Stop'

# Manual, local repair only. The updater never runs this script.
$package = Get-Item -LiteralPath $PSScriptRoot
$custom = $package.Parent
$sim = $custom.Parent
if ($package.Name -cne 'NRT_KIAH_Campus' -or $custom.Name -cne 'Custom Scenery' -or
    -not (Test-Path -LiteralPath (Join-Path $sim.FullName 'X-Plane.exe')) -or
    -not (Test-Path -LiteralPath (Join-Path $package.FullName 'Earth nav data\apt.dat'))) {
    throw 'Run this copy from X-Plane 12\Custom Scenery\NRT_KIAH_Campus.'
}
$ini = Join-Path $custom.FullName 'scenery_packs.ini'
$item = Get-Item -LiteralPath $ini
foreach ($node in @($item, $package, $custom, $sim)) {
    if ($node.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        throw 'Linked installation or configuration path: move the NRT line manually instead.'
    }
}
if (-not $CheckOnly -and @(Get-Process -Name 'X-Plane' -ErrorAction SilentlyContinue).Count) {
    throw 'Close X-Plane before repairing scenery order.'
}
$original = [IO.File]::ReadAllBytes($ini)
$prefixLength = 0
$encoding = New-Object Text.UTF8Encoding($false, $true)
if ($original.Length -ge 3 -and $original[0] -eq 239 -and $original[1] -eq 187 -and $original[2] -eq 191) {
    $prefixLength = 3
} elseif ($original.Length -ge 2 -and $original[0] -eq 255 -and $original[1] -eq 254) {
    $prefixLength = 2; $encoding = New-Object Text.UnicodeEncoding($false, $false, $true)
} elseif ($original.Length -ge 2 -and $original[0] -eq 254 -and $original[1] -eq 255) {
    $prefixLength = 2; $encoding = New-Object Text.UnicodeEncoding($true, $false, $true)
}
$body = $encoding.GetString($original, $prefixLength, $original.Length - $prefixLength)
if ($body -notmatch "`n") { throw 'Unrecognized configuration format; move the NRT line manually.' }
$lines = [Collections.Generic.List[string]]::new()
$lines.AddRange([string[]][regex]::Split($body, '(?<=\n)'))
$matchesNrt = @()
$firstActive = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i].Trim() -match '^(SCENERY_PACK(?:_DISABLED)?)\s+(.+?)\s*$') {
        $mode = $Matches[1]
        $path = $Matches[2].Replace('\', '/').TrimEnd('/')
        if ($mode -eq 'SCENERY_PACK' -and $firstActive -lt 0) { $firstActive = $i }
        if ($path -ieq 'Custom Scenery/NRT_KIAH_Campus' -or
            $path -ieq $package.FullName.Replace('\', '/').TrimEnd('/')) {
            $matchesNrt += [pscustomobject]@{ Index = $i; Mode = $mode }
        }
    }
}
if ($matchesNrt.Count -ne 1 -or $matchesNrt[0].Mode -ne 'SCENERY_PACK') {
    throw 'Expected exactly one enabled NRT_KIAH_Campus entry. Resolve missing, duplicate or disabled entries manually.'
}
$index = $matchesNrt[0].Index
if ($index -eq $firstActive) { Write-Output 'NRT is already the first enabled scenery package. No changes.'; exit 0 }
if ($CheckOnly) { Write-Output 'Repair needed: NRT must be above AEP, AEP Overlays and other KIAH scenery. No changes made.'; exit 0 }
$nrtLine = $lines[$index]
# A moved final line may not yet have a terminator.
if (-not $nrtLine.EndsWith("`n")) {
    $newline = if ($body.Contains("`r`n")) { "`r`n" } else { "`n" }
    $nrtLine += $newline
}
$lines.RemoveAt($index)
$lines.Insert($firstActive, $nrtLine)
$encoded = $encoding.GetBytes(($lines -join ''))
$updated = [byte[]]::new($prefixLength + $encoded.Length)
if ($prefixLength) { [Array]::Copy($original, 0, $updated, 0, $prefixLength) }
[Array]::Copy($encoded, 0, $updated, $prefixLength, $encoded.Length)
# Refuse to overwrite any concurrent edit; save the exact original before writing.
if ([Convert]::ToBase64String([IO.File]::ReadAllBytes($ini)) -cne [Convert]::ToBase64String($original)) {
    throw 'scenery_packs.ini changed during the check. Nothing was written; try again.'
}
$backup = $ini + '.before-NRT-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff') + '.bak'
$stream = [IO.File]::Open($backup, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
try { $stream.Write($original, 0, $original.Length) } finally { $stream.Dispose() }
[IO.File]::WriteAllBytes($ini, $updated)
Write-Output ('Moved only the NRT entry above the other enabled packages. Backup: ' + $backup)
Write-Output 'Start X-Plane again to load the corrected order.'
