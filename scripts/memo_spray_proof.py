#!/usr/bin/env python3
"""Deterministic proof: memo/clone-style sprays score ~0 fair, high raw."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from voyager.scoring import MEMO_V1, MEMO_V2, discovery_reward, discovery_reward_unfiltered


def spray(program_ids: list[str], count: int = 256) -> tuple[int, int]:
    fair_seen: dict[tuple[str, int], bool] = {}
    raw_seen: dict[tuple[str, int], bool] = {}
    instructions = []
    for prog in program_ids:
        for disc in range(count):
            instructions.append({"program_id": prog, "data": bytes([disc % 256])})
    fair = discovery_reward(instructions, fair_seen)
    raw = discovery_reward_unfiltered(instructions, raw_seen)
    return fair, raw


def main() -> None:
    memo_only = [MEMO_V2, MEMO_V1]
    fair_memo, raw_memo = spray(memo_only, 200)
    print("memo_spray fair=", fair_memo, "raw=", raw_memo)

    # Simulate six memo-equivalent clone program IDs (old farmer pattern)
    clones = [
        MEMO_V2,
        "A82cL14eLNHCw3dkpeqP3tTkwMb1sCxfCfcgfJxv1Jkd",
        "Fk9fW8QNtJA1EsG4xR1muYq3sKNeDK412ztBBrJotATq",
        "DBXveJ9U6YMrG8ZgEKebp1j2ktisa1V9gAntdSu8rbXR",
        "25WuDXE5R1pnGPr4ihJkEiqj9xevL1KszxYZS2T7EhAp",
        "DA3DUgh2fM7aXGz1X16ixHyGXbteLSNTB5drnrnw1N9Y",
    ]
    fair_clone, raw_clone = spray(clones, 200)
    print("clone_spray fair=", fair_clone, "raw=", raw_clone)

    # C1ix-style always-ok ELF clones: distinct IDs, not Memo, 94 × 32 first-bytes.
    c1ix = [f"C1ixSyntheticFarm{i:02d}111111111111111111111111" for i in range(94)]
    fair_c1ix, raw_c1ix = spray(c1ix, 32)
    print("c1ix_farm fair=", fair_c1ix, "raw=", raw_c1ix)


if __name__ == "__main__":
    main()
