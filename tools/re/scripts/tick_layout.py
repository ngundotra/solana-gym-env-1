#!/usr/bin/env python3
"""Parse Tessera tick (MRKTKV01) + BAT1 accounts.

The remaining 0xffff gate is a slot-bearing oracle. This script dumps the
live layout so we do not guess fields.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rpc_util import rpc  # noqa: E402
from tessera_codec import BAT1_ORACLE, TICK_ACCOUNT  # noqa: E402
from tick_codec import parse_bat1_slot, parse_tick  # noqa: E402

CLOCK = "SysvarC1ock11111111111111111111111111111111"


def get_account(pubkey: str) -> dict:
    info = rpc("getAccountInfo", [pubkey, {"encoding": "base64"}])
    if not info or not info.get("value"):
        raise RuntimeError(f"missing account {pubkey}")
    val = info["value"]
    raw_b64, _enc = val["data"]
    import base64

    data = base64.b64decode(raw_b64)
    return {
        "pubkey": pubkey,
        "owner": val["owner"],
        "lamports": val["lamports"],
        "len": len(data),
        "data_hex": data.hex(),
        "data": data,
    }


def tick_to_dict(data: bytes) -> dict:
    parsed = parse_tick(data)
    return {
        "len": len(data),
        "magic": parsed.magic.decode("ascii", "replace"),
        "magic_ok": parsed.magic_ok(),
        "signer_hex": parsed.signer.hex(),
        "slot": parsed.slot,
        "prev_ts_ns": parsed.prev_ts_ns,
        "curr_ts_ns": parsed.curr_ts_ns,
        "seq": parsed.seq,
        "target_interval_ns": parsed.target_interval_ns,
        "last_interval_ns": parsed.last_interval_ns,
    }


def parse_clock(data: bytes) -> dict:
    # Clock: slot u64, epoch_start_timestamp i64, epoch u64, leader_schedule_epoch u64, unix_timestamp i64
    if len(data) < 40:
        return {"len": len(data)}
    slot, epoch_start, epoch, leader_epoch, unix_ts = struct.unpack_from("<QqQQq", data, 0)
    return {
        "slot": slot,
        "epoch_start_timestamp": epoch_start,
        "epoch": epoch,
        "leader_schedule_epoch": leader_epoch,
        "unix_timestamp": unix_ts,
    }


def annotate_tick(tick: dict, clock: dict) -> dict:
    slot = clock.get("slot")
    if slot is not None:
        tick["slot_delta"] = tick["slot"] - slot
    return tick


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("tools/re/notes/tick_layout.json"))
    args = ap.parse_args()

    tick_acc = get_account(TICK_ACCOUNT)
    bat1 = get_account(BAT1_ORACLE)
    clock_acc = get_account(CLOCK)
    clock = parse_clock(clock_acc["data"])
    tick = annotate_tick(tick_to_dict(tick_acc["data"]), clock)

    report = {
        "clock": clock,
        "tick": {
            "pubkey": tick_acc["pubkey"],
            "owner": tick_acc["owner"],
            "lamports": tick_acc["lamports"],
            "data_hex": tick_acc["data"].hex(),
            **{k: v for k, v in tick.items()},
        },
        "bat1": {
            "pubkey": bat1["pubkey"],
            "owner": bat1["owner"],
            "lamports": bat1["lamports"],
            "len": bat1["len"],
            "head_hex": bat1["data"].hex()[:128],
            "slot": parse_bat1_slot(bat1["data"]),
        },
    }
    # drop raw bytes
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))
    print(json.dumps({
        "tick_magic": tick.get("magic"),
        "tick_slot": tick.get("slot"),
        "slot_delta": tick.get("slot_delta"),
        "clock_slot": clock.get("slot"),
        "bat1_slot": parse_bat1_slot(bat1["data"]),
        "out": str(args.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
