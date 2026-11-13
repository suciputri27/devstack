#!/usr/bin/env bash
set -euo pipefail
. /etc/os-release
containerd_ver="1.7.28-1~ubuntu.${VERSION_ID}~${VERSION_CODENAME}"
export DEBIAN_FRONTEND=noninteractive

if ! apt-cache madison containerd.io | awk '{print $3}' | grep -qx "$containerd_ver"; then
  echo "containerd.io $containerd_ver tidak tersedia di repo Docker untuk Ubuntu ${VERSION_ID}." >&2
  exit 1
fi

docker_ver=""
for v in $(apt-cache madison docker-ce | awk '{print $3}'); do
  req=$(apt-cache show "docker-ce=$v" | sed -n 's/.*containerd.io (>= \([^)]*\)).*/\1/p' | head -1)
  if [ -n "$req" ] && dpkg --compare-versions "$containerd_ver" ge "$req"; then
    docker_ver="$v"
    break
  fi
done
if [ -z "$docker_ver" ]; then
  echo "Tidak ada versi docker-ce yang cocok dengan containerd.io $containerd_ver." >&2
  exit 1
fi

installed() { dpkg-query -W -f='${Status} ${Version}' "$1" 2>/dev/null || true; }
if [ "$(installed containerd.io)" = "install ok installed $containerd_ver" ] &&
   [ "$(installed docker-ce)" = "install ok installed $docker_ver" ] &&
   [ "$(installed docker-ce-cli)" = "install ok installed $docker_ver" ]; then
  echo "UNCHANGED containerd.io=$containerd_ver docker-ce=$docker_ver"
  exit 0
fi

apt-mark unhold containerd.io docker-ce docker-ce-cli docker-ce-rootless-extras >/dev/null 2>&1 || true
apt-get install -y -q --allow-downgrades \
  "containerd.io=$containerd_ver" \
  "docker-ce=$docker_ver" \
  "docker-ce-cli=$docker_ver" \
  "docker-ce-rootless-extras=$docker_ver" \
  docker-buildx-plugin docker-compose-plugin
apt-mark hold containerd.io docker-ce docker-ce-cli docker-ce-rootless-extras >/dev/null
echo "CHANGED containerd.io=$containerd_ver docker-ce=$docker_ver"
