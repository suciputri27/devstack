import argparse
import base64
import json
import os
import re
import struct
import sys
import urllib.error
import urllib.request
import zlib
from datetime import date
from pathlib import Path

PACK = Path(__file__).resolve().parent.parent
VIEWPORTS = [(1440, 900), (375, 812)]
SEVERITY = {"high": 0, "medium": 1, "low": 2}

RUBRIC = """You are a senior product designer reviewing screenshots of a web screen.
Judge only what is visible. Be specific and actionable. Reply in Bahasa Indonesia.
Check, in order of importance:
1. Hierarchy: is the main task or message obvious within 3 seconds?
2. Layout: alignment, consistent spacing, crowded or empty areas, broken mobile layout.
3. Readability: text size, line length, contrast that looks weak even if technically passing.
4. Consistency with the design direction below: colors, type, radius, density.
5. Generic AI look: gradients without purpose, identical card grids, decorative noise, everything centered.
6. Forms and actions: clear primary action, labels, error and empty states if visible.
Return only JSON, no prose, in this shape:
{"score": 1-10, "summary": "one sentence", "findings": [{"severity": "high|medium|low", "where": "area on screen", "issue": "what is wrong", "fix": "concrete change using existing components"}]}
At most 8 findings, most important first. Do not invent problems to fill the list."""


class ReviewError(Exception):
    pass


def red_png(size=16):
    raw = b"".join(b"\x00" + b"\xd0\x20\x20" * size for _ in range(size))
    chunk = lambda tag, data: struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def load_config(args):
    project = Path(args.project).resolve()
    stored = {}
    taste = project / ".taste" / "taste.json"
    if taste.exists():
        stored = json.loads(taste.read_text(encoding="utf-8")).get("vision", {})
    base_url = args.base_url or os.environ.get("TASTE_VISION_BASE_URL") or stored.get("base_url")
    model = args.model or os.environ.get("TASTE_VISION_MODEL") or stored.get("model")
    key_env = stored.get("api_key_env", "TASTE_VISION_API_KEY")
    api_key = os.environ.get("TASTE_VISION_API_KEY") or os.environ.get(key_env) or ""
    if not base_url or not model:
        return None
    return {"base_url": base_url.rstrip("/"), "model": model, "api_key": api_key, "project": project}


def chat(config, messages, max_tokens, timeout):
    body = json.dumps({"model": config["model"], "messages": messages, "max_tokens": max_tokens, "temperature": 0.2}).encode()
    headers = {"Content-Type": "application/json"}
    if config["api_key"]:
        headers["Authorization"] = f"Bearer {config['api_key']}"
    request = urllib.request.Request(f"{config['base_url']}/chat/completions", data=body, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "ignore")[:200]
        raise ReviewError(f"HTTP {error.code}: {detail}")
    except (urllib.error.URLError, TimeoutError) as error:
        raise ReviewError(f"tidak bisa menghubungi {config['base_url']}: {error}")
    try:
        return data["choices"][0]["message"]["content"] or "", data.get("usage", {})
    except (KeyError, IndexError):
        raise ReviewError("respons tidak berformat chat completions")


def image_part(data, mime):
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{base64.b64encode(data).decode()}"}}


def supports_vision(config, refresh):
    cache_path = config["project"] / ".taste" / "vision-cache.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {}
    key = f"{config['base_url']}|{config['model']}"
    if key in cache and not refresh:
        return cache[key]["vision"], "cache"
    messages = [{"role": "user", "content": [{"type": "text", "text": "What is the main color of this image? Answer with one word."}, image_part(red_png(), "image/png")]}]
    try:
        answer, _ = chat(config, messages, 10, 60)
        ok = bool(re.search(r"\b(red|merah|crimson|scarlet)\b", answer.lower()))
    except ReviewError:
        ok = False
    cache[key] = {"vision": ok, "checked": date.today().isoformat()}
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(cache, indent=2) + "\n", encoding="utf-8")
    return ok, "probe"


def capture(urls, out_dir):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ReviewError("Playwright belum terpasang: pip install playwright && playwright install chromium")
    out_dir.mkdir(parents=True, exist_ok=True)
    shots = []
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    with sync_playwright() as p:
        browser = p.chromium.launch(proxy={"server": proxy, "bypass": "127.0.0.1,localhost"} if proxy else None)
        for url in urls:
            name = Path(url.split("?")[0]).stem or "page"
            for width, height in VIEWPORTS:
                page = browser.new_page(viewport={"width": width, "height": height}, reduced_motion="reduce")
                page.goto(url, wait_until="networkidle")
                page.wait_for_timeout(300)
                path = out_dir / f"review-{name}-{width}.jpg"
                page.screenshot(path=str(path), type="jpeg", quality=62)
                shots.append((url, width, path))
                page.close()
        browser.close()
    return shots


def direction(project):
    design = project / "DESIGN.md"
    if not design.exists():
        return "No DESIGN.md found."
    text = design.read_text(encoding="utf-8")
    match = re.search(r"## Direction(.*?)(\n## |\Z)", text, re.DOTALL)
    voice = re.search(r"## Voice(.*?)(\n## |\Z)", text, re.DOTALL)
    return ((match.group(1) if match else text[:600]) + (voice.group(1) if voice else "")).strip()[:900]


def parse_json(text):
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ReviewError("model tidak mengembalikan JSON")
    return json.loads(match.group(0))


def main():
    parser = argparse.ArgumentParser(description="Optional visual review with a vision model")
    parser.add_argument("urls", nargs="+")
    parser.add_argument("--project", default=".")
    parser.add_argument("--shots", default=".ai/screens")
    parser.add_argument("--base-url")
    parser.add_argument("--model")
    parser.add_argument("--refresh", action="store_true", help="probe the model again instead of using the cache")
    parser.add_argument("--strict", action="store_true", help="exit 1 when a high severity finding exists")
    args = parser.parse_args()
    config = load_config(args)
    try:
        shots = capture(args.urls, Path(args.shots))
    except ReviewError as error:
        print(f"review: FAIL {error}")
        return 1
    print(f"review: {len(shots)} screenshot di {args.shots}")
    if not config:
        print("review: vision dilewati, belum dikonfigurasi (opsional tapi disarankan, lihat TASTE.md bagian Vision)")
        return 0
    ok, source = supports_vision(config, args.refresh)
    if not ok:
        print(f"review: vision dilewati, model {config['model']} tidak bisa membaca gambar ({source}). Screenshot tetap tersedia untuk dicek manusia.")
        return 0
    results = []
    total_in = total_out = 0
    for url in args.urls:
        parts = [{"type": "text", "text": f"Design direction:\n{direction(config['project'])}\n\nScreen: {url}. First image desktop 1440px, second image mobile 375px."}]
        for shot_url, _, path in shots:
            if shot_url == url:
                parts.append(image_part(path.read_bytes(), "image/jpeg"))
        try:
            text, usage = chat(config, [{"role": "system", "content": RUBRIC}, {"role": "user", "content": parts}], 900, 180)
            data = parse_json(text)
        except (ReviewError, json.JSONDecodeError) as error:
            print(f"review: {url} gagal dinilai: {error}")
            continue
        total_in += usage.get("prompt_tokens", 0)
        total_out += usage.get("completion_tokens", 0)
        findings = sorted(data.get("findings", []), key=lambda f: SEVERITY.get(f.get("severity"), 3))
        results.append({"url": url, "score": data.get("score"), "summary": data.get("summary", ""), "findings": findings})
        print(f"\n{url}  skor {data.get('score')}/10  {data.get('summary', '')}")
        for f in findings:
            print(f"  [{f.get('severity', '?')}] {f.get('where', '')}: {f.get('issue', '')}\n      perbaikan: {f.get('fix', '')}")
    report = Path(args.shots) / "review.json"
    report.write_text(json.dumps({"model": config["model"], "date": date.today().isoformat(), "tokens": {"input": total_in, "output": total_out}, "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nreview: token input {total_in}, output {total_out}. Laporan: {report}")
    high = any(f.get("severity") == "high" for r in results for f in r["findings"])
    return 1 if (args.strict and high) else 0


if __name__ == "__main__":
    sys.exit(main())
