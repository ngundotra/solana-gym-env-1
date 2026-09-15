"""Tessera tick account (MRKTKV01) layout from live mainnet bytes + ELF strings.

Tick program (`tickUcs…`, `programs/market-tick/src/processor.rs`) rejects with:
- Instruction slot does not match the runtime clock slot
- Signer is not the signer selected for this slot
- Timestamp must strictly increase within a slot
- Target interval cannot change within a slot

88-byte account owned by tickUcs. Do not invent extra fields.
"""

from __future__ import annotations

from dataclasses import dataclass

TICK_MAGIC = b"MRKTKV01"
TICK_SIZE = 88
TICK_SLOT_OFF = 40

# BAT1 book (Tessera-owned, 2048B) stores a slot u64 at offset 0 (live).
BAT1_SLOT_OFF = 0


@dataclass(frozen=True)
class TickAccount:
    magic: bytes
    signer: bytes  # 32-byte pubkey selected for this slot
    slot: int
    prev_ts_ns: int
    curr_ts_ns: int
    seq: int
    target_interval_ns: int
    last_interval_ns: int

    def magic_ok(self) -> bool:
        return self.magic == TICK_MAGIC


def parse_tick(data: bytes) -> TickAccount:
    if len(data) < TICK_SIZE:
        raise ValueError(f"tick account shorter than {TICK_SIZE}: {len(data)}")
    return TickAccount(
        magic=data[0:8],
        signer=data[8:40],
        slot=int.from_bytes(data[40:48], "little"),
        prev_ts_ns=int.from_bytes(data[48:56], "little"),
        curr_ts_ns=int.from_bytes(data[56:64], "little"),
        seq=int.from_bytes(data[64:72], "little"),
        target_interval_ns=int.from_bytes(data[72:80], "little"),
        last_interval_ns=int.from_bytes(data[80:88], "little"),
    )


def parse_bat1_slot(data: bytes) -> int:
    if len(data) < 8:
        raise ValueError("BAT1 too short")
    return int.from_bytes(data[BAT1_SLOT_OFF : BAT1_SLOT_OFF + 8], "little")
