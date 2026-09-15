#!/usr/bin/env python3
"""Simulate a known-good mainnet Tessera/HumidiFi tx on Surfpool (sigVerify=false).

If a successful mainnet Jupiter+Tessera tx also fails 0xffff locally, the remaining
gate is cloned state / clock / tick freshness, not the instruction builder.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

SURFPOOL = "http://127.0.0.1:8899"
MAINNET = "https://api.mainnet-beta.solana.com"


def rpc(url: str, method: str, params):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode())
    if body.get("error"):
        raise RuntimeError(json.dumps(body["error"])[:4000])
    return body.get("result")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("sig")
    ap.add_argument("--out", type=Path, default=Path("tools/re/notes/mainnet_replay.json"))
    args = ap.parse_args()

    tx = rpc(
        MAINNET,
        "getTransaction",
        [args.sig, {"encoding": "base64", "maxSupportedTransactionVersion": 0}],
    )
    if not tx:
        print("mainnet tx missing", file=sys.stderr)
        return 2
    raw = tx["transaction"][0]
    slot_main = tx.get("slot")
    err_main = (tx.get("meta") or {}).get("err")

    clock = rpc(SURFPOOL, "getSlot", [])
    try:
        sim = rpc(
            SURFPOOL,
            "simulateTransaction",
            [
                raw,
                {
                    "encoding": "base64",
                    "sigVerify": False,
                    "replaceRecentBlockhash": True,
                    "commitment": "processed",
                },
            ],
        )
    except RuntimeError as exc:
        sim = {"rpc_error": str(exc)}

    logs = ((sim.get("value") or {}).get("logs") if isinstance(sim, dict) else None) or []
    report = {
        "sig": args.sig,
        "mainnet_slot": slot_main,
        "mainnet_err": err_main,
        "surfpool_slot": clock,
        "sim_err": (sim.get("value") or {}).get("err") if isinstance(sim, dict) else sim,
        "logs_tail": logs[-30:],
        "hit_0xffff": any("0xffff" in x for x in logs),
        "hit_tessera": any("TessVdML" in x for x in logs),
        "hit_humidifi": any("9H6tua7jkLhdm3w8BvgpTn5LZNU7g4ZynDmCiNN3q6Rp" in x for x in logs),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ("sig", "mainnet_err", "sim_err", "hit_0xffff", "surfpool_slot", "mainnet_slot")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
