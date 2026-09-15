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
