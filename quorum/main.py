from __future__ import annotations

import argparse
import json
from pathlib import Path

from .cycle import MEMORY, ROOT, load_book, load_config, run_cycle


def cmd_run(_: argparse.Namespace) -> None:
    payload = run_cycle()
    studio = payload.get("studio") or {}
    print(f"mode {payload.get('mode')}  equity {payload['equity']:.2f}  pnl {payload['pnl_pct']:+.3f}%  pos {len(payload['positions'])}")
    for d in payload["decisions"]:
        extra = f"  veto={d['veto']}" if d.get("veto") else ""
        print(f"  {d['symbol']:<10} {d['side'].upper():<5} conf={d['confidence']:.2f} {d.get('venue','')} last={d['last']}{extra}")
    if studio.get("briefing"):
        print()
        print(studio["briefing"])


def cmd_status(_: argparse.Namespace) -> None:
    cfg = load_config()
    book = load_book(float(cfg.get("starting_cash", 10_000)))
    last = MEMORY / "last_run.json"
    print(f"cash {book.cash:.2f}  starting {book.starting_cash:.2f}  open {len(book.positions)}")
    for p in book.positions.values():
        print(f"  {p.symbol} {p.side} qty={p.qty:.6g} avg={p.avg}")
    if last.exists():
        raw = json.loads(last.read_text(encoding="utf-8"))
        print(f"last run {raw.get('generated_at')} equity {raw.get('equity')} pnl {raw.get('pnl_pct')}%")


def cmd_reset(_: argparse.Namespace) -> None:
    for name in ("book.json", "last_run.json", "history.jsonl"):
        p = MEMORY / name
        if p.exists():
            p.unlink()
    web = ROOT / "web" / "last_run.json"
    if web.exists():
        web.unlink()
    print("paper book cleared")


def main() -> None:
    parser = argparse.ArgumentParser(prog="quorum", description="Quorum paper trading desk")
    sub = parser.add_subparsers(dest="cmd", required=False)
    p_run = sub.add_parser("run", help="one committee cycle")
    p_run.set_defaults(func=cmd_run)
    p_st = sub.add_parser("status", help="show paper book")
    p_st.set_defaults(func=cmd_status)
    p_rs = sub.add_parser("reset", help="wipe paper book")
    p_rs.set_defaults(func=cmd_reset)
    args = parser.parse_args()
    fn = getattr(args, "func", None)
    if fn is None:
        cmd_run(args)
        return
    fn(args)


if __name__ == "__main__":
    main()
