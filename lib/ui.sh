# shellcheck shell=bash
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ] && [ "${TERM:-dumb}" != "dumb" ]; then
  UI_TTY=1
  C_RESET=$'\033[0m'; C_BOLD=$'\033[1m'; C_DIM=$'\033[2m'
  C_GREEN=$'\033[32m'; C_RED=$'\033[31m'; C_YELLOW=$'\033[33m'; C_CYAN=$'\033[36m'
else
  UI_TTY=0
  C_RESET=""; C_BOLD=""; C_DIM=""; C_GREEN=""; C_RED=""; C_YELLOW=""; C_CYAN=""
fi
if [ "$(locale charmap 2>/dev/null)" = "UTF-8" ]; then
  S_OK="✓"; S_FAIL="✗"; S_WARN="!"; S_DOT="·"; S_ARROW="›"
  S_SPIN=(⠋ ⠙ ⠹ ⠸ ⠼ ⠴ ⠦ ⠧ ⠇ ⠏)
else
  S_OK="ok"; S_FAIL="x"; S_WARN="!"; S_DOT="-"; S_ARROW=">"
  S_SPIN=('|' '/' '-' '\')
fi

ui_banner() {
  local version="$1" subtitle="$2"
  printf '\n  %sdevstack%s %s%s%s  %s %s\n' "$C_BOLD" "$C_RESET" "$C_CYAN" "$version" "$C_RESET" "$S_DOT" "$subtitle"
  printf '  %s%s%s\n\n' "$C_DIM" "────────────────────────────────────────────────" "$C_RESET"
}
ui_kv() { printf '  %s%-8s%s %s\n' "$C_DIM" "$1" "$C_RESET" "$2"; }
ui_ok() { printf '  %s%s%s %s\n' "$C_GREEN" "$S_OK" "$C_RESET" "$*"; }
ui_warn() { printf '  %s%s%s %s\n' "$C_YELLOW" "$S_WARN" "$C_RESET" "$*"; }
ui_fail() { printf '  %s%s%s %s\n' "$C_RED" "$S_FAIL" "$C_RESET" "$*" >&2; }
ui_info() { printf '  %s%s%s %s\n' "$C_CYAN" "$S_ARROW" "$C_RESET" "$*"; }
ui_title() { printf '\n  %s%s%s\n' "$C_BOLD" "$*" "$C_RESET"; }
ui_die() { ui_fail "$*"; exit 1; }

ui_duration() {
  local s="$1"
  if [ "$s" -ge 60 ]; then printf '%dm%02ds' $((s / 60)) $((s % 60)); else printf '%ds' "$s"; fi
}

ui_run() {
  local label="$1" log="$2"; shift 2
  local start=$SECONDS
  if [ "$UI_TTY" -eq 1 ]; then
    "$@" >>"$log" 2>&1 &
    local pid=$! i=0
    while kill -0 "$pid" 2>/dev/null; do
      printf '\r  %s%s%s %s' "$C_CYAN" "${S_SPIN[i % ${#S_SPIN[@]}]}" "$C_RESET" "$label"
      i=$((i + 1))
      sleep 0.1
    done
    wait "$pid"
    local rc=$?
  else
    "$@" >>"$log" 2>&1
    local rc=$?
  fi
  local took
  took=$(ui_duration $((SECONDS - start)))
  if [ "$rc" -eq 0 ]; then
    [ "$UI_TTY" -eq 1 ] && printf '\r\033[K'
    printf '  %s%s%s %-34s %s%s%s\n' "$C_GREEN" "$S_OK" "$C_RESET" "$label" "$C_DIM" "$took" "$C_RESET"
  else
    [ "$UI_TTY" -eq 1 ] && printf '\r\033[K'
    printf '  %s%s%s %-34s %s%s%s\n' "$C_RED" "$S_FAIL" "$C_RESET" "$label" "$C_DIM" "$took" "$C_RESET"
  fi
  return "$rc"
}

ui_ask() {
  local var="$1" prompt="$2" default="${3:-}" answer
  if [ -n "$default" ]; then
    printf '  %s?%s %s %s[%s]%s ' "$C_CYAN" "$C_RESET" "$prompt" "$C_DIM" "$default" "$C_RESET"
  else
    printf '  %s?%s %s ' "$C_CYAN" "$C_RESET" "$prompt"
  fi
  IFS= read -r answer || { printf '\n'; ui_die "Input berakhir, setup dibatalkan."; }
  printf -v "$var" '%s' "${answer:-$default}"
}

ui_secret() {
  local var="$1" prompt="$2" answer
  printf '  %s?%s %s ' "$C_CYAN" "$C_RESET" "$prompt"
  IFS= read -rs answer || { printf '\n'; ui_die "Input berakhir, setup dibatalkan."; }
  printf '\n'
  printf -v "$var" '%s' "$answer"
}

ui_confirm() {
  local prompt="$1" default="${2:-y}" answer hint="[Y/n]"
  [ "$default" = "n" ] && hint="[y/N]"
  printf '  %s?%s %s %s%s%s ' "$C_CYAN" "$C_RESET" "$prompt" "$C_DIM" "$hint" "$C_RESET"
  IFS= read -r answer || { printf '\n'; return 1; }
  answer="${answer:-$default}"
  [[ "$answer" =~ ^[yY] ]]
}
