#!/usr/bin/env python3
"""Record Grant Agent Lab UI demos into docs/demo/.

Examples:
  PYTHONPATH=. python3 scripts/record_demo.py --target workbench
  PYTHONPATH=. python3 scripts/record_demo.py --target copilotkit
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "docs" / "demo"
RAW = Path("/tmp/grant-agent-demo-raw")
STILLS_TMP = Path("/tmp/grant-agent-demo-stills")

BANNER_JS = """
(text) => {
  let el = document.getElementById('demo-banner');
  if (!el) {
    el = document.createElement('div');
    el.id = 'demo-banner';
    el.style.cssText = 'position:fixed;left:16px;bottom:16px;z-index:99999;max-width:52%;'
      + 'background:#0e2a4a;color:#fff;padding:10px 14px;border-radius:10px;'
      + 'font:650 15px Segoe UI,system-ui,sans-serif;box-shadow:0 8px 24px rgba(0,0,0,.25);'
      + 'line-height:1.35';
    document.body.appendChild(el);
  }
  el.textContent = text;
}
"""

HIDE_CK_OVERLAY = """
() => {
  document.querySelectorAll('div,section,aside').forEach((el) => {
    const t = el.innerText || '';
    if (t.includes('Please upgrade your CopilotKit packages') && t.length < 2500) {
      el.style.display = 'none';
    }
  });
}
"""


def banner(page, text: str, hold: float = 2.2) -> None:
    page.evaluate(BANNER_JS, text)
    page.wait_for_timeout(int(hold * 1000))


def shot(page, name: str) -> None:
    STILLS_TMP.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(STILLS_TMP / f"{name}.png"), full_page=False)


def encode_mp4(webm: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".tmp.mp4")
    if tmp.exists():
        tmp.unlink()
    cmd = [
        "ffmpeg", "-y", "-i", str(webm),
        "-c:v", "libx264", "-crf", "23", "-preset", "medium", "-threads", "4",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an",
        str(tmp),
    ]
    subprocess.check_call(cmd)
    subprocess.check_call(["ffprobe", "-hide_banner", "-i", str(tmp)])
    tmp.replace(dest)
    print("wrote", dest, dest.stat().st_size, "bytes")


def copy_still(src_name: str, dest_name: str) -> None:
    src = STILLS_TMP / src_name
    if src.exists():
        shutil.copy2(src, DEMO / dest_name)
        print("still", dest_name)


def record_workbench(page) -> None:
    banner(page, "Grant Agent Lab — workbench end-to-end demo", 2.4)
    shot(page, "01_landing")

    banner(page, "1. Agents auto-review the sample Specific Aims .docx", 1.4)
    page.get_by_role("button", name="Review sample DOCX").click(force=True)
    page.wait_for_function(
        "() => { const n = document.getElementById('score'); return n && n.textContent.trim() !== '—'; }",
        timeout=60000,
    )
    page.wait_for_timeout(1200)
    shot(page, "02_review")
    banner(page, "2. Readiness score + reviewer / compliance findings", 2.8)

    page.locator("#check").scroll_into_view_if_needed()
    page.wait_for_timeout(600)
    shot(page, "03_checklist")
    banner(page, "3. Missing Essentials checklist — required R01 items", 2.8)

    page.locator("#q").fill("Review this grant DOCX")
    page.locator(".chat form button").click(force=True)
    page.wait_for_timeout(2000)
    shot(page, "04_chat")
    banner(page, "4. Copilot-style agent rail explains the review", 2.4)

    page.evaluate("document.querySelector('.chat') && (document.querySelector('.chat').style.display='none')")
    page.get_by_role("button", name="HITL: revise").click(force=True)
    page.wait_for_timeout(1200)
    banner(page, "5. HITL revise — graph pauses; PI sends the draft back", 2.6)
    page.get_by_role("button", name="HITL: approve freeze").click(force=True)
    page.wait_for_timeout(1200)
    banner(page, "6. HITL approve freeze — blocked if required items missing", 2.6)

    banner(page, "7. RBAC: PI cannot Submit to NIH", 2.0)
    shot(page, "05_pi")
    page.locator("#role").select_option("Office of Research Aid")
    page.wait_for_timeout(1000)
    shot(page, "06_ora")
    banner(page, "8. Office of Research Aid — Submit enables (demo, no eRA login)", 3.0)
    page.locator("#submit").click(force=True)
    page.wait_for_timeout(600)
    banner(page, "Package stays institutional until AOR submits. Demo complete.", 3.0)
    shot(page, "07_done")
    page.wait_for_timeout(500)


def record_copilotkit(page) -> None:
    page.wait_for_timeout(2000)
    page.evaluate(HIDE_CK_OVERLAY)
    banner(page, "CopilotKit UI — Grant Agent Lab R01 review demo", 2.4)
    shot(page, "01_landing")

    page.get_by_role("button", name="Review sample DOCX").click(force=True)
    page.wait_for_timeout(1500)
    page.evaluate(HIDE_CK_OVERLAY)
    try:
        page.wait_for_function(
            """() => {
              const n = document.querySelector('.score');
              return n && n.textContent && n.textContent.trim() !== '' && n.textContent.trim() !== '—';
            }""",
            timeout=45000,
        )
    except Exception:
        page.wait_for_timeout(4000)
    page.evaluate(HIDE_CK_OVERLAY)
    banner(page, "1. CopilotKit workbench reviews the sample Specific Aims .docx", 2.8)
    shot(page, "02_review")
    banner(page, "2. Findings rail: reviewer, compliance, budget scrutinizer", 2.6)

    page.evaluate(
        """() => {
          const ta = document.querySelector('textarea');
          if (!ta) return;
          const proto = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
          proto.set.call(ta, 'Review the Specific Aims document');
          ta.dispatchEvent(new Event('input', { bubbles: true }));
        }"""
    )
    page.wait_for_timeout(500)
    if page.locator("textarea").count():
        try:
            page.locator("textarea").first.press("Enter")
        except Exception:
            pass
    page.wait_for_timeout(1500)
    page.evaluate(HIDE_CK_OVERLAY)
    banner(page, "3. CopilotSidebar — ask Grant agents to review the DOCX", 2.8)
    shot(page, "04_sidebar")

    banner(page, "4. RBAC: PI cannot Submit to NIH", 2.0)
    page.locator("select").select_option("Office of Research Aid")
    page.wait_for_timeout(1000)
    page.evaluate(HIDE_CK_OVERLAY)
    banner(page, "5. Office of Research Aid — Submit enables (demo, no eRA)", 3.0)
    shot(page, "06_ora")
    page.get_by_role("button", name="Submit to NIH").click(force=True)
    page.wait_for_timeout(500)
    banner(page, "CopilotKit demo complete — package still requires human AOR.", 3.0)
    shot(page, "07_done")
    page.wait_for_timeout(500)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--target", choices=["workbench", "copilotkit"], required=True)
    p.add_argument("--url", default=None, help="Override UI URL")
    p.add_argument("--skip-encode", action="store_true")
    args = p.parse_args()

    url = args.url or ("http://127.0.0.1:8765/" if args.target == "workbench" else "http://127.0.0.1:3000/")
    RAW.mkdir(parents=True, exist_ok=True)
    if STILLS_TMP.exists():
        shutil.rmtree(STILLS_TMP)
    STILLS_TMP.mkdir(parents=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=str(RAW),
            record_video_size={"width": 1440, "height": 900},
        )
        page = context.new_page()
        video = page.video
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            if args.target == "workbench":
                record_workbench(page)
            else:
                record_copilotkit(page)
        finally:
            page.close()
            webm = Path(video.path()) if video else None
            context.close()
            browser.close()

    if not webm or not webm.exists():
        print("no video captured", file=sys.stderr)
        return 1
    print("raw", webm)

    if args.target == "workbench":
        dest = DEMO / "e2e-workbench-demo.mp4"
        stills = [
            ("02_review.png", "still-review.png"),
            ("03_checklist.png", "still-checklist.png"),
            ("06_ora.png", "still-office-of-research-aid-rbac.png"),
        ]
    else:
        dest = DEMO / "e2e-copilotkit-demo.mp4"
        stills = [
            ("02_review.png", "still-copilotkit-review.png"),
            ("06_ora.png", "still-copilotkit-ora.png"),
        ]

    if not args.skip_encode:
        encode_mp4(webm, dest)
        for src, name in stills:
            copy_still(src, name)
    else:
        print("skip encode; raw webm at", webm)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
