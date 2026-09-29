"""News scout. Default is silent. Firecrawl is used only when a key is present."""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass


@dataclass
class Headline:
    symbol: str
    title: str
    source: str
    url: str = ""


def _firecrawl_search(query: str, api_key: str, api: str, limit: int) -> list[Headline]:
    body = json.dumps({"query": query, "limit": limit}).encode("utf-8")
    req = urllib.request.Request(
        api.rstrip("/") + "/v1/search",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "quorum/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return []
    data = payload.get("data") or payload.get("web") or []
    out: list[Headline] = []
    for row in data[:limit]:
        title = row.get("title") or row.get("url") or ""
        if title:
            out.append(
                Headline(
                    symbol=query,
                    title=title,
                    source="firecrawl",
                    url=row.get("url") or "",
                )
            )
    return out


def headlines_for(base: str, cfg: dict) -> list[Headline]:
    news_cfg = cfg.get("news") or {}
    if not news_cfg.get("enabled"):
        return []
    provider = str(news_cfg.get("provider") or "none")
    limit = int(news_cfg.get("max_headlines") or 3)
    if provider == "firecrawl":
        key = os.environ.get("FIRECRAWL_API_KEY", "")
        if not key:
            return []
        api = str(news_cfg.get("firecrawl_api") or "https://api.firecrawl.dev")
        return _firecrawl_search(f"{base} crypto market", key, api, limit)
    return []
