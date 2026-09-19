"""HumidiFi swap instruction XOR codec.

Sources (do not invent IDL):
- michaelmorrell gist: https://gist.github.com/skynetcap/fb456a0ff0d1ab94b94ea9443e4da4aa
- X: https://x.com/michaelmorrell/status/1996401249055641759
- OKX DEX-Router XOR (ce15b2da, later stubbed to AdapterAbort)
- Live 2026-09 Chaintruth probe: 25-byte taker swaps use marker 0x30, not crate 0x14
"""

from __future__ import annotations

from dataclasses import dataclass

# First 8 bytes of HUMIDIFI_IX_DATA_KEY_SEED (Morrell / OKX / swaps crate).
HUMIDIFI_IX_DATA_KEY = bytes([58, 255, 47, 255, 226, 186, 235, 195])
POS_MASK_STEP = 0x0001_0001_0001_0001

# Historical selectors seen after deobfuscation at byte 24.
SELECTOR_V1 = 0x04  # Morrell gist examples
SELECTOR_V2_CRATE = 0x14  # swaps crate SWAP_V2_MARKER (stale vs live)
SELECTOR_LIVE_2026_09 = 0x30  # Chaintruth live 25B Jupiter-routed swaps

SWAP_DATA_SIZE = 25


def obfuscate(data: bytearray | bytes) -> bytearray:
    """In-place XOR stream cipher on u64 chunks. Symmetric."""
    buf = bytearray(data)
    pos_mask = 0
    i = 0
    while i < len(buf):
        chunk = buf[i : i + 8]
        padded = chunk + bytes(8 - len(chunk))
        qword = int.from_bytes(padded, "little")
        qword ^= int.from_bytes(HUMIDIFI_IX_DATA_KEY, "little")
        qword ^= pos_mask
        mixed = qword.to_bytes(8, "little")
        buf[i : i + len(chunk)] = mixed[: len(chunk)]
        pos_mask = (pos_mask + POS_MASK_STEP) & ((1 << 64) - 1)
        i += 8
    return buf


@dataclass(frozen=True)
class HumidiFiSwap:
    swap_id: int
    amount_in: int
    is_base_to_quote: bool
    padding: bytes
    selector: int

    def plaintext(self) -> bytes:
        out = bytearray(SWAP_DATA_SIZE)
        out[0:8] = self.swap_id.to_bytes(8, "little")
        out[8:16] = self.amount_in.to_bytes(8, "little")
        out[16] = 1 if self.is_base_to_quote else 0
        pad = self.padding[:7].ljust(7, b"\x00")
        out[17:24] = pad
        out[24] = self.selector
        return bytes(out)

    def encode(self) -> bytes:
        return bytes(obfuscate(self.plaintext()))


def decode_swap(data: bytes) -> HumidiFiSwap:
    if len(data) != SWAP_DATA_SIZE:
        raise ValueError(f"expected {SWAP_DATA_SIZE} bytes, got {len(data)}")
    plain = bytes(obfuscate(data))
    return HumidiFiSwap(
        swap_id=int.from_bytes(plain[0:8], "little"),
        amount_in=int.from_bytes(plain[8:16], "little"),
        is_base_to_quote=plain[16] == 1,
        padding=plain[17:24],
        selector=plain[24],
    )


def encode_swap(
    amount_in: int,
    *,
    swap_id: int,
    is_base_to_quote: bool,
    selector: int = SELECTOR_LIVE_2026_09,
    padding: bytes = b"\x00" * 7,
) -> bytes:
    return HumidiFiSwap(
        swap_id=swap_id,
        amount_in=amount_in,
        is_base_to_quote=is_base_to_quote,
        padding=padding,
        selector=selector,
    ).encode()
