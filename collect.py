"""
Africa Daily Brief — Collector

Scrapes RSS feeds across four tiers, fetches market data, and assembles
the context block consumed by digest.py.

Architecture mirrors Daily-China-Digest collect.py:
- Tier 1: news (24h)
- Tier 2: analysis / think tanks (36h)
- Tier 3: academic journals (72h)
- Tier 4: primary sources — AU, RECs, government press, multilaterals (24h)
- Plus: market data + monitor tracker context + press delta context
"""

import feedparser
import requests
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from urllib.parse import quote_plus, urlparse

import africa_monitor
import press_delta_tracker
from databases import build_baseline_references

# ─────────────────────────────────────────────────────────────────────────────
# FEED CONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────

def _gnews(query: str) -> str:
    """Build a Google News RSS search URL — used as fallback when native RSS
    is unavailable. Keep queries narrow."""
    return f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-US&gl=US&ceid=US:en"

# ── Tier 1: NEWS — 24h window ────────────────────────────────────────────────
# Mix of: aggregators, prestige outlets (always-include), pan-African,
# major-market national outlets, regional outlets, francophone (via Google News).

TIER1_NEWS = {
    # Aggregators — highest volume
    "AllAfrica · Top":                "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf",
    "AllAfrica · Sudan":              "https://allafrica.com/tools/headlines/rdf/sudan/headlines.rdf",
    "AllAfrica · Nigeria":            "https://allafrica.com/tools/headlines/rdf/nigeria/headlines.rdf",
    "AllAfrica · Kenya":              "https://allafrica.com/tools/headlines/rdf/kenya/headlines.rdf",
    "AllAfrica · South Africa":       "https://allafrica.com/tools/headlines/rdf/southafrica/headlines.rdf",
    "AllAfrica · Ethiopia":           "https://allafrica.com/tools/headlines/rdf/ethiopia/headlines.rdf",
    "AllAfrica · Democratic Republic of Congo": "https://allafrica.com/tools/headlines/rdf/drcongo/headlines.rdf",
    "AllAfrica · Mali":               "https://allafrica.com/tools/headlines/rdf/mali/headlines.rdf",
    "AllAfrica · Burkina Faso":       "https://allafrica.com/tools/headlines/rdf/burkinafaso/headlines.rdf",
    "AllAfrica · Niger":              "https://allafrica.com/tools/headlines/rdf/niger/headlines.rdf",
    "AllAfrica · Somalia":            "https://allafrica.com/tools/headlines/rdf/somalia/headlines.rdf",
    "AllAfrica · Egypt":              "https://allafrica.com/tools/headlines/rdf/egypt/headlines.rdf",

    # Prestige outlets — always include any Africa-related stories
    "Reuters · Africa":               _gnews("site:reuters.com Africa"),
    "BBC · Africa":                   "https://feeds.bbci.co.uk/news/world/africa/rss.xml",
    "AP · Africa":                    _gnews("site:apnews.com Africa"),
    "AFP · Africa":                   _gnews("site:barrons.com OR site:france24.com AFP Africa"),
    "FT · Africa":                    _gnews("site:ft.com Africa"),
    "Bloomberg · Africa":             _gnews("site:bloomberg.com Africa"),
    "WSJ · Africa":                   _gnews("site:wsj.com Africa"),
    "NYT · Africa":                   "https://rss.nytimes.com/services/xml/rss/nyt/Africa.xml",
    "Washington Post · Africa":       _gnews("site:washingtonpost.com Africa"),
    "The Economist · Middle East and Africa": "https://www.economist.com/middle-east-and-africa/rss.xml",
    "Al Jazeera · Africa":            "https://www.aljazeera.com/xml/rss/all.xml",
    "The Guardian · Africa":          "https://www.theguardian.com/world/africa/rss",

    # Pan-African outlets
    "Africanews":                     "https://www.africanews.com/feed/rss",
    "The Africa Report":              "https://www.theafricareport.com/feed/",
    "Africa Confidential · headlines":"https://www.africa-confidential.com/feeds/africa-confidential",
    "African Arguments":              "https://africanarguments.org/feed/",
    "The New Humanitarian · Africa":  _gnews("site:thenewhumanitarian.org Africa"),

    # South Africa
    "Mail & Guardian":                "https://mg.co.za/feed/",
    "Daily Maverick":                 "https://www.dailymaverick.co.za/section/africa/feed/",
    "News24 · Africa":                "https://www.news24.com/news24/rss/Africa",
    "eNCA · Top":                     "https://www.enca.com/rss/articles",
    "BusinessDay · ZA":               _gnews("site:businesslive.co.za"),
    "Engineering News":               "https://www.engineeringnews.co.za/rss/topic.xml?topic=africa",

    # Nigeria
    "Premium Times":                  "https://www.premiumtimesng.com/feed",
    "Punch · Nigeria":                "https://punchng.com/feed/",
    "Vanguard · Nigeria":             "https://www.vanguardngr.com/feed/",
    "TheCable":                       "https://www.thecable.ng/feed",
    "BusinessDay · NG":               "https://businessday.ng/feed/",

    # East Africa
    "Daily Nation":                   "https://nation.africa/kenya/rss",
    "The Standard · Kenya":           _gnews("site:standardmedia.co.ke"),
    "The East African":               "https://www.theeastafrican.co.ke/tea/rss",
    "The Citizen · Tanzania":         _gnews("site:thecitizen.co.tz"),
    "Daily Monitor · Uganda":         "https://www.monitor.co.ug/uganda/rss",
    "Capital FM · Kenya":             _gnews("site:capitalfm.co.ke politics"),

    # Horn of Africa
    "Sudan Tribune":                  "https://sudantribune.com/feed/",
    "Sudans Post":                    "https://www.sudanspost.com/feed/",
    "Dabanga Sudan":                  "https://www.dabangasudan.org/en/feed",
    "Addis Standard":                 "https://addisstandard.com/feed/",
    "The Reporter · Ethiopia":        _gnews("site:thereporterethiopia.com"),
    "Garowe Online":                  _gnews("site:garoweonline.com"),

    # North Africa
    "Mada Masr":                      _gnews("site:madamasr.com"),
    "Ahram Online":                   _gnews("site:english.ahram.org.eg"),
    "Middle East Eye · North Africa": _gnews("site:middleeasteye.net North Africa"),
    "Le Monde · Afrique (EN via gnews)": _gnews("lemonde.fr Africa"),

    # Francophone West Africa — via Google News for English coverage
    "Mali coverage":                  _gnews("Mali junta OR JNIM OR FUAES"),
    "Burkina Faso coverage":          _gnews("Burkina Faso Traoré OR JNIM"),
    "Niger coverage":                 _gnews("Niger Tchiani OR Niamey"),
    "Côte d'Ivoire coverage":         _gnews("Côte d'Ivoire OR Ivory Coast Ouattara"),
    "Senegal coverage":               _gnews("Senegal Faye OR Sonko"),

    # Gulf-relevant (Sudan/UAE coverage)
    "The National · UAE":             _gnews("site:thenationalnews.com Sudan OR RSF"),

    # Lusophone
    "Angola/Mozambique coverage":     _gnews("Angola OR Mozambique politics"),

    # Specialized
    "Africa Intelligence · public":   _gnews("site:africaintelligence.com"),
}

# ── Tier 2: ANALYSIS / THINK TANKS — 36h window ──────────────────────────────

TIER2_ANALYSIS = {
    # A-tier
    "CSIS · Africa Program":          "https://www.csis.org/programs/africa-program/rss.xml",
    "ISS Africa · Today":             "https://issafrica.org/iss-today/rss",
    "ACSS · Africa Center":           _gnews("site:africacenter.org"),
    "Brookings · Africa Growth Initiative": _gnews("site:brookings.edu Africa Growth Initiative"),
    "CFR · Africa Program":           _gnews("site:cfr.org Africa"),
    "Carnegie · Africa":              _gnews("site:carnegieendowment.org Africa"),
    "Atlantic Council · Africa Center": _gnews("site:atlanticcouncil.org Africa Center"),
    "Chatham House · Africa":         _gnews("site:chathamhouse.org Africa"),
    "IISS · Africa":                  _gnews("site:iiss.org Africa"),
    "ICG · Africa":                   "https://www.crisisgroup.org/crisiswatch/database?location%5B%5D=4&rss=1",

    # B-tier
    "Stimson · Africa":               _gnews("site:stimson.org Africa OR Sahel"),
    "FPRI · Africa":                  _gnews("site:fpri.org Africa"),
    "RAND · Africa":                  _gnews("site:rand.org Africa"),
    "USIP · Africa":                  _gnews("site:usip.org Africa"),
    "SAIIA":                          "https://saiia.org.za/feed/",
    "Amani Africa":                   _gnews("site:amaniafrica-et.org"),
    "ECDPM":                          _gnews("site:ecdpm.org Africa"),
    "Mo Ibrahim Foundation":          _gnews("site:mo.ibrahim.foundation"),

    # Specialized / data
    "ACLED · Africa":                 _gnews("site:acleddata.com Africa"),
    "ISW Critical Threats · Africa":  "https://www.criticalthreats.org/rss/africa-file",
    "ENACT · organized crime":        _gnews("site:enact-africa.org"),

    # Africa Center for Strategic Studies (NDU)
    "Africa Center · NDU":            "https://africacenter.org/feed/",
}

# ── Tier 3: ACADEMIC — 72h window ────────────────────────────────────────────

TIER3_ACADEMIC = {
    "African Affairs (Oxford)":             _gnews("\"African Affairs\" journal Oxford"),
    "J. Modern African Studies (Cambridge)":_gnews("\"Journal of Modern African Studies\""),
    "Review of African Political Economy":  _gnews("\"Review of African Political Economy\""),
    "African Studies Review":               _gnews("\"African Studies Review\""),
    "J. African Economies":                 _gnews("\"Journal of African Economies\""),
    "African Security Review":              _gnews("\"African Security Review\""),
    "J. Eastern African Studies":           _gnews("\"Journal of Eastern African Studies\""),
    "Africa Today":                         _gnews("\"Africa Today\" Indiana University"),
}

# ── Tier 4: PRIMARY SOURCES — 24h window ─────────────────────────────────────

TIER4_PRIMARY = {
    # Continental
    "African Union · Press":          _gnews("site:au.int press"),
    "AfCFTA Secretariat":             _gnews("AfCFTA Secretariat"),
    "African Development Bank":       _gnews("site:afdb.org"),
    "Afreximbank":                    _gnews("site:afreximbank.com"),

    # RECs
    "ECOWAS":                         _gnews("site:ecowas.int"),
    "EAC":                            _gnews("site:eac.int"),
    "SADC":                           _gnews("site:sadc.int"),
    "IGAD":                           _gnews("site:igad.int"),

    # US government
    "State · Africa Bureau":          _gnews("State Department Bureau of African Affairs"),
    "USTR · Africa":                  _gnews("USTR Africa AGOA"),
    "DFC":                            _gnews("DFC US International Development Finance"),
    "AFRICOM · PA":                   _gnews("AFRICOM US Africa Command"),
    "Treasury · OFAC Africa actions": _gnews("OFAC Treasury Sudan OR DRC OR Africa designation"),
    "House Foreign Affairs Committee · Africa": _gnews("HFAC House Foreign Affairs Africa Subcommittee"),

    # Multilateral
    "UN OCHA · Africa":               _gnews("site:reliefweb.int Africa"),
    "MONUSCO":                        _gnews("MONUSCO DRC"),
    "UN Peacekeeping":                _gnews("UN peacekeeping Africa"),
    "ICC · press":                    _gnews("site:icc-cpi.int Africa"),
}

ALL_TIERS = {
    "tier1": TIER1_NEWS,
    "tier2": TIER2_ANALYSIS,
    "tier3": TIER3_ACADEMIC,
    "tier4": TIER4_PRIMARY,
}

# ─────────────────────────────────────────────────────────────────────────────
# FETCH HELPERS
# ─────────────────────────────────────────────────────────────────────────────

TIER_WINDOWS = {"tier1": 24, "tier2": 36, "tier3": 72, "tier4": 24}

USER_AGENT = "Mozilla/5.0 (compatible; CSIS-Africa-Daily-Brief/1.0)"

def _now_utc():
    return datetime.now(timezone.utc)

def _within_window(entry_struct_time, window_hours: int) -> bool:
    if not entry_struct_time:
        return True  # If we can't parse a date, include it
    try:
        entry_dt = datetime(*entry_struct_time[:6], tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return True
    return (_now_utc() - entry_dt) < timedelta(hours=window_hours)

def _fetch_feed(source_name: str, url: str, window_hours: int):
    """Fetch and parse one RSS feed. Returns list of normalized article dicts."""
    try:
        feed = feedparser.parse(url, request_headers={"User-Agent": USER_AGENT})
    except Exception as exc:
        return source_name, []
    articles = []
    for entry in getattr(feed, "entries", [])[:50]:  # Cap entries per feed
        published = (
            entry.get("published_parsed")
            or entry.get("updated_parsed")
            or None
        )
        if not _within_window(published, window_hours):
            continue
        articles.append({
            "source":   source_name,
            "title":    entry.get("title", "").strip(),
            "link":     entry.get("link", ""),
            "summary":  re.sub(r"<[^>]+>", "", entry.get("summary", ""))[:400],
            "published": entry.get("published", "") or entry.get("updated", ""),
        })
    return source_name, articles

def _fetch_tier(tier_name: str, max_workers: int = 16) -> dict:
    """Fetch all feeds in one tier in parallel."""
    feeds = ALL_TIERS[tier_name]
    window_h = TIER_WINDOWS[tier_name]
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {ex.submit(_fetch_feed, name, url, window_h): name for name, url in feeds.items()}
        for fut in as_completed(futures):
            try:
                name, articles = fut.result(timeout=30)
                if articles:
                    results[name] = articles
            except Exception:
                continue
    return results

# ─────────────────────────────────────────────────────────────────────────────
# MARKET DATA
# ─────────────────────────────────────────────────────────────────────────────

def _yahoo_quote(symbol: str) -> dict | None:
    """Fetch a Yahoo Finance quote. Returns dict with last/change or None."""
    url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={symbol}"
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = data.get("quoteResponse", {}).get("result", [])
        if not results:
            return None
        q = results[0]
        return {
            "value":      q.get("regularMarketPrice"),
            "change":     q.get("regularMarketChange"),
            "change_pct": q.get("regularMarketChangePercent"),
            "as_of":      q.get("regularMarketTime"),
            "currency":   q.get("currency"),
        }
    except (requests.RequestException, KeyError, ValueError, IndexError):
        return None

def _stooq_quote(symbol: str) -> dict | None:
    """Stooq fallback. Symbols differ from Yahoo."""
    url = f"https://stooq.com/q/l/?s={symbol}&f=sd2t2ohlcv&h&e=csv"
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
        r.raise_for_status()
        lines = r.text.strip().split("\n")
        if len(lines) < 2:
            return None
        row = lines[1].split(",")
        if len(row) < 7 or row[6] == "N/D":
            return None
        close_idx = 6
        open_idx  = 3
        try:
            close = float(row[close_idx])
            open_ = float(row[open_idx])
            change_pct = round((close - open_) / open_ * 100, 2) if open_ else None
        except (ValueError, ZeroDivisionError):
            close, change_pct = float(row[close_idx]), None
        return {"value": close, "change_pct": change_pct, "as_of": row[1]}
    except (requests.RequestException, ValueError, IndexError):
        return None

def _investing_com_quote(url_path: str, pattern: str) -> dict | None:
    """Lightweight scrape of a publicly visible price from investing.com."""
    try:
        r = requests.get(
            f"https://api.investing.com/api/financialdata/{url_path}/historical/chart/",
            headers={"User-Agent": USER_AGENT, "domain-id": "www", "Accept": "application/json"},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            return None
        last = data[-1]
        return {"value": round(float(last[1]), 2), "change_pct": None}
    except Exception:
        return None

def fetch_markets() -> dict:
    """Fetch market data for the strip. Each cell falls back gracefully."""
    out = {}

    # Brent — primary global oil benchmark (most important for African exporters)
    brent = _yahoo_quote("BZ=F") or _stooq_quote("cb.f")
    out["brent"] = brent

    # Gold
    gold = _yahoo_quote("GC=F") or _stooq_quote("gc.f")
    out["gold"] = gold

    # JSE All-Share — primary African equity benchmark
    jse = _yahoo_quote("^JN0U.JO") or _yahoo_quote("J203.L")
    out["jse_all_share"] = jse

    # NGX All-Share (Nigeria) — Yahoo doesn't carry well, leave for digest.py
    # to fill from Tier 1 news headlines (NGX always-include rule)
    out["ngx_all_share"] = None

    # USD/ZAR
    zar = _yahoo_quote("ZAR=X")
    out["usd_zar"] = zar

    # USD/NGN — same problem as NGX; left to news cycle
    out["usd_ngn"] = None

    # USD/EGP
    egp = _yahoo_quote("EGP=X")
    out["usd_egp"] = egp

    return out

# ─────────────────────────────────────────────────────────────────────────────
# OUTLET VOLUME TALLY — feeds press_delta_tracker
# ─────────────────────────────────────────────────────────────────────────────

OUTLET_NAME_MAP = {
    # collect.py source name → press_delta outlet_id
    "AllAfrica · Top":         "allafrica",
    "AllAfrica · Sudan":       "allafrica",
    "AllAfrica · Nigeria":     "allafrica",
    "AllAfrica · Kenya":       "allafrica",
    "AllAfrica · South Africa":"allafrica",
    "AllAfrica · Ethiopia":    "allafrica",
    "AllAfrica · Democratic Republic of Congo": "allafrica",
    "AllAfrica · Mali":        "allafrica",
    "AllAfrica · Burkina Faso":"allafrica",
    "AllAfrica · Niger":       "allafrica",
    "AllAfrica · Somalia":     "allafrica",
    "AllAfrica · Egypt":       "allafrica",
    "Africanews":              "africanews",
    "The Africa Report":       "africa_report",
    "Sudan Tribune":           "sudan_tribune",
    "Sudans Post":             "sudans_post",
    "Dabanga Sudan":           "dabanga",
    "Addis Standard":          "addis_standard",
    "Mail & Guardian":         "mg_za",
    "Daily Maverick":          "daily_maverick",
    "News24 · Africa":         "news24",
    "eNCA · Top":              "enca",
    "Premium Times":           "premium_times",
    "Punch · Nigeria":         "punch_ng",
    "TheCable":                "thecable_ng",
    "Daily Nation":            "daily_nation",
    "The Standard · Kenya":    "the_standard_ke",
    "The East African":        "east_african",
    "Mada Masr":               "mada_masr",
    "Ahram Online":            "ahram_online",
}

def _tally_outlet_volumes(tier1_articles: dict) -> dict:
    volumes = {}
    for source_name, articles in tier1_articles.items():
        outlet_id = OUTLET_NAME_MAP.get(source_name)
        if not outlet_id:
            continue
        volumes[outlet_id] = volumes.get(outlet_id, 0) + len(articles)
    return volumes

# ─────────────────────────────────────────────────────────────────────────────
# MAIN ASSEMBLY
# ─────────────────────────────────────────────────────────────────────────────

def collect_all(dry_run: bool = False) -> dict:
    """Run the full collection. Returns the dict consumed by digest.py."""
    start = time.time()
    print(f"[collect] Starting at {_now_utc().isoformat()}")

    out = {
        "collected_at": _now_utc().isoformat(),
        "tier1": [], "tier2": [], "tier3": [], "tier4": [],
        "markets": {},
        "monitor": {"sahel": [], "sudan_horn": [], "great_lakes": []},
        "press_delta": {},
        "baseline": build_baseline_references(),
    }

    # ── Tier 1 ──
    print("[collect] Tier 1 (news)…")
    t1 = _fetch_tier("tier1")
    out["tier1"] = [a for arts in t1.values() for a in arts]
    print(f"[collect]   → {sum(len(a) for a in t1.values())} articles from {len(t1)} sources")

    # ── Tier 2 ──
    print("[collect] Tier 2 (analysis)…")
    t2 = _fetch_tier("tier2")
    out["tier2"] = [a for arts in t2.values() for a in arts]
    print(f"[collect]   → {sum(len(a) for a in t2.values())} articles from {len(t2)} sources")

    # ── Tier 3 ──
    print("[collect] Tier 3 (academic)…")
    t3 = _fetch_tier("tier3")
    out["tier3"] = [a for arts in t3.values() for a in arts]
    print(f"[collect]   → {sum(len(a) for a in t3.values())} articles from {len(t3)} sources")

    # ── Tier 4 ──
    print("[collect] Tier 4 (primary)…")
    t4 = _fetch_tier("tier4")
    out["tier4"] = [a for arts in t4.values() for a in arts]
    print(f"[collect]   → {sum(len(a) for a in t4.values())} articles from {len(t4)} sources")

    # ── Markets ──
    print("[collect] Market data…")
    out["markets"] = fetch_markets()
    for k, v in out["markets"].items():
        if v is None:
            print(f"[collect]   ! {k}: no data (fallback or news-cycle fill)")

    # ── Monitor context ──
    out["monitor"]["sahel"]       = africa_monitor.build_context_block("Sahel")
    out["monitor"]["sudan_horn"]  = africa_monitor.build_context_block("Sudan & Horn")
    out["monitor"]["great_lakes"] = africa_monitor.build_context_block("Great Lakes")

    # ── Press delta tracker update ──
    if not dry_run:
        volumes = _tally_outlet_volumes(t1)
        press_delta_tracker.update_outlet_volumes(volumes)
    out["press_delta"] = press_delta_tracker.build_context_block()

    elapsed = time.time() - start
    print(f"[collect] Done in {elapsed:.1f}s")
    return out


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Don't persist tracker state")
    p.add_argument("--out", default="collected.json", help="Output path")
    args = p.parse_args()

    data = collect_all(dry_run=args.dry_run)
    with open(args.out, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"[collect] Wrote {args.out}")
