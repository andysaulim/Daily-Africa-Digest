"""
Africa Daily Brief — Orchestration Entry Point

Runs the full pipeline: collect → digest → render → send → archive.

Flags:
  --dry-run    Collect only, do not persist tracker state or write outputs
  --no-send    Run full pipeline but skip email delivery
  --from-cache Skip collection, read collected.json from disk
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import collect
import digest as digest_mod
import render
import send_email
import update_readme

ROOT       = Path(__file__).parent
PUBLIC_DIR = ROOT / "public"
ARCHIVE_DIR = PUBLIC_DIR / "archive"

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run",     action="store_true", help="Collect only, no persistence")
    p.add_argument("--no-send",     action="store_true", help="Skip email delivery")
    p.add_argument("--from-cache",  action="store_true", help="Read collected.json from disk")
    p.add_argument("--subject-prefix", default="CSIS Daily Africa Brief")
    args = p.parse_args()

    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    # ── Collect ────────────────────────────────────────────────────────────
    collected_path = ROOT / "collected.json"
    if args.from_cache and collected_path.exists():
        print("[run] Loading collected.json from cache")
        with open(collected_path) as f:
            collected = json.load(f)
    else:
        collected = collect.collect_all(dry_run=args.dry_run)
        if not args.dry_run:
            with open(collected_path, "w") as f:
                json.dump(collected, f, indent=2, ensure_ascii=False, default=str)

    if args.dry_run:
        print("[run] Dry run complete. Exiting before generation.")
        return 0

    # ── Digest ─────────────────────────────────────────────────────────────
    print()
    try:
        digest = digest_mod.generate(collected)
    except RuntimeError as exc:
        print(f"[run] FATAL: digest generation failed: {exc}")
        return 1

    digest_path = ROOT / "digest.json"
    with open(digest_path, "w") as f:
        json.dump(digest, f, indent=2, ensure_ascii=False)

    # ── Render ─────────────────────────────────────────────────────────────
    print()
    html = render.render_html(digest)
    index_path = PUBLIC_DIR / "index.html"
    index_path.write_text(html)
    print(f"[run] Wrote {index_path} ({len(html):,} bytes)")

    # Archive copy with date stamp
    digest_date = digest.get("digest_date", datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    date_slug = digest_date.replace(",", "").replace(" ", "-").lower()
    archive_path = ARCHIVE_DIR / f"{date_slug}.html"
    shutil.copy(index_path, archive_path)
    print(f"[run] Archived to {archive_path}")

    # ── README update ──────────────────────────────────────────────────────
    update_readme.update_readme(collected, digest)

    # ── Send ───────────────────────────────────────────────────────────────
    if args.no_send:
        print("[run] --no-send flag set; skipping email")
        return 0

    print()
    subject = f"{args.subject_prefix} · {digest_date}"
    ok = send_email.send_digest(html, subject=subject)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
