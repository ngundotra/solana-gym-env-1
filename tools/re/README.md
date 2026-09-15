# Reverse-engineering toolkit (HumidiFi + Tessera)

See `notes/HYPOTHESIS_LOG.md` and `notes/TX_SAMPLE.md`.

```bash
# ELF dumps (gitignores *.so)
./tools/re/scripts/dump_programs.sh
python3 tools/re/scripts/elf_catalog.py
python3 tools/re/scripts/tick_layout.py   # live MRKTKV01 slot vs clock

# Mainnet clustering (Tessera 0x10+14 Jupiter-only; HumidiFi 25B taker)
python3 tools/re/scripts/archaeology.py --target both --limit 40

# Jupiter quote + Surfpool replay
# requires: surfpool start --no-tui -u https://api.mainnet-beta.solana.com
#           and solders (uv venv)
python3 tools/re/scripts/surfpool_jup_replay.py --dex HumidiFi
python3 tools/re/scripts/surfpool_jup_replay.py --dex TesseraV

# Replay a known-good mainnet sig on Surfpool (sigVerify=false)
python3 tools/re/scripts/replay_mainnet_tx.py <SIG>
```

Codecs: `humidifi_codec.py` (XOR + live markers `0x14`/`0x30`), `tessera_codec.py` (`0x10` + 18B), `tick_codec.py` (`MRKTKV01` 88B).

Tests: `uv run python -m pytest tests/test_humidifi_codec.py tests/test_tessera_codec.py tests/test_tick_codec.py`.
