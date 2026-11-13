#!/usr/bin/env bash
set -euo pipefail
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
fail=0
step() { printf '==> %s\n' "$1"; }

step "Syntax shell"
for f in install.sh get.sh lib/ui.sh bin/devstack bin/devstack-doctor bin/devstack-sync-config scripts/*.sh omp-config/install.sh omp-config/bin/ai-init omp-config/hooks/pre-commit brain/bin/taste brain/bin/devstack-audit brain/bin/lessons client/setup-laptop.sh; do
  bash -n "$f" || { echo "  gagal: $f"; fail=1; }
done

step "Syntax Python"
python3 -m py_compile brain/bin/devstack-verify brain/*/tools/*.py ansible/callback_plugins/devstack.py || fail=1
find . -name __pycache__ -type d -prune -exec rm -rf {} +

step "YAML dan JSON"
python3 - <<'PY' || fail=1
import glob, json, yaml
for f in glob.glob("ansible/**/*.yml", recursive=True) + glob.glob("brain/audit/semgrep/*.yml") + glob.glob(".github/workflows/*.yml") + ["omp-config/agent/config.yml"]:
    yaml.safe_load(open(f, encoding="utf-8"))
for f in ["omp-config/agent/mcp.json", "brain/taste-pack/presets/manifest.json"]:
    json.load(open(f, encoding="utf-8"))
PY

step "Em dash dan en dash"
if LC_ALL=C grep -rnI $'\xe2\x80[\x93\x94]' --exclude-dir=.git --exclude-dir=fonts . ; then fail=1; fi

step "Line ending Unix"
if grep -rlI $'\r' --exclude-dir=.git . ; then echo "  file di atas memakai CRLF"; fail=1; fi

step "Bit eksekusi"
for f in install.sh get.sh bin/* scripts/*.sh omp-config/install.sh omp-config/bin/ai-init omp-config/hooks/pre-commit brain/bin/*; do
  [ -x "$f" ] || { echo "  tidak executable: $f"; fail=1; }
done

step "Kontras preset taste"
python3 brain/taste-pack/tools/contrast.py >/dev/null || fail=1

if command -v semgrep >/dev/null; then
  step "Aturan keamanan menangkap contoh rentan"
  php=$(semgrep --config brain/audit/semgrep --metrics=off --json --quiet brain/audit/fixtures/vulnerable | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["results"]))')
  node=$(semgrep --config brain/audit/semgrep --metrics=off --json --quiet brain/audit/fixtures/vulnerable-node | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["results"]))')
  echo "  PHP $php temuan (minimal 20), Node $node temuan (minimal 12)"
  [ "$php" -ge 20 ] && [ "$node" -ge 12 ] || fail=1
fi

if command -v ansible-playbook >/dev/null; then
  step "Syntax playbook"
  (cd ansible && ANSIBLE_CONFIG=ansible.cfg ansible-playbook site.yml --syntax-check >/dev/null) || fail=1
fi

[ "$fail" -eq 0 ] && echo "Semua pemeriksaan lulus." || { echo "Ada pemeriksaan yang gagal."; exit 1; }
