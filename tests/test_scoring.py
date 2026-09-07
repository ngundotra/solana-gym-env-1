import base64

from voyager.scoring import (
    collect_ordered_instructions,
    decode_ix_data,
    discovery_reward,
    instruction_discriminator,
    unique_instruction_key,
    unique_instructions_by_program,
)

SYSTEM = "11111111111111111111111111111111"
MEMO = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"


def test_decode_bytes_and_empty():
    assert decode_ix_data(b"\x02\x00") == b"\x02\x00"
    assert decode_ix_data(None) == b""
    assert decode_ix_data([]) == b""
    assert decode_ix_data([2, 0, 1]) == b"\x02\x00\x01"


def test_decode_base64_and_raw_string():
    payload = base64.b64encode(b"\x03\x01").decode()
    assert decode_ix_data(payload) == b"\x03\x01"
    assert decode_ix_data("") == b""


def test_discriminator_defaults_to_zero():
    assert instruction_discriminator(b"") == 0
    assert instruction_discriminator(b"\x07\xff") == 7


def test_collect_ordered_instructions_skips_missing_inners():
    top = [
        {"program_id": SYSTEM, "data": b"\x02"},
        {"program_id": MEMO, "data": b"hello"},
    ]
    inner = {1: [{"program_id": SYSTEM, "data": b"\x00"}]}
    ordered = collect_ordered_instructions(top, inner)
    assert [ix["program_id"] for ix in ordered] == [SYSTEM, MEMO, SYSTEM]
    # Index 0 has no inners; must not raise.
    assert collect_ordered_instructions(top, None)[0]["program_id"] == SYSTEM


def test_discovery_reward_is_unique_and_filterable():
    seen = {}
    first = collect_ordered_instructions(
        [
            {"program_id": SYSTEM, "data": b"\x02"},
            {"program_id": SYSTEM, "data": b"\x02"},
            {"program_id": MEMO, "data": b"a"},
        ]
    )
    assert discovery_reward(first, seen) == 2
    assert discovery_reward(first, seen) == 0
    swap_only = discovery_reward(
        first,
        {},
        allowed_programs=[MEMO],
    )
    assert swap_only == 1


def test_unique_instruction_key_and_grouping():
    assert unique_instruction_key(SYSTEM, b"\x02") == (SYSTEM, 2)
    grouped = unique_instructions_by_program(
        [
            {"program_id": SYSTEM, "data": b"\x02"},
            {"program_id": SYSTEM, "data": b"\x03"},
        ]
    )
    assert grouped[SYSTEM] == [2, 3]
