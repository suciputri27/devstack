import math
import re
import sys
from pathlib import Path

PAIRS = [
    ("ink", "bg", 4.5),
    ("ink-2", "bg", 4.5),
    ("ink-3", "bg", 4.5),
    ("ink", "bg-2", 4.5),
    ("ink-2", "bg-2", 4.5),
    ("ink-3", "bg-2", 4.5),
    ("ink-2", "surface", 4.5),
    ("ink-3", "surface", 4.5),
    ("ink-2", "surface-2", 4.5),
    ("on-accent", "accent", 4.5),
    ("accent", "bg", 3.0),
    ("accent", "surface", 3.0),
    ("danger", "surface", 4.5),
    ("danger", "bg", 4.5),
    ("on-danger", "danger", 4.5),
    ("success", "surface", 3.0),
    ("warning", "surface", 3.0),
    ("sidebar-ink", "sidebar-bg", 4.5),
    ("sidebar-muted", "sidebar-bg", 4.5),
    ("sidebar-count-ink", "sidebar-bg", 4.5),
]

TOKEN = re.compile(r"--([\w-]+):\s*oklch\(([^)]*)\)")


def parse(css):
    tokens = {}
    for name, body in TOKEN.findall(css):
        parts = body.replace("/", " / ").split()
        alpha = 1.0
        if "/" in parts:
            idx = parts.index("/")
            alpha = float(parts[idx + 1])
            parts = parts[:idx]
        l, c, h = (float(p) for p in parts)
        tokens[name] = (l, c, h, alpha)
    return tokens


def oklch_to_srgb(l, c, h):
    a = c * math.cos(math.radians(h))
    b = c * math.sin(math.radians(h))
    l_ = l + 0.3963377774 * a + 0.2158037573 * b
    m_ = l - 0.1055613458 * a - 0.0638541728 * b
    s_ = l - 0.0894841775 * a - 1.2914855480 * b
    lc, mc, sc = l_ ** 3, m_ ** 3, s_ ** 3
    r = 4.0767416621 * lc - 3.3077115913 * mc + 0.2309699292 * sc
    g = -1.2684380046 * lc + 2.6097574011 * mc - 0.3413193965 * sc
    bl = -0.0041960863 * lc - 0.7034186147 * mc + 1.7076147010 * sc
    return tuple(min(1.0, max(0.0, v)) for v in (r, g, bl))


def luminance(rgb):
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def to_gamma(v):
    return 12.92 * v if v <= 0.0031308 else 1.055 * v ** (1 / 2.4) - 0.055


def from_gamma(v):
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def resolve(tokens, name, base):
    l, c, h, alpha = tokens[name]
    rgb = oklch_to_srgb(l, c, h)
    if alpha >= 1 or base is None:
        return rgb
    fg = [to_gamma(v) for v in rgb]
    bg = [to_gamma(v) for v in base]
    return tuple(from_gamma(alpha * f + (1 - alpha) * b) for f, b in zip(fg, bg))


def ratio(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def check(path):
    tokens = parse(Path(path).read_text())
    failures = 0
    rows = []
    for fg, bg, need in PAIRS:
        if fg not in tokens or bg not in tokens:
            continue
        base = resolve(tokens, bg, None)
        value = ratio(resolve(tokens, fg, base), base)
        ok = value >= need
        failures += 0 if ok else 1
        rows.append(f"  {'ok  ' if ok else 'FAIL'} {fg:>10} on {bg:<10} {value:5.2f} (min {need})")
    return failures, rows


def main(paths):
    total = 0
    for path in paths:
        failures, rows = check(path)
        total += failures
        if failures:
            print(f"{path}: {failures} contrast failure(s)")
            print("\n".join(rows))
        else:
            print(f"{path}: contrast ok ({len(rows)} pairs)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:] or sorted(str(p) for p in Path(__file__).resolve().parent.parent.joinpath("presets").glob("*.css"))))
