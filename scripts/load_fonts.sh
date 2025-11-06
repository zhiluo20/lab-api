#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 /path/to/fonts/*.ttf"
  exit 1
fi

TARGET_DIR="$(dirname "$0")/fonts"
mkdir -p "$TARGET_DIR"

for font in "$@"; do
  if [[ -f "$font" ]]; then
    cp "$font" "$TARGET_DIR"
    echo "Copied $(basename "$font") to $TARGET_DIR"
  else
    echo "Skipping missing font: $font"
  fi
done

if command -v docker &>/dev/null; then
  echo "Remember to run 'docker compose restart onlyoffice-d' to reload fonts."
fi
