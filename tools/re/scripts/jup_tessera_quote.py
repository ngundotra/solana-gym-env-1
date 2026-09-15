#!/usr/bin/env python3
"""Fetch a Jupiter TesseraV (or HumidiFi) quote + swap-instructions.

Does not send on mainnet. Used to build a Surfpool replay candidate.
"""

from __future__ import annotations

import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

SOL = "So11111111111111111111111111111111111111112"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
JUP_LITE = "https://lite-api.jup.ag/swap/v1"


def http_get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode())


def http_post(url: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def quote(dex: str, amount: int, input_mint: str, output_mint: str) -> dict:
    q = urllib.parse.urlencode(
        {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": amount,
            "slippageBps": 100,
            "dexes": dex,
            "onlyDirectRoutes": "true",
        }
    )
    return http_get(f"{JUP_LITE}/quote?{q}")


def swap_instructions(quote_resp: dict, user: str) -> dict:
    return http_post(
        f"{JUP_LITE}/swap-instructions",
        {
            "quoteResponse": quote_resp,
            "userPublicKey": user,
            "wrapAndUnwrapSol": True,
            "dynamicComputeUnitLimit": True,
        },
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dex", default="TesseraV", help="Jupiter label, e.g. TesseraV or HumidiFi")
    ap.add_argument("--amount", type=int, default=10_000_000)
    ap.add_argument("--user", required=True)
    ap.add_argument("--out", type=Path, default=Path("tools/re/notes/jup_quote.json"))
    args = ap.parse_args()

    q = quote(args.dex, args.amount, SOL, USDC)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    bundle = {"quote": q}
    if q.get("error") or "routePlan" not in q:
        # try reverse
        q2 = quote(args.dex, args.amount, USDC, SOL)
        bundle["quote_reverse"] = q2
        q = q2 if "routePlan" in q2 else q
        bundle["quote"] = q
    if "routePlan" in q:
        try:
            bundle["swap_instructions"] = swap_instructions(q, args.user)
        except Exception as exc:
            bundle["swap_instructions_error"] = str(exc)
    args.out.write_text(json.dumps(bundle, indent=2))
    print(json.dumps({"dex": args.dex, "has_route": "routePlan" in q, "out": str(args.out)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
