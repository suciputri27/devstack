#!/usr/bin/env bash
set -uo pipefail

DEVSTACK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/ui.sh
. "$DEVSTACK_DIR/lib/ui.sh"

ENV_DIR=/etc/devstack
ENV_FILE="${DEVSTACK_ENV:-$ENV_DIR/devstack.env}"
LOG_DIR=/var/log/devstack
DS_VERSION="$(cat "$DEVSTACK_DIR/VERSION" 2>/dev/null || echo "?")"
verbose=false
assume_yes=false
ansible_args=()
for arg in "$@"; do
  case "$arg" in
    --verbose|-v) verbose=true ;;
    --yes|-y) assume_yes=true ;;
    *) ansible_args+=("$arg") ;;
  esac
done

[ "$(id -u)" -eq 0 ] || ui_die "Jalankan dengan sudo: sudo ./install.sh"

. /etc/os-release
virt="$(systemd-detect-virt 2>/dev/null || echo unknown)"
ui_banner "$DS_VERSION" "server agentic coding"
ui_kv "Host" "$(hostname) $S_DOT ${PRETTY_NAME:-?} $S_DOT ${virt}"
case "${VERSION_ID:-}" in
  22.04|24.04) ;;
  *) ui_die "Butuh Ubuntu 22.04 atau 24.04. Terdeteksi: ${PRETTY_NAME:-tidak diketahui}" ;;
esac

install -d -m 0700 "$ENV_DIR"
install -d -m 0750 "$LOG_DIR"
if [ ! -f "$ENV_FILE" ] && [ -f "$DEVSTACK_DIR/.env" ]; then
  install -m 0600 "$DEVSTACK_DIR/.env" "$ENV_FILE"
  ui_ok "Konfigurasi lama dipindah ke $ENV_FILE (aman dari update)"
fi

set_kv() {
  python3 - "$ENV_FILE" "$1" "$2" <<'PY'
import re, shlex, sys
path, key, value = sys.argv[1:4]
text = open(path, encoding="utf-8").read()
line = f"{key}={shlex.quote(value) if value else ''}"
pattern = re.compile(rf"^{re.escape(key)}=.*$", re.M)
text = pattern.sub(lambda m: line, text, count=1) if pattern.search(text) else text.rstrip("\n") + "\n" + line + "\n"
open(path, "w", encoding="utf-8").write(text)
PY
}

valid_ip() { python3 -c 'import ipaddress,sys; ipaddress.ip_address(sys.argv[1])' "$1" 2>/dev/null; }
valid_nets() { [ -n "$1" ] && python3 -c 'import ipaddress,sys; [ipaddress.ip_network(n, strict=False) for n in sys.argv[1:]]' $1 2>/dev/null; }

network_of() {
  python3 -c 'import ipaddress,sys; print(ipaddress.ip_network(sys.argv[1], strict=False))' "$1" 2>/dev/null
}

wizard() {
  ui_title "Setup awal"
  printf '  %sJawab beberapa pertanyaan. Tekan Enter untuk memakai nilai di dalam kurung.%s\n\n' "$C_DIM" "$C_RESET"
  local ip cidr subnet client client_net vpn user password password2 pubkey_default pubkey git_name git_email sudo_home
  ip=$(ip -4 route get 1.1.1.1 2>/dev/null | awk '{for (i = 1; i <= NF; i++) if ($i == "src") print $(i + 1)}')
  cidr=$(ip -o -4 addr show 2>/dev/null | awk -v ip="$ip" '{split($4, a, "/"); if (a[1] == ip) print $4}' | head -n 1)
  subnet=$(network_of "${cidr:-$ip/24}")
  client=$(who -m 2>/dev/null | sed -n 's/.*(\([0-9.]*\)).*/\1/p')

  while true; do
    ui_ask ip "IP server ini di jaringan kantor" "$ip"
    valid_ip "$ip" && break
    ui_warn "Bukan alamat IP yang valid. Cek dengan: ip -4 addr"
    ip=""
  done
  [ -n "$subnet" ] || subnet=$(network_of "$ip/24")
  while true; do
    ui_ask subnet "Subnet yang boleh mengakses (LAN kantor)" "$subnet"
    valid_nets "$subnet" && break
    ui_warn "Format subnet salah, contoh: 192.168.1.0/24"
    subnet=""
  done
  vpn=""
  if [ -n "$client" ] && ! python3 -c 'import ipaddress,sys; sys.exit(0 if ipaddress.ip_address(sys.argv[1]) in ipaddress.ip_network(sys.argv[2], strict=False) else 1)' "$client" "$subnet" 2>/dev/null; then
    client_net=$(network_of "$client/24")
    ui_warn "Sesi SSH Anda datang dari $client, di luar $subnet (kemungkinan VPN)."
    ui_ask vpn "Subnet VPN yang juga diizinkan" "$client_net"
  else
    ui_ask vpn "Subnet VPN kantor jika berbeda (kosongkan jika tidak ada)" ""
  fi
  while [ -n "$vpn" ] && ! valid_nets "$vpn"; do
    ui_warn "Format subnet salah, contoh: 10.10.0.0/24"
    ui_ask vpn "Subnet VPN (kosongkan jika tidak ada)" ""
  done

  ui_ask user "Nama user kerja" "dev"
  if id -u "$user" >/dev/null 2>&1; then
    ui_info "User $user sudah ada, password tidak diubah."
    password=""
  else
    while true; do
      ui_secret password "Password sudo untuk $user (minimal 12 karakter)"
      ui_secret password2 "Ulangi password"
      if [ "${#password}" -lt 12 ]; then ui_warn "Terlalu pendek."; elif [ "$password" != "$password2" ]; then ui_warn "Tidak sama."; else break; fi
    done
  fi

  sudo_home=$(getent passwd "${SUDO_USER:-root}" | cut -d: -f6)
  pubkey_default=$(grep -hE '^(ssh-(ed25519|rsa)|ecdsa-sha2-|sk-)' "$sudo_home/.ssh/authorized_keys" "/home/$user/.ssh/authorized_keys" 2>/dev/null | head -n 1)
  if [ -n "$pubkey_default" ]; then
    ui_info "Ditemukan key yang sudah dipakai login: $(printf '%s' "$pubkey_default" | ssh-keygen -lf - 2>/dev/null | awk '{print $2, $3}')"
    if ui_confirm "Pakai key ini untuk user $user?" y; then
      pubkey="$pubkey_default"
    fi
  fi
  while [ -z "${pubkey:-}" ] || ! [[ "$pubkey" =~ ^(ssh-(ed25519|rsa)|ecdsa-sha2-|sk-) ]]; do
    ui_ask pubkey "Tempel public key laptop (isi file ~/.ssh/id_ed25519.pub)" ""
  done

  git_name=$(sudo -u "${SUDO_USER:-root}" git config --global user.name 2>/dev/null || true)
  git_email=$(sudo -u "${SUDO_USER:-root}" git config --global user.email 2>/dev/null || true)
  ui_ask git_name "Nama untuk commit Git" "$git_name"
  ui_ask git_email "Email untuk commit Git" "$git_email"

  install -m 0600 "$DEVSTACK_DIR/.env.example" "$ENV_FILE"
  set_kv SERVER_IP "$ip"
  set_kv ALLOWED_SUBNETS "$(printf '%s %s' "$subnet" "$vpn" | xargs)"
  set_kv DEVSTACK_USER "$user"
  set_kv DEVSTACK_USER_PASSWORD "$password"
  set_kv DEVSTACK_SSH_PUBKEY "$pubkey"
  set_kv GIT_NAME "$git_name"
  set_kv GIT_EMAIL "$git_email"
  unset password password2

  ui_title "Ringkasan"
  ui_kv "IP" "$ip"
  ui_kv "Akses" "$(printf '%s %s' "$subnet" "$vpn" | xargs)"
  ui_kv "User" "$user"
  ui_kv "Git" "$git_name <$git_email>"
  ui_kv "Config" "$ENV_FILE"
  printf '  %sNilai lain (tim, token, port) bisa diubah nanti: sudo devstack config%s\n\n' "$C_DIM" "$C_RESET"
  ui_confirm "Lanjut install?" y || { ui_info "Dibatalkan. Konfigurasi tersimpan, jalankan lagi kapan saja."; exit 0; }
}

if [ ! -f "$ENV_FILE" ]; then
  if [ -t 0 ] && ! $assume_yes; then
    wizard
  else
    install -m 0600 "$DEVSTACK_DIR/.env.example" "$ENV_FILE"
    ui_info "Konfigurasi dibuat di $ENV_FILE. Isi nilainya, lalu jalankan lagi: sudo ./install.sh"
    exit 0
  fi
fi
chmod 600 "$ENV_FILE"

if grep -qE "^(DEVSTACK_SSH_PUBKEY|SERVER_IP|ALLOWED_SUBNETS)=(\"\"|'')?$" "$ENV_FILE"; then
  ui_die "DEVSTACK_SSH_PUBKEY, SERVER_IP, dan ALLOWED_SUBNETS di $ENV_FILE wajib diisi (sudo devstack config)."
fi

LOG_FILE="$LOG_DIR/install-$(date +%Y%m%d-%H%M%S).log"
ln -sfn "$LOG_FILE" "$LOG_DIR/latest.log"
ui_kv "Config" "$ENV_FILE"
ui_kv "Log" "$LOG_FILE"
printf '\n'

export DEBIAN_FRONTEND=noninteractive
bootstrap() {
  apt-get update -qq &&
  apt-get install -y -qq ansible acl python3 python3-passlib git curl ca-certificates iproute2
}
ui_run "Menyiapkan installer" "$LOG_FILE" bootstrap || ui_die "Gagal memasang Ansible. Lihat: sudo devstack logs"

set -a
. "$DEVSTACK_DIR/versions.env"
# shellcheck disable=SC1090
. "$ENV_FILE"
set +a
export DEVSTACK_ENV_FILE="$ENV_FILE" DEVSTACK_LOG="$LOG_FILE"

cd "$DEVSTACK_DIR/ansible" || exit 1
export ANSIBLE_CONFIG="$DEVSTACK_DIR/ansible/ansible.cfg"
if $verbose; then
  ANSIBLE_STDOUT_CALLBACK=default ansible-playbook site.yml "${ansible_args[@]}" 2>&1 | tee -a "$LOG_FILE"
  rc=${PIPESTATUS[0]}
else
  ansible-playbook site.yml "${ansible_args[@]}"
  rc=$?
fi
if [ "$rc" -eq 0 ] && grep -qE '^DEVSTACK_USER_PASSWORD=.+' "$ENV_FILE"; then
  set_kv DEVSTACK_USER_PASSWORD ""
  ui_info "Password sudo dihapus dari $ENV_FILE (hanya dibutuhkan saat membuat user)."
fi
exit "$rc"
