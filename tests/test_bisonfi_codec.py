"""BisonFi 0x02 encoder from the Surfpool Jupiter CPI vector."""

from tools.re.scripts.bisonfi_codec import decode_swap, encode_swap

# Surfpool sig 22nFohKR… (BisonFi invoke success, 0-fill because min_out=0)
LIVE = bytes.fromhex("028096980000000000000000000000000000")


def test_live_vector():
    sw = decode_swap(LIVE)
    assert sw["selector"] == 0x02
    assert sw["amount_in"] == 10_000_000
    assert sw["min_out"] == 0
    assert encode_swap(10_000_000, min_out=0) == LIVE


def test_min_out_roundtrip():
    blob = encode_swap(1_000_000, min_out=2)
    sw = decode_swap(blob)
    assert sw["min_out"] == 2
    assert sw["amount_in"] == 1_000_000
