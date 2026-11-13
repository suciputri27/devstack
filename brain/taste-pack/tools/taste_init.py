import argparse
import json
import math
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import assemble
from contrast import luminance, oklch_to_srgb, parse, ratio

PACK = Path(__file__).resolve().parent.parent

QUESTIONS = [
    ("name", "Nama produk atau aplikasi", None),
    ("product", "Jenis produk", [
        ("panel", "Panel admin atau sistem internal"),
        ("publik", "Portal layanan publik atau formulir warga"),
        ("saas", "Produk digital atau SaaS"),
        ("landing", "Landing page atau situs pemasaran"),
        ("umkm", "Toko, UMKM, atau komunitas"),
        ("data", "Dashboard data dan laporan"),
    ]),
    ("users", "Pengguna utama", [
        ("internal", "Petugas internal yang memakai setiap hari"),
        ("publik", "Masyarakat umum, sesekali memakai"),
        ("profesional", "Klien bisnis atau profesional"),
        ("teknis", "Developer atau pengguna teknis"),
    ]),
    ("mood", "Kesan yang diinginkan", [
        ("tenang", "Tenang dan terpercaya"),
        ("berani", "Berani dan modern"),
        ("hangat", "Hangat dan ramah"),
        ("elegan", "Elegan dan editorial"),
    ]),
    ("mode", "Tema", [
        ("any", "Bebas, pilihkan yang paling cocok"),
        ("light", "Terang"),
        ("dark", "Gelap"),
    ]),
    ("density", "Kepadatan isi", [
        ("any", "Ikuti preset"),
        ("comfortable", "Lega, untuk pengguna sesekali"),
        ("compact", "Padat, untuk data banyak dan pengguna harian"),
    ]),
    ("shape", "Bentuk sudut", [
        ("any", "Ikuti preset"),
        ("sharp", "Tegas"),
        ("soft", "Lembut"),
        ("round", "Bulat"),
    ]),
    ("brand", "Warna merek dalam hex, contoh #0E7C66 (kosongkan jika tidak ada)", None),
]

RADII = {"sharp": (4, 6, 10), "soft": (8, 12, 16), "round": (12, 18, 28)}
COMPACT = {"--control-h": "38px", "--space-5": "1.25rem", "--space-6": "1.5rem", "--space-7": "2.25rem", "--space-8": "3rem", "--space-9": "clamp(3rem, 2.4rem + 3vw, 5rem)"}
VOICE = {
    "tenang": "Formal and calm. Address the reader as \"Anda\". Short sentences, no exclamation marks.",
    "berani": "Direct and confident. \"Anda\" by default. Verbs first, concrete numbers, no hype words.",
    "hangat": "Warm and friendly. \"Kamu\" is fine for consumer audiences. Simple everyday words.",
    "elegan": "Measured and refined. \"Anda\". Fewer words, strong nouns, no slang.",
}


class InitError(Exception):
    pass


def ask_interactive():
    answers = {}
    for key, prompt, options in QUESTIONS:
        if not options:
            answers[key] = input(f"\n{prompt}: ").strip()
            continue
        print(f"\n{prompt}")
        for index, (_, label) in enumerate(options, start=1):
            print(f"  {index}. {label}")
        while True:
            raw = input("Pilih nomor: ").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(options):
                answers[key] = options[int(raw) - 1][0]
                break
            print("  Ketik salah satu nomor di atas.")
    return answers


def validate_answers(answers):
    clean = {"name": (answers.get("name") or "Aplikasi").strip(), "brand": (answers.get("brand") or "").strip()}
    for key, _, options in QUESTIONS:
        if not options:
            continue
        allowed = [value for value, _ in options]
        value = answers.get(key, "any" if "any" in allowed else allowed[0])
        if value not in allowed:
            raise InitError(f"jawaban '{key}' harus salah satu dari: {', '.join(allowed)}")
        clean[key] = value
    if clean["brand"] and not re.fullmatch(r"#?[0-9a-fA-F]{6}", clean["brand"]):
        raise InitError("warna merek harus hex 6 digit, contoh #0E7C66")
    return clean


def score(manifest, answers):
    ranked = []
    for order, (name, meta) in enumerate(manifest.items()):
        tags = meta["tags"]
        points = 0
        points += 3 if answers["product"] in tags["product"] else 0
        points += 2 if answers["users"] in tags["users"] else 0
        points += 3 if answers["mood"] in tags["mood"] else 0
        if answers["mode"] != "any":
            points += 1 if tags["mode"] == answers["mode"] else -6
        if answers["density"] == "compact" and tags["density"] == "compact":
            points += 1
        ranked.append((points, -order, name))
    ranked.sort(reverse=True)
    if answers["mode"] != "any":
        matching = [item for item in ranked if manifest[item[2]]["tags"]["mode"] == answers["mode"]]
        ranked = matching or ranked
    return [name for _, _, name in ranked[:3]]


def srgb_to_oklch(hex_value):
    value = hex_value.lstrip("#")
    rgb = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    l_ = 0.4122214708 * lin[0] + 0.5363325363 * lin[1] + 0.0514459929 * lin[2]
    m_ = 0.2119034982 * lin[0] + 0.6806995451 * lin[1] + 0.1073969566 * lin[2]
    s_ = 0.0883024619 * lin[0] + 0.2817188376 * lin[1] + 0.6299787005 * lin[2]
    l_, m_, s_ = (v ** (1 / 3) for v in (l_, m_, s_))
    lightness = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    b = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
    chroma = math.hypot(a, b)
    hue = math.degrees(math.atan2(b, a)) % 360
    return lightness, chroma, hue


def in_gamut(l, c, h):
    a = c * math.cos(math.radians(h))
    b = c * math.sin(math.radians(h))
    l_ = l + 0.3963377774 * a + 0.2158037573 * b
    m_ = l - 0.1055613458 * a - 0.0638541728 * b
    s_ = l - 0.0894841775 * a - 1.2914855480 * b
    lc, mc, sc = l_ ** 3, m_ ** 3, s_ ** 3
    rgb = (4.0767416621 * lc - 3.3077115913 * mc + 0.2309699292 * sc, -1.2684380046 * lc + 2.6097574011 * mc - 0.3413193965 * sc, -0.0041960863 * lc - 0.7034186147 * mc + 1.7076147010 * sc)
    return all(-0.001 <= v <= 1.001 for v in rgb)


def fit_brand(hex_value, preset_tokens, dark):
    l, c, h = srgb_to_oklch(hex_value)
    c = min(c, 0.2)
    if dark:
        l = max(l, 0.74)
    bg = oklch_to_srgb(*preset_tokens["bg"][:3])
    surface = oklch_to_srgb(*preset_tokens["surface"][:3])
    on = (0.99, 0.004, h) if not dark else (0.2, 0.04, h)
    on_rgb = oklch_to_srgb(*on)
    step = 0.01 if dark else -0.01
    for _ in range(80):
        cc = c
        while not in_gamut(l, cc, h) and cc > 0:
            cc -= 0.005
        rgb = oklch_to_srgb(l, cc, h)
        if ratio(on_rgb, rgb) >= 4.5 and ratio(rgb, bg) >= 3 and ratio(rgb, surface) >= 3:
            return (round(l, 3), round(cc, 3), round(h, 1)), on
        l = min(0.95, max(0.25, l + step))
    raise InitError("warna merek tidak bisa dibuat lolos kontras pada preset ini")


def overrides_for(preset, answers):
    tokens = parse((PACK / "presets" / f"{preset}.css").read_text(encoding="utf-8"))
    manifest = json.loads((PACK / "presets" / "manifest.json").read_text(encoding="utf-8"))
    dark = manifest[preset]["tags"]["mode"] == "dark"
    lines = []
    if answers["brand"]:
        (l, c, h), on = fit_brand(answers["brand"], tokens, dark)
        accent = f"oklch({l} {c} {h})"
        lines += [
            f"  --accent: {accent};",
            f"  --on-accent: oklch({on[0]} {on[1]} {round(on[2], 1)});",
            f"  --accent-soft: oklch({l} {c} {h} / {0.12 if dark else 0.09});",
            f"  --focus: {accent};",
        ]
    shape = answers["shape"] if answers["shape"] != "any" else None
    if shape:
        s, m, lg = RADII[shape]
        lines += [f"  --radius-s: {s}px;", f"  --radius-m: {m}px;", f"  --radius-l: {lg}px;"]
    density = answers["density"] if answers["density"] != "any" else manifest[preset]["tags"]["density"]
    if density == "compact":
        lines += [f"  {key}: {value};" for key, value in COMPACT.items()]
    return ":root {\n" + "\n".join(lines) + "\n}\n" if lines else ""


def taste_dir(project):
    path = Path(project).resolve() / ".taste"
    path.mkdir(parents=True, exist_ok=True)
    return path


def build_candidate(preset, answers, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    tokens = out_dir / "tokens.css"
    tokens.write_text(overrides_for(preset, answers), encoding="utf-8")
    shell = json.loads((PACK / "content" / "app-shell.json").read_text(encoding="utf-8"))
    shell["app_name"] = answers["name"]
    shell["mark"] = answers["name"][:1].upper()
    (out_dir / "shell.json").write_text(json.dumps(shell, ensure_ascii=False), encoding="utf-8")
    spec = json.loads((PACK / "content" / "app-specimen.json").read_text(encoding="utf-8"))
    spec["include_data"] = [str(out_dir / "shell.json")]
    spec["screen"] = str(PACK / "screens" / "specimen.html")
    spec_path = out_dir / "specimen.json"
    spec_path.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
    assemble.build(spec_path, out_dir / "app.html", preset, tokens if tokens.read_text().strip() else "")
    landing_src = PACK / "content" / "konsultan.clean-corporate.json"
    assemble.build(landing_src, out_dir / "landing.html", preset, tokens if tokens.read_text().strip() else "")


def compare_page(candidates, manifest, answers, path):
    buttons = []
    for index, name in enumerate(candidates):
        meta = manifest[name]
        selected = "true" if index == 0 else "false"
        buttons.append(f'<button type="button" role="tab" aria-selected="{selected}" data-preset="{name}"><strong>{index + 1}. {meta["label"]}</strong><span>{meta["use_for"]}</span></button>')
    page = f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pilih arah visual: {answers['name']}</title>
<style>
:root {{ color-scheme: light; --ink: oklch(0.21 0.015 255); --muted: oklch(0.47 0.015 255); --line: oklch(0.21 0.015 255 / 0.14); --accent: oklch(0.52 0.19 256); --bg: oklch(0.975 0.003 250); }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; font: 15px/1.5 system-ui, "Segoe UI", sans-serif; color: var(--ink); background: var(--bg); }}
header {{ display: grid; gap: 12px; padding: 20px 24px; border-bottom: 1px solid var(--line); background: oklch(1 0 0); position: sticky; top: 0; z-index: 2; }}
h1 {{ margin: 0; font-size: 18px; }}
p {{ margin: 0; color: var(--muted); }}
.bar {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: stretch; }}
.bar button {{ display: grid; gap: 2px; text-align: left; min-height: 44px; padding: 8px 14px; border: 1px solid var(--line); border-radius: 10px; background: oklch(1 0 0); color: var(--ink); font: inherit; cursor: pointer; }}
.bar button span {{ font-size: 12px; color: var(--muted); }}
.bar button[aria-selected="true"] {{ border-color: var(--accent); box-shadow: 0 0 0 2px var(--accent); }}
.views button {{ min-height: 44px; display: flex; align-items: center; }}
code {{ padding: 2px 6px; border-radius: 6px; background: oklch(0.21 0.015 255 / 0.07); font-size: 13px; }}
iframe {{ display: block; width: 100%; height: calc(100vh - 190px); min-height: 520px; border: 0; background: oklch(1 0 0); }}
</style>
</head>
<body>
<header>
  <h1>Pilih arah visual untuk {answers['name']}</h1>
  <p>Klik kandidat untuk membandingkan. Setelah memilih, jalankan <code id="cmd">taste pick {candidates[0]}</code></p>
  <div class="bar" role="tablist" aria-label="Kandidat">{''.join(buttons)}</div>
  <div class="bar views" role="tablist" aria-label="Tampilan">
    <button type="button" role="tab" aria-selected="true" data-view="app">Layar aplikasi</button>
    <button type="button" role="tab" aria-selected="false" data-view="landing">Landing page</button>
  </div>
</header>
<iframe id="frame" title="Pratinjau kandidat" src="candidates/{candidates[0]}/app.html"></iframe>
<script>
(() => {{
  let preset = "{candidates[0]}";
  let view = "app";
  const frame = document.getElementById("frame");
  const cmd = document.getElementById("cmd");
  const sync = () => {{ frame.src = `candidates/${{preset}}/${{view}}.html`; cmd.textContent = `taste pick ${{preset}}`; }};
  document.querySelectorAll("[data-preset]").forEach((b) => b.addEventListener("click", () => {{
    preset = b.dataset.preset;
    document.querySelectorAll("[data-preset]").forEach((x) => x.setAttribute("aria-selected", String(x === b)));
    sync();
  }}));
  document.querySelectorAll("[data-view]").forEach((b) => b.addEventListener("click", () => {{
    view = b.dataset.view;
    document.querySelectorAll("[data-view]").forEach((x) => x.setAttribute("aria-selected", String(x === b)));
    sync();
  }}));
}})();
</script>
</body>
</html>
"""
    path.write_text(page, encoding="utf-8")


def command_ask(args):
    if args.answers:
        raw = json.loads(Path(args.answers).read_text(encoding="utf-8"))
    elif sys.stdin.isatty():
        raw = ask_interactive()
    else:
        raise InitError("tidak ada terminal interaktif; isi jawaban di file JSON lalu pakai --answers")
    answers = validate_answers(raw)
    manifest = json.loads((PACK / "presets" / "manifest.json").read_text(encoding="utf-8"))
    candidates = score(manifest, answers)
    target = taste_dir(args.project)
    (target / "answers.json").write_text(json.dumps(answers, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    shutil.rmtree(target / "candidates", ignore_errors=True)
    for name in candidates:
        build_candidate(name, answers, target / "candidates" / name)
    compare_page(candidates, manifest, answers, target / "compare.html")
    print(f"taste: kandidat {', '.join(candidates)}")
    print(f"taste: buka {target / 'compare.html'} lalu jalankan: taste pick <preset>")


def design_md(answers, preset, meta, tokens_css, assets_rel):
    fonts = sorted({face["family"] for face in meta["fonts"]})
    overrides = tokens_css.strip() or "none, preset defaults"
    return f"""# DESIGN.md

Generated by taste init on {date.today().isoformat()}. Change it only by running taste init again; do not edit tokens by hand inside a task.

## Direction
- Product: {answers['name']}
- Preset: `{preset}` ({meta['label']}): {meta['use_for']}
- Product type: {answers['product']}; users: {answers['users']}; mood: {answers['mood']}
- Fonts: {', '.join(fonts)} (self-hosted)

## Tokens
- Base tokens: `{PACK}/presets/{preset}.css`
- Project overrides (`.taste/tokens.css`):

```css
{overrides}
```

- Runtime bundle for layouts: `{assets_rel}/taste.css` and `{assets_rel}/taste.js`. Load both once in the main layout.

## Rules
- Think with `{PACK}/BRAIN.md`, build with `{PACK}/TASTE.md`. Reuse pack components and screens where they fit; compose anything new from primitives and tokens.
- New components use only `var(--token)` values. No new colors, font sizes, radii, or shadows. No inline styles.
- Pick the form pattern from the table in TASTE.md. Long forms get sections, a sticky action bar, and a draft key.
- Every screen needs its states: loading, empty, error, success, disabled, long content, no permission.
- Avoid generic AI patterns: purple-to-blue gradients, emoji icons, hero plus three identical cards, everything centered, cards inside cards.

## Voice
{VOICE[answers['mood']]}
Labels say what to enter, hints say the format, errors say how to fix it. Bahasa Indonesia, no translated idioms, no em dashes.

## Review
- Always: `taste lint`, `taste contrast`, and `taste check <url>`.
- Optional, recommended: `taste review <url>` when a vision model is configured. Without one it is skipped and the operator reviews `.ai/screens/`.
"""


def command_pick(args):
    target = taste_dir(args.project)
    answers_path = target / "answers.json"
    if not answers_path.exists():
        raise InitError("jalankan 'ask' dulu")
    answers = json.loads(answers_path.read_text(encoding="utf-8"))
    manifest = json.loads((PACK / "presets" / "manifest.json").read_text(encoding="utf-8"))
    if args.preset not in manifest:
        raise InitError(f"preset tidak dikenal: {args.preset}")
    meta = manifest[args.preset]
    tokens_css = overrides_for(args.preset, answers)
    (target / "tokens.css").write_text(tokens_css, encoding="utf-8")
    project = Path(args.project).resolve()
    assets = project / args.assets
    (assets / "fonts").mkdir(parents=True, exist_ok=True)
    faces = []
    for face in meta["fonts"]:
        shutil.copyfile(PACK / "fonts" / face["file"], assets / "fonts" / face["file"])
        faces.append(f"@font-face {{ font-family: \"{face['family']}\"; src: url(\"fonts/{face['file']}\") format(\"woff2\"); font-weight: {face['weight']}; font-style: {face['style']}; font-display: swap; }}")
    css_parts = ["\n".join(faces), (PACK / "presets" / f"{args.preset}.css").read_text(encoding="utf-8")]
    css_parts += [(PACK / "core" / name).read_text(encoding="utf-8") for name in ("base.css", "app.css")]
    css_parts.append(tokens_css)
    (assets / "taste.css").write_text("\n".join(css_parts), encoding="utf-8")
    js = "\n".join((PACK / "core" / name).read_text(encoding="utf-8") for name in ("motion.js", "app.js"))
    (assets / "taste.js").write_text(js, encoding="utf-8")
    config = {"pack": str(PACK), "preset": args.preset, "assets": args.assets, "answers": answers, "locked": date.today().isoformat()}
    (target / "taste.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    design = project / "DESIGN.md"
    if design.exists() and not args.force:
        shutil.copyfile(design, project / "DESIGN.md.bak")
    design.write_text(design_md(answers, args.preset, meta, tokens_css, args.assets), encoding="utf-8")
    shutil.rmtree(target / "candidates", ignore_errors=True)
    (target / "compare.html").unlink(missing_ok=True)
    print(f"taste: terkunci ke {args.preset}")
    print(f"taste: DESIGN.md, .taste/taste.json, .taste/tokens.css, {args.assets}/taste.css, {args.assets}/taste.js")


def command_vision(args):
    target = taste_dir(args.project)
    config_path = target / "taste.json"
    config = json.loads(config_path.read_text(encoding="utf-8")) if config_path.exists() else {}
    if args.off:
        config.pop("vision", None)
        print("taste: vision dimatikan untuk proyek ini")
    else:
        config["vision"] = {"base_url": args.base_url, "model": args.model, "api_key_env": args.api_key_env}
        print(f"taste: vision memakai {args.model} di {args.base_url}, key dari env {args.api_key_env}")
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (target / "vision-cache.json").unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description="Choose and lock a visual direction for a project")
    sub = parser.add_subparsers(dest="command", required=True)
    ask = sub.add_parser("ask", help="answer the questions and build candidates")
    ask.add_argument("--answers", help="JSON file with answers, for non-interactive use")
    ask.add_argument("--project", default=".")
    pick = sub.add_parser("pick", help="lock a candidate into the project")
    pick.add_argument("preset")
    pick.add_argument("--project", default=".")
    pick.add_argument("--assets", default="public/assets/taste", help="where taste.css, taste.js and fonts go, relative to the project")
    pick.add_argument("--force", action="store_true", help="overwrite DESIGN.md without a .bak copy")
    vision = sub.add_parser("vision", help="configure an optional vision model for taste_review.py")
    vision.add_argument("--project", default=".")
    vision.add_argument("--base-url", default="http://localhost:20128/v1")
    vision.add_argument("--model", default="code-vision")
    vision.add_argument("--api-key-env", default="NINEROUTER_API_KEY")
    vision.add_argument("--off", action="store_true")
    args = parser.parse_args()
    try:
        {"ask": command_ask, "pick": command_pick, "vision": command_vision}[args.command](args)
    except (InitError, json.JSONDecodeError, KeyError, FileNotFoundError, assemble.AssembleError) as error:
        print(f"taste: FAIL {error}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
