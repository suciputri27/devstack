import json
import locale
import os
import shutil
import sys
import time

from ansible.plugins.callback import CallbackBase

DOCUMENTATION = """
name: devstack
type: stdout
short_description: Compact progress output for the devstack installer
description: One line per stage with duration, short errors, full details in DEVSTACK_LOG.
"""

LABELS = {
    "preflight": "Pemeriksaan awal",
    "base": "Sistem dasar dan user",
    "hardening": "Keamanan server",
    "toolchain": "PHP, Node, Docker, tools",
    "brain": "Otak devstack (taste, audit, memori)",
    "ninerouter": "9Router",
    "searxng": "SearXNG",
    "workspace": "Agent dan konfigurasi user",
    "finalize": "Finalisasi",
}
SUMMARY_TASKS = {"Ringkasan", "Hasil sinkron config"}


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = "stdout"
    CALLBACK_NAME = "devstack"

    def __init__(self):
        super().__init__()
        self.tty = sys.stdout.isatty() and not os.environ.get("NO_COLOR")
        utf8 = (locale.getpreferredencoding(False) or "").upper().replace("-", "") == "UTF8"
        self.sym_ok, self.sym_fail, self.sym_run = ("✓", "✗", "›") if utf8 else ("ok", "x", ">")
        self.c = {k: (v if self.tty else "") for k, v in {
            "reset": "\033[0m", "bold": "\033[1m", "dim": "\033[2m", "green": "\033[32m", "red": "\033[31m", "cyan": "\033[36m", "yellow": "\033[33m",
        }.items()}
        self.log = None
        path = os.environ.get("DEVSTACK_LOG")
        if path:
            try:
                self.log = open(path, "a", encoding="utf-8")
            except OSError:
                self.log = None
        self.roles = []
        self.current = None
        self.stage_start = 0.0
        self.total_start = time.time()
        self.changed = 0
        self.failed = False
        self.summaries = []

    def _write(self, text):
        sys.stdout.write(text)
        sys.stdout.flush()

    def _log(self, kind, task, result=None):
        if not self.log:
            return
        stamp = time.strftime("%H:%M:%S")
        line = f"[{stamp}] {kind:<8} {task}"
        if result is not None:
            data = {k: v for k, v in result.items() if k in ("msg", "stdout", "stderr", "rc", "cmd", "changed", "results", "failed_when_result") and v not in ("", None, [])}
            if data:
                line += "\n" + json.dumps(data, ensure_ascii=False, indent=2, default=str)[:6000]
        self.log.write(line + "\n")
        self.log.flush()

    def _width(self):
        return shutil.get_terminal_size((100, 20)).columns

    def _stage_line(self, symbol, color, suffix):
        index = self.roles.index(self.current) + 1 if self.current in self.roles else 0
        label = LABELS.get(self.current, self.current)
        counter = f"[{index}/{len(self.roles)}]" if index else ""
        return f"  {self.c[color]}{symbol}{self.c['reset']} {self.c['dim']}{counter:>6}{self.c['reset']} {label:<38} {self.c['dim']}{suffix}{self.c['reset']}"

    def _finish_stage(self, ok=True):
        if not self.current:
            return
        took = int(time.time() - self.stage_start)
        duration = f"{took // 60}m{took % 60:02d}s" if took >= 60 else f"{took}s"
        extra = f"  {self.changed} berubah" if self.changed else ""
        line = self._stage_line(self.sym_ok if ok else self.sym_fail, "green" if ok else "red", duration + extra)
        self._write(("\r\033[K" if self.tty else "") + line + "\n")
        self.current = None
        self.changed = 0

    def v2_playbook_on_play_start(self, play):
        names = []
        for role in play.get_roles():
            name = role.get_name()
            if name not in names:
                names.append(name)
        skip_searxng = os.environ.get("ENABLE_SEARXNG", "true").lower() in ("false", "0", "no")
        self.roles = [n for n in names if not (n == "searxng" and skip_searxng)]
        self._log("PLAY", play.get_name())

    def v2_playbook_on_task_start(self, task, is_conditional):
        role = task._role.get_name() if task._role else None
        if role and role != self.current:
            self._finish_stage(True)
            self.current = role
            if role not in self.roles:
                self.roles.append(role)
            self.stage_start = time.time()
        name = task.get_name().split(" : ")[-1]
        self._log("TASK", name)
        if self.tty and self.current:
            line = self._stage_line(self.sym_run, "cyan", name)
            self._write("\r\033[K" + line[: self._width() + 30])

    def v2_runner_on_ok(self, result):
        if result._result.get("changed"):
            self.changed += 1
        name = result._task.get_name().split(" : ")[-1]
        self._log("CHANGED" if result._result.get("changed") else "OK", name, result._result if result._result.get("changed") else None)
        if name in SUMMARY_TASKS and result._task.action in ("debug", "ansible.builtin.debug"):
            msg = result._result.get("msg")
            if isinstance(msg, list):
                self.summaries.extend(str(m) for m in msg if str(m).strip())
            elif msg:
                self.summaries.append(str(msg))

    def v2_runner_on_skipped(self, result):
        self._log("SKIP", result._task.get_name())

    def v2_runner_on_failed(self, result, ignore_errors=False):
        name = result._task.get_name().split(" : ")[-1]
        self._log("IGNORED" if ignore_errors else "FAILED", name, result._result)
        if ignore_errors:
            return
        self.failed = True
        self._finish_stage(False)
        r = result._result
        message = r.get("stderr") or r.get("msg") or r.get("stdout") or ""
        if isinstance(r.get("results"), list):
            for item in r["results"]:
                if item.get("failed"):
                    message = item.get("stderr") or item.get("msg") or message
                    break
        lines = [l for l in str(message).strip().splitlines() if l.strip()][-6:]
        self._write(f"\n  {self.c['red']}{self.c['bold']}Gagal:{self.c['reset']} {name}\n")
        for line in lines:
            self._write(f"    {line[:200]}\n")

    def v2_runner_on_unreachable(self, result):
        self.v2_runner_on_failed(result)

    def v2_runner_item_on_failed(self, result):
        self._log("FAILED", f"{result._task.get_name()} (item)", result._result)

    def v2_playbook_on_stats(self, stats):
        if not self.failed:
            self._finish_stage(True)
        took = int(time.time() - self.total_start)
        duration = f"{took // 60}m{took % 60:02d}s" if took >= 60 else f"{took}s"
        log = os.environ.get("DEVSTACK_LOG", "")
        if self.failed:
            self._write(f"\n  {self.c['red']}{self.sym_fail} Install berhenti setelah {duration}.{self.c['reset']}\n")
            self._write(f"  {self.c['dim']}Detail lengkap: {log or 'jalankan dengan --verbose'}{self.c['reset']}\n")
            self._write(f"  {self.c['dim']}Perbaiki penyebabnya, lalu jalankan lagi. Installer aman diulang.{self.c['reset']}\n\n")
        else:
            self._write(f"\n  {self.c['green']}{self.c['bold']}{self.sym_ok} Selesai dalam {duration}{self.c['reset']}\n")
            if self.summaries:
                self._write("\n")
                for line in self.summaries:
                    self._write(f"  {line}\n")
            self._write("\n")
        if self.log:
            self.log.write(f"[{time.strftime('%H:%M:%S')}] END      {'failed' if self.failed else 'ok'} in {duration}\n")
            self.log.close()
