"""
Africa Daily Brief — README Latest-Run Updater

Updates the "Latest Run" metadata table in README.md so the public-facing
GitHub repo page shows the most recent digest stats.
"""

import json
import re
from datetime import datetime, timezone
from pathlib import Path

README_PATH = Path(__file__).parent / "README.md"

LATEST_RUN_RE = re.compile(
    r"<!-- LATEST_RUN_START -->.*?<!-- LATEST_RUN_END -->",
    re.DOTALL,
)

def update_readme(collected: dict, digest: dict, html_path: str = "public/index.html") -> None:
    """Replace the LATEST_RUN block in README.md with the freshest stats."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    digest_date = digest.get("digest_date", "—")

    tier_counts = {
        "Tier 1 (news)":     len(collected.get("tier1", [])),
        "Tier 2 (analysis)": len(collected.get("tier2", [])),
        "Tier 3 (academic)": len(collected.get("tier3", [])),
        "Tier 4 (primary)":  len(collected.get("tier4", [])),
    }
    total_articles = sum(tier_counts.values())
    unique_sources = len({
        a.get("source") for tier in ["tier1","tier2","tier3","tier4"]
        for a in collected.get(tier, [])
    })

    word_count = _walk_word_count(digest)

    top_count = len(digest.get("top_stories", []))
    flash_count = len(digest.get("overnight_flash", []))

    block = f"""<!-- LATEST_RUN_START -->
| Metric | Value |
| --- | --- |
| Last generated | {now} |
| Digest date | {digest_date} |
| Articles collected | {total_articles} |
| Unique sources | {unique_sources} |
| Top stories | {top_count} |
| Overnight items | {flash_count} |
| Word count | {word_count} |
| Tier breakdown | {' · '.join(f'{k}: {v}' for k, v in tier_counts.items())} |
<!-- LATEST_RUN_END -->"""

    text = README_PATH.read_text() if README_PATH.exists() else ""
    if LATEST_RUN_RE.search(text):
        text = LATEST_RUN_RE.sub(block, text)
    else:
        text += "\n\n## Latest Run\n\n" + block + "\n"
    README_PATH.write_text(text)
    print(f"[readme] Updated with run stats — {total_articles} articles, {word_count} words")

def _walk_word_count(node) -> int:
    if isinstance(node, str):
        return len(node.split())
    if isinstance(node, dict):
        return sum(_walk_word_count(v) for v in node.values())
    if isinstance(node, list):
        return sum(_walk_word_count(v) for v in node)
    return 0


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--collected", default="collected.json")
    p.add_argument("--digest",    default="digest.json")
    args = p.parse_args()
    with open(args.collected) as f:
        collected = json.load(f)
    with open(args.digest) as f:
        digest = json.load(f)
    update_readme(collected, digest)
