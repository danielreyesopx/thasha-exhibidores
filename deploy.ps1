# Single source of truth for Netlify deploys.
# Creates a clean staging dir, deploys, cleans up.
# Usage:  .\deploy.ps1          (production)    .\deploy.ps1 -Draft  (draft/preview)

param(
    [switch]$Draft
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$Staging = Join-Path $ProjectRoot "_deploy"

# Files/dirs that make up the actual website.
# NOTE: the catalog references the "- sin precio" (price-removed) image folders,
# so those are what ship — not the original with-price folders.
$DeployItems = @(
    "index.html",
    "catalogo.html",
    "Exhibidores de joyeria fina - sin precio",
    "Exhibidores de joyeria negro - sin precio",
    "Exhibidores de joyeria gris - sin precio",
    "Exhibidores de Yute - sin precio"
)

Write-Host "Building staging dir: $Staging" -ForegroundColor Cyan
if (Test-Path $Staging) { Remove-Item $Staging -Recurse -Force }
New-Item -ItemType Directory -Path $Staging -Force | Out-Null

foreach ($item in $DeployItems) {
    $src = Join-Path $ProjectRoot $item
    if (-not (Test-Path $src)) {
        Write-Host "  MISSING: $item (skipped)" -ForegroundColor Yellow
        continue
    }
    Copy-Item -LiteralPath $src -Destination $Staging -Recurse
    Write-Host "  copied: $item"
}

$count = (Get-ChildItem $Staging -File -Recurse | Measure-Object).Count
Write-Host "Staging complete: $count files" -ForegroundColor Green

$flags = @("--dir", "_deploy", "--no-build")
if ($Draft) {
    Write-Host "Deploying DRAFT..." -ForegroundColor Cyan
} else {
    Write-Host "Deploying PRODUCTION..." -ForegroundColor Cyan
    $flags += "--prod"
}

& ntl deploy @flags
$exitCode = $LASTEXITCODE

Write-Host "Cleaning up staging dir..." -ForegroundColor Cyan
Remove-Item $Staging -Recurse -Force

if ($exitCode -ne 0) { exit $exitCode }
