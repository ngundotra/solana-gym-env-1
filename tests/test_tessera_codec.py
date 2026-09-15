"""Live-byte tests for Tessera 0x10 encoder."""

from tools.re.scripts.tessera_codec import decode_swap, encode_swap

# Mainnet success 2AUbcsTE... (BpZpRbuy, slot 447168171)
LIVE = bytes.fromhex("1000bdfded00000000000000000000000000")


def test_live_success_vector():
    sw = decode_swap(LIVE)
    assert sw["selector"] == 0x10
    assert sw["side"] == 0
    assert sw["amount_in"] == 0xEDFDBD
    assert sw["min_out"] == 0
    assert encode_swap(sw["amount_in"], side=0, min_out=0) == LIVE


def test_side_one():
    blob = encode_swap(1_000_000, side=1, min_out=2)
    sw = decode_swap(blob)
    assert sw["side"] == 1
    assert sw["min_out"] == 2
