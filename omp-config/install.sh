#!/usr/bin/env bash
set -euo pipefail
src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/agent"
dst="$HOME/.omp/agent"
mkdir -p "$dst"
for item in AGENTS.md BACKEND.md config.yml models.yml mcp.json skills agents; do
  [ -e "$src/$item" ] || { echo "Lewati $item (tidak ada di $src)"; continue; }
  if [ -L "$dst/$item" ] && [ "$(readlink "$dst/$item")" = "$src/$item" ]; then
    continue
  fi
  if [ -e "$dst/$item" ] && [ ! -L "$dst/$item" ]; then
    mv "$dst/$item" "$dst/$item.bak.$(date +%s)"
  fi
  ln -sfn "$src/$item" "$dst/$item"
  echo "Linked $item"
done
