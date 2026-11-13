#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"
version="${1:-}"
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo "Pakai: scripts/release.sh X.Y.Z"; exit 2; }

branch=$(git rev-parse --abbrev-ref HEAD)
[ "$branch" != "main" ] || { echo "Jangan rilis langsung dari main. Pindah ke develop: git switch develop"; exit 1; }
[ -z "$(git status --porcelain -- . ':!VERSION' ':!CHANGELOG.md')" ] || { echo "Commit atau buang perubahan lain dulu."; git status --short; exit 1; }
git fetch -q --tags origin
git rev-parse -q --verify "refs/tags/v$version" >/dev/null && { echo "Versi $version sudah pernah dirilis."; exit 1; }
current=$(cat VERSION)
[ "$(printf '%s\n%s\n' "$current" "$version" | sort -V | tail -n 1)" = "$version" ] && [ "$current" != "$version" ] || { echo "Versi baru harus lebih besar dari $current."; exit 1; }
head -n 5 CHANGELOG.md | grep -q "^## $version\$" || { echo "Tambahkan bagian '## $version' paling atas di CHANGELOG.md dulu."; exit 1; }

echo "$version" > VERSION
scripts/check.sh
git add VERSION CHANGELOG.md
git commit -q -m "release: v$version"
git push -q -u origin "$branch"
cat <<MSG
Siap dirilis: v$version di branch $branch.
Buka Pull Request $branch ke main di GitHub. Setelah CI hijau dan PR di-merge,
tag v$version dan GitHub Release dibuat otomatis, lalu server melihatnya lewat: devstack update --check
MSG
