# Fairytail uninstaller (Windows / PowerShell 7+)
# Usage:
#   .\uninstall.ps1 -Scope global      # remove from ~/.claude
#   .\uninstall.ps1 -Scope project     # remove from ./.claude
#   .\uninstall.ps1 -KeepConfig        # keep fairytail.config.json

param(
  [ValidateSet('global', 'project', '')]
  [string]$Scope = '',
  [switch]$KeepConfig
)

$ErrorActionPreference = 'Stop'

if (-not $Scope) {
  Write-Host "Uninstall scope:"
  Write-Host "  [1] global   ~/.claude/"
  Write-Host "  [2] project  ./.claude/"
  $choice = Read-Host "Choice [1-2]"
  switch ($choice) {
    '1' { $Scope = 'global' }
    '2' { $Scope = 'project' }
    default { Write-Error "invalid choice"; exit 1 }
  }
}

if ($Scope -eq 'global') {
  $target = Join-Path $HOME '.claude'
} else {
  $target = Join-Path (Get-Location) '.claude'
}
Write-Host "target: $target"

$files = @(
  (Join-Path $target 'skills\fairytail\SKILL.md'),
  (Join-Path $target 'workflows\fairytail.js'),
  (Join-Path $target 'fairytail\fairytail-ascii.txt'),
  (Join-Path $target 'fairytail\.banner_shown')
)
if (-not $KeepConfig) {
  $files += (Join-Path $target 'fairytail.config.json')
} else {
  Write-Host "keep config: $(Join-Path $target 'fairytail.config.json')"
}

foreach ($f in $files) {
  if (Test-Path $f) {
    Remove-Item -Path $f -Force
    Write-Host "removed $f"
  } else {
    Write-Host "absent  $f"
  }
}

foreach ($emptyCand in @((Join-Path $target 'skills\fairytail'), (Join-Path $target 'fairytail'))) {
  if ((Test-Path $emptyCand) -and -not (Get-ChildItem -Path $emptyCand -Force -ErrorAction SilentlyContinue)) {
    Remove-Item -Path $emptyCand -Force
    Write-Host "removed empty dir $emptyCand"
  }
}

Write-Host ""
Write-Host "uninstall complete."
