$ErrorActionPreference = 'Stop'

$GitleaksVersion = '8.30.1'
$ArchiveName = "gitleaks_${GitleaksVersion}_windows_x64.zip"
$ExpectedSha256 = 'D29144DEFF3A68AA93CED33DDDF84B7FDC26070ADD4AA0F4513094C8332AFC4E'
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$WorkspaceRoot = [System.IO.Path]::GetFullPath((Join-Path $RepositoryRoot 'workspace'))
$InstallDirectory = [System.IO.Path]::GetFullPath(
    (Join-Path $WorkspaceRoot 'tools\gitleaks')
)

if (-not $InstallDirectory.StartsWith(
    $WorkspaceRoot + [System.IO.Path]::DirectorySeparatorChar,
    [System.StringComparison]::OrdinalIgnoreCase
)) {
    throw 'Resolved Gitleaks directory escaped the ignored workspace directory.'
}

New-Item -ItemType Directory -Force -Path $InstallDirectory | Out-Null
$ArchivePath = Join-Path $InstallDirectory $ArchiveName
$DownloadUrl = (
    "https://github.com/gitleaks/gitleaks/releases/download/" +
    "v${GitleaksVersion}/${ArchiveName}"
)

if (-not (Test-Path -LiteralPath $ArchivePath)) {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ArchivePath
}

$ActualSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $ArchivePath).Hash
if ($ActualSha256 -ne $ExpectedSha256) {
    throw 'The downloaded Gitleaks archive did not match the pinned SHA-256 checksum.'
}

$ExecutablePath = Join-Path $InstallDirectory 'gitleaks.exe'
if (-not (Test-Path -LiteralPath $ExecutablePath)) {
    Expand-Archive -LiteralPath $ArchivePath -DestinationPath $InstallDirectory
}

& $ExecutablePath version
