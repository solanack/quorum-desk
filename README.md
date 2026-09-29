# Quorum

Eight-plane paper trading desk. Defined from the solanack fork set.
Excluded: A-Bulls App, Bull Invaders, Claude-of-Duty, and kalshi_wash_trade.

This repository implements the desk. It does not vendor Freqtrade,
Hummingbot, Firecrawl, Blender, or the other monorepos. Those attach as
optional processes per ARCHITECTURE.md.

## Planes implemented

1. Scout — Binance.US then Coinbase public quotes
2. Research — range, vol, momentum, acceleration features
3. Committee — bull, bear, news (context), risk veto
4. Memory — memory/book.json, last_run.json, history.jsonl
5. Paper ledger — default
6. Live adapter — dry-run intents only; live routing refused
7. Studio — briefing, post line, voice script
8. Ops — config.yaml, CLI

## Commands

    python3 -m pip install -r requirements.txt
    python3 -m quorum run
    python3 -m quorum status
    python3 -m quorum reset

Open web/index.html after a run.

No exchange keys are required. Optional FIRECRAWL_API_KEY and LLM_API_KEY
are unused until you set news.provider: firecrawl or llm.enabled: true.

## Honest limit

The committee is rules plus optional future LLM JSON. It is not a
forecast and not a source of income. Paper exists so you can see
chase-highs and vetoes before any live executor is attached.
