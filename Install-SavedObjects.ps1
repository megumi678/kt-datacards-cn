$ErrorActionPreference = 'Stop'
$documents = [Environment]::GetFolderPath('MyDocuments')
if (-not $documents) { throw 'Windows Documents folder was not found.' }
$target = Join-Path $documents 'My Games\Tabletop Simulator\Saves\Saved Objects\KT Chinese GitHub'
New-Item -ItemType Directory -Path $target -Force | Out-Null
Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot 'SavedObjects') -Filter '*.json' -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $target $_.Name) -Force
}
Write-Host "Installed into: $target"
