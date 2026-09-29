"""Scout: public CEX quotes. binance.com is often HTTP 451 in the US."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .http import get_json_safe


@dataclass
class Bar:
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class Snapshot:
    symbol: str
    venue: str
    last: float
    change_24h_pct: float
    high_24h: float
    low_24h: float
    volume: float
    bars: list[Bar] = field(default_factory=list)
    error: str | None = None


def pair(base: str, quote: str = "USDT") -> str:
    return f"{base.upper()}{quote.upper()}"


def _bars_from_binance(rows: list[list[Any]]) -> list[Bar]:
    return [
        Bar(
            open_time=int(row[0]),
            open=float(row[1]),
            high=float(row[2]),
            low=float(row[3]),
            close=float(row[4]),
            volume=float(row[5]),
        )
        for row in rows
    ]


def from_binanceus(base: str, quote: str, interval: str, limit: int) -> Snapshot:
    symbol = pair(base, quote)
    host = "https://api.binance.us"
    tick, err = get_json_safe(f"{host}/api/v3/ticker/24hr", {"symbol": symbol})
    if err or not tick:
        return Snapshot(symbol, "binanceus", 0, 0, 0, 0, 0, error=err or "empty ticker")
    kl, kerr = get_json_safe(
        f"{host}/api/v3/klines",
        {"symbol": symbol, "interval": interval, "limit": limit},
    )
    bars = _bars_from_binance(kl) if kl else []
    return Snapshot(
        symbol=symbol,
        venue="binanceus",
        last=float(tick["lastPrice"]),
        change_24h_pct=float(tick["priceChangePercent"]),
        high_24h=float(tick["highPrice"]),
        low_24h=float(tick["lowPrice"]),
        volume=float(tick["volume"]),
        bars=bars,
        error=None if bars else kerr,
    )


def from_coinbase(base: str, quote: str, interval: str, limit: int) -> Snapshot:
    q = "USD" if quote.upper() in {"USDT", "USD"} else quote.upper()
    product = f"{base.upper()}-{q}"
    host = "https://api.exchange.coinbase.com"
    tick, err = get_json_safe(f"{host}/products/{product}/ticker")
    stats, serr = get_json_safe(f"{host}/products/{product}/stats")
    if err or not tick:
        return Snapshot(pair(base, quote), "coinbase", 0, 0, 0, 0, 0, error=err or "empty ticker")
    last = float(tick["price"])
    open_24 = float(stats["open"]) if stats and stats.get("open") else last
    high = float(stats["high"]) if stats and stats.get("high") else last
    low = float(stats["low"]) if stats and stats.get("low") else last
    vol = float(stats["volume"]) if stats and stats.get("volume") else 0.0
    chg = ((last / open_24) - 1.0) * 100.0 if open_24 else 0.0
    gran = 3600 if str(interval).endswith("h") else 300
    candles, _ = get_json_safe(f"{host}/products/{product}/candles", {"granularity": gran})
    bars: list[Bar] = []
    if isinstance(candles, list):
        rows = sorted(candles, key=lambda r: r[0])[-limit:]
        for row in rows:
            bars.append(
                Bar(
                    open_time=int(row[0]) * 1000,
                    open=float(row[3]),
                    high=float(row[2]),
                    low=float(row[1]),
                    close=float(row[4]),
                    volume=float(row[5]),
                )
            )
    return Snapshot(pair(base, quote), "coinbase", last, chg, high, low, vol, bars, serr)


def snapshot(
    base: str,
    quote: str = "USDT",
    interval: str = "1h",
    limit: int = 48,
    venues: list[str] | None = None,
) -> Snapshot:
    order = venues or ["binanceus", "coinbase"]
    errors: list[str] = []
    for venue in order:
        if venue == "binanceus":
            snap = from_binanceus(base, quote, interval, limit)
        elif venue == "coinbase":
            snap = from_coinbase(base, quote, interval, limit)
        else:
            continue
        if snap.last > 0:
            return snap
        errors.append(f"{venue}: {snap.error}")
    return Snapshot(
        symbol=pair(base, quote),
        venue=",".join(order),
        last=0,
        change_24h_pct=0,
        high_24h=0,
        low_24h=0,
        volume=0,
        error=" | ".join(errors) or "no venue",
    )


def features(bars: list[Bar]) -> dict[str, float]:
    if not bars:
        return {}
    closes = [b.close for b in bars]
    last = closes[-1]
    ret_n = (last / closes[0] - 1.0) * 100.0 if closes[0] else 0.0
    window = closes[-24:] if len(closes) >= 24 else closes
    mean = sum(window) / len(window)
    var = sum((c - mean) ** 2 for c in window) / max(len(window) - 1, 1)
    std = var**0.5
    vol_pct = (std / mean * 100.0) if mean else 0.0
    highs = [b.high for b in bars]
    lows = [b.low for b in bars]
    rng = max(highs) - min(lows)
    pos_in_range = ((last - min(lows)) / rng) if rng else 0.5
    prior = closes[-13:-1] if len(closes) >= 13 else closes[:-1]
    prior_mean = sum(prior) / len(prior) if prior else last
    momentum = (last / prior_mean - 1.0) * 100.0 if prior_mean else 0.0
    if len(closes) >= 12:
        a = sum(closes[-6:]) / 6
        b = sum(closes[-12:-6]) / 6
        accel = (a / b - 1.0) * 100.0 if b else 0.0
    else:
        accel = 0.0
    return {
        "lookback_return_pct": round(ret_n, 3),
        "realized_vol_pct": round(vol_pct, 3),
        "position_in_range": round(pos_in_range, 3),
        "momentum_pct": round(momentum, 3),
        "accel_pct": round(accel, 3),
        "range_pct": round((rng / last * 100.0) if last else 0.0, 3),
    }
