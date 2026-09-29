"""Studio: briefing, posts, voice script from the same cycle JSON. No orders."""

from __future__ import annotations

from datetime import datetime, timezone


def build(payload: dict, cfg: dict) -> dict:
    studio_cfg = cfg.get("studio") or {}
    if not studio_cfg.get("enabled", True):
        return {}
    decisions = payload.get("decisions") or []
    lines = []
    for d in decisions:
        extra = d.get("veto") or d.get("invalidation") or ""
        lines.append(
            f"{d.get('symbol')} {str(d.get('side')).upper()} "
            f"conf {d.get('confidence')} last {d.get('last')} "
            f"24h {d.get('change_24h_pct')}%. {extra}"
        )
    acted = [d for d in decisions if d.get("side") != "flat" and not d.get("veto")]
    flat = [d for d in decisions if d.get("side") == "flat" or d.get("veto")]
    briefing = (
        f"Quorum paper desk {payload.get('generated_at')}. "
        f"Equity {payload.get('equity')} ({payload.get('pnl_pct')}%). "
        f"{len(acted)} action(s), {len(flat)} flat/veto. "
        "This is not investment advice and no live order was sent."
    )
    posts = []
    if studio_cfg.get("emit_posts"):
        if acted:
            a = acted[0]
            posts.append(
                f"{a['symbol']} committee: {a['side']} @ {a['last']} "
                f"(conf {a['confidence']}). Paper only. Invalidation: {a.get('invalidation') or 'n/a'}"
            )
        else:
            posts.append("Quorum: no paper action this cycle. Coverage logged. Not a trade recommendation.")
    voice = ""
    if studio_cfg.get("emit_voice_script"):
        voice = (
            briefing
            + " "
            + ("First action: " + posts[0] if posts else "Book unchanged.")
        )
    return {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "briefing": briefing,
        "lines": lines,
        "posts": posts,
        "voice_script": voice,
        "disclaimer": payload.get("disclaimer"),
    }
