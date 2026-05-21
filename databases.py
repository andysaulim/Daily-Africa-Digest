"""
Africa Daily Brief — Baseline References

Static reference data that grounds Claude generation in digest.py.
Update cadence: monthly for personnel, quarterly for structural items.
"""

# ─────────────────────────────────────────────────────────────────────────────
# HEADS OF STATE (as of May 2026)
# ─────────────────────────────────────────────────────────────────────────────
# Use only verified current officeholders. Update on resignation, death,
# coup, or election.

HEADS_OF_STATE = {
    "South Africa":      {"name": "Cyril Ramaphosa",      "role": "President", "since": "2018"},
    "Nigeria":           {"name": "Bola Tinubu",          "role": "President", "since": "2023"},
    "Kenya":             {"name": "William Ruto",          "role": "President", "since": "2022"},
    "Egypt":             {"name": "Abdel Fattah el-Sisi", "role": "President", "since": "2014"},
    "Ethiopia":          {"name": "Abiy Ahmed",            "role": "Prime Minister", "since": "2018"},
    "DRC":               {"name": "Félix Tshisekedi",     "role": "President", "since": "2019"},
    "Rwanda":            {"name": "Paul Kagame",            "role": "President", "since": "2000"},
    "Uganda":            {"name": "Yoweri Museveni",        "role": "President", "since": "1986"},
    "Tanzania":          {"name": "Samia Suluhu Hassan",    "role": "President", "since": "2021"},
    "Ghana":             {"name": "John Dramani Mahama",    "role": "President", "since": "2025"},
    "Côte d'Ivoire":     {"name": "Alassane Ouattara",     "role": "President", "since": "2011"},
    "Senegal":           {"name": "Bassirou Diomaye Faye",  "role": "President", "since": "2024"},
    "Morocco":           {"name": "Mohammed VI",            "role": "King",      "since": "1999"},
    "Algeria":           {"name": "Abdelmadjid Tebboune",   "role": "President", "since": "2019"},
    "Tunisia":           {"name": "Kais Saied",             "role": "President", "since": "2019"},
    "Libya (GNU)":       {"name": "Abdulhamid Dbeibah",     "role": "Prime Minister", "since": "2021"},
    "Sudan (SAF)":       {"name": "Abdel Fattah al-Burhan", "role": "Chairman, Transitional Sovereignty Council", "since": "2019"},
    "South Sudan":       {"name": "Salva Kiir",             "role": "President", "since": "2011"},
    "Somalia":           {"name": "Hassan Sheikh Mohamud",  "role": "President", "since": "2022"},
    "Somaliland":        {"name": "Abdirahman Mohamed Abdullahi 'Irro'", "role": "President", "since": "2024"},
    "Angola":            {"name": "João Lourenço",          "role": "President", "since": "2017"},
    "Mozambique":        {"name": "Daniel Chapo",            "role": "President", "since": "2025"},
    "Zimbabwe":          {"name": "Emmerson Mnangagwa",      "role": "President", "since": "2017"},
    "Zambia":            {"name": "Hakainde Hichilema",      "role": "President", "since": "2021"},
    "Botswana":          {"name": "Duma Boko",                "role": "President", "since": "2024"},
    "Namibia":           {"name": "Netumbo Nandi-Ndaitwah",   "role": "President", "since": "2025"},
    "Cameroon":          {"name": "Paul Biya",                "role": "President", "since": "1982"},
    "Chad":              {"name": "Mahamat Idriss Déby",      "role": "President", "since": "2021"},
    "CAR":               {"name": "Faustin-Archange Touadéra","role": "President", "since": "2016"},
}

# Junta-led transitional governments (Sahel)
TRANSITIONAL_LEADERS = {
    "Mali":         {"name": "Assimi Goïta",      "role": "President of the Transition",  "since": "2021", "election_timeline": "indefinite"},
    "Burkina Faso": {"name": "Ibrahim Traoré",    "role": "President of the Transition",  "since": "2022", "election_timeline": "indefinite"},
    "Niger":        {"name": "Abdourahamane Tchiani", "role": "President of the Transition", "since": "2023", "election_timeline": "to 2030"},
    "Guinea":       {"name": "Mamadi Doumbouya",  "role": "President of the Transition",  "since": "2021", "election_timeline": "indefinite"},
    "Gabon":        {"name": "Brice Oligui Nguema", "role": "President",                  "since": "2023 (elected 2025)", "election_timeline": "transition complete"},
}

# Key foreign ministers / strategic officials worth tracking
MONITORED_OFFICIALS = {
    "South Africa": [
        {"name": "Ronald Lamola",   "role": "Minister of International Relations and Cooperation"},
        {"name": "Angie Motshekga", "role": "Minister of Defence"},
    ],
    "Nigeria": [
        {"name": "Yusuf Tuggar",    "role": "Minister of Foreign Affairs"},
        {"name": "Mohammed Badaru", "role": "Minister of Defence"},
    ],
    "Kenya": [
        {"name": "Musalia Mudavadi", "role": "Prime Cabinet Secretary, Foreign Affairs"},
    ],
    "Egypt": [
        {"name": "Badr Abdelatty",   "role": "Minister of Foreign Affairs"},
    ],
    "Ethiopia": [
        {"name": "Gedion Timothewos", "role": "Minister of Foreign Affairs"},
    ],
    "DRC": [
        {"name": "Thérèse Kayikwamba Wagner", "role": "Minister of Foreign Affairs"},
    ],
    "Sudan (SAF)": [
        {"name": "Mohieldin Salim", "role": "Acting Minister of Foreign Affairs"},
    ],
    "AU": [
        {"name": "Mahmoud Ali Youssouf", "role": "Chairperson of the AU Commission"},
        {"name": "Bankole Adeoye",        "role": "Commissioner for PAPS"},
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# CONFLICT LOCATIONS — 16 monitor sites (analogous to China 16-location BP)
# ─────────────────────────────────────────────────────────────────────────────

SAHEL_LOCATIONS = [
    {"id": "sahel-bamako",     "name": "Bamako",        "country": "Mali",         "context": "AES capital, Africa Corps HQ"},
    {"id": "sahel-gao",        "name": "Gao",           "country": "Mali",         "context": "April 25 attack site"},
    {"id": "sahel-menaka",     "name": "Ménaka",        "country": "Mali",         "context": "April 25 attack site, FLA stronghold"},
    {"id": "sahel-kidal",      "name": "Kidal",         "country": "Mali",         "context": "April 25 attack site, Tuareg corridor"},
    {"id": "sahel-ouagadougou","name": "Ouagadougou",   "country": "Burkina Faso", "context": "AES leadership, FUAES command"},
    {"id": "sahel-niamey",     "name": "Niamey",        "country": "Niger",        "context": "Base 101, Jan 29 ISSP attack"},
]

SUDAN_HORN_LOCATIONS = [
    {"id": "sh-khartoum",     "name": "Khartoum",      "country": "Sudan",      "context": "SAF capital, war front line"},
    {"id": "sh-port-sudan",   "name": "Port Sudan",    "country": "Sudan",      "context": "SAF interim seat, Russia base talks"},
    {"id": "sh-el-fasher",    "name": "El Fasher",     "country": "Sudan",      "context": "North Darfur, RSF genocide allegations"},
    {"id": "sh-nyala",        "name": "Nyala",         "country": "Sudan",      "context": "RSF-aligned government seat"},
    {"id": "sh-damazin",      "name": "Ed Damazin",    "country": "Sudan",      "context": "Blue Nile state SAF garrison"},
    {"id": "sh-hargeisa",     "name": "Hargeisa",      "country": "Somaliland", "context": "Self-declared capital, Israel recognition"},
]

GREAT_LAKES_LOCATIONS = [
    {"id": "gl-goma",         "name": "Goma",          "country": "DRC",         "context": "N. Kivu capital, M23-controlled since Jan 2025"},
    {"id": "gl-bukavu",       "name": "Bukavu",        "country": "DRC",         "context": "S. Kivu capital, contested"},
    {"id": "gl-ruzizi",       "name": "Ruzizi Plain",  "country": "DRC",         "context": "M23 May 15 withdrawal"},
    {"id": "gl-rutshuru",     "name": "Rutshuru",      "country": "DRC",         "context": "Wazalendo-M23 clashes"},
]

ALL_MONITOR_LOCATIONS = (
    [{**loc, "region": "Sahel"} for loc in SAHEL_LOCATIONS]
    + [{**loc, "region": "Sudan & Horn"} for loc in SUDAN_HORN_LOCATIONS]
    + [{**loc, "region": "Great Lakes"} for loc in GREAT_LAKES_LOCATIONS]
)

# ─────────────────────────────────────────────────────────────────────────────
# SANCTIONS ARCHITECTURE — OFAC active Africa programs
# ─────────────────────────────────────────────────────────────────────────────

OFAC_AFRICA_PROGRAMS = {
    "Sudan":        {"status": "active",  "last_major_action": "Jan 2026 — RSF genocide determination (State)"},
    "South Sudan":  {"status": "active",  "last_major_action": "standing"},
    "DRC":          {"status": "active",  "last_major_action": "April 30 2026 — Joseph Kabila designated"},
    "CAR":          {"status": "active",  "last_major_action": "standing"},
    "Somalia":      {"status": "active",  "last_major_action": "standing (Al-Shabaab focus)"},
    "Libya":        {"status": "active",  "last_major_action": "standing"},
    "Mali":         {"status": "limited", "last_major_action": "Wagner/Africa Corps secondary sanctions"},
    "Burundi":      {"status": "lifted",  "last_major_action": "lifted Nov 2021"},
    "Zimbabwe":     {"status": "lifted",  "last_major_action": "program ended March 2024"},
    "Ethiopia":     {"status": "lifted",  "last_major_action": "EO 14046 revoked"},
    "Eritrea":      {"status": "limited", "last_major_action": "Tigray-era designations"},
}

# US trade preferences — AGOA status
AGOA_STATUS = {
    "current": "lapsed",
    "expiry": "September 30, 2025",
    "replacement_legislation": "circulating between SFRC and HFAC; no consolidated text yet",
    "eligible_countries_at_expiry": 32,
    "next_action_window": "FY26 trade legislative track",
}

# ─────────────────────────────────────────────────────────────────────────────
# REGIONAL ECONOMIC COMMUNITIES & CONTINENTAL BODIES
# ─────────────────────────────────────────────────────────────────────────────

RECS = {
    "AU":         {"members": 55, "seat": "Addis Ababa", "leader": "Mahmoud Ali Youssouf (AUC Chair)"},
    "ECOWAS":     {"members": 12, "seat": "Abuja",       "leader": "Omar Touray (President of Commission)",
                   "note": "AES (Mali, Burkina, Niger) formally exited Jan 2025"},
    "EAC":        {"members": 8,  "seat": "Arusha",      "leader": "Veronica Nduva (Secretary General)"},
    "SADC":       {"members": 16, "seat": "Gaborone",    "leader": "Elias Magosi (Executive Secretary)"},
    "IGAD":       {"members": 8,  "seat": "Djibouti",    "leader": "Workneh Gebeyehu (Executive Secretary)"},
    "AES":        {"members": 3,  "seat": "Niamey (rotating)", "leader": "Confederation of Sahel States",
                   "note": "Mali, Burkina Faso, Niger; common-currency timeline unresolved"},
    "AfCFTA":     {"members": 54, "seat": "Accra",       "leader": "Wamkele Mene (Secretary General)"},
}

# ─────────────────────────────────────────────────────────────────────────────
# ELECTION CALENDAR (forward-looking)
# ─────────────────────────────────────────────────────────────────────────────

ELECTION_CALENDAR_2026 = [
    {"date": "2026-09-13", "country": "Côte d'Ivoire", "type": "Presidential",
     "note": "Ouattara intentions unclear; opposition coalition negotiations ongoing"},
    {"date": "2026-10-25", "country": "Tanzania",      "type": "General",
     "note": "CCM continuity expected; opposition crackdown questions"},
    {"date": "2026-TBD",   "country": "South Africa",  "type": "Local government",
     "note": "ANC framing in flux per May 20 2026 announcement"},
    {"date": "2026-11",    "country": "Seychelles",    "type": "Presidential & legislative",
     "note": "Standing date"},
    {"date": "2027-02",    "country": "Cameroon",      "type": "Presidential",
     "note": "Biya succession question dominant"},
    {"date": "2027-Q1",    "country": "Nigeria",       "type": "Presidential",
     "note": "Tinubu re-election cycle opening"},
]

# ─────────────────────────────────────────────────────────────────────────────
# EXPERT ANALYST ROSTER (track for op-eds, briefings, public commentary)
# ─────────────────────────────────────────────────────────────────────────────

EXPERT_ANALYSTS = {
    "CSIS Africa Program": [
        {"name": "Cameron Hudson",     "role": "Senior Fellow, Africa Program (head)"},
        {"name": "Mvemba Phezo Dizolele", "role": "Director, Africa Program"},
    ],
    "ISS Africa": [
        {"name": "Liesl Louw-Vaudran", "role": "Senior Researcher, ISS Pretoria"},
        {"name": "Andrews Atta-Asamoah", "role": "Programme Head, ISS Pretoria"},
    ],
    "Stimson Center": [
        {"name": "Aly Verjee",          "role": "Senior Fellow, Africa program"},
        {"name": "Annette Weber",       "role": "Sahel and Horn coverage"},
    ],
    "FPRI": [
        {"name": "Adam Lammon",         "role": "Africa Program"},
    ],
    "Brookings AGI": [
        {"name": "Aloysius Uche Ordu",  "role": "Director, Africa Growth Initiative"},
        {"name": "Landry Signé",        "role": "Senior Fellow, AGI"},
    ],
    "Atlantic Council Africa Center": [
        {"name": "Rama Yade",           "role": "Senior Director, Africa Center"},
    ],
    "Chatham House Africa": [
        {"name": "Alex Vines",          "role": "Director, Africa Programme"},
    ],
    "ISW Critical Threats Project": [
        {"name": "Liam Karr",           "role": "Africa Team Lead"},
    ],
    "ACSS (NDU)": [
        {"name": "Joseph Siegle",       "role": "Director of Research"},
    ],
}

# ─────────────────────────────────────────────────────────────────────────────
# AGGREGATE EXPORT — for digest.py consumption
# ─────────────────────────────────────────────────────────────────────────────

def build_baseline_references() -> dict:
    """Return the structured baseline reference dict consumed by digest.py."""
    return {
        "heads_of_state": HEADS_OF_STATE,
        "transitional_leaders": TRANSITIONAL_LEADERS,
        "monitored_officials": MONITORED_OFFICIALS,
        "sahel_locations": SAHEL_LOCATIONS,
        "sudan_horn_locations": SUDAN_HORN_LOCATIONS,
        "great_lakes_locations": GREAT_LAKES_LOCATIONS,
        "all_monitor_locations": ALL_MONITOR_LOCATIONS,
        "ofac_africa_programs": OFAC_AFRICA_PROGRAMS,
        "agoa_status": AGOA_STATUS,
        "recs": RECS,
        "election_calendar": ELECTION_CALENDAR_2026,
        "expert_analysts": EXPERT_ANALYSTS,
    }
