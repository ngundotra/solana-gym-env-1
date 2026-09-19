"""Offline parse of a captured Tessera tick account (no RPC)."""

from tools.re.scripts.tick_codec import (
    TICK_MAGIC,
    parse_bat1_slot,
    parse_tick,
    patch_bat1_slot,
    patch_tick_slot,
)

# Captured 2026-09-15, clock slot 447170946, tick slot 447170943 (delta -3).
TICK_HEX = (
    "4d524b544b56303196fa7d4a92db045534df681fc0d8699e"
    "399df52d2e6eaec7699a9808b33aab197f49a71a00000000"
    "dbe4d7129f67d5189210d6229f67d5180900000000000000"
    "80c3c90100000000de64c90100000000"
)
BAT1_HEAD = "7449a71a000000000000000100000201"


def test_tick_magic_and_slot():
    tick = parse_tick(bytes.fromhex(TICK_HEX))
    assert tick.magic == TICK_MAGIC
    assert tick.magic_ok()
    assert tick.slot == 447170943
    assert len(tick.signer) == 32
    assert tick.seq == 9
    assert tick.target_interval_ns == 30_000_000
    assert tick.last_interval_ns == 29_975_774
    assert tick.curr_ts_ns > tick.prev_ts_ns
    # ns timestamps are ~1e9 * unix seconds (~1789450360 on this capture)
    assert 1_789_450_359_000_000_000 <= tick.prev_ts_ns < 1_789_450_361_000_000_000


def test_bat1_slot_header():
    assert parse_bat1_slot(bytes.fromhex(BAT1_HEAD)) == 447170932


def test_patch_tick_slot_only_rewrites_offset_40():
    raw = bytes.fromhex(TICK_HEX)
    patched = patch_tick_slot(raw, 447171000)
    assert parse_tick(patched).slot == 447171000
    assert patched[:40] == raw[:40]
    assert patched[48:] == raw[48:]


def test_patch_bat1_slot():
    raw = bytes.fromhex(BAT1_HEAD + "00" * 8)
    patched = patch_bat1_slot(raw, 99)
    assert parse_bat1_slot(patched) == 99
    assert patched[8:] == raw[8:]
