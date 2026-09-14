import base64

from voyager.scoring import (
    MEMO_V1,
    MEMO_V2,
    collect_ordered_instructions,
    decode_ix_data,
    default_fair_allowed_programs,
    discovery_reward,
    discovery_reward_unfiltered,
    instruction_discriminator,
    load_top100_program_ids,
    unique_instruction_key,
    unique_instructions_by_program,
)

SYSTEM = "11111111111111111111111111111111"
TOKEN = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
MEMO = MEMO_V2
# Rank 100 in docs/top100_programs_snapshot.json — last allowlisted slot.
TOP100_LAST = "ForaPmWWcahJbcnUXM1JJKfzntvAsACddY4rm85wtt4j"
# Rank 101 — present in the snapshot file but outside the fair top-100 set.
SNAPSHOT_RANK_101 = "Send9wszHjEiS3hwKcPeSLsPRu5Gb62iCrJEcG4Mq3b"


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
    assert discovery_reward(first, seen) == 1
    assert discovery_reward(first, seen) == 0
    swap_only = discovery_reward(
        first,
        {},
        allowed_programs=[MEMO],
    )
    assert swap_only == 1


def test_memo_instructions_award_zero_under_defaults():
    seen = {}
    memo_ixs = collect_ordered_instructions(
        [
            {"program_id": MEMO_V2, "data": b"memo-a"},
            {"program_id": MEMO_V1, "data": b"memo-b"},
            {"program_id": MEMO_V2, "data": b"memo-c"},
        ]
    )
    assert discovery_reward(memo_ixs, seen) == 0
    assert seen == {}


def test_per_program_unique_cap_blocks_33rd_discriminator():
    seen = {}
    program = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
    instructions = [
        {"program_id": program, "data": bytes([disc])}
        for disc in range(33)
    ]
    reward = discovery_reward(
        instructions,
        seen,
        excluded_programs=[],
        max_unique_per_program=32,
    )
    assert reward == 32
    assert _program_unique_count(seen, program) == 32
    extra = discovery_reward(
        [{"program_id": program, "data": b"\xff"}],
        seen,
        excluded_programs=[],
        max_unique_per_program=32,
    )
    assert extra == 0


def test_non_memo_programs_still_score_under_defaults():
    seen = {}
    instructions = collect_ordered_instructions(
        [
            {"program_id": SYSTEM, "data": b"\x02"},
            {"program_id": TOKEN, "data": b"\x03"},
            {"program_id": MEMO_V2, "data": b"ignored"},
        ]
    )
    assert discovery_reward(instructions, seen) == 2


def test_default_fair_allowlist_is_top100_minus_memo():
    """Fair score measures coverage of the checked-in top-100 usage set."""
    top100 = load_top100_program_ids()
    allowlist = default_fair_allowed_programs()
    assert allowlist is not None
    assert len(top100) == 100
    assert len(allowlist) == 98
    assert SYSTEM in allowlist
    assert TOKEN in allowlist
    assert TOP100_LAST in allowlist
    assert MEMO_V1 not in allowlist
    assert MEMO_V2 not in allowlist
    assert SNAPSHOT_RANK_101 not in allowlist
    assert MEMO_V1 in top100
    assert MEMO_V2 in top100


def test_c1ix_synthetic_clone_farm_fair_zero_raw_unfiltered():
    """Always-ok ELF clones (distinct IDs, not Memo) must not climb fair."""
    clones = [f"C1ixSyntheticFarm{i:02d}111111111111111111111111" for i in range(94)]
    instructions = [
        {"program_id": prog, "data": bytes([disc])}
        for prog in clones
        for disc in range(32)
    ]
    fair = discovery_reward(instructions, {})
    raw = discovery_reward_unfiltered(instructions, {})
    assert fair == 0
    assert raw == 94 * 32


def test_allowlisted_programs_still_score_beside_clone_farm():
    clones = [
        {"program_id": f"C1ixExtra{i:02d}11111111111111111111111111", "data": bytes([i])}
        for i in range(8)
    ]
    honest = [
        {"program_id": SYSTEM, "data": b"\x02"},
        {"program_id": TOKEN, "data": b"\x03"},
        {"program_id": TOP100_LAST, "data": b"\x01"},
        {"program_id": SNAPSHOT_RANK_101, "data": b"\x01"},
        {"program_id": MEMO_V2, "data": b"memo"},
    ]
    instructions = clones + honest
    fair = discovery_reward(instructions, {})
    raw = discovery_reward_unfiltered(instructions, {})
    assert fair == 3  # System + Token + rank-100; not rank-101, Memo, or clones
    assert raw == len(instructions)


def test_fair_allowlist_disable_env_restores_legacy_include_all(monkeypatch):
    monkeypatch.setenv("SCORE_FAIR_ALLOWLIST", "0")
    synth = [{"program_id": "C1ixLegacyMode111111111111111111111111111", "data": b"\x07"}]
    assert discovery_reward(synth, {}) == 1
    assert default_fair_allowed_programs() is None


def test_allowed_programs_still_works_with_memo_whitelist():
    instructions = collect_ordered_instructions(
        [
            {"program_id": SYSTEM, "data": b"\x02"},
            {"program_id": MEMO, "data": b"a"},
        ]
    )
    assert discovery_reward(instructions, {}, allowed_programs=[MEMO]) == 1


def test_spam_filter_skips_zero_account_nonempty_data():
    seen = {}
    instructions = [
        {
            "program_id": SYSTEM,
            "data": b"\x01",
            "accounts": [],
        }
    ]
    assert discovery_reward(
        instructions,
        seen,
        excluded_programs=[],
        apply_spam_filter=True,
    ) == 0
    assert discovery_reward(
        instructions,
        {},
        excluded_programs=[],
        apply_spam_filter=False,
    ) == 1


def test_raw_unfiltered_includes_memo_and_ignores_cap():
    seen = {}
    instructions = [
        {"program_id": MEMO_V2, "data": bytes([i])} for i in range(40)
    ]
    assert discovery_reward_unfiltered(instructions, seen) == 40


def test_unique_instruction_key_and_grouping():
    assert unique_instruction_key(SYSTEM, b"\x02") == (SYSTEM, 2)
    grouped = unique_instructions_by_program(
        [
            {"program_id": SYSTEM, "data": b"\x02"},
            {"program_id": SYSTEM, "data": b"\x03"},
        ]
    )
    assert grouped[SYSTEM] == [2, 3]


def _program_unique_count(seen, program_id):
    return sum(1 for prog, _ in seen if prog == program_id)
