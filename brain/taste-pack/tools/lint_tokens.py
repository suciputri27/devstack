import argparse
import re
import sys
from pathlib import Path

DEFAULT_PATHS = ["resources/views", "resources/css", "application/views", "public", "src", "assets/css"]
SKIP_PARTS = {"vendor", "node_modules", "storage", ".taste", "dist", ".git", "taste"}
VIEW_EXT = {".html", ".php", ".blade.php", ".twig"}
CSS_EXT = {".css", ".scss"}

COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgb|rgba|hsl|hsla|oklch|oklab|lab|lch)\(")
DECL = re.compile(r"(?P<prop>[a-z-]+)\s*:\s*(?P<value>[^;{}]+)")
LENGTH = re.compile(r"(?<![\w-])-?\d*\.?\d+(px|rem|em)\b")
CHECKED = {
    "font-size": "font size",
    "font-family": "font family",
    "border-radius": "radius",
    "box-shadow": "shadow",
    "margin": "spacing", "margin-top": "spacing", "margin-bottom": "spacing", "margin-left": "spacing", "margin-right": "spacing", "margin-inline": "spacing", "margin-block": "spacing",
    "padding": "spacing", "padding-top": "spacing", "padding-bottom": "spacing", "padding-left": "spacing", "padding-right": "spacing", "padding-inline": "spacing", "padding-block": "spacing",
    "gap": "spacing", "row-gap": "spacing", "column-gap": "spacing",
}
ALLOWED_VALUES = {"0", "auto", "none", "inherit", "initial", "unset", "0 auto", "auto 0"}


def is_view(path):
    return any(path.name.endswith(ext) for ext in VIEW_EXT)


def collect(paths):
    files = []
    for raw in paths:
        base = Path(raw)
        if not base.exists():
            continue
        candidates = [base] if base.is_file() else base.rglob("*")
        for path in candidates:
            if not path.is_file() or SKIP_PARTS & set(path.parts):
                continue
            if path.suffix in CSS_EXT or is_view(path):
                files.append(path)
    return files


def check_css(text, offset_line, add):
    for number, line in enumerate(text.splitlines(), start=offset_line):
        stripped = line.strip()
        if stripped.startswith("--") or stripped.startswith("@"):
            continue
        for match in DECL.finditer(line):
            prop, value = match.group("prop"), match.group("value").strip()
            if prop.startswith("--"):
                continue
            if COLOR.search(value) and not value.startswith("var("):
                add(number, "color literal, use a color token", f"{prop}: {value}")
                continue
            kind = CHECKED.get(prop)
            if not kind or value in ALLOWED_VALUES or value.startswith("var(") and "px" not in value and "rem" not in value:
                continue
            if kind == "font family" and "var(" not in value:
                add(number, "font family outside tokens, use var(--font-body) or var(--font-display)", f"{prop}: {value}")
            elif kind == "shadow" and "var(" not in value:
                add(number, "shadow outside tokens, use var(--shadow-1) or var(--shadow-2)", f"{prop}: {value}")
            elif kind in ("font size", "radius", "spacing"):
                lengths = [m.group(0) for m in LENGTH.finditer(value) if m.group(0).lstrip("-") not in ("0px", "0rem", "1px")]
                if lengths:
                    token = {"font size": "var(--step-N)", "radius": "var(--radius-s|m|l|pill)", "spacing": "var(--space-N)"}[kind]
                    add(number, f"{kind} literal {', '.join(lengths)}, use {token}", f"{prop}: {value}")


def lint_file(path, add_issue):
    text = path.read_text(encoding="utf-8", errors="ignore")
    add = lambda line, rule, snippet: add_issue(path, line, rule, snippet)
    for number, line in enumerate(text.splitlines(), start=1):
        if "\u2014" in line or "\u2013" in line:
            add(number, "em dash or en dash", line.strip()[:80])
    if path.suffix in CSS_EXT:
        check_css(text, 1, add)
        return
    for number, line in enumerate(text.splitlines(), start=1):
        style = re.search(r"\sstyle\s*=\s*[\"']([^\"']*)", line)
        if style and style.group(1).strip() and not style.group(1).strip().startswith("--"):
            add(number, "inline style, move it to a class that uses tokens", line.strip()[:80])
        if re.search(r"\son(click|change|submit|input|load)\s*=", line, re.I):
            add(number, "inline event handler, bind it in JavaScript", line.strip()[:80])
    for match in re.finditer(r"<style[^>]*>(.*?)</style>", text, re.DOTALL | re.I):
        start = text[: match.start(1)].count("\n") + 1
        check_css(match.group(1), start, add)


def main():
    parser = argparse.ArgumentParser(description="Fail when UI code bypasses design tokens")
    parser.add_argument("paths", nargs="*", help=f"files or folders (default: {', '.join(DEFAULT_PATHS)})")
    parser.add_argument("--max", type=int, default=40)
    args = parser.parse_args()
    issues = []
    files = collect(args.paths or DEFAULT_PATHS)
    for path in files:
        lint_file(path, lambda p, line, rule, snippet: issues.append((p, line, rule, snippet)))
    if not issues:
        print(f"lint-tokens: ok ({len(files)} files)")
        return 0
    for path, line, rule, snippet in issues[: args.max]:
        print(f"{path}:{line}  {rule}\n    {snippet}")
    more = len(issues) - args.max
    print(f"lint-tokens: {len(issues)} issue(s) in {len(files)} files" + (f", {more} not shown" if more > 0 else ""))
    return 1


if __name__ == "__main__":
    sys.exit(main())
