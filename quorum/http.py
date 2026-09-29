from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def get_json(url: str, params: dict[str, Any] | None = None, timeout: int = 20) -> Any:
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "quorum/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json_safe(url: str, params: dict[str, Any] | None = None, timeout: int = 20) -> tuple[Any | None, str | None]:
    try:
        return get_json(url, params=params, timeout=timeout), None
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code} {url}"
    except Exception as exc:  # noqa: BLE001
        return None, f"{type(exc).__name__}: {exc}"
