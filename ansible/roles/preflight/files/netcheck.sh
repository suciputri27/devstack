#!/usr/bin/env bash
urls=(
  https://ppa.launchpadcontent.net/ondrej/php/ubuntu/
  https://deb.nodesource.com/
  https://download.docker.com/linux/ubuntu/
  https://cli.github.com/packages/
  https://getcomposer.org/installer
  https://composer.github.io/installer.sig
  https://bun.sh/install
  https://astral.sh/uv/install.sh
  https://registry.npmjs.org/
  https://registry-1.docker.io/v2/
  https://github.com/
  https://objects.githubusercontent.com/
)
if ! grep -rqs "ppa.launchpadcontent.net/ondrej/php" /etc/apt/sources.list /etc/apt/sources.list.d/; then
  urls+=("https://keyserver.ubuntu.com/")
fi

blocked=0
for url in "${urls[@]}"; do
  code=$(curl -4 -s -o /dev/null -m 10 -w '%{http_code}' "$url")
  if [ "$code" = "000" ]; then
    echo "  - $url"
    blocked=1
  fi
done
exit "$blocked"
