# Quorum — full-fork definition

Excluded by request: A-Bulls App and variants, Bull Invaders, Claude-of-Duty.
Excluded by law: `kalshi_wash_trade` (wash trading is illegal). Do not wire it.

This file defines the bot from every remaining fork on `solanack`. Quorum is
one desk with eight planes. Repositories are adapters and patterns. They are
not vendored into a single binary.

## Planes

```
 1 SCOUT     public CEX + Solana tape + web
 2 RESEARCH  features, regimes, optional RL offline
 3 COMMITTEE bull / bear / news / risk  (TradingAgents shape)
 4 MEMORY    claims, fills, vetoes, hit-rate
 5 PAPER     ledger at last public price
 6 LIVE      one executor, dry-run first, keys optional and gated
 7 STUDIO    briefing → voice → clip → schedule  (optional)
 8 OPS       model gateway, tools, logs, operator UI
```

Paper is the default path. Live is a separate process. Studio never places
an order.

## Plane 1 — Scout (see)

CEX and prediction-market quotes

- `ccxt` — unified fetch for 100+ venues. Replace the Binance.US-only client
  in `quorum/data.py` when you want multi-venue mid/last/OHLCV.

Solana tape

- `solana` / `solana-web3.js` — chain access
- `carbon` + `jetstreamer` — live index / backfill
- `squid-sdk` — ETL if you add another chain later
- `trickshot` — rebuild a mint and replay a wallet’s prints
- `gmgn-skills` — token / wallet / market queries for the committee
- `solana-awesome` / `solana-dev-skill` / `program-examples` /
  `metaplex-program-library` / `solana-playground` / `create-solana-dapp`
  — reference only, not runtime

Web and social context

- `firecrawl` — hosted API (AGPL if you fork the server)
- `Scrapling` / `patchright-enhanced` — adaptive scrape when Firecrawl is not used
- `Agent-Reach` — X / web reach for “what is being said about this pair”

`solana-ui` is a multi-wallet trading UI pattern (Pump / Raydium / launchpad).
Use it as a screen design reference. Do not copy its execution path until
plane 6 is explicitly enabled.

## Plane 2 — Research (measure)

- `qlib` — feature store, walk-forward, offline models
- `machine-learning-for-trading` — data → live textbook pipeline; steal the
  research order, not a strategy blindly
- `FinRL` / `FinRL-Trading` — train policies offline on historical tapes.
  A trained policy is a voter in plane 3, never the only voter.
- `SETS` — “self-improving” loop = retrain on the paper journal, not live PnL
- `dspy` — compile the committee prompts against labeled days

No plane-2 job is allowed to send an order.

## Plane 3 — Committee (argue)

Same JSON contract as v0: `side`, `confidence`, `size_pct`, `invalidation`.

Seats

- Bull, Bear, News, Risk — from `TradingAgents` and `ai-hedge-fund`
- Conversational trader seat — `Vibe-Trading` as the human-language wrapper
- Orchestration — `crewAI` (roles) or `autogen` / `eliza` / `langchain` /
  `Flowise` if you want a graph. Pick **one** orchestrator. Default: crew
  pattern inside Quorum, no extra server.
- TypeScript agents if the desk UI is TS — `ai` (Vercel AI SDK)

Risk seat rules that stay even when the model is used

- realized vol cap
- opposite-side high-confidence veto
- max open positions
- no order if Scout coverage is missing
- no order that the journal already marked as a repeated loser in the same regime

## Plane 4 — Memory (remember)

- `mem0` — durable facts: watchlist, banned pairs, last claims
- `hindsight` — memory that learns from outcomes
- `drizzle-orm` — if the desk grows a real database
- local `memory/book.json` remains the v0 store

Every decision writes: features, votes, veto, fill or skip, and the next-day
mark. Hit rate is computed from that file, not from model confidence.

## Plane 5 — Paper (v0, already running)

Current code in this folder.

- Quotes: Binance.US public REST (U.S.-reachable)
- Committee: deterministic bull / bear / risk
- Ledger: cash, positions, fills
- UI: `web/index.html`

This plane stays on even after live exists. Live must be able to be turned
off without breaking paper.

## Plane 6 — Live (gated, one executor)

Enable only after paper hit rate is measured.

Directional

- `jesse` — MIT, preferred first live adapter
- `freqtrade` — GPL-3.0, run as its **own** process; do not copy into Quorum
- `solana-trading-bot-v3` — on-chain Solana execution, separate process,
  separate keys, never mixed with CEX keys

Market-making

- `hummingbot` — HFT / making. Different job. Do not let the committee
  directional book share inventory with a maker bot.

Hard gates

- dry-run flag default on
- max daily loss
- max notional
- kill switch file
- no withdrawal / transfer APIs

## Plane 7 — Studio (optional, no orders)

After a briefing exists:

- Voice: `pipecat` runtime, `elevenlabs-python` hosted, or `VoiceStudio`
  as a separate AGPL service
- Cut: `open-edit`, `brag`, `motion-skills`, `lottie`, `gsap-skills`,
  `MoneyPrinterTurbo`, `ComfyUI`, `PDoomVideo` / `Math-To-Manim` as render
  recipes
- Schedule: `postiz-app` hosted or AGPL-separate
- Taste: `impeccable`, `skills-emily`

Studio may speak paper results. It may not claim live profit that the
ledger does not show. It may not instruct a viewer to buy or sell.

## Plane 8 — Ops

Model door

- `litellm` or `OmniRoute` as the single OpenAI-compatible gateway
- `ollama` for local models
- `pi`, `hermes-agent`, `free-claude-code` — operator agents, not traders

Operator

- `orca` — fleet of coding agents working on Quorum itself
- `composio` — tool auth (exchange read, GitHub, calendar)
- `aider` / `continue` / `openinterpreter` — edit this repo
- `ai-engineering-from-scratch` — build/ship discipline
- `posthog` — hosted product analytics, not the monorepo
- NVIDIA `skills` — only if you train FinRL / Comfy on NVIDIA hardware

Skills packs `skill` and `solana-dev-skill` install into the operator
harness. They do not execute trades.

## Explicitly not in the trading path

These forks stay available for other products. They do not vote or fill.

- Game / 3D: `pixijs`, `threejs-skills`, `threejs-game-skills`,
  `threejs-particle-fluids`, `awesome-gamedev-agent-skills`,
  `agentic-gamedev-skills`, `unity-mcp`, `mcp-for-blender`, `blender`,
  `image-to-3dlab`
- Device / odd sensors: `RuView`, `OpenLogi`
- Security lists: `Awesome-Hacking`, `reverse-skill`,
  `the-book-of-secret-knowledge` (reference only)

## License map for anything Quorum imports

Safe to import into this MIT tree: `ccxt`, `jesse`, `crewAI`,
`TradingAgents`, `ai-hedge-fund`, `mem0`, `trickshot`, `gmgn-skills`,
`pipecat`, `brag`, `open-edit`, `solana-web3.js` (Apache).

Separate process only: `freqtrade` (GPL-3.0), `firecrawl` (AGPL-3.0),
`postiz-app` (AGPL-3.0), `VoiceStudio` (AGPL-3.0).

## Runtime sequence (one cycle)

1. Scout pulls CEX OHLCV (`ccxt` or Binance.US) and, if configured, a
   Solana mint/wallet tape (`trickshot` / `carbon` / `gmgn-skills`).
2. Optional Firecrawl / Agent-Reach headlines for those symbols.
3. Research features (`qlib`-style, currently computed in `agents.py`).
4. Committee votes. Risk may veto.
5. Paper fill at last price. Journal append.
6. If live flag and dry-run passed and loss cap intact, hand a single
   order intent to `jesse` (CEX) or `solana-trading-bot-v3` (chain).
7. Optional Studio briefing from the same JSON.

## What v0 already is vs this definition

V0 implements planes 1 (narrow), 3 (rules), 4 (file), 5 (ledger).
This document is the contract for planes 1–8 using the full fork set.
Do not flatten 87 repositories into one process.
