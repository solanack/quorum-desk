"""Gated live adapter. v1 only emits dry-run intents. No exchange keys."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass
class Intent:
    time: str
    executor: str
    symbol: str
    side: str
    size_pct: float
    price: float
    dry_run: bool
    accepted: bool
    reason: str


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def intend(
    cfg: dict,
    symbol: str,
    side: str,
    size_pct: float,
    price: float,
    daily_pnl_pct: float,
) -> Intent:
    live = cfg.get("live") or {}
    mode = str(cfg.get("mode") or "paper")
    executor = str(live.get("executor") or "jesse")
    dry = bool(live.get("dry_run", True))
    max_loss = float(cfg.get("max_daily_loss_pct") or 3)
    confirm = bool(cfg.get("confirm_live"))

    if mode == "paper":
        return Intent(_now(), executor, symbol, side, size_pct, price, True, False, "Paper mode — no live intent.")
    if daily_pnl_pct <= -max_loss:
        return Intent(_now(), executor, symbol, side, size_pct, price, True, False, "Kill switch: daily loss cap.")
    if mode == "live" and not confirm:
        return Intent(_now(), executor, symbol, side, size_pct, price, True, False, "live refused: confirm_live is false.")
    if mode == "live" and not dry and confirm:
        return Intent(
            _now(),
            executor,
            symbol,
            side,
            size_pct,
            price,
            False,
            False,
            "Live routing is not implemented in this build. Keep dry_run true.",
        )
    return Intent(
        _now(),
        executor,
        symbol,
        side,
        size_pct,
        price,
        True,
        True,
        f"Dry-run accepted for {executor}. No order sent.",
    )


def as_row(intent: Intent) -> dict:
    return asdict(intent)
