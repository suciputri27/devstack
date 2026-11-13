import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

PACK = Path(__file__).resolve().parent.parent
SECTION = re.compile(r"\{\{([#^])([\w.-]+)\}\}(.*?)\{\{/\2\}\}", re.DOTALL)
VARIABLE = re.compile(r"\{\{\s*([\w.-]+)\s*\}\}")
EMPHASIS = re.compile(r"\*([^*]+)\*")
INCLUDE = re.compile(r"\{\{>\s*([\w/.-]+)\s*\}\}")
BANNED = [
    "unlock the power",
    "revolusioner",
    "solusi terbaik",
    "next level",
    "game changer",
    "seamless",
    "di era digital",
    "tingkatkan produktivitas anda",
]


class AssembleError(Exception):
    pass


def lookup(name, stack):
    if name == ".":
        top = stack[-1]
        return top.get(".") if isinstance(top, dict) else top
    if name.startswith("has_"):
        return bool(lookup(name[4:], stack))
    plain = name.endswith("_plain")
    key = name[: -len("_plain")] if plain else name
    for frame in reversed(stack):
        if isinstance(frame, dict) and key in frame:
            value = frame[key]
            return EMPHASIS.sub(r"\1", value) if plain and isinstance(value, str) else value
    return None


def fmt(value):
    if value is None or value is False:
        return ""
    if value is True:
        return "true"
    text = html.escape(str(value), quote=True)
    return EMPHASIS.sub(r"<em>\1</em>", text)


def render(template, stack):
    def section(match):
        kind, name, inner = match.groups()
        value = lookup(name, stack)
        if kind == "^":
            return "" if value else render(inner, stack)
        if isinstance(value, list):
            out = []
            for index, item in enumerate(value, start=1):
                frame = dict(item) if isinstance(item, dict) else {".": item}
                frame.setdefault("_i", index)
                frame.setdefault("_first", index == 1)
                out.append(render(inner, stack + [frame]))
            return "".join(out)
        if value:
            return render(inner, stack + [value] if isinstance(value, dict) else stack)
        return ""

    template = INCLUDE.sub(lambda m: (PACK / "screens" / f"{m.group(1)}.html").read_text(encoding="utf-8"), template)
    previous = None
    while previous != template:
        previous = template
        template = SECTION.sub(section, template)
    return VARIABLE.sub(lambda m: fmt(lookup(m.group(1), stack)), template)


def format_number(value):
    number = float(value)
    decimals = len(str(value).split(".")[1]) if "." in str(value) else 0
    text = f"{number:,.{decimals}f}"
    return text.replace(",", "_").replace(".", ",").replace("_", ".")


def normalize(block):
    if block["type"] == "stats":
        for item in block.get("items", []):
            item.setdefault("display", format_number(item["value"]))
    return block


def scan_copy(page):
    hits = []
    blob = json.dumps(page, ensure_ascii=False).lower()
    for phrase in BANNED:
        if phrase in blob:
            hits.append(phrase)
    if "\u2014" in blob or "\u2013" in blob:
        hits.append("em dash / en dash")
    return hits


def load_page(page_path):
    page = json.loads(Path(page_path).read_text(encoding="utf-8"))
    merged = {}
    for extra in page.get("include_data", []):
        options = [Path(page_path).parent / extra, PACK / "content" / extra, PACK / extra]
        found = next((o for o in options if o.exists()), None)
        if not found:
            raise AssembleError(f"include_data not found: {extra}")
        merged.update(json.loads(found.read_text(encoding="utf-8")))
    merged.update(page.get("globals", {}))
    active = page.get("active")
    for group in merged.get("nav", []):
        for link in group.get("links", []):
            link["current"] = bool(active) and link.get("key") == active
    page["globals"] = merged
    return page


def project_taste():
    config = Path.cwd() / ".taste" / "taste.json"
    if not config.exists():
        return None, None
    data = json.loads(config.read_text(encoding="utf-8"))
    tokens = Path.cwd() / ".taste" / "tokens.css"
    return data.get("preset"), tokens if tokens.exists() else None


def build(page_path, out_path, preset_override=None, extra_css=None):
    page = load_page(page_path)
    manifest = json.loads((PACK / "presets" / "manifest.json").read_text(encoding="utf-8"))
    locked_preset, locked_tokens = project_taste()
    extra_css = locked_tokens if extra_css is None else extra_css
    preset = preset_override or locked_preset or page.get("preset")
    if preset not in manifest:
        raise AssembleError(f"unknown preset '{preset}', choose one of: {', '.join(manifest)}")
    problems = scan_copy(page)
    if problems:
        raise AssembleError("copy check failed: " + "; ".join(problems))
    kind = page.get("kind", "landing")
    parts = []
    if kind == "app":
        screen = Path(page["screen"])
        screen_path = screen if screen.is_absolute() else (Path(page_path).parent / screen if (Path(page_path).parent / screen).exists() else PACK / screen)
        if not screen_path.exists():
            raise AssembleError(f"screen not found: {page['screen']}")
        parts.append(render(screen_path.read_text(encoding="utf-8"), [page.get("globals", {}), page]))
    else:
        for block in page["blocks"]:
            template_path = PACK / "blocks" / f"{block['type']}.html"
            if not template_path.exists():
                raise AssembleError(f"unknown block '{block['type']}'")
            parts.append(render(template_path.read_text(encoding="utf-8"), [page.get("globals", {}), normalize(block)]))
    meta = manifest[preset]
    font_dir = Path(out_path).parent / "fonts"
    font_dir.mkdir(parents=True, exist_ok=True)
    faces = []
    for face in meta["fonts"]:
        shutil.copyfile(PACK / "fonts" / face["file"], font_dir / face["file"])
        faces.append(f"@font-face {{ font-family: \"{face['family']}\"; src: url(\"fonts/{face['file']}\") format(\"woff2\"); font-weight: {face['weight']}; font-style: {face['style']}; font-display: swap; }}")
    styles = ["base.css", "app.css"] if kind == "app" else ["base.css"]
    scripts = ["app.js"] if kind == "app" else ["motion.js"]
    css = "\n".join(faces) + "\n" + (PACK / "presets" / f"{preset}.css").read_text(encoding="utf-8") + "\n" + "\n".join((PACK / "core" / name).read_text(encoding="utf-8") for name in styles)
    if extra_css:
        css += "\n" + Path(extra_css).read_text(encoding="utf-8")
    js = "\n".join((PACK / "core" / name).read_text(encoding="utf-8") for name in scripts)
    preload = meta["fonts"][0]["file"]
    document = f"""<!doctype html>
<html lang="{fmt(page.get('lang', 'id'))}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{fmt(page['title'])}</title>
<meta name="description" content="{fmt(page.get('description', ''))}">
<meta name="theme-color" content="{meta['theme_color']}">
<link rel="preload" href="fonts/{preload}" as="font" type="font/woff2" crossorigin>
<style>
{css}
</style>
</head>
<body{' class="app-body"' if kind == "app" else ""}>
{chr(10).join(parts)}
<script>
{js}
</script>
</body>
</html>
"""
    leftovers = re.findall(r"\{\{[^}]*\}\}", document)
    if leftovers:
        raise AssembleError("unrendered tags: " + ", ".join(sorted(set(leftovers))))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(document, encoding="utf-8")
    return len(page.get("blocks", [])) or 1, len(document)


def main():
    parser = argparse.ArgumentParser(description="Assemble a page from taste-pack blocks")
    parser.add_argument("page", help="page JSON file")
    parser.add_argument("out", help="output HTML file")
    parser.add_argument("--preset", help="override the preset (default: .taste/taste.json, then the page file)")
    parser.add_argument("--extra-css", help="token overrides appended last (default: .taste/tokens.css)")
    args = parser.parse_args()
    try:
        blocks, size = build(args.page, args.out, args.preset, args.extra_css)
    except (AssembleError, KeyError, json.JSONDecodeError, FileNotFoundError) as error:
        print(f"assemble: FAIL {error}")
        return 1
    print(f"assemble: ok {blocks} blocks, {size // 1024} KB -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
