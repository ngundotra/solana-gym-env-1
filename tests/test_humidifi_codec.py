"""Golden-vector tests for HumidiFi XOR codec (Morrell gist + live marker)."""

from tools.re.scripts.humidifi_codec import (
    SELECTOR_LIVE_2026_09,
    SELECTOR_V1,
    decode_swap,
    encode_swap,
    obfuscate,
)


# michaelmorrell / skynetcap gist examples (selector 0x04 after decode).
GIST_1 = bytes.fromhex("0bc7a29d90470eb94aabc533e3baeac338ff2dffe0bae9c33d")
GIST_2 = bytes.fromhex("236176715d8fa196ed9c61feebbaeac338ff2dffe0bae9c33d")


def test_obfuscate_is_symmetric():
    raw = bytearray(b"abcdefghijklmnopqrstruvwx")
    once = obfuscate(raw)
    twice = obfuscate(once)
    assert bytes(twice) == bytes(raw)


def test_gist_example_1_layout():
    sw = decode_swap(GIST_1)
    assert sw.selector == SELECTOR_V1
    assert sw.amount_in > 0
    assert encode_swap(
        sw.amount_in,
        swap_id=sw.swap_id,
        is_base_to_quote=sw.is_base_to_quote,
        selector=sw.selector,
        padding=sw.padding,
    ) == GIST_1


def test_gist_example_2_roundtrip():
    sw = decode_swap(GIST_2)
    assert sw.selector == SELECTOR_V1
    assert decode_swap(sw.encode()) == sw


def test_live_marker_0x30_roundtrip():
    blob = encode_swap(
        1_000_000,
        swap_id=0x1122334455667788,
        is_base_to_quote=True,
        selector=SELECTOR_LIVE_2026_09,
    )
    sw = decode_swap(blob)
    assert sw.selector == 0x30
    assert sw.amount_in == 1_000_000
    assert sw.swap_id == 0x1122334455667788
    assert sw.is_base_to_quote is True
