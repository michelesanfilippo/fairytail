# Fairytail installer (Windows / PowerShell 7+)
# Usage:
#   .\install.ps1                    # interactive, asks scope
#   .\install.ps1 -Scope global      # install to ~/.claude (user global)
#   .\install.ps1 -Scope project     # install to ./.claude (current dir)
#   .\install.ps1 -Force             # overwrite existing files without prompt

param(
  [ValidateSet('global', 'project', '')]
  [string]$Scope = '',
  [switch]$Force
)

$ErrorActionPreference = 'Stop'

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "fairytail | source: $repoRoot"

# ---- pick scope ----
if (-not $Scope) {
  Write-Host ""
  Write-Host "Install scope:"
  Write-Host "  [1] global   ~/.claude/         (all projects)"
  Write-Host "  [2] project  ./.claude/         (current directory only)"
  $choice = Read-Host "Choice [1-2]"
  switch ($choice) {
    '1' { $Scope = 'global' }
    '2' { $Scope = 'project' }
    default { Write-Error "Invalid choice: $choice"; exit 1 }
  }
}

# ---- resolve target ----
if ($Scope -eq 'global') {
  $target = Join-Path $HOME '.claude'
} else {
  $target = Join-Path (Get-Location) '.claude'
}
Write-Host "target: $target"

# ---- ensure target dirs ----
$dirs = @(
  (Join-Path $target 'skills\fairytail'),
  (Join-Path $target 'workflows'),
  (Join-Path $target 'fairytail')
)
foreach ($d in $dirs) {
  if (-not (Test-Path $d)) { New-Item -ItemType Directory -Force -Path $d | Out-Null }
}

# ---- copy operation with overwrite guard ----
function Copy-Guarded {
  param([string]$Src, [string]$Dst)
  if ((Test-Path $Dst) -and -not $Force) {
    $ans = Read-Host "exists: $Dst — overwrite? [y/N]"
    if ($ans -ne 'y' -and $ans -ne 'Y') {
      Write-Host "skip $Dst"
      return
    }
  }
  Copy-Item -Path $Src -Destination $Dst -Force
  Write-Host "wrote $Dst"
}

# ---- payload ----
Copy-Guarded (Join-Path $repoRoot 'skills\fairytail\SKILL.md')           (Join-Path $target 'skills\fairytail\SKILL.md')
Copy-Guarded (Join-Path $repoRoot 'workflows\fairytail.js')              (Join-Path $target 'workflows\fairytail.js')
Copy-Guarded (Join-Path $repoRoot 'assets\fairytail-ascii.txt')          (Join-Path $target 'fairytail\fairytail-ascii.txt')

$configTarget = Join-Path $target 'fairytail.config.json'
if ((Test-Path $configTarget) -and -not $Force) {
  Write-Host "config exists at $configTarget — preserving (use -Force to overwrite)"
} else {
  Copy-Item (Join-Path $repoRoot 'config\fairytail.config.json') $configTarget -Force
  Write-Host "wrote $configTarget"
}

Write-Host ""
Write-Host "install complete."
Write-Host "usage:"
Write-Host "  /fairytail <task>"
Write-Host "  /fairytail --leader=fable <task>"
Write-Host "  /fairytail --workers=haiku --summary=sonnet <task>"
Write-Host ""
Write-Host "config: $configTarget"
Write-Host "note: workflow tool requires opt-in. First run may prompt for permission."
