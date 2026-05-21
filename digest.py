"""
Africa Daily Brief — Digest Generator

Calls Claude with collected.json + baseline references and returns the
structured digest dict consumed by render.py.

Architecture mirrors Daily-China-Digest:
- Sonnet 4.6 primary
- Opus 4.6 retry if content minimums fail validation
- Strict grounding rules — no fabricated quotes, URLs, or attributions
- Word-count target: 1,400–1,800
"""

import json
import os
from datetime import datetime, timezone

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None  # Allows --dry-run without anthropic installed

MODEL_PRIMARY  = "claude-sonnet-4-6"
MODEL_FALLBACK = "claude-opus-4-6"

MAX_TOKENS = 12_000

WORD_COUNT_MIN = 1_400
WORD_COUNT_TARGET = 2_500
WORD_COUNT_MAX = 3_600

# ─────────────────────────────────────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the editor of the CSIS Daily Africa Brief, the morning intelligence briefing of the CSIS Korea Chair's continental Africa companion product. You write for senior analysts, government officials, congressional staff, journalists, and institutional investors who need a single dense morning read covering the continent.

YOUR VOICE
- Tight institutional. Active verbs. No hedge words, no filler.
- Numbers over adjectives. "KOSPI fell 3.2%" beats "markets tumbled."
- Single-paragraph editorial summaries, not bulleted thought-spaghetti.
- "Dec 6" not "6 DEC." Year always prominent.
- No passive voice. No "it is important to note that."
- Avoid "experts say" without naming the expert.

GROUNDING — ABSOLUTE RULES
1. Every factual claim must be traceable to a specific article in the collected articles list, or to the baseline references provided, or to a known structural fact that an informed reader could verify. If you don't have a source, omit the claim.
2. NO fabricated quotes. If you attribute a quote, it must appear in the source article. If unsure, paraphrase and cite.
3. NO fabricated URLs. Source-line citations should name the outlet and a real date.
4. NO fabricated figures. If a number isn't in your sources, leave the slot empty rather than inventing one.
5. Body-count claims (military casualty figures) must be explicitly attributed: "DHQ claims X killed" not "X killed."
6. Treat African outlets and Western outlets evenhandedly. Where they diverge on a dossier, flag the divergence as data, not as one being correct.

STRUCTURE
You produce a JSON object with these top-level keys, each populated from real source material:

{
  "digest_date":       "Thursday, May 21, 2026",
  "re_line":           "5-7 short clauses summarizing today's news, separated by middots (·)",
  "market_strip":      {
    "brent": {"value": 107.80, "change_pct": -0.4, "sub": "USD/bbl"},
    "gold":  {"value": 4508,   "change_pct":  0.2, "sub": "USD/oz"}
  },
  "delta_since_yesterday": {"items": ["chip 1 (max 6 words)", "chip 2", "chip 3", "chip 4", "chip 5"]},
  "morning_memo": [
    {"lead": "Bold opening sentence — the news hook.", "text": "Remaining 50-70 words of context and significance, sourced."},
    {"lead": "Bold opening sentence — the news hook.", "text": "Remaining 50-70 words of context and significance, sourced."},
    {"lead": "Bold opening sentence — the news hook.", "text": "Remaining 50-70 words of context and significance, sourced."}
  ],
  "stat_of_day": {"number": "528", "label": "label text", "context": "context sentence", "source": "outlet, date"},
  "top_stories": [
    {"kicker": "KICKER TEXT", "headline": "Headline here", "dek": "3-4 sentence dek.", "source_line": "Outlet · Date", "url": "https://source-url-from-articles"},
    {"kicker": "KICKER TEXT", "headline": "Headline here", "dek": "3-4 sentence dek.", "source_line": "Outlet · Date", "url": "https://source-url-from-articles"},
    {"kicker": "KICKER TEXT", "headline": "Headline here", "dek": "3-4 sentence dek.", "source_line": "Outlet · Date", "url": "https://source-url-from-articles"}
  ],
  "overnight_flash": [
    {"kicker": "COUNTRY", "headline": "Headline", "dek": "1-2 sentence dek.", "source": "Outlet · Date", "url": "https://source-url"},
    {"kicker": "COUNTRY", "headline": "Headline", "dek": "1-2 sentence dek.", "source": "Outlet · Date", "url": "https://source-url"},
    {"kicker": "COUNTRY", "headline": "Headline", "dek": "1-2 sentence dek.", "source": "Outlet · Date", "url": "https://source-url"},
    {"kicker": "COUNTRY", "headline": "Headline", "dek": "1-2 sentence dek.", "source": "Outlet · Date", "url": "https://source-url"}
  ],
  "the_wire": [
    {"kicker": "COUNTRY", "text": "1-2 sentence item with inline source attribution.", "url": "https://source-url"},
    {"kicker": "COUNTRY", "text": "1-2 sentence item with inline source attribution.", "url": "https://source-url"},
    {"kicker": "COUNTRY", "text": "1-2 sentence item with inline source attribution.", "url": "https://source-url"},
    {"kicker": "COUNTRY", "text": "1-2 sentence item with inline source attribution.", "url": "https://source-url"},
    {"kicker": "COUNTRY", "text": "1-2 sentence item with inline source attribution.", "url": "https://source-url"}
  ],
  "continental_bodies": [
    {"kicker": "AFRICAN UNION", "headline": "Headline", "dek": "1-2 sentence dek."},
    {"kicker": "AES", "headline": "Headline", "dek": "1-2 sentence dek."},
    {"kicker": "EAC", "headline": "Headline", "dek": "1-2 sentence dek."},
    {"kicker": "SADC / SAMIDRC", "headline": "Headline", "dek": "1-2 sentence dek."}
  ],
  "us_africa_policy": [
    {"kicker": "THIRD-COUNTRY REMOVALS", "headline": "Headline", "dek": "1-2 sentence dek."},
    {"kicker": "OFAC ACTION", "headline": "Headline", "dek": "1-2 sentence dek."},
    {"kicker": "AFRICOM / STATE", "headline": "Headline", "dek": "1-2 sentence dek."}
  ],
  "congressional_watch": {"text": "paragraph covering HFAC/SFRC items and standing items"},
  "sahel_monitor": {
    "fuaes": "Paragraph on FUAES/AES allied armed forces posture — sourced.",
    "threat_actors": "Paragraph on JNIM/GSIM/VDP threat actor activity — sourced.",
    "africa_corps": "Paragraph on Russia Africa Corps presence and operations — sourced."
  },
  "sudan_horn_monitor": {
    "territorial": "Paragraph on RSF/SAF territorial state and front lines — sourced.",
    "defections": "Paragraph on defections cluster and unit-level shifts — sourced.",
    "somaliland_ethiopia": "Paragraph on Somaliland-Ethiopia-Somalia dynamics — sourced."
  },
  "great_lakes_monitor": {
    "m23_territory": "Paragraph on M23 territorial control and FARDC posture — sourced.",
    "humanitarian": "Paragraph on IDP flows, aid access, casualty figures — sourced.",
    "peace_track": "Paragraph on Luanda/Nairobi peace process status — sourced.",
    "cobalt": "Paragraph on cobalt/critical minerals market developments — sourced."
  },
  "external_powers_watch": [
    {"kicker": "CHINA / DRC", "headline": "Headline", "dek": "1-2 sentence dek."},
    {"kicker": "RUSSIA / SAHEL", "headline": "Headline", "dek": "1-2 sentence dek."},
    {"kicker": "UAE / SUDAN", "headline": "Headline", "dek": "1-2 sentence dek."},
    {"kicker": "ISRAEL / SOMALILAND", "headline": "Headline", "dek": "1-2 sentence dek."}
  ],
  "critical_minerals_energy": {
    "oil_producers": "Paragraph on Brent price and impact on African exporters (Nigeria, Angola, Libya) — sourced.",
    "cobalt": "Paragraph on cobalt market, DRC output, and EV supply-chain developments — sourced.",
    "gold": "Paragraph on gold price, African mine output, and central-bank demand — sourced."
  },
  "personnel_elections": [
    {"date_label": "MAY 21", "text": "event description"},
    {"date_label": "MAY 22", "text": "event description"},
    {"date_label": "END 2026", "text": "event description"}
  ],
  "expert_analysts": [
    {"institution": "INSTITUTION NAME", "text": "event or publication description", "url": "https://url-to-paper-or-event"},
    {"institution": "INSTITUTION NAME", "text": "event or publication description", "url": "https://url-to-paper-or-event"},
    {"institution": "INSTITUTION NAME", "text": "event or publication description", "url": "https://url-to-paper-or-event"}
  ],
  "calendar_watch": [
    {"month": "MAY", "day": "21", "text": "event description"},
    {"month": "MAY", "day": "22", "text": "event description"},
    {"month": "MAY", "day": "25", "text": "event description"},
    {"month": "JUN", "day": "1",  "text": "event description"}
  ],
  "press_delta": {
    "divergence_1": "TOPIC — [topic name]. African framing: [how African outlets cover it]. Western framing: [how Western outlets cover it]. Significance: [why the gap matters].",
    "divergence_2": "TOPIC — [topic name]. African framing: ... Western framing: ... Significance: ...",
    "divergence_3": "TOPIC — [topic name]. African framing: ... Western framing: ... Significance: ..."
  },
  "footer_note": "single line confirming sourcing and methodology"
}

EVERY paragraph anchors to a real story or structural fact. If a section can't be populated from sources, leave it minimal — DO NOT pad. A short, sourced section beats a long fabricated one.

WORD COUNT TARGET: 2,000–3,000 words across the digest. Below 1,400 is too thin. Above 3,600 starts to bloat.

OUTPUT FORMAT: Return only the JSON object. No preamble, no commentary, no markdown code fence."""

# ─────────────────────────────────────────────────────────────────────────────
# CONTEXT BUILDER — converts collected.json to a compact prompt
# ─────────────────────────────────────────────────────────────────────────────

def _compact_article(a: dict, idx: int) -> str:
    """One-line article summary for the prompt."""
    title = a.get("title", "")[:160]
    src   = a.get("source", "")
    link  = a.get("link", "")
    summary = a.get("summary", "")[:280]
    return f"[A{idx}] {src} — {title}\n      {summary}\n      URL: {link}"

def build_prompt_context(collected: dict) -> str:
    """Turn the collected.json into a structured prompt context block."""
    bits = []

    # Date header
    today = datetime.now(timezone.utc).strftime("%A, %B %d, %Y")
    bits.append(f"# COLLECTION CONTEXT — {today}\n")

    # Markets
    m = collected.get("markets", {})
    bits.append("## MARKET DATA\n")
    for key, val in m.items():
        if val:
            bits.append(f"  {key}: {val}")
        else:
            bits.append(f"  {key}: (no data — fill from news cycle if available, else leave empty)")
    bits.append("")

    # Monitor state
    mon = collected.get("monitor", {})
    bits.append("## MONITOR TRACKER STATE")
    for region, locs in mon.items():
        bits.append(f"\n  ### {region}")
        for loc in locs[:8]:
            change = loc.get("last_change_summary") or "(no recent change)"
            bits.append(f"    - {loc['name']} ({loc['country']}) · {loc['status']} · {change}")
    bits.append("")

    # Baseline references
    base = collected.get("baseline", {})
    bits.append("## BASELINE REFERENCES\n")
    bits.append(f"  AGOA status: {base.get('agoa_status', {}).get('current', 'unknown')}")
    bits.append(f"  OFAC active Africa programs: {list(base.get('ofac_africa_programs', {}).keys())}")
    bits.append(f"  Upcoming elections: {len(base.get('election_calendar', []))}")
    bits.append(f"  Monitored heads of state: {len(base.get('heads_of_state', {}))}")
    bits.append(f"  Junta-led transitions: {list(base.get('transitional_leaders', {}).keys())}")
    bits.append("")

    # Press delta framing dossiers
    pd = collected.get("press_delta", {})
    bits.append("## PRESS DELTA — FRAMING DOSSIERS")
    for key, d in pd.get("framing_dossiers", {}).items():
        bits.append(f"  · {d['label']}")
        bits.append(f"    African frame: {d['african_frame']}")
        bits.append(f"    Western frame: {d['western_frame']}")
    bits.append("")

    # Articles — by tier, capped
    for tier_name, cap in [("tier1", 120), ("tier2", 40), ("tier3", 20), ("tier4", 40)]:
        articles = collected.get(tier_name, [])
        if not articles:
            continue
        bits.append(f"## {tier_name.upper()} ARTICLES ({len(articles)} — showing up to {cap})\n")
        for i, a in enumerate(articles[:cap], 1):
            bits.append(_compact_article(a, i))
            bits.append("")

    return "\n".join(bits)

# ─────────────────────────────────────────────────────────────────────────────
# GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def _call_claude(model: str, system: str, user: str, max_tokens: int = MAX_TOKENS) -> str:
    """Single Claude call. Returns raw text response."""
    if Anthropic is None:
        raise RuntimeError("anthropic package not installed")
    client = Anthropic()
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    # Concatenate text blocks (handles tool_use safely if model ever returns one)
    return "\n".join(b.text for b in resp.content if hasattr(b, "text"))

def _strip_code_fence(s: str) -> str:
    """Remove markdown code fences if model included them."""
    s = s.strip()
    if s.startswith("```"):
        # Strip leading fence line
        s = s.split("\n", 1)[1] if "\n" in s else s
    if s.endswith("```"):
        s = s.rsplit("```", 1)[0]
    return s.strip()

def _parse_json(raw: str) -> dict | None:
    """Try to parse JSON. Returns None on failure."""
    try:
        return json.loads(_strip_code_fence(raw))
    except json.JSONDecodeError:
        return None

# ─────────────────────────────────────────────────────────────────────────────
# VALIDATION
# ─────────────────────────────────────────────────────────────────────────────

REQUIRED_SECTIONS = [
    "digest_date", "re_line", "market_strip", "delta_since_yesterday",
    "morning_memo", "stat_of_day", "top_stories", "overnight_flash",
    "the_wire", "continental_bodies", "us_africa_policy", "congressional_watch",
    "sahel_monitor", "sudan_horn_monitor", "great_lakes_monitor",
    "external_powers_watch", "critical_minerals_energy", "personnel_elections",
    "expert_analysts", "calendar_watch", "press_delta",
]

def _word_count(digest: dict) -> int:
    """Total word count across all text in the digest."""
    def _walk(node):
        if isinstance(node, str):
            return len(node.split())
        if isinstance(node, dict):
            return sum(_walk(v) for v in node.values())
        if isinstance(node, list):
            return sum(_walk(v) for v in node)
        return 0
    return _walk(digest)

def validate(digest: dict) -> tuple[bool, list]:
    """Return (passed, list_of_errors)."""
    errs = []
    for section in REQUIRED_SECTIONS:
        if section not in digest:
            errs.append(f"missing required section: {section}")
    wc = _word_count(digest)
    if wc < WORD_COUNT_MIN:
        errs.append(f"word count too low: {wc} < {WORD_COUNT_MIN}")
    if wc > WORD_COUNT_MAX:
        errs.append(f"word count too high: {wc} > {WORD_COUNT_MAX}")
    # Top stories must be a non-empty list
    if not isinstance(digest.get("top_stories"), list) or len(digest.get("top_stories", [])) < 2:
        errs.append("top_stories must be a list with at least 2 leads")
    # Morning memo must have 3 paragraphs
    mm = digest.get("morning_memo", [])
    if not isinstance(mm, list) or len(mm) != 3:
        errs.append(f"morning_memo must have exactly 3 items (got {len(mm) if isinstance(mm, list) else 'non-list'})")
    return (len(errs) == 0, errs)

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def generate(collected: dict) -> dict:
    """Run the generation pipeline. Returns the validated digest dict."""
    user_prompt = build_prompt_context(collected)

    # Primary attempt — Sonnet
    print(f"[digest] Primary call: {MODEL_PRIMARY}")
    raw = _call_claude(MODEL_PRIMARY, SYSTEM_PROMPT, user_prompt)
    digest = _parse_json(raw)

    if digest:
        passed, errs = validate(digest)
        if passed:
            print(f"[digest] Sonnet pass · word count {_word_count(digest)}")
            return digest
        else:
            print(f"[digest] Sonnet validation failed: {errs}")

    # Retry — Opus
    print(f"[digest] Retry call: {MODEL_FALLBACK}")
    raw = _call_claude(MODEL_FALLBACK, SYSTEM_PROMPT, user_prompt)
    digest = _parse_json(raw)

    if digest is None:
        raise RuntimeError("Both Sonnet and Opus failed to return valid JSON")

    passed, errs = validate(digest)
    if not passed:
        print(f"[digest] WARNING: Opus also failed validation: {errs}")
        print(f"[digest] Returning anyway with degraded confidence")

    print(f"[digest] Opus pass · word count {_word_count(digest)}")
    return digest


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--collected", default="collected.json")
    p.add_argument("--out", default="digest.json")
    args = p.parse_args()

    with open(args.collected) as f:
        collected = json.load(f)
    digest = generate(collected)
    with open(args.out, "w") as f:
        json.dump(digest, f, indent=2, ensure_ascii=False)
    print(f"[digest] Wrote {args.out}")
