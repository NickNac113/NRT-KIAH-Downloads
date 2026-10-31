param([string]$XPlaneRoot)
$ErrorActionPreference = 'Stop'
if (-not $XPlaneRoot) { $XPlaneRoot = Read-Host 'Folder containing X-Plane.exe' }
$simPath = [IO.Path]::GetFullPath($XPlaneRoot.Trim('"')).TrimEnd('\')
$iniPath = Join-Path $simPath 'Custom Scenery\scenery_packs.ini'
if (-not (Test-Path -LiteralPath $iniPath)) { throw 'scenery_packs.ini was not found.' }
$lines = [IO.File]::ReadAllLines($iniPath)
$active = @($lines | Where-Object { $_ -match '^SCENERY_PACK\s+Custom Scenery/(NRT_KIAH_Campus|KIAH_NRT_R\d+_[^/]+)/?$' })
Write-Host 'NRT / OpenSAM diagnostic - read only'
Write-Host "Active NRT entries: $($active.Count)"
if ($active.Count -ne 1) { Write-Warning 'Select exactly one NRT scenery package before starting X-Plane.' }
foreach ($entry in $active) {
    Write-Host $entry
    if (-not $entry.EndsWith('/')) { Write-Warning 'The final slash is missing. OpenSAM concatenates this path with its XML and apt.dat names.' }
    $relative = $entry -replace '^SCENERY_PACK\s+',''
    $folder = Join-Path $simPath $relative
    $xmlPath = Join-Path $folder 'opensam.xml'
    $aptPath = Join-Path $folder 'Earth nav data\apt.dat'
    if (Test-Path -LiteralPath $xmlPath) {
        [xml]$control = Get-Content -LiteralPath $xmlPath -Raw
        Write-Host "Door checkboxes in package: $(@($control.scenery.gui.checkbox).Count)"
    } else { Write-Warning 'opensam.xml is missing from the selected package.' }
    if (Test-Path -LiteralPath $aptPath) {
        $aptLines = [IO.File]::ReadAllLines($aptPath)
        Write-Host "Native jetways in package: $(@($aptLines | Where-Object { $_ -match '^1500 ' }).Count)"
    } else { Write-Warning 'apt.dat is missing from the selected package.' }
}
$library = Join-Path $simPath 'Custom Scenery\openSAM_Library\library.txt'
Write-Host "openSAM_Library installed: $(Test-Path -LiteralPath $library)"
$logPath = Join-Path $simPath 'Log.txt'
if (Test-Path -LiteralPath $logPath) {
    $logLines = [IO.File]::ReadAllLines($logPath)
    $loadedXml = @($logLines | Where-Object { $_ -match '(?i)opensam:.*(?:Processing.*(?:NRT_KIAH|KIAH_NRT).*sam\.xml|Parsing (?:open)?sam\.xml from.*(?:NRT_KIAH|KIAH_NRT))' })
    $loadedApt = @($logLines | Where-Object { $_ -match '(?i)opensam:.*(NRT_KIAH|KIAH_NRT).*apt\.dat' })
    Write-Host "Last Log.txt timestamp: $((Get-Item -LiteralPath $logPath).LastWriteTime)"
    Write-Host "OpenSAM NRT XML load evidence: $($loadedXml.Count -gt 0)"
    Write-Host "OpenSAM NRT apt.dat load evidence: $($loadedApt.Count -gt 0)"
    foreach ($line in $loadedXml + $loadedApt) { Write-Host $line }
    if (-not $loadedXml.Count -or -not $loadedApt.Count) {
        Write-Warning 'This log does not confirm NRT discovery by OpenSAM. Fully exit and relaunch X-Plane with the scenery entry already present, load KIAH, then run this checker again. An old log is not evidence about a newly installed revision.'
    }
} else { Write-Host 'No Log.txt yet. Load KIAH once, exit X-Plane, then run this checker.' }
Write-Host 'At KIAH, view the hangars before checking their Close controls. OpenSAM activates custom controls when their animated objects are drawn.'
Write-Host 'For a ground-only DGS test, enable the aircraft beacon and use the OpenSAM Activate command or select NRT CANOPY in its stand menu.'
Write-Host 'No files or plugin settings were changed.'
