"""Committee: bull, bear, news, risk. Optional LLM later fills the same JSON."""

from __future__ import annotations

from dataclasses import dataclass, field

from .data import Snapshot, features
from .news import Headline


@dataclass
class Vote:
    seat: str
    side: str
    confidence: float
    thesis: str
    invalidation: str


@dataclass
class Decision:
    symbol: str
    venue: str
    side: str
    confidence: float
    size_pct: float
    thesis: str
    bear: str
    news: str
    invalidation: str
    veto: str | None
    features: dict[str, float] = field(default_factory=dict)
    votes: list[Vote] = field(default_factory=list)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def bull(snap: Snapshot, feat: dict[str, float]) -> Vote:
    mom = feat.get("momentum_pct", 0.0)
    pos = feat.get("position_in_range", 0.5)
    chg = snap.change_24h_pct
    accel = feat.get("accel_pct", 0.0)
    stretch_penalty = 0.18 if pos > 0.88 else 0.0
    score = 0.5 + 0.02 * mom + 0.008 * chg + 0.01 * accel + 0.12 * (pos - 0.5) - stretch_penalty
    score = _clamp(score, 0.05, 0.95)
    if score >= 0.58 and pos < 0.88:
        return Vote(
            "bull",
            "long",
            score,
            (
                f"{snap.symbol} on {snap.venue}: {chg:+.2f}% / 24h, momentum {mom:+.2f}%, "
                f"accel {accel:+.2f}%, range position {pos:.0%}."
            ),
            f"Fail if close loses the 12-bar mean or the 24h low {snap.low_24h}.",
        )
    return Vote("bull", "flat", score, f"{snap.symbol} has no clean long ({score:.2f}; pos {pos:.0%}).", "No long.")


def bear(snap: Snapshot, feat: dict[str, float]) -> Vote:
    vol = feat.get("realized_vol_pct", 0.0)
    pos = feat.get("position_in_range", 0.5)
    chg = snap.change_24h_pct
    stretched = pos > 0.82 and chg > 4
    score = 0.5 + 0.015 * max(-chg, 0) + (0.22 if stretched else 0.0) + 0.01 * max(vol - 3, 0)
    score = _clamp(score, 0.05, 0.95)
    if stretched:
        return Vote(
            "bear",
            "short",
            score,
            (
                f"{snap.symbol} extended at {pos:.0%} of range after {chg:+.2f}% / 24h. "
                f"Vol {vol:.2f}% — mean-reversion case, not chase."
            ),
            "Invalidate on a held new 24h high.",
        )
    if chg < -4 and pos < 0.25:
        mid = (snap.high_24h + snap.low_24h) / 2
        return Vote(
            "bear",
            "short",
            score,
            f"{snap.symbol} breaking down ({chg:+.2f}%, pos {pos:.0%}).",
            f"Invalidate on reclaim of midpoint {mid:.6g}.",
        )
    return Vote("bear", "flat", score, f"{snap.symbol} is not a quality short ({score:.2f}).", "No short.")


def news_seat(snap: Snapshot, lines: list[Headline]) -> Vote:
    if not lines:
        return Vote("news", "flat", 0.5, "No headlines attached this cycle.", "n/a")
    titles = " | ".join(h.title[:80] for h in lines[:3])
    return Vote("news", "flat", 0.5, f"Context only, not a vote: {titles}", "Headlines do not size risk.")


def risk(
    bull_v: Vote,
    bear_v: Vote,
    feat: dict[str, float],
    min_confidence: float,
    max_pct: float,
    max_vol: float,
) -> tuple[str, float, str | None]:
    vol = feat.get("realized_vol_pct", 0.0)
    if vol > max_vol:
        return "flat", 0.0, f"Veto: realized vol {vol:.2f}% exceeds {max_vol}%."
    if bull_v.side == "long" and bear_v.side == "short" and min(bull_v.confidence, bear_v.confidence) >= 0.7:
        return "flat", 0.0, "Veto: bull and bear both confident, opposite sides."
    if bull_v.side == "long" and bull_v.confidence >= min_confidence and bull_v.confidence >= bear_v.confidence:
        size = max_pct * (bull_v.confidence - 0.5) / 0.5
        return "long", round(_clamp(size, 0.02, max_pct), 4), None
    if bear_v.side == "short" and bear_v.confidence >= min_confidence and bear_v.confidence > bull_v.confidence:
        size = max_pct * (bear_v.confidence - 0.5) / 0.5
        return "short", round(_clamp(size, 0.02, max_pct), 4), None
    return "flat", 0.0, None


def decide(
    snap: Snapshot,
    headlines: list[Headline],
    min_confidence: float,
    max_pct: float,
    max_vol: float,
) -> Decision:
    if snap.error and snap.last <= 0:
        return Decision(
            symbol=snap.symbol,
            venue=snap.venue,
            side="flat",
            confidence=0.0,
            size_pct=0.0,
            thesis=f"No quote: {snap.error}",
            bear="",
            news="",
            invalidation="",
            veto="Veto: data error.",
        )
    feat = features(snap.bars)
    b = bull(snap, feat)
    s = bear(snap, feat)
    n = news_seat(snap, headlines)
    side, size, veto = risk(b, s, feat, min_confidence, max_pct, max_vol)
    conf = b.confidence if side == "long" else s.confidence if side == "short" else max(b.confidence, s.confidence)
    return Decision(
        symbol=snap.symbol,
        venue=snap.venue,
        side=side,
        confidence=round(conf, 3),
        size_pct=size,
        thesis=b.thesis,
        bear=s.thesis,
        news=n.thesis,
        invalidation=b.invalidation if side == "long" else s.invalidation if side == "short" else "",
        veto=veto,
        features=feat,
        votes=[b, s, n],
    )
