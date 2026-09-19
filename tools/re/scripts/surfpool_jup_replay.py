#!/usr/bin/env python3
"""Replay a Jupiter-wrapped Tessera/HumidiFi swap against local Surfpool.

Uses lite-api.jup.ag for quote + swap-instructions, then solders to sign
and send to http://127.0.0.1:8899. Surfpool clones missing mainnet accounts.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SOL = "So11111111111111111111111111111111111111112"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
JUP_LITE = "https://lite-api.jup.ag/swap/v1"
SURFPOOL = "http://127.0.0.1:8899"
TESSERA = "TessVdML9pBGgG9yGks7o4HewRaXVAMuoVj4x83GLQH"
HUMIDIFI = "9H6tua7jkLhdm3w8BvgpTn5LZNU7g4ZynDmCiNN3q6Rp"
BISON = "BiSoNHVpsVZW2F7rx2eQ59yQwKxzU5NvBcmKshCSUypi"
SCORCH = "SCoRcH8c2dpjvcJD6FiPbCSQyQgu3PcUAWj2Xxx3mqn"


def rpc(url: str, method: str, params):
    payload = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        body = json.loads(resp.read().decode())
    if body.get("error"):
        raise RuntimeError(body["error"])
    return body.get("result")


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
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode())


def wait_surfpool(timeout: float = 90.0) -> None:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            h = rpc(SURFPOOL, "getHealth", [])
            if h == "ok" or h is None or h == {}:
                return
            last = h
        except Exception as exc:
            last = str(exc)
        time.sleep(1.5)
    raise RuntimeError(f"surfpool not healthy: {last}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dex", default="TesseraV")
    ap.add_argument("--amount", type=int, default=10_000_000)
    ap.add_argument("--slippage-bps", type=int, default=300)
    ap.add_argument(
        "--refresh-tessera",
        choices=["off", "time_travel", "patch_slot", "stream"],
        default="off",
        help="Align Tessera tick/BAT1 with Surfpool clock before send",
    )
    ap.add_argument("--out", type=Path, default=Path("tools/re/notes/surfpool_replay.json"))
    args = ap.parse_args()

    from solders.keypair import Keypair
    from solders.pubkey import Pubkey
    from solders.instruction import Instruction, AccountMeta
    from solders.message import MessageV0
    from solders.transaction import VersionedTransaction
    from solders.hash import Hash
    from solders.system_program import transfer, TransferParams

    wait_surfpool()
    if args.refresh_tessera != "off":
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from tessera_freshness import refresh as refresh_tessera

        report_pre = {"dex": args.dex}
        try:
            report_pre["tessera_freshness"] = refresh_tessera(mode=args.refresh_tessera)
        except Exception as exc:
            report_pre["tessera_freshness_error"] = str(exc)
        # keep going even if refresh is partial; send will prove the gate
    else:
        report_pre = {}

    kp = Keypair()
    user = str(kp.pubkey())
    airdrop = rpc(SURFPOOL, "requestAirdrop", [user, 5_000_000_000])
    # confirm
    for _ in range(20):
        time.sleep(0.4)
        bal = rpc(SURFPOOL, "getBalance", [user])
        if (bal or {}).get("value", 0) >= 4_000_000_000:
            break

    q_url = (
        f"{JUP_LITE}/quote?"
        + urllib.parse.urlencode(
            {
                "inputMint": SOL,
                "outputMint": USDC,
                "amount": args.amount,
                "slippageBps": args.slippage_bps,
                "dexes": args.dex,
                "onlyDirectRoutes": "true",
            }
        )
    )
    quote = http_get(q_url)
    report = {
        "dex": args.dex,
        "user": user,
        "airdrop": airdrop,
        **report_pre,
        "quote_keys": list(quote.keys()),
        "routePlan": quote.get("routePlan"),
        "error": quote.get("error") or quote.get("message"),
    }
    if "routePlan" not in quote:
        # try reverse USDC->SOL (won't have USDC unless we clone)
        q2 = http_get(
            f"{JUP_LITE}/quote?"
            + urllib.parse.urlencode(
                {
                    "inputMint": USDC,
                    "outputMint": SOL,
                    "amount": args.amount,
                    "slippageBps": args.slippage_bps,
                    "dexes": args.dex,
                    "onlyDirectRoutes": "true",
                }
            )
        )
        report["quote_reverse"] = {k: q2.get(k) for k in ("routePlan", "error", "message", "inAmount", "outAmount")}
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=str))
        print(json.dumps({"ok": False, "reason": "no_quote", "out": str(args.out)}))
        return 2

    try:
        ixs = http_post(
            f"{JUP_LITE}/swap-instructions",
            {
                "quoteResponse": quote,
                "userPublicKey": user,
                "wrapAndUnwrapSol": True,
                "dynamicComputeUnitLimit": True,
            },
        )
    except Exception as exc:
        report["swap_instructions_error"] = str(exc)
        args.out.write_text(json.dumps(report, indent=2, default=str))
        print(json.dumps({"ok": False, "reason": "swap_ix_error", "err": str(exc)}))
        return 3

    report["swap_instruction_keys"] = list(ixs.keys()) if isinstance(ixs, dict) else type(ixs).__name__

    def parse_ix(raw: dict) -> Instruction:
        metas = raw.get("accounts") or raw.get("keys") or []
        keys = [
            AccountMeta(
                Pubkey.from_string(a["pubkey"]),
                a.get("isSigner", False),
                a.get("isWritable", False),
            )
            for a in metas
        ]
        blob = raw["data"]
        if isinstance(blob, list):
            data = bytes(blob)
        elif isinstance(blob, str):
            import base64 as _b64
            try:
                data = _b64.b64decode(blob)
            except Exception:
                data = bytes.fromhex(blob)
        else:
            data = bytes(blob)
        return Instruction(Pubkey.from_string(raw["programId"]), data, keys)

    compiled: list[Instruction] = []
    for bucket in ("computeBudgetInstructions", "setupInstructions", "otherInstructions"):
        for raw in ixs.get(bucket) or []:
            compiled.append(parse_ix(raw))
    if ixs.get("swapInstruction"):
        compiled.append(parse_ix(ixs["swapInstruction"]))
    if ixs.get("cleanupInstruction"):
        compiled.append(parse_ix(ixs["cleanupInstruction"]))

    # Annotate Tessera/HumidiFi inner-looking top-level ixs
    layouts = []
    for ins in compiled:
        pid = str(ins.program_id)
        data = bytes(ins.data)
        layouts.append(
            {
                "program": pid,
                "data_hex": data.hex(),
                "nacc": len(ins.accounts),
                "selector": data[0] if data else None,
            }
        )
    report["built_ixs"] = layouts

    bh = rpc(SURFPOOL, "getLatestBlockhash", [{"commitment": "confirmed"}])
    blockhash = Hash.from_string(bh["value"]["blockhash"])
    msg = MessageV0.try_compile(kp.pubkey(), compiled, [], blockhash)
    tx = VersionedTransaction(msg, [kp])
    raw = bytes(tx)
    import base64

    try:
        sig = rpc(
            SURFPOOL,
            "sendTransaction",
            [
                base64.b64encode(raw).decode(),
                {"encoding": "base64", "skipPreflight": False, "maxRetries": 2},
            ],
        )
    except RuntimeError as exc:
        report["send_error"] = str(exc)
        report["success"] = False
        report["receipt_err"] = "send_failed"
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, indent=2, default=str))
        print(json.dumps({"ok": False, "reason": "send_failed", "err": str(exc)[:400], "out": str(args.out)}))
        return 4
    report["sig"] = sig
    # confirm + fetch
    time.sleep(1.2)
    rec = rpc(
        SURFPOOL,
        "getTransaction",
        [sig, {"encoding": "json", "maxSupportedTransactionVersion": 0, "commitment": "confirmed"}],
    )
    report["receipt_err"] = (rec or {}).get("meta", {}).get("err") if rec else "no_receipt"
    report["logs"] = ((rec or {}).get("meta") or {}).get("logMessages", [])[-40:]
    # look for tessera/humidifi in logs
    logs = ((rec or {}).get("meta") or {}).get("logMessages") or []
    report["hit_tessera"] = any(TESSERA in x for x in logs)
    report["hit_humidifi"] = any(HUMIDIFI in x for x in logs)
    report["hit_bison"] = any(BISON in x for x in logs)
    report["hit_scorch"] = any(SCORCH in x for x in logs)
    report["success"] = rec is not None and report["receipt_err"] is None

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps({"ok": report["success"], "sig": sig, "err": report["receipt_err"], "out": str(args.out)}))
    return 0 if report["success"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
