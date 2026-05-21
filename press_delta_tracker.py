"""
Africa Daily Brief — Pan-African Press Delta Tracker

Tracks African outlet output volume and editorial framing on key dossiers
where African and Western press systematically diverge. Persistent state.

Analogous to xinhua_tracker.py in the China digest architecture.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

TRACKER_PATH = Path(__file__).parent / "trackers" / "press_delta.json"

# ─────────────────────────────────────────────────────────────────────────────
# OUTLET ROSTER
# ─────────────────────────────────────────────────────────────────────────────
# Mix of pan-African aggregators, English-language continental outlets,
# and major-market national outlets where framing gaps are most pronounced.

OUTLETS = [
    # Pan-African / aggregators
    {"id": "allafrica",     "name": "AllAfrica",         "scope": "pan-african", "language": "en"},
    {"id": "africanews",    "name": "Africanews",        "scope": "pan-african", "language": "en"},
    {"id": "africa_report", "name": "The Africa Report", "scope": "pan-african", "language": "en"},
    {"id": "africa_intel",  "name": "Africa Intelligence","scope": "pan-african","language": "en"},
    # National outlets
    {"id": "sudan_tribune", "name": "Sudan Tribune",     "scope": "national",    "language": "en"},
    {"id": "sudans_post",   "name": "Sudans Post",       "scope": "national",    "language": "en"},
    {"id": "dabanga",       "name": "Dabanga Sudan",     "scope": "national",    "language": "en"},
    {"id": "addis_standard","name": "Addis Standard",    "scope": "national",    "language": "en"},
    {"id": "mg_za",         "name": "Mail & Guardian (SA)","scope": "national", "language": "en"},
    {"id": "daily_maverick","name": "Daily Maverick (SA)","scope": "national", "language": "en"},
    {"id": "news24",        "name": "News24 (SA)",       "scope": "national",    "language": "en"},
    {"id": "enca",          "name": "eNCA (SA)",         "scope": "national",    "language": "en"},
    {"id": "premium_times", "name": "Premium Times (NG)","scope": "national",   "language": "en"},
    {"id": "punch_ng",      "name": "Punch (NG)",        "scope": "national",    "language": "en"},
    {"id": "thecable_ng",   "name": "TheCable (NG)",     "scope": "national",    "language": "en"},
    {"id": "daily_nation",  "name": "Daily Nation (KE)", "scope": "national",    "language": "en"},
    {"id": "the_standard_ke","name": "The Standard (KE)","scope": "national",   "language": "en"},
    {"id": "east_african",  "name": "The East African",  "scope": "regional",    "language": "en"},
    {"id": "mada_masr",     "name": "Mada Masr (EG)",    "scope": "national",    "language": "en"},
    {"id": "ahram_online",  "name": "Ahram Online (EG)", "scope": "national",    "language": "en"},
]

# ─────────────────────────────────────────────────────────────────────────────
# FRAMING DOSSIERS — where African/Western press systematically diverges
# ─────────────────────────────────────────────────────────────────────────────

FRAMING_DOSSIERS = {
    "sudan_uae_attribution": {
        "label": "Sudan · UAE attribution",
        "african_frame": "UAE named explicitly as RSF primary backer, with defector accounts cited as evidence",
        "western_frame": "UAE attribution treated as Khartoum claim; hedged language",
        "watch": "Defector accounts (Adam, Al-Savana) push the gap closer",
    },
    "drc_rwanda_attribution": {
        "label": "DRC · Rwanda M23 backing",
        "african_frame": "Rwanda backing explicit; UN Group of Experts findings cited",
        "western_frame": "Hedged; \"Rwanda-backed\" used sparingly, often with denial",
        "watch": "Treasury Kabila sanctions and ICW reporting close some gap",
    },
    "anc_decline": {
        "label": "South Africa · ANC political trajectory",
        "african_frame": "Coalition repositioning, internal succession dynamics",
        "western_frame": "Decline narrative, post-apartheid order erosion",
        "watch": "Local elections 2026 will test both reads",
    },
    "agoa_post_lapse": {
        "label": "AGOA · post-expiry framing",
        "african_frame": "Sovereignty leverage, BRICS+ pivot opening",
        "western_frame": "Trade-policy gap, replacement legislation focus",
        "watch": "Both correct; gap is emphasis",
    },
    "somaliland_recognition": {
        "label": "Somaliland recognition geometry",
        "african_frame": "Israel recognition fact-stated; Taiwan/UAE/UK presence noted as structural",
        "western_frame": "Regional curiosity; recognition treated as one-off",
        "watch": "Taiwan attendance at independence ceremony May 18 signals widening",
    },
    "sahel_western_disengagement": {
        "label": "Sahel · Western disengagement",
        "african_frame": "Sovereignty assertion, decolonial sequencing",
        "western_frame": "Russian/Wagner gains, security vacuum",
        "watch": "Both framings select for different evidence",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# LOAD / SAVE
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_dir():
    TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_state() -> dict:
    _ensure_dir()
    if not TRACKER_PATH.exists():
        return _initialize_state()
    try:
        with open(TRACKER_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return _initialize_state()

def save_state(state: dict) -> None:
    _ensure_dir()
    with open(TRACKER_PATH, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False, sort_keys=True)

def _initialize_state() -> dict:
    now = datetime.now(timezone.utc).isoformat()
    return {
        "outlets": {
            o["id"]: {**o, "article_count_24h": 0, "last_seen": None}
            for o in OUTLETS
        },
        "framing_dossiers": FRAMING_DOSSIERS,
        "last_update": now,
    }

# ─────────────────────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────────────────────

def record_articles(outlet_id: str, count: int) -> None:
    """Update 24h article count for an outlet."""
    state = load_state()
    if outlet_id not in state["outlets"]:
        return
    state["outlets"][outlet_id]["article_count_24h"] = count
    state["outlets"][outlet_id]["last_seen"] = datetime.now(timezone.utc).isoformat()
    state["last_update"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

def update_outlet_volumes(volumes: dict) -> None:
    """Bulk-update outlet volumes from collect.py output."""
    state = load_state()
    now = datetime.now(timezone.utc).isoformat()
    for outlet_id, count in volumes.items():
        if outlet_id in state["outlets"]:
            state["outlets"][outlet_id]["article_count_24h"] = count
            state["outlets"][outlet_id]["last_seen"] = now
    state["last_update"] = now
    save_state(state)

# ─────────────────────────────────────────────────────────────────────────────
# READ HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def total_24h_volume() -> int:
    state = load_state()
    return sum(o.get("article_count_24h", 0) for o in state["outlets"].values())

def top_outlets(n: int = 5) -> list:
    state = load_state()
    ranked = sorted(
        state["outlets"].values(),
        key=lambda o: o.get("article_count_24h", 0),
        reverse=True,
    )
    return ranked[:n]

def build_context_block() -> dict:
    """Return the press-delta context dict consumed by digest.py."""
    state = load_state()
    return {
        "outlets": list(state["outlets"].values()),
        "total_24h_volume": total_24h_volume(),
        "top_outlets": top_outlets(5),
        "framing_dossiers": state["framing_dossiers"],
    }


if __name__ == "__main__":
    state = load_state()
    print(f"Outlets tracked: {len(state['outlets'])}")
    print(f"Total 24h volume: {total_24h_volume()}")
    print()
    print("Framing dossiers:")
    for key, d in state["framing_dossiers"].items():
        print(f"  {d['label']}")
