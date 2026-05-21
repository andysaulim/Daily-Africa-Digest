"""
Africa Daily Brief — HTML Renderer

Takes the validated digest dict and produces email-safe HTML matching
the v2 preview design. China visual register:
- Navy #1B2A4A header + saturated CSIS palette
- Arial/Georgia type stack
- Status pills (rounded), colored left-borders on cards
- Dark Pan-African Press Delta panel
- Email-safe inline CSS, table-based layout

Mirrors render.py architecture from Daily-China-Digest.
"""

import html as _html
import re as _re
from datetime import datetime, timezone
from urllib.parse import urlparse as _urlparse

# ─────────────────────────────────────────────────────────────────────────────
# UTILITIES
# ─────────────────────────────────────────────────────────────────────────────

def _esc(s) -> str:
    if s is None:
        return ""
    return _html.escape(str(s), quote=True)

def _as_dict(item, text_key: str = "text") -> dict:
    """Normalize a list item Claude may return as a string instead of a dict."""
    if isinstance(item, dict):
        return item
    return {text_key: str(item) if item is not None else ""}

def _clean_src(raw: str) -> str:
    if not raw:
        return ""
    stripped = str(raw).strip()
    if _re.match(r"^https?://", stripped) and " " not in stripped:
        try:
            host = _urlparse(stripped).hostname or ""
            return host[4:] if host.startswith("www.") else host
        except Exception:
            return raw
    return stripped

def _market_cell(label: str, value, change_pct=None, sub: str = "") -> str:
    """Render one market cell. Color the change in red/green based on sign."""
    if value is None:
        value_str = "— pending"
        change_html = '<div style="font-size:11px;color:rgba(255,255,255,0.55);">no live data this run</div>'
    else:
        value_str = str(value)
        if change_pct is None:
            change_html = f'<div style="font-size:11px;color:rgba(255,255,255,0.65);">{_esc(sub)}</div>'
        else:
            try:
                pct = float(change_pct)
                color = "#7fb87f" if pct >= 0 else "#e8a0a0"
                sign = "+" if pct >= 0 else ""
                change_html = f'<div style="font-size:11px;color:{color};">{sign}{pct:.2f}% &nbsp;·&nbsp; {_esc(sub)}</div>'
            except (TypeError, ValueError):
                change_html = f'<div style="font-size:11px;color:rgba(255,255,255,0.65);">{_esc(sub)}</div>'
    return f"""
      <div style="font-family:'Courier New',Courier,monospace;font-size:9px;letter-spacing:1.3px;text-transform:uppercase;color:rgba(255,255,255,0.55);margin-bottom:4px;">{_esc(label)}</div>
      <div style="font-size:18px;font-weight:bold;color:#ffffff;">{_esc(value_str)}</div>
      {change_html}"""

# ─────────────────────────────────────────────────────────────────────────────
# COMPONENT BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def _build_header(d: dict) -> str:
    date_str = _esc(d.get("digest_date", "—"))
    re_line  = _esc(d.get("re_line", ""))
    return f"""
<tr><td style="background:#1B2A4A;padding:28px 32px 24px 32px;color:#ffffff;">
  <div style="font-family:'Courier New',Courier,monospace;font-size:11px;letter-spacing:1.4px;text-transform:uppercase;color:rgba(255,255,255,0.55);margin-bottom:10px;">CSIS · Daily Africa Brief</div>
  <div style="font-family:Georgia,'Times New Roman',serif;font-size:30px;line-height:1.15;color:#ffffff;font-weight:400;letter-spacing:-0.5px;margin-bottom:14px;">Africa Daily Brief</div>
  <div style="font-family:Arial,sans-serif;font-size:13px;color:rgba(255,255,255,0.75);line-height:1.55;">{date_str} &nbsp;·&nbsp; 7:30 AM ET</div>
  <div style="border-top:1px solid rgba(255,255,255,0.18);margin:18px 0 14px 0;"></div>
  <div style="font-family:'Courier New',Courier,monospace;font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:rgba(255,255,255,0.55);margin-bottom:6px;">RE</div>
  <div style="font-family:Arial,sans-serif;font-size:14px;line-height:1.6;color:rgba(255,255,255,0.92);">{re_line}</div>
</td></tr>
"""

def _build_market_strip(d: dict) -> str:
    m = d.get("market_strip", {}) or {}

    def cell(key, label, sub_default=""):
        v = m.get(key) or {}
        if isinstance(v, str):
            return _market_cell(label, v, None, sub_default)
        return _market_cell(
            label,
            v.get("value"),
            v.get("change_pct"),
            v.get("sub", sub_default),
        )

    return f"""
<tr><td style="background:#1B2A4A;padding:0;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">
    <tr>
      <td width="50%" style="padding:14px 18px;background:#1B2A4A;border-right:1px solid rgba(255,255,255,0.10);color:#ffffff;font-family:Arial,sans-serif;">{cell("brent", "Brent crude")}</td>
      <td width="50%" style="padding:14px 18px;background:#1B2A4A;color:#ffffff;font-family:Arial,sans-serif;">{cell("gold", "Gold")}</td>
    </tr>
    <tr>
      <td width="50%" style="padding:14px 18px;background:#22325a;border-right:1px solid rgba(255,255,255,0.10);border-top:1px solid rgba(255,255,255,0.10);color:#ffffff;font-family:Arial,sans-serif;">{cell("jse_all_share", "FTSE/JSE All-Share")}</td>
      <td width="50%" style="padding:14px 18px;background:#22325a;border-top:1px solid rgba(255,255,255,0.10);color:#ffffff;font-family:Arial,sans-serif;">{cell("ngx_all_share", "NGX All-Share")}</td>
    </tr>
    <tr>
      <td width="50%" style="padding:14px 18px;background:#293b66;border-right:1px solid rgba(255,255,255,0.10);border-top:1px solid rgba(255,255,255,0.10);color:#ffffff;font-family:Arial,sans-serif;">{cell("usd_zar", "USD / ZAR")}</td>
      <td width="50%" style="padding:14px 18px;background:#293b66;border-top:1px solid rgba(255,255,255,0.10);color:#ffffff;font-family:Arial,sans-serif;">{cell("usd_egp", "USD / EGP")}</td>
    </tr>
  </table>
</td></tr>
"""

def _build_delta_bar(d: dict) -> str:
    items = (d.get("delta_since_yesterday") or {}).get("items") or []
    palettes = [
        ("rgba(127,184,127,0.15)", "#7fb87f", "rgba(127,184,127,0.40)"),
        ("rgba(192,57,43,0.18)",   "#e8a0a0", "rgba(192,57,43,0.45)"),
        ("rgba(212,172,13,0.15)",  "#e8c876", "rgba(212,172,13,0.40)"),
        ("rgba(41,128,185,0.15)",  "#9ec8e8", "rgba(41,128,185,0.40)"),
        ("rgba(142,68,173,0.15)",  "#c9a0e3", "rgba(142,68,173,0.40)"),
    ]
    chips = []
    for i, item in enumerate(items[:8]):
        bg, fg, bd = palettes[i % len(palettes)]
        chips.append(
            f'<span style="display:inline-block;background:{bg};color:{fg};padding:3px 9px;margin-right:6px;border:1px solid {bd};">{_esc(item)}</span>'
        )
    return f"""
<tr><td style="background:#0a0f1e;padding:16px 32px;">
  <div style="font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,0.55);margin-bottom:10px;">Δ Since Yesterday</div>
  <div style="font-family:Arial,sans-serif;font-size:12px;line-height:1.9;color:rgba(255,255,255,0.92);">{''.join(chips)}</div>
</td></tr>
"""

def _build_morning_memo(d: dict) -> str:
    memo = d.get("morning_memo") or []
    paragraphs = "".join(
        f'<p style="margin:0 0 12px 0;">{_esc(p)}</p>' if isinstance(p, str)
        else f'<p style="margin:0 0 12px 0;"><strong>{_esc(p.get("lead",""))}</strong> {_esc(p.get("text",""))}</p>'
        for p in memo
    )
    return f"""
<tr><td style="padding:24px 32px 8px 32px;background:#ffffff;">
  <div style="display:inline-block;background:#1B2A4A;color:#ffffff;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:2px;margin-bottom:14px;">Morning Memo</div>
  <div style="font-family:Georgia,'Times New Roman',serif;font-size:21px;line-height:1.4;color:#1B2A4A;margin-bottom:14px;letter-spacing:-0.3px;">Three notes for the desk this morning</div>
  <div style="border-left:3px solid #1B2A4A;padding-left:16px;font-family:Arial,sans-serif;font-size:14px;line-height:1.7;color:#2c2c2c;">{paragraphs}</div>
</td></tr>
"""

def _build_stat_of_day(d: dict) -> str:
    s = d.get("stat_of_day") or {}
    if not s or not isinstance(s, dict):
        return ""
    number = _esc(s.get("number", ""))
    label  = _esc(s.get("label", ""))
    ctx    = _esc(s.get("context", ""))
    src    = _esc(s.get("source", ""))
    return f"""
<tr><td style="padding:8px 32px 24px 32px;background:#ffffff;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#1B2A4A;">
    <tr>
      <td width="40%" style="padding:28px 24px;background:#1B2A4A;border-right:1px solid rgba(255,255,255,0.12);">
        <div style="font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:rgba(255,255,255,0.55);margin-bottom:8px;">Stat of the Day</div>
        <div style="font-family:Georgia,'Times New Roman',serif;font-size:60px;line-height:1;color:#ffffff;font-weight:bold;letter-spacing:-2px;">{number}</div>
      </td>
      <td width="60%" style="padding:28px 24px;background:#1B2A4A;">
        <div style="font-family:Arial,sans-serif;font-size:15px;line-height:1.55;color:#ffffff;margin-bottom:10px;font-weight:bold;">{label}</div>
        <div style="font-family:Arial,sans-serif;font-size:12px;line-height:1.6;color:rgba(255,255,255,0.75);">{ctx}</div>
        <div style="font-family:'Courier New',Courier,monospace;font-size:10px;color:rgba(255,255,255,0.55);margin-top:12px;letter-spacing:0.5px;">Source · {src}</div>
      </td>
    </tr>
  </table>
</td></tr>
"""

def _build_top_stories(d: dict) -> str:
    stories = d.get("top_stories") or []
    blocks = []
    for s in stories:
        s = _as_dict(s, "headline")
        kicker  = _esc(s.get("kicker", ""))
        headline= _esc(s.get("headline", ""))
        dek     = _esc(s.get("dek", ""))
        src     = _esc(s.get("source_line", ""))
        blocks.append(f"""
<tr><td style="padding:0 32px 12px 32px;background:#ffffff;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#F8F9FA;border-left:4px solid #2980B9;">
    <tr><td style="padding:18px 22px;">
      <div style="font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:#2980B9;margin-bottom:8px;">{kicker}</div>
      <div style="font-family:Georgia,'Times New Roman',serif;font-size:18px;line-height:1.35;color:#1B2A4A;margin-bottom:10px;">{headline}</div>
      <div style="font-family:Arial,sans-serif;font-size:13px;line-height:1.65;color:#2c2c2c;margin-bottom:12px;">{dek}</div>
      <div style="font-family:'Courier New',Courier,monospace;font-size:10px;color:#6b7280;letter-spacing:0.5px;">{src}</div>
    </td></tr>
  </table>
</td></tr>
""")
    header = """
<tr><td style="padding:24px 32px 8px 32px;background:#ffffff;">
  <div style="display:inline-block;background:#2980B9;color:#ffffff;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:2px;margin-bottom:6px;">Top Stories</div>
  <div style="font-family:Arial,sans-serif;font-size:11px;color:#6b7280;margin-bottom:18px;text-transform:uppercase;letter-spacing:0.5px;">""" + f"{len(stories)} leads · continent-wide</div></td></tr>"
    return header + "".join(blocks)

def _build_overnight_flash(d: dict) -> str:
    items = d.get("overnight_flash") or []
    # 2x2 grid
    cells = []
    for it in items[:4]:
        it = _as_dict(it, "headline")
        kicker  = _esc(it.get("kicker") or it.get("country_or_kicker", ""))
        headline= _esc(it.get("headline", ""))
        dek     = _esc(it.get("dek", ""))
        cells.append(f"""
<td width="50%" valign="top" style="padding:0 8px 12px 0;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#fafafa;border-left:3px solid #C0392B;">
    <tr><td style="padding:14px 16px;">
      <div style="font-family:'Courier New',Courier,monospace;font-size:9px;color:#C0392B;letter-spacing:1.2px;text-transform:uppercase;margin-bottom:6px;">{kicker}</div>
      <div style="font-family:Arial,sans-serif;font-size:13px;line-height:1.5;color:#1B2A4A;font-weight:bold;margin-bottom:6px;">{headline}</div>
      <div style="font-family:Arial,sans-serif;font-size:12px;line-height:1.55;color:#444;">{dek}</div>
    </td></tr>
  </table>
</td>""")
    # Pair into rows
    rows = []
    for i in range(0, len(cells), 2):
        pair = cells[i:i+2]
        rows.append(f"<tr>{''.join(pair)}</tr>")
    return f"""
<tr><td style="padding:24px 32px 8px 32px;background:#ffffff;">
  <div style="display:inline-block;background:#C0392B;color:#ffffff;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:2px;margin-bottom:6px;">Overnight Flash</div>
  <div style="font-family:Arial,sans-serif;font-size:11px;color:#6b7280;margin-bottom:18px;text-transform:uppercase;letter-spacing:0.5px;">{len(items)} items · 24h window</div>
</td></tr>
<tr><td style="padding:0 32px 24px 32px;background:#ffffff;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">{''.join(rows)}</table>
</td></tr>
"""

def _build_the_wire(d: dict) -> str:
    items = d.get("the_wire") or []
    rows = []
    for i, it in enumerate(items):
        it = _as_dict(it)
        kicker = _esc(it.get("kicker", ""))
        text   = _esc(it.get("text", ""))
        is_last = (i == len(items) - 1)
        border = "" if is_last else "border-bottom:1px solid #e5e7eb;"
        rows.append(f"""
<tr><td style="padding:12px 0;{border}font-family:Arial,sans-serif;font-size:13px;line-height:1.55;color:#2c2c2c;">
  <span style="font-family:'Courier New',Courier,monospace;font-size:10px;color:#6b7280;text-transform:uppercase;letter-spacing:0.8px;">{kicker} · </span>
  {text}
</td></tr>""")
    return f"""
<tr><td style="padding:0 32px 24px 32px;background:#ffffff;">
  <div style="display:inline-block;background:#6b7280;color:#ffffff;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:2px;margin-bottom:14px;">The Wire</div>
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-top:1px solid #e5e7eb;">{''.join(rows)}</table>
</td></tr>
"""

def _build_card_grid(items: list, accent: str, label: str, kicker_color: str = "#1B2A4A") -> str:
    """Render a 2-column card grid for sections like Continental Bodies, External Powers, US-Africa."""
    cells = []
    for it in items[:4]:
        it = _as_dict(it, "headline")
        kicker   = _esc(it.get("kicker", ""))
        headline = _esc(it.get("headline", ""))
        dek      = _esc(it.get("dek", ""))
        cells.append(f"""
<td width="50%" valign="top" style="padding:0 8px 12px 0;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#fafafa;border-left:3px solid {accent};">
    <tr><td style="padding:14px 16px;">
      <div style="font-family:'Courier New',Courier,monospace;font-size:9px;color:{accent};letter-spacing:1.2px;text-transform:uppercase;margin-bottom:6px;">{kicker}</div>
      <div style="font-family:Arial,sans-serif;font-size:13px;line-height:1.55;color:{kicker_color};font-weight:bold;margin-bottom:4px;">{headline}</div>
      <div style="font-family:Arial,sans-serif;font-size:12px;line-height:1.55;color:#444;">{dek}</div>
    </td></tr>
  </table>
</td>""")
    rows = []
    for i in range(0, len(cells), 2):
        rows.append(f"<tr>{''.join(cells[i:i+2])}</tr>")
    return f"""
<tr><td style="padding:24px 32px 8px 32px;background:#ffffff;">
  <div style="display:inline-block;background:{accent};color:#ffffff;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:2px;margin-bottom:18px;">{label}</div>
</td></tr>
<tr><td style="padding:0 32px 24px 32px;background:#ffffff;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%">{''.join(rows)}</table>
</td></tr>
"""

def _build_monitor_block(d: dict, key: str, label: str) -> str:
    block = d.get(key) or {}
    if not isinstance(block, dict):
        block = {}
    paragraphs = []
    for k, v in block.items():
        if k.startswith("source"):
            continue
        if isinstance(v, str):
            paragraphs.append(f'<p style="margin:0 0 10px 0;">{_esc(v)}</p>')
    sources = block.get("sources") or block.get("source_line") or ""
    return f"""
<tr><td style="padding:24px 32px 8px 32px;background:#ffffff;">
  <div style="display:inline-block;background:#8E44AD;color:#ffffff;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:2px;margin-bottom:18px;">{label}</div>
</td></tr>
<tr><td style="padding:0 32px 24px 32px;background:#ffffff;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#faf7fc;border-left:4px solid #8E44AD;">
    <tr><td style="padding:18px 22px;">
      <div style="font-family:Arial,sans-serif;font-size:14px;line-height:1.7;color:#2c2c2c;">{''.join(paragraphs)}</div>
      <div style="font-family:'Courier New',Courier,monospace;font-size:10px;color:#6b7280;letter-spacing:0.5px;margin-top:14px;text-transform:uppercase;">{_esc(sources)}</div>
    </td></tr>
  </table>
</td></tr>
"""

def _build_congressional_watch(d: dict) -> str:
    block = d.get("congressional_watch") or {}
    text  = block if isinstance(block, str) else block.get("text", "")
    return f"""
<tr><td style="padding:24px 32px 8px 32px;background:#ffffff;">
  <div style="display:inline-block;background:#C0392B;color:#ffffff;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:2px;margin-bottom:18px;">Congressional Watch</div>
</td></tr>
<tr><td style="padding:0 32px 24px 32px;background:#ffffff;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#fafafa;border-left:3px solid #C0392B;">
    <tr><td style="padding:18px 22px;font-family:Arial,sans-serif;font-size:14px;line-height:1.65;color:#2c2c2c;">{_esc(text)}</td></tr>
  </table>
</td></tr>
"""

def _build_personnel_elections(d: dict) -> str:
    items = d.get("personnel_elections") or []
    rows = []
    for i, it in enumerate(items):
        it = _as_dict(it)
        date_label = _esc(it.get("date_label", ""))
        text       = _esc(it.get("text", ""))
        border = "" if i == len(items) - 1 else "border-bottom:1px solid #e5e7eb;"
        rows.append(f"""
<tr>
  <td width="25%" style="padding:14px 12px 14px 0;font-family:'Courier New',Courier,monospace;font-size:11px;color:#1B2A4A;text-transform:uppercase;letter-spacing:0.5px;font-weight:bold;{border}">{date_label}</td>
  <td style="padding:14px 0;font-family:Arial,sans-serif;font-size:13px;line-height:1.55;color:#2c2c2c;{border}">{text}</td>
</tr>""")
    return f"""
<tr><td style="padding:24px 32px 8px 32px;background:#ffffff;">
  <div style="display:inline-block;background:#2C3E50;color:#ffffff;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:2px;margin-bottom:18px;">Personnel &amp; Elections</div>
</td></tr>
<tr><td style="padding:0 32px 24px 32px;background:#ffffff;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-top:1px solid #e5e7eb;">{''.join(rows)}</table>
</td></tr>
"""

def _build_experts(d: dict) -> str:
    items = d.get("expert_analysts") or []
    rows = []
    for i, it in enumerate(items):
        it = _as_dict(it, "institution")
        institution = _esc(it.get("institution", ""))
        text        = _esc(it.get("text", ""))
        border = "" if i == len(items) - 1 else "border-bottom:1px solid #e5e7eb;"
        rows.append(f"""
<tr><td style="padding:14px 0;{border}">
  <div style="font-family:Arial,sans-serif;font-size:13px;line-height:1.55;color:#2c2c2c;">
    <strong style="color:#1B2A4A;">{institution}:</strong> {text}
  </div>
</td></tr>""")
    return f"""
<tr><td style="padding:24px 32px 8px 32px;background:#ffffff;">
  <div style="display:inline-block;background:#2980B9;color:#ffffff;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:2px;margin-bottom:18px;">Expert Analysts</div>
</td></tr>
<tr><td style="padding:0 32px 24px 32px;background:#ffffff;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-top:1px solid #e5e7eb;">{''.join(rows)}</table>
</td></tr>
"""

def _build_calendar(d: dict) -> str:
    items = d.get("calendar_watch") or []
    rows = []
    for i, it in enumerate(items):
        it = _as_dict(it)
        month_label = _esc(it.get("month", ""))
        day_label   = _esc(it.get("day", ""))
        text        = _esc(it.get("text", ""))
        border = "" if i == len(items) - 1 else "border-bottom:1px solid #e5e7eb;"
        rows.append(f"""
<tr>
  <td width="80" valign="top" style="padding:14px 16px 14px 0;{border}font-family:Georgia,serif;color:#1B2A4A;">
    <div style="font-size:11px;text-transform:uppercase;letter-spacing:1.2px;color:#6b7280;">{month_label}</div>
    <div style="font-size:24px;font-weight:bold;line-height:1;">{day_label}</div>
  </td>
  <td style="padding:14px 0;{border}font-family:Arial,sans-serif;font-size:13px;line-height:1.55;color:#2c2c2c;">{text}</td>
</tr>""")
    return f"""
<tr><td style="padding:24px 32px 8px 32px;background:#ffffff;">
  <div style="display:inline-block;background:#2C3E50;color:#ffffff;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:2px;margin-bottom:18px;">Calendar Watch</div>
</td></tr>
<tr><td style="padding:0 32px 24px 32px;background:#ffffff;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-top:1px solid #e5e7eb;">{''.join(rows)}</table>
</td></tr>
"""

def _build_minerals_energy(d: dict) -> str:
    block = d.get("critical_minerals_energy") or {}
    paragraphs = []
    for k, v in block.items():
        if isinstance(v, str):
            paragraphs.append(f'<p style="margin:0 0 10px 0;">{_esc(v)}</p>')
    return f"""
<tr><td style="padding:24px 32px 8px 32px;background:#ffffff;">
  <div style="display:inline-block;background:#D4AC0D;color:#ffffff;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:2px;margin-bottom:18px;">Critical Minerals &amp; Energy</div>
</td></tr>
<tr><td style="padding:0 32px 24px 32px;background:#ffffff;">
  <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#fffbf0;border-left:4px solid #D4AC0D;">
    <tr><td style="padding:18px 22px;">
      <div style="font-family:Arial,sans-serif;font-size:14px;line-height:1.7;color:#2c2c2c;">{''.join(paragraphs)}</div>
    </td></tr>
  </table>
</td></tr>
"""

def _build_press_delta(d: dict) -> str:
    block = d.get("press_delta") or {}
    paragraphs = []
    for k, v in block.items():
        if isinstance(v, str) and not k.startswith("source"):
            paragraphs.append(f'<p style="margin:0 0 12px 0;">{_esc(v)}</p>')
    sources = block.get("sources") or block.get("source_line") or ""
    return f"""
<tr><td style="background:#1a1f2e;padding:32px;color:#ffffff;">
  <div style="display:inline-block;background:rgba(255,255,255,0.12);color:#ffffff;font-family:'Courier New',Courier,monospace;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;padding:5px 12px;border-radius:2px;margin-bottom:14px;">Pan-African Press Delta</div>
  <div style="font-family:Georgia,'Times New Roman',serif;font-size:22px;line-height:1.35;color:#ffffff;margin-bottom:18px;letter-spacing:-0.3px;">Where African and Western press diverge today</div>
  <div style="border-top:1px solid rgba(255,255,255,0.15);padding-top:18px;">
    <div style="font-family:Arial,sans-serif;font-size:14px;line-height:1.7;color:rgba(255,255,255,0.92);">{''.join(paragraphs)}</div>
  </div>
  <div style="font-family:'Courier New',Courier,monospace;font-size:10px;color:rgba(255,255,255,0.5);letter-spacing:0.5px;margin-top:18px;text-transform:uppercase;">{_esc(sources)}</div>
</td></tr>
"""

def _build_footer(d: dict) -> str:
    note = _esc(d.get("footer_note", "Every claim sourced. No fabricated quotes, URLs, or attributions."))
    return f"""
<tr><td style="padding:22px 32px;background:#F5F5F5;text-align:center;font-family:Arial,sans-serif;font-size:11px;line-height:1.7;color:#6b7280;">
  CSIS · Daily Africa Brief · Vol. 1<br>
  {note}<br>
  Companion to Daily Korea Digest and Daily China Digest.
</td></tr>
"""

# ─────────────────────────────────────────────────────────────────────────────
# MAIN RENDER
# ─────────────────────────────────────────────────────────────────────────────

def render_html(digest: dict) -> str:
    """Render a validated digest dict to email-safe HTML."""
    title = _esc(digest.get("digest_date", "Africa Daily Brief"))

    sections = [
        _build_header(digest),
        _build_market_strip(digest),
        _build_delta_bar(digest),
        _build_morning_memo(digest),
        _build_stat_of_day(digest),
        _build_top_stories(digest),
        _build_overnight_flash(digest),
        _build_the_wire(digest),
        _build_card_grid(digest.get("continental_bodies") or [], "#1B2A4A", "Continental Bodies"),
        _build_card_grid(digest.get("us_africa_policy") or [], "#C0392B", "US–Africa Policy"),
        _build_congressional_watch(digest),
        _build_monitor_block(digest, "sahel_monitor", "Sahel Monitor"),
        _build_monitor_block(digest, "sudan_horn_monitor", "Sudan &amp; Horn Monitor"),
        _build_monitor_block(digest, "great_lakes_monitor", "Great Lakes Monitor"),
        _build_card_grid(digest.get("external_powers_watch") or [], "#C0392B", "External Powers Watch"),
        _build_minerals_energy(digest),
        _build_personnel_elections(digest),
        _build_experts(digest),
        _build_calendar(digest),
        _build_press_delta(digest),
        _build_footer(digest),
    ]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Africa Daily Brief — {title}</title>
</head>
<body style="margin:0;padding:0;background:#e9ecef;font-family:Arial,Helvetica,sans-serif;-webkit-text-size-adjust:100%;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#e9ecef;">
<tr><td align="center" style="padding:24px 12px;">
<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="720" style="max-width:720px;width:100%;background:#ffffff;border:1px solid #d0d4d9;">
{''.join(sections)}
</table>
</td></tr>
</table>
</body>
</html>
"""


if __name__ == "__main__":
    import argparse, json as _json
    p = argparse.ArgumentParser()
    p.add_argument("--digest", default="digest.json")
    p.add_argument("--out", default="preview.html")
    args = p.parse_args()
    with open(args.digest) as f:
        digest = _json.load(f)
    html_str = render_html(digest)
    with open(args.out, "w") as f:
        f.write(html_str)
    print(f"[render] Wrote {args.out} ({len(html_str):,} bytes)")
