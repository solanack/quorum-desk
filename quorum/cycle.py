from __future__ import annotations

import json
from pathlib import Path

import yaml

from .agents import decide
from .data import snapshot
from .live import as_row, intend
from .news import headlines_for
from .paper import Book, Fill, Position, apply, dump
from .studio import build as studio_build


ROOT = Path(__file__).resolve().parents[1]
MEMORY = ROOT / "memory"


def load_config() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))


def load_book(starting: float) -> Book:
    p = MEMORY / "book.json"
    if not p.exists():
        return Book(cash=starting, starting_cash=starting)
    raw = json.loads(p.read_text(encoding="utf-8"))
    book = Book(cash=float(raw.get("cash", starting)), starting_cash=float(raw.get("starting_cash", starting)))
    for pos in raw.get("positions", []):
        book.positions[pos["symbol"]] = Position(**pos)
    for f in raw.get("fills", []):
        book.fills.append(Fill(**f))
    return book


def save_book(book: Book) -> None:
    MEMORY.mkdir(parents=True, exist_ok=True)
    (MEMORY / "book.json").write_text(
        json.dumps(
            {
                "cash": book.cash,
                "starting_cash": book.starting_cash,
                "positions": [p.__dict__ for p in book.positions.values()],
                "fills": [f.__dict__ for f in book.fills],
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def run_cycle(cfg: dict | None = None) -> dict:
    cfg = cfg or load_config()
    quote = cfg.get("quote", "USDT")
    venues = list(cfg.get("venues") or ["binanceus", "coinbase"])
    book = load_book(float(cfg.get("starting_cash", 10_000)))
    marks: dict[str, float] = {}
    decisions = []
    intents = []
    max_open = int(cfg.get("max_open_positions", 4))
    eq_start = book.equity({})
    # mark existing names after scout

    for base in cfg.get("watchlist", []):
        snap = snapshot(
            str(base),
            quote=quote,
            interval=str(cfg.get("interval", "1h")),
            limit=int(cfg.get("lookback_hours", 48)),
            venues=venues,
        )
        heads = headlines_for(str(base), cfg)
        dec = decide(
            snap,
            heads,
            min_confidence=float(cfg.get("min_confidence", 0.62)),
            max_pct=float(cfg.get("max_position_pct", 0.15)),
            max_vol=float(cfg.get("max_realized_vol_pct", 12)),
        )
        marks[dec.symbol] = snap.last
        row = {
            "symbol": dec.symbol,
            "venue": dec.venue,
            "last": snap.last,
            "change_24h_pct": round(snap.change_24h_pct, 3),
            "side": dec.side,
            "confidence": dec.confidence,
            "size_pct": dec.size_pct,
            "thesis": dec.thesis,
            "bear": dec.bear,
            "news": dec.news,
            "invalidation": dec.invalidation,
            "veto": dec.veto,
            "features": dec.features,
            "headlines": [h.__dict__ for h in heads],
            "error": snap.error,
        }
        decisions.append(row)
        daily_pnl = ((book.equity(marks) / book.starting_cash) - 1.0) * 100.0 if book.starting_cash else 0.0
        if dec.side != "flat" and not dec.veto and snap.last > 0:
            existing = book.positions.get(dec.symbol)
            if existing and existing.side == dec.side:
                row["veto"] = "Hold: already open in this direction. No pyramid."
            elif dec.symbol not in book.positions and len(book.positions) >= max_open:
                row["veto"] = f"Veto: already {max_open} open paper positions."
            else:
                apply(
                    book,
                    dec.symbol,
                    dec.side,
                    dec.size_pct,
                    snap.last,
                    book.equity(marks),
                    dec.thesis,
                )
                intent = intend(cfg, dec.symbol, dec.side, dec.size_pct, snap.last, daily_pnl)
                intents.append(as_row(intent))
                row["live_intent"] = as_row(intent)

    payload = dump(book, marks, decisions, MEMORY / "last_run.json")
    payload["intents"] = intents
    payload["equity_at_open"] = round(eq_start, 4)
    payload["studio"] = studio_build(payload, cfg)
    payload["mode"] = cfg.get("mode", "paper")
    (MEMORY / "last_run.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (ROOT / "web" / "last_run.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    save_book(book)
    hist = MEMORY / "history.jsonl"
    with hist.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"generated_at": payload["generated_at"], "equity": payload["equity"], "pnl_pct": payload["pnl_pct"], "n": len(decisions)}) + "\n")
    return payload
