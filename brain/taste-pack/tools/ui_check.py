import argparse
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

VIEWPORTS = [(375, 812), (768, 1024), (1440, 900)]

OVERFLOW_JS = """
() => {
  const width = document.documentElement.clientWidth;
  const offenders = [];
  document.querySelectorAll('body *').forEach((el) => {
    const style = getComputedStyle(el);
    if (style.position === 'fixed' || style.visibility === 'hidden') return;
    if (el.closest('.marquee, .tabs__list, .codecard__body, .terminal__body, [inert]')) return;
    const rect = el.getBoundingClientRect();
    if (rect.width && (rect.right > width + 1 || rect.left < -1)) {
      offenders.push(`${el.tagName.toLowerCase()}.${String(el.className).split(' ')[0]} right=${Math.round(rect.right)}`);
    }
  });
  return { scroll: document.documentElement.scrollWidth, width, offenders: offenders.slice(0, 8) };
}
"""

TARGETS_JS = """
() => Array.from(document.querySelectorAll('a, button, summary, [role=tab]'))
  .filter((el) => el.offsetParent !== null && !el.closest('.footer__links, .nav__menu:not(.is-open), [inert]'))
  .map((el) => { const r = el.getBoundingClientRect(); return { h: Math.round(r.height), t: (el.textContent || '').trim().slice(0, 30) }; })
  .filter((x) => x.h > 0 && x.h < 24)
  .slice(0, 8)
"""


def check(page_file, shots_dir, full):
    url = page_file if page_file.startswith("http") else Path(page_file).resolve().as_uri()
    name = Path(page_file.split("?")[0]).stem
    failures = 0
    with sync_playwright() as p:
        proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
        browser = p.chromium.launch(proxy={"server": proxy, "bypass": "127.0.0.1,localhost"} if proxy else None)
        for width, height in VIEWPORTS:
            context = browser.new_context(viewport={"width": width, "height": height}, reduced_motion="reduce")
            page = context.new_page()
            errors = []
            page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda exc: errors.append(str(exc)))
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(300)
            overflow = page.evaluate(OVERFLOW_JS)
            small = page.evaluate(TARGETS_JS)
            problems = []
            if overflow["scroll"] > overflow["width"] or overflow["offenders"]:
                problems.append(f"overflow {overflow['offenders']}")
            if errors:
                problems.append(f"console {errors[:3]}")
            if small:
                problems.append(f"targets under 24px (WCAG 2.5.8) {small}")
            shot = Path(shots_dir) / f"{name}-{width}.png"
            shot.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(shot), full_page=full)
            status = "ok  " if not problems else "FAIL"
            failures += 1 if problems else 0
            print(f"  {status} {width}px {'; '.join(problems)}")
            context.close()
        browser.close()
    return failures


def main():
    parser = argparse.ArgumentParser(description="Check overflow, console errors and touch targets")
    parser.add_argument("pages", nargs="+")
    parser.add_argument("--shots", default=".ai/screens")
    parser.add_argument("--viewport-only", action="store_true")
    args = parser.parse_args()
    total = 0
    for page_file in args.pages:
        print(f"ui-check {page_file}")
        total += check(page_file, args.shots, not args.viewport_only)
    print("ui-check: ok" if not total else f"ui-check: {total} failure(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
