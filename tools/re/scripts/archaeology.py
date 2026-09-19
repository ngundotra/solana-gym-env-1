#!/usr/bin/env python3
"""Mainnet tx archaeology for Tessera 0x10 (Jupiter) and HumidiFi 25B taker swaps.

Tessera FIRST: only keep selector 0x10 + 14 accounts that appear under Jupiter.
Ignore BAM MM 0x0d / 784B / KAM\\0 from FVnv5qH7dsrBzEDwJ8dN2m9PFtKTBAQFtqWF3M9LpwMg.

HumidiFi SECOND: only 25-byte / ~18-account taker swaps. Ignore 65B/3acc MM updates.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

from humidifi_codec import decode_swap
from rpc_util import b58decode, rpc

TESSERA = "TessVdML9pBGgG9yGks7o4HewRaXVAMuoVj4x83GLQH"
HUMIDIFI = "9H6tua7jkLhdm3w8BvgpTn5LZNU7g4ZynDmCiNN3q6Rp"
# Live 2026-09 Jupiter aggregator that actually CPIs Tessera.
JUPITER_V6 = "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"
JUPITER_V6_LEGACY = "JUP6LkbZbjS1jKKwapdHNyBwDxjC3VheXv4TtCedZH8x"
JUPITER_V4 = "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB"

JUP_FEE_PAYERS = (
    "BpZpRbuyiqNrdnxnWQrzN5cX8g3ymaoJ4qB5TJmUsMGk",
    "shakRDxyKwaBbduqZTZt8Q4etTALbDLnAANStv9TLH3",
)
HUMIDIFI_JUP_FP = "AgmLJBMDCqWynYnQiPCuj9ewsNNsBJXyzoUhD9LJzN51"
BAM_MM = "FVnv5qH7dsrBzEDwJ8dN2m9PFtKTBAQFtqWF3M9LpwMg"

JUPITER_PROGRAMS = {JUPITER_V6, JUPITER_V6_LEGACY, JUPITER_V4}


def resolve_keys(tx: dict) -> list[str]:
    msg = tx["transaction"]["message"]
    keys = list(msg.get("accountKeys") or [])
    # jsonParsed / json encoding may already be strings
    out: list[str] = []
    for k in keys:
        if isinstance(k, dict):
            out.append(k.get("pubkey", str(k)))
        else:
            out.append(str(k))
    loaded = (tx.get("meta") or {}).get("loadedAddresses") or {}
    out.extend(str(x) for x in (loaded.get("writable") or []))
    out.extend(str(x) for x in (loaded.get("readonly") or []))
    return out


def ix_program(ix: dict, keys: list[str]) -> str:
    if "programId" in ix:
        return str(ix["programId"])
    idx = ix.get("programIdIndex")
    if idx is None:
        return ""
    return keys[idx] if idx < len(keys) else ""


def ix_accounts(ix: dict, keys: list[str]) -> list[str]:
    accs = ix.get("accounts") or []
    out: list[str] = []
    for a in accs:
        if isinstance(a, int):
            out.append(keys[a] if a < len(keys) else str(a))
        else:
            out.append(str(a))
    return out


def ix_data_bytes(ix: dict) -> bytes:
    data = ix.get("data")
    if data is None:
        return b""
    if isinstance(data, list):
        return bytes(data)
    if isinstance(data, str):
        try:
            return b58decode(data)
        except Exception:
            return b""
    return b""


def walk_instructions(tx: dict, keys: list[str]) -> list[tuple[str, dict, bytes, list[str], bool, str]]:
    """Yield (program, ix, data, accounts, is_inner, parent_program)."""
    msg = tx["transaction"]["message"]
    outer = msg.get("instructions") or []
    rows = []
    for i, ix in enumerate(outer):
        prog = ix_program(ix, keys)
        data = ix_data_bytes(ix)
        accs = ix_accounts(ix, keys)
        rows.append((prog, ix, data, accs, False, ""))
    for inner_group in (tx.get("meta") or {}).get("innerInstructions") or []:
        parent_idx = inner_group.get("index", 0)
        parent_prog = ""
        if parent_idx < len(outer):
            parent_prog = ix_program(outer[parent_idx], keys)
        for ix in inner_group.get("instructions") or []:
            prog = ix_program(ix, keys)
            data = ix_data_bytes(ix)
            accs = ix_accounts(ix, keys)
            rows.append((prog, ix, data, accs, True, parent_prog))
    return rows


def fetch_sigs(address: str, limit: int) -> list[str]:
    rows = rpc(
        "getSignaturesForAddress",
        [address, {"limit": limit}],
    ) or []
    return [r["signature"] for r in rows]


def fetch_tx(sig: str) -> dict | None:
    return rpc(
        "getTransaction",
        [sig, {"encoding": "json", "maxSupportedTransactionVersion": 0, "commitment": "confirmed"}],
    )


def classify_tessera(data: bytes, nacc: int, parent: str, fee_payer: str) -> str | None:
    if not data:
        return None
    disc = data[0]
    if disc == 0x0D and nacc >= 1:
        return "skip_bam_0x0d"
    if b"KAM\x00" in data:
        return "skip_kam"
    if disc == 0x10 and nacc == 14 and parent in JUPITER_PROGRAMS:
        return "keep_jup_0x10_14"
    if disc == 0x10 and nacc == 14:
        return "0x10_14_not_jup"
    if disc == 0x10:
        return f"0x10_{nacc}acc"
    return f"other_{disc:#x}_{nacc}acc"


def classify_humidifi(data: bytes, nacc: int) -> str | None:
    if len(data) == 65 and nacc == 3:
        return "skip_mm_65b_3acc"
    if len(data) == 25:
        return f"taker_25b_{nacc}acc"
    return f"other_{len(data)}b_{nacc}acc"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", choices=["tessera", "humidifi", "both"], default="tessera")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--out", type=Path, default=Path("tools/re/notes/tx_sample.json"))
    args = ap.parse_args()

    report: dict = {"tessera": [], "humidifi": [], "tessera_counts": {}, "humidifi_counts": {}}

    if args.target in {"tessera", "both"}:
        seen = 0
        counts: Counter[str] = Counter()
        sources = list(JUP_FEE_PAYERS) + [TESSERA]
        for src in sources:
            print(f"[tessera] sigs from {src}", file=sys.stderr)
            try:
                sigs = fetch_sigs(src, args.limit)
            except Exception as exc:
                print(f"  fail {exc}", file=sys.stderr)
                continue
            for sig in sigs:
                if seen >= args.limit * 2:
                    break
                try:
                    tx = fetch_tx(sig)
                except Exception as exc:
                    print(f"  tx fail {sig[:8]} {exc}", file=sys.stderr)
                    continue
                if not tx:
                    continue
                keys = resolve_keys(tx)
                fee_payer = keys[0] if keys else ""
                if fee_payer == BAM_MM:
                    continue
                for prog, _ix, data, accs, is_inner, parent in walk_instructions(tx, keys):
                    if prog != TESSERA:
                        continue
                    tag = classify_tessera(data, len(accs), parent, fee_payer)
                    if not tag:
                        continue
                    counts[tag] += 1
                    # Keep every 0x10+14acc hop (Jupiter or not) so parent
                    # detection misses still land in the sample table.
                    if tag not in {"keep_jup_0x10_14", "0x10_14_not_jup"}:
                        continue
                    seen += 1
                    row = {
                        "sig": sig,
                        "slot": tx.get("slot"),
                        "err": (tx.get("meta") or {}).get("err"),
                        "fee_payer": fee_payer,
                        "inner": is_inner,
                        "parent": parent,
                        "nacc": len(accs),
                        "accounts": accs,
                        "data_hex": data.hex(),
                        "data_len": len(data),
                        "selector": data[0] if data else None,
                    }
                    report["tessera"].append(row)
                    print(
                        f"KEEP {sig} slot={row['slot']} nacc={len(accs)} "
                        f"parent={parent[:8]} data={data.hex()}",
                        file=sys.stderr,
                    )
        report["tessera_counts"] = dict(counts)
        print("tessera_counts", dict(counts), file=sys.stderr)

    if args.target in {"humidifi", "both"}:
        counts: Counter[str] = Counter()
        sources = [HUMIDIFI_JUP_FP, HUMIDIFI]
        kept = 0
        for src in sources:
            print(f"[humidifi] sigs from {src}", file=sys.stderr)
            try:
                sigs = fetch_sigs(src, args.limit)
            except Exception as exc:
                print(f"  fail {exc}", file=sys.stderr)
                continue
            for sig in sigs:
                if kept >= 20:
                    break
                try:
                    tx = fetch_tx(sig)
                except Exception as exc:
                    print(f"  tx fail {sig[:8]} {exc}", file=sys.stderr)
                    continue
                if not tx:
                    continue
                keys = resolve_keys(tx)
                for prog, _ix, data, accs, is_inner, parent in walk_instructions(tx, keys):
                    if prog != HUMIDIFI:
                        continue
                    tag = classify_humidifi(data, len(accs))
                    counts[tag or "none"] += 1
                    if not tag or not tag.startswith("taker_25b"):
                        continue
                    decoded = None
                    try:
                        sw = decode_swap(data)
                        decoded = {
                            "swap_id": sw.swap_id,
                            "amount_in": sw.amount_in,
                            "is_base_to_quote": sw.is_base_to_quote,
                            "selector": sw.selector,
                            "padding_hex": sw.padding.hex(),
                        }
                    except Exception as exc:
                        decoded = {"error": str(exc)}
                    kept += 1
                    row = {
                        "sig": sig,
                        "slot": tx.get("slot"),
                        "err": (tx.get("meta") or {}).get("err"),
                        "fee_payer": keys[0] if keys else "",
                        "inner": is_inner,
                        "parent": parent,
                        "nacc": len(accs),
                        "accounts": accs,
                        "data_hex": data.hex(),
                        "decoded": decoded,
                    }
                    report["humidifi"].append(row)
                    print(
                        f"KEEP {sig} nacc={len(accs)} parent={parent[:12]} decoded={decoded}",
                        file=sys.stderr,
                    )
        report["humidifi_counts"] = dict(counts)
        print("humidifi_counts", dict(counts), file=sys.stderr)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
