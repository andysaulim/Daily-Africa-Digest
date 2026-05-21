# Daily Africa Brief

Continental Africa daily intelligence brief from the **CSIS Korea Chair**, companion product to the [Daily Korea Digest](https://andysaulim.github.io/Daily-Korea-Digest) and [Daily China Digest](https://andysaulim.github.io/Daily-China-Digest).

Collects from 100+ sources across four tiers, generates an analyst-grade digest via Claude, and delivers a styled HTML email at **7:30 AM ET** alongside the China brief.

**Live archive:** `andysaulim.github.io/Daily-Africa-Digest` (planned)

---

## Latest Run

<!-- LATEST_RUN_START -->
| Metric | Value |
| --- | --- |
| Last generated | 2026-05-21 16:08 UTC |
| Digest date | Thursday, May 21, 2026 |
| Articles collected | 492 |
| Unique sources | 51 |
| Top stories | 3 |
| Overnight items | 4 |
| Word count | 3477 |
| Tier breakdown | Tier 1 (news): 454 · Tier 2 (analysis): 17 · Tier 3 (academic): 0 · Tier 4 (primary): 21 |
<!-- LATEST_RUN_END -->

---

## How It Works

```
collect.py          digest.py           render.py          send_email.py
100+ RSS feeds  -->  Claude Sonnet 4.6  -->  HTML email  -->  Gmail SMTP
  + market data       (Opus 4.6 retry)       + archive        + GitHub Pages
  + monitor state      + CSIS context        (public/)
  + press delta         (Sahel, Sudan,
                         Great Lakes)
```

**Pipeline:**

1. **Collect** — Parallel RSS fetch across four tiers, plus Brent / Gold / JSE All-Share / USD/ZAR / USD/EGP market data
2. **Enrich** — Loads CSIS baseline references (heads of state, sanctions architecture, 16 monitor locations, expert analyst roster, election calendar)
3. **Digest** — Claude Sonnet 4.6 generates the initial briefing; Opus 4.6 escalates on retry if content minimums fail
4. **Validate** — Pre-send gate checks word count, required-section coverage, source diversity, duplicates
5. **Render** — Email-safe table-based HTML matching China-register visual language (navy header, Arial/Georgia, saturated CSIS pills, dark Pan-African Press Delta panel)
6. **Send** — Gmail SMTP with retry
7. **Archive** — Pushes to GitHub Pages

---

## Coverage

| Tier | Sources | Window | Content |
| --- | --- | --- | --- |
| **1 — News** | 60+ feeds | 24h | AllAfrica (12 country slices), prestige outlets (Reuters/BBC/FT/Bloomberg/NYT/WaPo/Economist), pan-African (Africanews, The Africa Report, African Arguments), national majors (Mail & Guardian, Daily Maverick, News24, eNCA, Premium Times, Punch, TheCable, Daily Nation, East African), Sudan Tribune + Sudans Post + Dabanga, North Africa (Mada Masr, Ahram Online, Middle East Eye), francophone via Google News |
| **2 — Analysis** | 22 feeds | 36h | CSIS Africa Program, ISS Africa, ACSS, Brookings AGI, CFR, Carnegie, Atlantic Council, Chatham House, IISS, Crisis Group, Stimson, FPRI, RAND, USIP, SAIIA, Amani Africa, ECDPM, ACLED, ISW Critical Threats Project, Africa Center for Strategic Studies |
| **3 — Academic** | 8 feeds | 72h | African Affairs (Oxford), Journal of Modern African Studies, Review of African Political Economy, African Studies Review, Journal of African Economies, African Security Review, Journal of Eastern African Studies, Africa Today |
| **4 — Primary** | 18 feeds | 24h | AU press, AfCFTA Secretariat, AfDB, Afreximbank, ECOWAS, EAC, SADC, IGAD, State Africa Bureau, USTR, DFC, AFRICOM PA, Treasury OFAC actions, HFAC, UN OCHA, MONUSCO, ICC press |

**Always-include rule:** Africa stories from WSJ, NYT, Washington Post, Bloomberg, Financial Times, The Economist, Reuters, BBC, AP, AFP, Al Jazeera, The Guardian are always pulled in regardless of dedup window.

---

## Brief Structure (20 sections)

1. Header + RE line
2. Market strip (Brent, Gold, JSE, NGX, USD/ZAR, USD/EGP)
3. Δ Since Yesterday bar
4. Morning Memo (3 paragraphs)
5. Stat of the Day
6. Top Stories (3 leads)
7. Overnight Flash (4 items, 2x2 grid)
8. The Wire (5 short items)
9. Continental Bodies (AU, AES, EAC, SADC)
10. US–Africa Policy (third-country removals, OFAC, AFRICOM)
11. Congressional Watch (SFRC + HFAC + Select Committee)
12. Sahel Monitor (AES, JNIM, ISSP, Africa Corps)
13. Sudan & Horn Monitor (SAF/RSF, Somaliland, Ethiopia, Somalia)
14. Great Lakes Monitor (DRC/M23, Rwanda, Burundi)
15. External Powers Watch (China, Russia, UAE, Israel, Türkiye)
16. Critical Minerals & Energy (Brent, cobalt, gold)
17. Personnel & Elections
18. Expert Analysts (CSIS Africa, ISS, ACSS, Stimson, FPRI, ISW)
19. Calendar Watch (next 60 days)
20. Pan-African Press Delta (dark section)

---

## Monitor Locations (16 sites)

| Region | Sites |
| --- | --- |
| **Sahel** | Bamako · Gao · Ménaka · Kidal · Ouagadougou · Niamey |
| **Sudan & Horn** | Khartoum · Port Sudan · El Fasher · Nyala · Ed Damazin · Hargeisa |
| **Great Lakes** | Goma · Bukavu · Ruzizi Plain · Rutshuru |

Status tracker persists per-location state across runs (`trackers/africa_monitor.json`).

---

## Deployment

### One-time setup

1. Create the GitHub repo `Daily-Africa-Digest` and push these files
2. Set the same five secrets as Korea/China:
   - `ANTHROPIC_API_KEY`
   - `GMAIL_USER`
   - `GMAIL_APP_PASS` (Google account app password, not regular password)
   - `DIGEST_TO` (comma-separated recipient list)
   - `GH_PAT` (personal access token with `repo` scope, for auto-commits)
3. Set repo variable `WEB_URL` to `https://andysaulim.github.io/Daily-Africa-Digest`
4. Enable GitHub Pages on the repo (deploy from `public/`)

### First-run sanity

```bash
# Test collection only (no API spend, no email)
python run.py --dry-run

# Full pipeline locally without sending email
ANTHROPIC_API_KEY=sk-... python run.py --no-send
open public/index.html
```

### Manual workflow trigger

```bash
gh workflow run "Daily Africa Brief"
gh workflow run "Daily Africa Brief" -f dry_run=true
```

---

## Editorial Conventions

- Tight institutional voice. Active verbs. Numbers over adjectives.
- "May 21" not "21 MAY." Year always prominent.
- Every claim sourced. Body-count claims explicit ("DHQ claims X killed").
- No fabricated quotes, URLs, or attributions.
- Where African and Western press diverge on a dossier, the divergence is the story.

---

## Architecture Files

| File | Purpose | LOC |
| --- | --- | --- |
| `collect.py`               | RSS + markets + tracker context        | ~440 |
| `digest.py`                | Claude generation + validation         | ~280 |
| `render.py`                | HTML rendering (China register)        | ~430 |
| `send_email.py`            | Gmail SMTP with retry                  | ~80  |
| `databases.py`             | Baseline references                    | ~210 |
| `africa_monitor.py`        | 16-location status tracker             | ~150 |
| `press_delta_tracker.py`   | Outlet volume + framing dossiers       | ~190 |
| `update_readme.py`         | README run-metadata update             | ~75  |
| `run.py`                   | Orchestration entry point              | ~115 |
| `.github/workflows/daily-digest.yml` | Cron schedule              | ~55  |

---

## Maintenance

- **Monthly:** Update `databases.py` heads of state and monitored officials for personnel changes
- **Quarterly:** Refresh `databases.py` election calendar; review monitor location list for relevance
- **Annual:** Refresh expert analyst roster

---

## Acknowledgments

Built as the third in the CSIS Korea Chair daily-digest series, following Daily Korea Digest (7:00 AM ET) and Daily China Digest (7:30 AM ET). Companion product, not a replacement, for the CSIS Africa Program's analytical output.
