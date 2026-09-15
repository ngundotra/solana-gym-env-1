"""BisonFi taker swap layout from a Jupiter CPI that the program accepted.

Live Jupiter route (2026-09-15) + Surfpool invoke[2] success:
18-byte data `0x02 | amount_in:u64le | min_out:u64le`, 10 accounts.
Do not invent more fields. A 0-fill still used this blob (min_out=0).
"""

from __future__ import annotations

SWAP_SELECTOR = 0x02
SWAP_DATA_SIZE = 18
PROGRAM_ID = "BiSoNHVpsVZW2F7rx2eQ59yQwKxzU5NvBcmKshCSUypi"


def encode_swap(amount_in: int, *, min_out: int = 0) -> bytes:
    data = bytearray(SWAP_DATA_SIZE)
    data[0] = SWAP_SELECTOR
    data[1:9] = int(amount_in).to_bytes(8, "little")
    data[9:17] = int(min_out).to_bytes(8, "little")
    return bytes(data)


def decode_swap(data: bytes) -> dict:
    if not data or data[0] != SWAP_SELECTOR:
        raise ValueError("not a BisonFi 0x02 swap")
    return {
        "selector": data[0],
        "amount_in": int.from_bytes(data[1:9], "little"),
        "min_out": int.from_bytes(data[9:17], "little") if len(data) >= 17 else 0,
    }
