#!/usr/bin/env bash
# Fairytail installer (macOS / Linux)
# Usage:
#   ./install.sh                # interactive
#   ./install.sh --scope global # install to ~/.claude
#   ./install.sh --scope project
#   ./install.sh --force        # overwrite without prompting

set -euo pipefail

SCOPE=""
FORCE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope) SCOPE="$2"; shift 2;;
    --scope=*) SCOPE="${1#*=}"; shift;;
    --force) FORCE=1; shift;;
    -h|--help)
      echo "Usage: $0 [--scope global|project] [--force]"
      exit 0;;
    *) echo "unknown arg: $1"; exit 1;;
  esac
done

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "fairytail | source: $REPO_ROOT"

if [[ -z "$SCOPE" ]]; then
  echo ""
  echo "Install scope:"
  echo "  [1] global   ~/.claude/         (all projects)"
  echo "  [2] project  ./.claude/         (current directory only)"
  read -r -p "Choice [1-2]: " choice
  case "$choice" in
    1) SCOPE="global";;
    2) SCOPE="project";;
    *) echo "invalid choice"; exit 1;;
  esac
fi

if [[ "$SCOPE" == "global" ]]; then
  TARGET="$HOME/.claude"
elif [[ "$SCOPE" == "project" ]]; then
  TARGET="$(pwd)/.claude"
else
  echo "invalid --scope: $SCOPE (global|project)"
  exit 1
fi
echo "target: $TARGET"

mkdir -p "$TARGET/skills/fairytail" "$TARGET/workflows" "$TARGET/fairytail"

copy_guarded() {
  local src="$1"
  local dst="$2"
  if [[ -f "$dst" && $FORCE -eq 0 ]]; then
    read -r -p "exists: $dst — overwrite? [y/N]: " ans
    if [[ "$ans" != "y" && "$ans" != "Y" ]]; then
      echo "skip $dst"
      return
    fi
  fi
  cp -f "$src" "$dst"
  echo "wrote $dst"
}

copy_guarded "$REPO_ROOT/skills/fairytail/SKILL.md"    "$TARGET/skills/fairytail/SKILL.md"
copy_guarded "$REPO_ROOT/workflows/fairytail.js"       "$TARGET/workflows/fairytail.js"
copy_guarded "$REPO_ROOT/assets/fairytail-ascii.txt"   "$TARGET/fairytail/fairytail-ascii.txt"

CONFIG_TARGET="$TARGET/fairytail.config.json"
if [[ -f "$CONFIG_TARGET" && $FORCE -eq 0 ]]; then
  echo "config exists at $CONFIG_TARGET — preserving (use --force to overwrite)"
else
  cp -f "$REPO_ROOT/config/fairytail.config.json" "$CONFIG_TARGET"
  echo "wrote $CONFIG_TARGET"
fi

echo ""
echo "install complete."
echo "usage:"
echo "  /fairytail <task>"
echo "  /fairytail --leader=fable <task>"
echo "  /fairytail --workers=haiku --summary=sonnet <task>"
echo ""
echo "config: $CONFIG_TARGET"
echo "note: workflow tool requires opt-in. First run may prompt for permission."
