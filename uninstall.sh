#!/usr/bin/env bash
# Fairytail uninstaller (macOS / Linux)
# Usage:
#   ./uninstall.sh --scope global
#   ./uninstall.sh --scope project
#   ./uninstall.sh --keep-config

set -euo pipefail

SCOPE=""
KEEP_CONFIG=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scope) SCOPE="$2"; shift 2;;
    --scope=*) SCOPE="${1#*=}"; shift;;
    --keep-config) KEEP_CONFIG=1; shift;;
    -h|--help) echo "Usage: $0 [--scope global|project] [--keep-config]"; exit 0;;
    *) echo "unknown arg: $1"; exit 1;;
  esac
done

if [[ -z "$SCOPE" ]]; then
  echo "Uninstall scope:"
  echo "  [1] global   ~/.claude/"
  echo "  [2] project  ./.claude/"
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
  echo "invalid --scope: $SCOPE"; exit 1
fi

echo "target: $TARGET"

FILES=(
  "$TARGET/skills/fairytail/SKILL.md"
  "$TARGET/workflows/fairytail.js"
  "$TARGET/fairytail/fairytail-ascii.txt"
  "$TARGET/fairytail/.banner_shown"
)
if [[ $KEEP_CONFIG -eq 0 ]]; then
  FILES+=("$TARGET/fairytail.config.json")
else
  echo "keep config: $TARGET/fairytail.config.json"
fi

for f in "${FILES[@]}"; do
  if [[ -f "$f" ]]; then
    rm -f "$f"
    echo "removed $f"
  else
    echo "absent  $f"
  fi
done

for d in "$TARGET/skills/fairytail" "$TARGET/fairytail"; do
  if [[ -d "$d" ]] && [[ -z "$(ls -A "$d" 2>/dev/null)" ]]; then
    rmdir "$d"
    echo "removed empty dir $d"
  fi
done

echo ""
echo "uninstall complete."
