"""Paper ledger. Mark-to-market at last price. No exchange orders."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class Fill:
    time: str
    symbol: str
    side: str
    qty: float
    price: float
    note: str


@dataclass
class Position:
    symbol: str
    qty: float
    avg: float
    side: str


@dataclass
class Book:
    cash: float
    starting_cash: float
    positions: dict[str, Position] = field(default_factory=dict)
    fills: list[Fill] = field(default_factory=list)

    def equity(self, marks: dict[str, float]) -> float:
        eq = self.cash
        for sym, pos in self.positions.items():
            px = marks.get(sym, pos.avg)
            eq += pos.qty * px
        return eq


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def apply(book: Book, symbol: str, side: str, size_pct: float, price: float, equity: float, note: str) -> None:
    if side == "flat" or size_pct <= 0 or price <= 0:
        return
    notional = equity * size_pct
    qty = notional / price
    if side == "short":
        qty = -qty
    existing = book.positions.get(symbol)
    if existing:
        new_qty = existing.qty + qty
        if abs(new_qty) < 1e-12:
            book.positions.pop(symbol, None)
        else:
            # running average in position direction
            existing.avg = (existing.avg * existing.qty + price * qty) / new_qty if new_qty else price
            existing.qty = new_qty
            existing.side = "long" if new_qty > 0 else "short"
    else:
        book.positions[symbol] = Position(symbol=symbol, qty=qty, avg=price, side=side)
    book.cash -= qty * price
    book.fills.append(Fill(_now(), symbol, side, qty, price, note))


def dump(book: Book, marks: dict[str, float], decisions: list[dict], path: Path) -> dict:
    eq = book.equity(marks)
    payload = {
        "generated_at": _now(),
        "mode": "paper",
        "starting_cash": book.starting_cash,
        "cash": round(book.cash, 4),
        "equity": round(eq, 4),
        "pnl_pct": round((eq / book.starting_cash - 1.0) * 100.0, 3) if book.starting_cash else 0.0,
        "positions": [asdict(p) for p in book.positions.values()],
        "fills": [asdict(f) for f in book.fills[-50:]],
        "marks": marks,
        "decisions": decisions,
        "disclaimer": (
            "Paper marks only. Public last prices. No live orders. "
            "Committee rules are not a forecast and are not investment advice."
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
