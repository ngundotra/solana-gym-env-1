#!/usr/bin/env python3
"""Catalog rust paths, magics, and error strings from dumped ELFs.

Does not invent IDL. Used to pin Tessera 0xffff to tick-slot strings and
to recover HumidiFi router crumbs (GIT_HASH, dflow/jupiter modules).
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

DUMPS = Path(__file__).resolve().parent.parent / "dumps"
NOTES = Path(__file__).resolve().parent.parent / "notes"

GIT_HASH = re.compile(rb"GIT_HASH:([0-9a-f]{40})")
PRINTABLE_RUN = re.compile(rb"[\x20-\x7e]{8,120}")
PATH_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_/+-")
PATH_PFX = ("contract/src/", "programs/", "toxmodel/src/", "src/")

PINNED_STRINGS = (
    b"Instruction slot does not match the runtime clock slot",
    b"Signer is not the signer selected for this slot",
    b"Timestamp must strictly increase within a slot",
    b"Target interval cannot change within a slot",
    b"market-tick: initialized",
    b"dflow_score",
    b"rotate_pool_authority",
    b"GIT_HASH:",
)

KEEP = (
    "slot",
    "clock",
    "tick",
    "signer",
    "timestamp",
    "interval",
    "oracle",
    "swap",
    "router",
    "dflow",
    "jupiter",
    "pool",
    "authority",
    "initialized",
    "mismatch",
    "stale",
    "instruction",
    "git_hash",
    "panicked",
)


def rust_paths(blob: bytes) -> set[str]:
    """Split concatenated rustc paths (`.` is a path char, so regex over-matches)."""
    text = blob.decode("latin1")
    out: set[str] = set()
    start = 0
    while True:
        i = text.find(".rs", start)
        if i < 0:
            break
        j = i
        while j > 0 and text[j - 1] in PATH_CHARS:
            j -= 1
        candidate = text[j : i + 3]
        for pfx in PATH_PFX:
            k = candidate.rfind(pfx)
            if k >= 0:
                out.add(candidate[k:])
                break
        start = i + 3
    return out


def extract(path: Path) -> dict:
    blob = path.read_bytes()
    rust = rust_paths(blob)
    hashes = [m.group(1).decode("ascii") for m in GIT_HASH.finditer(blob)]
    magics: set[str] = set()
    if b"MRKTKV01" in blob:
        magics.add("MRKTKV01")
    elif b"MRKT" in blob:
        magics.add("MRKT")
    if b"KAM\x00" in blob:
        magics.add("KAM\\0")
    strings: list[str] = []
    seen: set[str] = set()
    for pin in PINNED_STRINGS:
        if pin in blob:
            s = pin.decode("ascii").rstrip(":")
            if pin == b"GIT_HASH:":
                continue
            seen.add(s)
            strings.append(s)
    for m in PRINTABLE_RUN.finditer(blob):
        s = m.group().decode("ascii")
        low = s.lower()
        if any(k in low for k in KEEP) and s not in seen:
            if "platform-tools" in s or s.startswith("library/"):
                continue
            if any(n in s for n in ("Constraint", "AccountNot", "AnchorError", "ProgramError")):
                continue
            if len(s) > 120:
                continue
            seen.add(s)
            strings.append(s)
    return {
        "file": path.name,
        "size": len(blob),
        "git_hashes": hashes,
        "rust_paths": sorted(rust),
        "magics": sorted(magics),
        "interesting_strings": strings,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dumps", type=Path, default=DUMPS)
    ap.add_argument("--out", type=Path, default=NOTES / "elf_catalog.json")
    args = ap.parse_args()

    report = {}
    for name in ("humidifi.so", "tessera.so", "tick.so"):
        p = args.dumps / name
        if not p.exists():
            report[name] = {"missing": True}
            continue
        report[name] = extract(p)
        print(
            f"{name}: rust={len(report[name]['rust_paths'])} "
            f"git={report[name]['git_hashes']} "
            f"strings={len(report[name]['interesting_strings'])}"
        )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
