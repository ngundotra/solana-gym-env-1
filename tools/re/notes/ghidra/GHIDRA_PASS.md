# Ghidra / ELF pass (2026-09-15)

## Dumps
| program | pubkey | ELF | arch |
|---|---|---|---|
| HumidiFi | `9H6tua7jkLhdm3w8BvgpTn5LZNU7g4ZynDmCiNN3q6Rp` | 339440 B | SBF `EM=0x107` |
| Tessera | `TessVdML9pBGgG9yGks7o4HewRaXVAMuoVj4x83GLQH` | 576932 B | eBPF |
| Tick | `tickUcsEQegChaAuo9VYQQztB4ZGApY6ZT4FkULWY6N` | 148368 B | SBF `EM=0x107` |

`*.so` gitignored; regenerate with `tools/re/scripts/dump_programs.sh` plus tick dump.

## Ghidra 12.1.3
- `BPF:LE:64:default` unsupported.
- Tessera imported as **`eBPF:LE:64:default`**. Analysis succeeded (~4s).
- Post-script `DumpTesseraFuncs.java`: **236 functions** (Chris Chang Breakpoint recap said ~415 in Binary Ninja — different splitter).
- No named `swap`/`tick` symbols (stripped). Function list: `tessera_funcs.txt`.
- HumidiFi / tick SBF `0x107` has no stock Ghidra language; rizin strings used instead.

## Tick program strings (watertight)
`programs/market-tick/src/processor.rs` / `lib.rs`. Magic `MRKTKV01` in both Tessera and tick ELFs.

Tick rejects with:
- `Instruction slot does not match the runtime clock slot`
- `Signer is not the signer selected for this slot`
- `Timestamp must strictly increase within a slot`
- `Target interval cannot change within a slot`

## Tessera ELF strings
- `src/utils/batch_clock.rs`, `src/utils/swap_math.rs`, `src/instruction.rs`, `src/entrypoint.rs`, `src/processor.rs`, `src/state.rs`
- Embedded `MRKT` / `KV01` (validates tick account header)
- Syscalls: `sol_get_clock_sysvar`, `sol_get_last_restart_slot`

This matches the Surfpool `0xffff` gate: `0x10` reads `MRKTKV01` + clock; one-shot clones go stale.

## Tick account layout (live, 88 B)

Captured vs clock slot `447170946` / tick slot `447170943` (delta −3), later recapture delta −6. Parser: `tools/re/scripts/tick_codec.py`.

| off | type | field | evidence |
|---|---|---|---|
| 0 | `[u8;8]` | magic `MRKTKV01` | ELF + account |
| 8 | `[u8;32]` | signer selected for this slot | tick error string |
| 40 | `u64le` | **slot** | matches clock ± a few |
| 48 | `u64le` | prev timestamp ns | `~1e9 * unix` |
| 56 | `u64le` | curr timestamp ns | strictly increases |
| 64 | `u64le` | seq (observed 9) | increments intra-slot |
| 72 | `u64le` | target interval ns (30_000_000) | "cannot change within a slot" |
| 80 | `u64le` | last interval ns (~29.97 ms) | |

BAT1 (`BAT1Ndpu…`, Tessera-owned, 2048 B) stores a **slot u64 at offset 0** (same epoch, a few slots behind tick).

Surfpool local clock lagged mainnet by hundreds of slots while the live tick tracked clock within 6. One-shot clones cannot satisfy `Instruction slot does not match the runtime clock slot`.

## HumidiFi ELF crumbs
`GIT_HASH:26ebfd833cbb015b1cd1160840f8620c24f19b67` plus `contract/src/routers/{dflow,jupiter}.rs`. See `notes/ELF_CATALOG.md`. SBF `0x107` still has no Ghidra language; rizin strings only.
