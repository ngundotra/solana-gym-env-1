#!/usr/bin/env python3
"""Keep Tessera tick + BAT1 aligned with the Surfpool clock.

Two modes:
  time_travel — write fresh mainnet oracles, then surfnet_timeTravel to the
                tick slot and pause the clock (preferred).
  patch_slot  — rewrite tick@40 and BAT1@0 to the current Surfpool clock.

Uses surfnet cheatcodes (setAccount / timeTravel / pauseClock / streamAccount).
"""

from __future__ import annotations

import argparse
import base64
import json
import struct
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from rpc_util import rpc  # noqa: E402
from tessera_codec import (  # noqa: E402
    BAT1_ORACLE,
    GLOBAL_STATE,
    TICK_ACCOUNT,
    TICK_PROGRAM,
)
from tick_codec import (  # noqa: E402
    parse_bat1_slot,
    parse_tick,
    patch_bat1_slot,
    patch_tick_slot,
)

SURFPOOL = "http://127.0.0.1:8899"
MAINNET = "https://api.mainnet-beta.solana.com"
CLOCK = "SysvarC1ock11111111111111111111111111111111"
SYSVAR_OWNER = "Sysvar1111111111111111111111111111111111111"
POOL = "FLckHLGMJy5gEoXWwcE68Nprde1D4araK4TGLw4pQq2n"

ORACLES = (TICK_ACCOUNT, BAT1_ORACLE, GLOBAL_STATE, POOL)


def surf(method: str, params: list, timeout: float = 45.0):
    """Call Surfpool only — never fall back to mainnet (cheatcodes are local)."""
    payload = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        SURFPOOL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = json.loads(resp.read().decode())
    if "error" in body:
        raise RuntimeError(body["error"])
    return body.get("result")


def fetch_account(pubkey: str, *, url: str) -> dict:
    info = rpc("getAccountInfo", [pubkey, {"encoding": "base64"}], url=url)
    if not info or not info.get("value"):
        raise RuntimeError(f"missing account {pubkey} on {url}")
    val = info["value"]
    data = base64.b64decode(val["data"][0])
    return {
        "pubkey": pubkey,
        "owner": val["owner"],
        "lamports": val["lamports"],
        "executable": val.get("executable", False),
        "rent_epoch": val.get("rentEpoch", 0),
        "data": data,
    }


def pack_clock(slot: int, epoch_start: int, epoch: int, leader_epoch: int, unix_ts: int) -> bytes:
    return struct.pack("<QqQQq", slot, epoch_start, epoch, leader_epoch, unix_ts)


def parse_clock(data: bytes) -> dict:
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


def set_account(acc: dict) -> None:
    """surfnet_setAccount — data is hex (v1.1+)."""
    surf(
        "surfnet_setAccount",
        [
            acc["pubkey"],
            {
                "lamports": acc["lamports"],
                "owner": acc["owner"],
                "executable": acc.get("executable", False),
                "data": acc["data"].hex(),
            },
        ],
    )


def enable_cheats() -> list[str]:
    wanted = [
        "surfnet_setAccount",
        "surfnet_timeTravel",
        "surfnet_pauseClock",
        "surfnet_resumeClock",
        "surfnet_streamAccount",
        "surfnet_resetAccount",
    ]
    enabled = []
    try:
        surf("surfnet_enableCheatcode", [wanted])
        enabled = wanted
    except Exception as exc:
        enabled.append(f"enable_failed:{exc}")
    return enabled


def stream_oracles() -> dict:
    out = {}
    for pk in ORACLES:
        try:
            surf("surfnet_streamAccount", [pk, {"includeOwnedAccounts": False}])
            out[pk] = "streamed"
        except Exception as exc:
            out[pk] = f"fail:{exc}"
    return out


def refresh(*, mode: str) -> dict:
    report: dict = {"mode": mode, "ts": time.time()}
    report["cheats"] = enable_cheats()

    mainnet = {pk: fetch_account(pk, url=MAINNET) for pk in (TICK_ACCOUNT, BAT1_ORACLE)}
    tick = parse_tick(mainnet[TICK_ACCOUNT]["data"])
    bat1_slot = parse_bat1_slot(mainnet[BAT1_ORACLE]["data"])
    report["mainnet_tick_slot"] = tick.slot
    report["mainnet_bat1_slot"] = bat1_slot
    report["mainnet_tick_magic"] = tick.magic.decode("ascii", "replace")

    clock_acc = fetch_account(CLOCK, url=SURFPOOL)
    clock = parse_clock(clock_acc["data"])
    report["surfpool_clock_before"] = clock

    if mode == "stream":
        report["stream"] = stream_oracles()
        # after stream, local copies should match mainnet; still need clock align
        mode = "time_travel"

    if mode == "time_travel":
        for pk in (TICK_ACCOUNT, BAT1_ORACLE, GLOBAL_STATE, POOL):
            try:
                acc = fetch_account(pk, url=MAINNET)
                set_account(acc)
                report.setdefault("wrote", {})[pk] = acc["lamports"]
            except Exception as exc:
                report.setdefault("write_err", {})[pk] = str(exc)
        # Surfpool timeTravel leaves Clock.slot as epoch slotIndex
        # (~37k), while the tick stores the absolute slot. Tessera
        # compares those via sol_get_clock_sysvar → 0xffff. Write the
        # Clock account to the absolute tick slot + matching unix ts.
        try:
            report["pause"] = surf("surfnet_pauseClock", [])
        except Exception as exc:
            report["pause_err"] = str(exc)
        try:
            report["time_travel"] = surf("surfnet_timeTravel", [{"absoluteSlot": tick.slot}])
        except Exception as exc:
            report["time_travel_err"] = str(exc)
        # Write Clock LAST so timeTravel cannot smash slot back to slotIndex.
        try:
            mn_clock = fetch_account(CLOCK, url=MAINNET)
            mn_c = parse_clock(mn_clock["data"])
            clock_bytes = pack_clock(
                tick.slot,
                mn_c.get("epoch_start_timestamp") or 0,
                mn_c.get("epoch") or 0,
                mn_c.get("leader_schedule_epoch") or 0,
                int(tick.curr_ts_ns // 1_000_000_000),
            )
            set_account(
                {
                    "pubkey": CLOCK,
                    "owner": SYSVAR_OWNER,
                    "lamports": mn_clock["lamports"],
                    "executable": False,
                    "data": clock_bytes,
                }
            )
            report["wrote_clock"] = parse_clock(clock_bytes)
        except Exception as exc:
            report["clock_write_err"] = str(exc)
            report["fallback"] = "patch_slot"
            mode = "patch_slot"

    if mode == "patch_slot":
        clock_acc = fetch_account(CLOCK, url=SURFPOOL)
        clock = parse_clock(clock_acc["data"])
        target = clock["slot"]
        report["patch_target_slot"] = target
        tick_acc = dict(mainnet[TICK_ACCOUNT])
        tick_acc["data"] = patch_tick_slot(tick_acc["data"], target)
        bat1_acc = dict(mainnet[BAT1_ORACLE])
        bat1_acc["data"] = patch_bat1_slot(bat1_acc["data"], target)
        set_account(tick_acc)
        set_account(bat1_acc)
        report["patched"] = True

    # verify
    local_tick = fetch_account(TICK_ACCOUNT, url=SURFPOOL)
    local_bat1 = fetch_account(BAT1_ORACLE, url=SURFPOOL)
    local_clock = parse_clock(fetch_account(CLOCK, url=SURFPOOL)["data"])
    lt = parse_tick(local_tick["data"])
    report["verify"] = {
        "clock_slot": local_clock.get("slot"),
        "tick_slot": lt.slot,
        "bat1_slot": parse_bat1_slot(local_bat1["data"]),
        "slot_delta": lt.slot - (local_clock.get("slot") or 0),
        "magic_ok": lt.magic_ok(),
        "owner": local_tick["owner"],
        "owner_ok": local_tick["owner"] == TICK_PROGRAM,
    }
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--mode",
        choices=["time_travel", "patch_slot", "stream"],
        default="time_travel",
    )
    ap.add_argument("--out", type=Path, default=Path("tools/re/notes/tessera_freshness.json"))
    args = ap.parse_args()
    report = refresh(mode=args.mode)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, default=str))
    print(json.dumps({"ok": report.get("verify", {}).get("slot_delta") == 0, **report.get("verify", {}), "out": str(args.out)}))
    return 0 if report.get("verify", {}).get("slot_delta") == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
