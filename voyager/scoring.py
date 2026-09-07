"""Pure unique-instruction scoring helpers.

These functions have no RPC, validator, or LLM dependencies so reward
logic can be tested offline.
"""

from __future__ import annotations

import base64
from typing import Any, Iterable, Mapping, Sequence

try:
    import base58
except ImportError:  # pragma: no cover - optional in unit tests
    base58 = None


def decode_ix_data(data: Any) -> bytes:
    """Normalize instruction data from bytes, int lists, base58, or base64."""
    if data is None:
        return b""
    if isinstance(data, bytes):
        return data
    if isinstance(data, bytearray):
        return bytes(data)
    if isinstance(data, memoryview):
        return bytes(data)
    if isinstance(data, (list, tuple)):
        try:
            return bytes(data)
        except (ValueError, TypeError):
            return b""
    if isinstance(data, str):
        if not data:
            return b""
        if base58 is not None:
            try:
                return base58.b58decode(data)
            except Exception:
                pass
        try:
            return base64.b64decode(data, validate=True)
        except Exception:
            try:
                return base64.b64decode(data)
            except Exception:
                return data.encode("utf-8")
    return b""


def instruction_discriminator(data: Any) -> int:
    """First byte of instruction data, or 0 when data is empty."""
    decoded = decode_ix_data(data)
    return decoded[0] if decoded else 0


def normalize_program_id(program_id: Any) -> str:
    return str(program_id)


def unique_instruction_key(program_id: Any, data: Any) -> tuple[str, int]:
    return (normalize_program_id(program_id), instruction_discriminator(data))


def collect_ordered_instructions(
    top_level: Sequence[Mapping[str, Any]],
    inner_by_index: Mapping[int, Sequence[Mapping[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    """Flatten top-level + inner instructions.

    Missing inner-instruction indexes are treated as empty. This is the
    sandbox scoring equivalent of Solana's ordered instruction list.
    """
    inner_by_index = inner_by_index or {}
    ordered: list[dict[str, Any]] = []
    for idx, ix in enumerate(top_level):
        ordered.append(
            {
                "program_id": ix["program_id"],
                "data": decode_ix_data(ix.get("data")),
            }
        )
        for inner in inner_by_index.get(idx, []) or []:
            ordered.append(
                {
                    "program_id": inner["program_id"],
                    "data": decode_ix_data(inner.get("data")),
                }
            )
    return ordered


def discovery_reward(
    instructions: Iterable[Mapping[str, Any]],
    seen: dict[tuple[str, int], bool],
    allowed_programs: Sequence[str] | None = None,
) -> int:
    """+1 for each new (program_id, discriminator) pair.

    ``seen`` is mutated in place so repeated instructions across
    transactions are not double-counted.
    """
    reward = 0
    allowed = set(allowed_programs) if allowed_programs else None
    for ix in instructions:
        prog = normalize_program_id(ix["program_id"])
        if allowed is not None and prog not in allowed:
            continue
        key = unique_instruction_key(prog, ix.get("data"))
        if key not in seen:
            seen[key] = True
            reward += 1
    return reward


def unique_instructions_by_program(
    instructions: Iterable[Mapping[str, Any]],
) -> dict[str, list[int]]:
    grouped: dict[str, list[int]] = {}
    for ix in instructions:
        prog = normalize_program_id(ix["program_id"])
        disc = instruction_discriminator(ix.get("data"))
        grouped.setdefault(prog, [])
        grouped[prog].append(disc)
    return grouped
