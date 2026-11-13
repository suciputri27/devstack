#!/usr/bin/env bash
set -euo pipefail

REPO="${DEVSTACK_REPO:-https://github.com/suciputri27/devstack.git}"
DEST="${DEVSTACK_SRC:-/opt/devstack/src}"
REF="${DEVSTACK_REF:-}"

[ "$(id -u)" -eq 0 ] || { echo "Jalankan dengan sudo: curl -fsSL <url>/get.sh | sudo bash"; exit 1; }
command -v git >/dev/null || { apt-get update -qq && apt-get install -y -qq git ca-certificates >/dev/null; }

if [ -d "$DEST/.git" ]; then
  git -C "$DEST" fetch -q --tags origin
else
  mkdir -p "$(dirname "$DEST")"
  git clone -q "$REPO" "$DEST"
fi
if [ -z "$REF" ]; then
  REF=$(git -C "$DEST" tag -l 'v[0-9]*' --sort=-v:refname | head -n 1)
fi
[ -n "$REF" ] || { echo "Repo belum punya rilis (tag v*)."; exit 1; }
git -C "$DEST" -c advice.detachedHead=false checkout -q "$REF"
echo "devstack $REF dari $REPO"

if (exec </dev/tty) 2>/dev/null; then
  exec "$DEST/install.sh" "$@" </dev/tty
else
  exec "$DEST/install.sh" "$@"
fi
