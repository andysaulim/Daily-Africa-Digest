"""
Africa Daily Brief — Monitor Tracker

Persistent JSON tracker for the 16 monitor locations across three regions.
Each location stores: last-known status, last-update date, most recent
material change, and source URL.

Designed to mirror the China bp_tracker.py architecture so future port
work is straightforward.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from databases import ALL_MONITOR_LOCATIONS

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────

TRACKER_PATH = Path(__file__).parent / "trackers" / "africa_monitor.json"

# Status vocabulary — restricted to enforce consistency
VALID_STATUS = {
    "stable",        # no change in 7+ days
    "active",        # ongoing operations / contestation
    "elevated",      # heightened activity, new development this week
    "alert",         # major event in past 48h
    "withdrawing",   # force/territory withdrawal in progress
}

# ─────────────────────────────────────────────────────────────────────────────
# LOAD / SAVE
# ─────────────────────────────────────────────────────────────────────────────

def _ensure_dir():
    TRACKER_PATH.parent.mkdir(parents=True, exist_ok=True)

def load_state() -> dict:
    """Load tracker state. Returns dict keyed by location id."""
    _ensure_dir()
    if not TRACKER_PATH.exists():
        return _initialize_state()
    try:
        with open(TRACKER_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return _initialize_state()

def save_state(state: dict) -> None:
    """Persist tracker state."""
    _ensure_dir()
    with open(TRACKER_PATH, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False, sort_keys=True)

def _initialize_state() -> dict:
    """Seed tracker with all 16 locations in 'stable' status."""
    now = datetime.now(timezone.utc).isoformat()
    return {
        loc["id"]: {
            "location_id":   loc["id"],
            "name":          loc["name"],
            "country":       loc["country"],
            "region":        loc["region"],
            "context":       loc["context"],
            "status":        "stable",
            "last_update":   now,
            "last_change":   None,
            "last_change_summary": None,
            "last_source_url":     None,
        }
        for loc in ALL_MONITOR_LOCATIONS
    }

# ─────────────────────────────────────────────────────────────────────────────
# UPDATE
# ─────────────────────────────────────────────────────────────────────────────

def update_location(
    state: dict,
    location_id: str,
    status: str,
    change_summary: str,
    source_url: str = "",
) -> dict:
    """Update one location's status, summary, and source. Returns state."""
    if status not in VALID_STATUS:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUS}")
    if location_id not in state:
        raise KeyError(f"Unknown location_id: {location_id}")

    now = datetime.now(timezone.utc).isoformat()
    entry = state[location_id]
    prev_status = entry.get("status")

    entry["status"] = status
    entry["last_update"] = now
    if status != prev_status or change_summary != entry.get("last_change_summary"):
        entry["last_change"] = now
        entry["last_change_summary"] = change_summary
        entry["last_source_url"] = source_url

    return state

# ─────────────────────────────────────────────────────────────────────────────
# CONTEXT BUILDERS — consumed by digest.py and render.py
# ─────────────────────────────────────────────────────────────────────────────

def build_context_block(region: str = None) -> list:
    """
    Return a list of dicts describing each location's current state, optionally
    filtered to one region ('Sahel', 'Sudan & Horn', 'Great Lakes').
    """
    state = load_state()
    out = []
    for loc_id, entry in state.items():
        if region and entry.get("region") != region:
            continue
        out.append({
            "id":              loc_id,
            "name":            entry["name"],
            "country":         entry["country"],
            "region":          entry["region"],
            "context":         entry["context"],
            "status":          entry["status"],
            "last_change":     entry.get("last_change"),
            "last_change_summary": entry.get("last_change_summary"),
            "last_source_url": entry.get("last_source_url"),
        })
    # Order by region, then country, then name
    region_order = {"Sahel": 0, "Sudan & Horn": 1, "Great Lakes": 2}
    out.sort(key=lambda e: (region_order.get(e["region"], 99), e["country"], e["name"]))
    return out

def status_summary() -> dict:
    """Return aggregate counts of locations by status, for the delta bar."""
    state = load_state()
    counts = {}
    for entry in state.values():
        s = entry.get("status", "stable")
        counts[s] = counts.get(s, 0) + 1
    return counts

# ─────────────────────────────────────────────────────────────────────────────
# CLI HELPERS — for one-off manual updates
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        # Print current state
        for loc in build_context_block():
            print(f"  {loc['region']:14} {loc['name']:18} {loc['country']:14} {loc['status']}")
        print()
        print("Status counts:", status_summary())
    elif sys.argv[1] == "init":
        state = _initialize_state()
        save_state(state)
        print(f"Initialized {len(state)} locations to 'stable'")
    elif sys.argv[1] == "update" and len(sys.argv) >= 5:
        _, _, loc_id, status, *summary_parts = sys.argv
        state = load_state()
        update_location(state, loc_id, status, " ".join(summary_parts))
        save_state(state)
        print(f"Updated {loc_id} → {status}")
    else:
        print("Usage:")
        print("  python africa_monitor.py             # show current state")
        print("  python africa_monitor.py init        # initialize all 16 locations")
        print("  python africa_monitor.py update <id> <status> <summary>")
