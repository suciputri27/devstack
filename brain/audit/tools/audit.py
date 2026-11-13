import argparse
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

AUDIT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"vendor", "node_modules", ".git", "storage", ".taste", "dist", "build", ".ai", ".next"}
TEXT_EXT = {".php", ".js", ".ts", ".vue", ".html", ".env", ".yml", ".yaml", ".json", ".xml", ".ini", ".conf", ".sh", ".py", ".sql", ".md", ".txt"}
SECRETS = [
    ("private key", re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("GitLab token", re.compile(r"\bglpat-[A-Za-z0-9_\-]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Stripe live key", re.compile(r"\b(sk|rk)_live_[0-9A-Za-z]{16,}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b")),
    ("hardcoded credential", re.compile(r"(?i)\b(password|passwd|secret|api_?key|access_?token|client_?secret)\b\s*(=>|=|:)\s*['\"](?!\s*['\"])(?!(env|config)\()[^'\"\s$]{12,}['\"]")),
]
EXPOSURES = [
    ("/.env", re.compile(r"APP_KEY|DB_PASSWORD|DB_HOST")),
    ("/.git/HEAD", re.compile(r"ref: refs/")),
    ("/composer.json", re.compile(r"\"require\"")),
    ("/storage/logs/laravel.log", re.compile(r"\[\d{4}-\d{2}-\d{2}")),
    ("/application/logs/", re.compile(r"log-\d{4}")),
    ("/phpinfo.php", re.compile(r"PHP Version")),
    ("/info.php", re.compile(r"PHP Version")),
]
SEVERITY_ORDER = {"ERROR": 0, "WARNING": 1, "INFO": 2}


def run(cmd, cwd, timeout=600):
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return result.returncode, result.stdout, result.stderr
    except (FileNotFoundError, subprocess.TimeoutExpired) as error:
        return 127, "", str(error)


def changed_files(project, base, staged=False):
    if staged:
        code, out, _ = run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], project)
        untracked = ""
    else:
        code, out, _ = run(["git", "diff", "--name-only", "--diff-filter=ACMR", base], project)
        _, untracked, _ = run(["git", "ls-files", "--others", "--exclude-standard"], project)
    if code != 0:
        return None
    return sorted({line for line in (out + untracked).splitlines() if line and (project / line).is_file()})


def walk(project, only):
    if only is not None:
        return [project / f for f in only]
    files = []
    for path in project.rglob("*"):
        if path.is_file() and not (SKIP_DIRS & set(path.relative_to(project).parts)) and (path.suffix in TEXT_EXT or path.name.startswith(".env")):
            if path.stat().st_size < 1_000_000:
                files.append(path)
    return files


def semgrep(project, only):
    if not shutil.which("semgrep"):
        return [], "semgrep belum terpasang: pip install semgrep (dilewati)"
    targets = only if only is not None else ["."]
    if only is not None and not only:
        return [], "tidak ada file berubah"
    configs = ["--config", str(AUDIT / "semgrep")]
    project_rules = project / ".ai" / "rules"
    if project_rules.exists() and any(project_rules.glob("*.yml")):
        configs += ["--config", str(project_rules)]
    cmd = ["semgrep", *configs, "--metrics=off", "--json", "--quiet", "--exclude", "vendor", "--exclude", "node_modules", "--exclude", "storage", "--exclude", ".ai", "--exclude", "dist", "--exclude", ".next", "--exclude", ".taste", "--exclude", "public/assets/taste"] + targets
    code, out, err = run(cmd, project, 900)
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return [], f"semgrep gagal: {err.strip()[:200]}"
    findings = []
    for r in data.get("results", []):
        findings.append({
            "tool": "lesson" if r["check_id"].split(".")[-1].startswith("lesson-") else "semgrep", "rule": r["check_id"].split(".")[-1], "severity": r["extra"].get("severity", "WARNING"),
            "area": r["extra"].get("metadata", {}).get("area", "general"), "file": r["path"], "line": r["start"]["line"],
            "message": r["extra"].get("message", ""), "code": r["extra"].get("lines", "").strip()[:160],
        })
    return findings, f"semgrep: {len(findings)} temuan"


def secrets(project, files):
    findings = []
    code, tracked, _ = run(["git", "ls-files"], project)
    if code == 0:
        for name in tracked.splitlines():
            base = Path(name).name
            if base == ".env" or (base.startswith(".env.") and not base.endswith((".example", ".sample", ".dist"))):
                findings.append({"tool": "secrets", "rule": "env-committed", "severity": "ERROR", "area": "config-secrets", "file": name, "line": 1, "message": "File .env masuk ke git. Hapus dari repo, rotasi semua secret di dalamnya.", "code": ""})
    for path in files:
        if path.name.endswith((".example", ".sample", ".dist", ".lock")):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for number, line in enumerate(lines, start=1):
            for label, pattern in SECRETS:
                if pattern.search(line):
                    findings.append({"tool": "secrets", "rule": label.replace(" ", "-"), "severity": "ERROR", "area": "config-secrets", "file": str(path.relative_to(project)), "line": number, "message": f"Kemungkinan {label} tertulis di kode. Pindahkan ke .env dan rotasi nilainya.", "code": pattern.sub("***", line.strip())[:120]})
                    break
    return findings, f"secrets: {len(findings)} temuan"


def dependencies(project):
    findings, notes = [], []
    if (project / "composer.lock").exists() and shutil.which("composer"):
        code, out, err = run(["composer", "audit", "--format=json", "--no-interaction"], project, 300)
        try:
            data = json.loads(out or "{}")
            for package, items in (data.get("advisories") or {}).items():
                for item in (items.values() if isinstance(items, dict) else items):
                    findings.append({"tool": "composer", "rule": item.get("cve") or item.get("advisoryId", "advisory"), "severity": "ERROR", "area": "dependencies", "file": "composer.lock", "line": 1, "message": f"{package}: {item.get('title', '')} (affected {item.get('affectedVersions', '?')})", "code": ""})
            notes.append(f"composer audit: {len(findings)} advisory")
        except json.JSONDecodeError:
            notes.append(f"composer audit gagal: {(err or out).strip()[:160]}")
    if (project / "package-lock.json").exists() and shutil.which("npm"):
        code, out, err = run(["npm", "audit", "--json", "--omit=dev"], project, 300)
        try:
            vulns = json.loads(out or "{}").get("vulnerabilities", {})
            count = 0
            for name, item in vulns.items():
                if item.get("severity") in ("high", "critical"):
                    count += 1
                    findings.append({"tool": "npm", "rule": f"npm-{item.get('severity')}", "severity": "ERROR", "area": "dependencies", "file": "package-lock.json", "line": 1, "message": f"{name} ({item.get('severity')}), range {item.get('range', '?')}", "code": ""})
            notes.append(f"npm audit: {count} high/critical")
        except json.JSONDecodeError:
            notes.append(f"npm audit gagal: {(err or out).strip()[:160]}")
    return findings, "; ".join(notes) or "dependensi: tidak ada lockfile atau tool (dilewati)"


def fetch(url, timeout=8):
    request = urllib.request.Request(url, headers={"User-Agent": "devstack-audit"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers), response.headers.get_all("Set-Cookie") or [], response.read(4096).decode("utf-8", "ignore")
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.headers.get_all("Set-Cookie") or [], ""
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        return None, {}, [], str(error)


def live(url):
    if not url:
        return [], "cek live dilewati (tanpa --url)"
    findings = []
    add = lambda rule, severity, message: findings.append({"tool": "live", "rule": rule, "severity": severity, "area": "config-secrets", "file": url, "line": 0, "message": message, "code": ""})
    status, headers, cookies, body = fetch(url)
    if status is None:
        return [], f"cek live gagal: {body[:120]}"
    h = {k.lower(): v for k, v in headers.items()}
    if "content-security-policy" not in h:
        add("missing-csp", "WARNING", "Header Content-Security-Policy tidak ada.")
    elif "unsafe-inline" in h["content-security-policy"] and "script-src" in h["content-security-policy"]:
        add("csp-unsafe-inline", "INFO", "CSP mengizinkan unsafe-inline untuk script.")
    if url.startswith("https") and "strict-transport-security" not in h:
        add("missing-hsts", "WARNING", "Header Strict-Transport-Security tidak ada.")
    if h.get("x-content-type-options", "").lower() != "nosniff":
        add("missing-nosniff", "WARNING", "Header X-Content-Type-Options: nosniff tidak ada.")
    if "x-frame-options" not in h and "frame-ancestors" not in h.get("content-security-policy", ""):
        add("clickjacking", "WARNING", "Tidak ada X-Frame-Options atau CSP frame-ancestors.")
    if "referrer-policy" not in h:
        add("missing-referrer-policy", "INFO", "Header Referrer-Policy tidak ada.")
    for leak in ("x-powered-by", "server"):
        if leak in h and re.search(r"\d", h[leak]):
            add(f"version-leak-{leak}", "INFO", f"Header {leak} membocorkan versi: {h[leak]}")
    for cookie in cookies:
        name = cookie.split("=", 1)[0]
        low = cookie.lower()
        if "httponly" not in low and re.search(r"session|token|auth", name, re.I):
            add("cookie-httponly", "WARNING", f"Cookie {name} tanpa HttpOnly.")
        if url.startswith("https") and "secure" not in low:
            add("cookie-secure", "WARNING", f"Cookie {name} tanpa Secure.")
        if "samesite" not in low:
            add("cookie-samesite", "INFO", f"Cookie {name} tanpa SameSite.")
    base = re.match(r"https?://[^/]+", url).group(0)
    for path, signature in EXPOSURES:
        code, _, _, content = fetch(base + path, 5)
        if code == 200 and signature.search(content):
            add("exposed" + path.replace("/", "-").replace(".", ""), "ERROR", f"{path} bisa diakses publik. Blokir di web server.")
    return findings, f"cek live: {len(findings)} temuan"


def inventory(project):
    routes = []
    if (project / "artisan").exists() and shutil.which("php"):
        code, out, _ = run(["php", "artisan", "route:list", "--json"], project, 120)
        if code == 0:
            try:
                for r in json.loads(out):
                    routes.append({"method": r.get("method"), "uri": r.get("uri"), "action": r.get("action"), "middleware": r.get("middleware")})
            except json.JSONDecodeError:
                pass
    controllers = project / "application" / "controllers"
    if controllers.exists():
        for path in controllers.rglob("*.php"):
            text = path.read_text(encoding="utf-8", errors="ignore")
            for method in re.findall(r"public\s+function\s+(\w+)\s*\(", text):
                if not method.startswith("_"):
                    routes.append({"method": "ANY", "uri": f"{path.stem.lower()}/{method}", "action": f"{path.relative_to(project)}::{method}", "middleware": []})
    return routes


def write_reports(project, findings, notes, routes, mode):
    out = project / ".ai" / "security"
    out.mkdir(parents=True, exist_ok=True)
    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f["severity"], 3), f["area"], f["file"], f["line"]))
    (out / "phase1.json").write_text(json.dumps({"generated": datetime.now().isoformat(timespec="seconds"), "mode": mode, "notes": notes, "findings": findings, "routes": routes}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [f"# Security audit fase 1 ({mode})", "", *[f"- {n}" for n in notes], ""]
    by_area = {}
    for f in findings:
        by_area.setdefault(f["area"], []).append(f)
    for area, items in by_area.items():
        lines.append(f"## {area} ({len(items)})")
        for f in items[:25]:
            lines.append(f"- [{f['severity']}] {f['file']}:{f['line']} {f['rule']}: {f['message']}")
        if len(items) > 25:
            lines.append(f"- ... {len(items) - 25} lagi di phase1.json")
        lines.append("")
    lines.append(f"Route atau endpoint terdeteksi: {len(routes)} (lihat phase1.json)")
    (out / "phase1.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


def main():
    parser = argparse.ArgumentParser(description="devstack security audit, phase 1 (deterministic)")
    parser.add_argument("--project", default=".")
    parser.add_argument("--diff", metavar="BASE", help="only files changed since BASE (e.g. origin/main)")
    parser.add_argument("--staged", action="store_true", help="only staged files (for pre-commit)")
    parser.add_argument("--url", help="running dev or staging URL for header and exposure checks. Never production.")
    parser.add_argument("--fail-on", choices=["error", "warning", "never"], default="error")
    args = parser.parse_args()
    project = Path(args.project).resolve()
    only = None
    if args.staged:
        args.diff = "staged"
    if args.diff:
        only = changed_files(project, args.diff, args.staged)
        if only is None:
            print("audit: FAIL git diff gagal, periksa nama branch atau jalankan di root repo")
            return 2
    mode = f"diff {args.diff}" if args.diff else "full"
    files = walk(project, only)
    findings, notes = [], []
    for result, note in (semgrep(project, only), secrets(project, files), dependencies(project) if not args.diff else ([], "dependensi: dilewati di mode diff"), live(args.url)):
        findings += result
        notes.append(note)
    routes = inventory(project) if not args.diff else []
    out = write_reports(project, findings, notes, routes, mode)
    counts = {s: sum(1 for f in findings if f["severity"] == s) for s in ("ERROR", "WARNING", "INFO")}
    for n in notes:
        print(f"audit: {n}")
    print(f"audit: {counts['ERROR']} error, {counts['WARNING']} warning, {counts['INFO']} info. Laporan: {out / 'phase1.md'}")
    if args.fail_on == "error" and counts["ERROR"]:
        return 1
    if args.fail_on == "warning" and (counts["ERROR"] or counts["WARNING"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
