"""Minimal Solana JSON-RPC helper (stdlib only)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

DEFAULT_RPC = "https://api.mainnet-beta.solana.com"
FALLBACK_RPCS = (
    "https://api.mainnet-beta.solana.com",
    "https://solana-rpc.publicnode.com",
)


def _post(url: str, payload: dict[str, Any], timeout: float = 30.0) -> dict[str, Any]:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def rpc(method: str, params: list[Any], *, url: str = DEFAULT_RPC, retries: int = 4) -> Any:
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    last_err: Exception | None = None
    urls = [url, *[u for u in FALLBACK_RPCS if u != url]]
    for attempt in range(retries):
        for candidate in urls:
            try:
                body = _post(candidate, payload)
                if "error" in body:
                    raise RuntimeError(body["error"])
                return body.get("result")
            except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
                last_err = exc
                time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"RPC {method} failed: {last_err}")


# Minimal base58 (Bitcoin alphabet) for instruction data.
_B58 = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def b58decode(s: str) -> bytes:
    n = 0
    for ch in s.encode():
        idx = _B58.find(ch)
        if idx < 0:
            raise ValueError(f"invalid base58 char {ch!r}")
        n = n * 58 + idx
    raw = n.to_bytes((n.bit_length() + 7) // 8 or 1, "big")
    pad = 0
    for ch in s:
        if ch == "1":
            pad += 1
        else:
            break
    return b"\x00" * pad + raw.lstrip(b"\x00")


def b58encode(data: bytes) -> str:
    n = int.from_bytes(data, "big")
    out = bytearray()
    while n > 0:
        n, rem = divmod(n, 58)
        out.append(_B58[rem])
    pad = 0
    for b in data:
        if b == 0:
            pad += 1
        else:
            break
    return ("1" * pad) + out[::-1].decode()
