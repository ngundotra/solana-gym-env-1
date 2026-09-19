"""Tessera V taker swap layout from live Jupiter CPI (0x10 + 14 accounts).

Do not invent IDL. Bytes taken from mainnet successes (fee-payer BpZpRbuy...).
Direct / stale-tick sends return custom 0xffff.
"""

from __future__ import annotations

SWAP_SELECTOR = 0x10
SWAP_DATA_SIZE = 18

# Constant extra accounts on every observed 0x10 + 14acc Jupiter hop.
GLOBAL_STATE = "8ekCy2jHHUbW2yeNGFWYJT9Hm9FW7SvZcZK66dSZCDiF"
BAT1_ORACLE = "BAT1Ndpu5gbLTp2AZkSXP79LJBZfCH4B3zGhi6LtvdhK"
TICK_ACCOUNT = "4cG31VNF9TzFinNc7BmnjhFvGjxkY3sCETVMtMgbrhPs"
TICK_PROGRAM = "tickUcsEQegChaAuo9VYQQztB4ZGApY6ZT4FkULWY6N"
TICK_MAGIC = b"MRKTKV01"


def encode_swap(amount_in: int, *, side: int = 0, min_out: int = 0) -> bytes:
    if side not in (0, 1):
        raise ValueError("side must be 0 (quote->base) or 1 (base->quote)")
    data = bytearray(SWAP_DATA_SIZE)
    data[0] = SWAP_SELECTOR
    data[1] = side
    data[2:10] = int(amount_in).to_bytes(8, "little")
    data[10:18] = int(min_out).to_bytes(8, "little")
    return bytes(data)


def decode_swap(data: bytes) -> dict:
    if not data or data[0] != SWAP_SELECTOR:
        raise ValueError("not a Tessera 0x10 swap")
    return {
        "selector": data[0],
        "side": data[1],
        "amount_in": int.from_bytes(data[2:10], "little"),
        "min_out": int.from_bytes(data[10:18], "little") if len(data) >= 18 else 0,
    }
