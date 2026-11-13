#!/usr/bin/env bash
set -euo pipefail
v="$1"
apt-get install -y -q --reinstall -o Dpkg::Options::="--force-confmiss" "php${v}-common" >/dev/null
mods="/etc/php/${v}/mods-available"
for entry in pdo:10 phar:20 calendar:20 ctype:20 exif:20 fileinfo:20 ffi:20 ftp:20 gettext:20 iconv:20 posix:20 shmop:20 sockets:20 sysvmsg:20 sysvsem:20 sysvshm:20 tokenizer:20; do
  name="${entry%%:*}"
  prio="${entry##*:}"
  [ -f "${mods}/${name}.ini" ] || printf '; configuration for php %s module\n; priority=%s\nextension=%s.so\n' "$name" "$prio" "$name" > "${mods}/${name}.ini"
done
for ini in /etc/php/"${v}"/*/php.ini; do
  [ -f "$ini" ] || continue
  if grep -qE '^[[:space:]]*extension[[:space:]]*=[[:space:]]*"?(pdo|pdo_mysql|pdo_sqlite|pdo_pgsql|phar)(\.so)?"?[[:space:]]*$' "$ini"; then
    cp -n "$ini" "${ini}.devstack.bak"
    sed -i -E 's/^[[:space:]]*extension[[:space:]]*=[[:space:]]*"?(pdo|pdo_mysql|pdo_sqlite|pdo_pgsql|phar)(\.so)?"?[[:space:]]*$/;&/' "$ini"
  fi
done
phpenmod -v "$v" pdo phar calendar ctype exif fileinfo ffi ftp gettext iconv posix shmop sockets sysvmsg sysvsem sysvshm tokenizer
