#!/usr/bin/env bash
set -euo pipefail

SERVER_IP="${1:-}"
SSH_USER="${2:-dev}"
ALIAS="${DEVSTACK_ALIAS:-devbox}"

if [ -z "$SERVER_IP" ]; then
  echo "Pemakaian: ./setup-laptop.sh <SERVER_IP> [user]"
  echo "Contoh   : ./setup-laptop.sh 192.168.1.50 dev"
  exit 1
fi

step() { printf '\n==> %s\n' "$*"; }

case "$(uname -s)" in
  Darwin) rc="$HOME/.zshrc" ;;
  *) rc="$HOME/.bashrc" ;;
esac
[ -n "${SHELL:-}" ] && [ "$(basename "$SHELL")" = "zsh" ] && rc="$HOME/.zshrc"

step "Alias SSH $ALIAS"
mkdir -p "$HOME/.ssh" && chmod 700 "$HOME/.ssh"
touch "$HOME/.ssh/config" && chmod 600 "$HOME/.ssh/config"
if ! grep -qE "^Host[[:space:]]+$ALIAS\$" "$HOME/.ssh/config"; then
  cat >> "$HOME/.ssh/config" <<EOF

Host $ALIAS
  HostName $SERVER_IP
  User $SSH_USER
  IdentityFile ~/.ssh/id_ed25519
  ServerAliveInterval 30
  ServerAliveCountMax 4
EOF
  echo "Ditambahkan ke ~/.ssh/config"
else
  echo "Sudah ada, dilewati"
fi
ssh -o BatchMode=yes -o ConnectTimeout=8 "$ALIAS" true \
  || { echo "Tidak bisa SSH ke $ALIAS. Pastikan Anda di jaringan kantor atau VPN aktif, dan public key laptop ada di .env server."; exit 1; }

step "Bun dan OMP"
if ! command -v bun >/dev/null && [ ! -x "$HOME/.bun/bin/bun" ]; then
  curl -fsSL https://bun.sh/install | bash
fi
export PATH="$HOME/.bun/bin:$PATH"
command -v omp >/dev/null || bun install -g @oh-my-pi/pi-coding-agent
omp --version || true

step "omp-config dari server"
if [ ! -d "$HOME/omp-config/.git" ]; then
  git clone "$ALIAS:omp-config" "$HOME/omp-config"
else
  echo "$HOME/omp-config sudah ada, dilewati (git pull manual jika perlu)"
fi
"$HOME/omp-config/install.sh"

step "Secret OMP laptop"
envf="$HOME/.omp/agent/.env"
if [ ! -f "$envf" ]; then
  cat > "$envf" <<'EOF'
# Isi key 9Router KHUSUS laptop ini (buat key terpisah di dashboard 9Router).
NINEROUTER_API_KEY=
GITHUB_TOKEN=
GITLAB_TOKEN=
GITLAB_API_URL=https://gitlab.com/api/v4
CONTEXT7_API_KEY=
EOF
fi
chmod 600 "$envf"

step "PATH dan override mesin"
if ! grep -q '# BEGIN devstack' "$rc" 2>/dev/null; then
  cat >> "$rc" <<'EOF'
# BEGIN devstack
export PATH="$HOME/.bun/bin:$HOME/omp-config/bin:$PATH"
export PI_CONFIG_FILES="$HOME/omp-config/machine/laptop.yml"
# END devstack
EOF
fi

cat <<EOF

Selesai. Sisa langkah:
  1. Isi NINEROUTER_API_KEY di $envf
  2. Buka terminal baru, uji: omp -p --model nr/code-main "Reply with exactly: OK"
  3. Pasang Orca dari https://onorca.dev, lalu Settings > SSH > Add Target: $ALIAS > Test
EOF
