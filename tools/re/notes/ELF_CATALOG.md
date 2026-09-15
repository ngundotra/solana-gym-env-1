# ELF catalog (2026-09-15)

Regenerate: `python3 tools/re/scripts/elf_catalog.py` (needs `tools/re/dumps/*.so`).

## HumidiFi `9H6tua7jkLhdm3w8BvgpTn5LZNU7g4ZynDmCiNN3q6Rp`

| | |
|---|---|
| size | 339440 B |
| arch | SBF `EM=0x107` (no stock Ghidra language) |
| `GIT_HASH` | `26ebfd833cbb015b1cd1160840f8620c24f19b67` (not found on public GitHub commit search) |

Router-shaped rust paths inside the **swap program** (not an aggregator):

- `contract/src/routers/dflow.rs`
- `contract/src/routers/jupiter.rs`
- `contract/src/router_swap.rs`
- `contract/src/dexes/directional_arb.rs`
- `contract/src/instructions.rs` / `stateupdate.rs` / `ops.rs`
- `toxmodel/src/lib.rs`

Other strings: `dflow_score`, `rotate_pool_authority`, `routerv1`, `sol_get_last_restart_slot`.

This matches live 25B takers: DFlow parent `DF1ow4tspfHX…` uses selector **`0x30`**; Jupiter `JUP6…V4` uses **`0x14`**. A third parent `B3111yJCeHBcA1bizdJjUFPALfhAfSRnAbJzGUtnt56A` (Binance Wallet router) also CPIs 18acc / `0x30`.

## Tessera `TessVdML9pBGgG9yGks7o4HewRaXVAMuoVj4x83GLQH`

| | |
|---|---|
| size | 576932 B |
| arch | eBPF (Ghidra `eBPF:LE:64:default`, 236 funcs) |
| magic | `MRKT` / `MRKTKV01` |

Project paths: `src/processor.rs`, `src/instruction.rs`, `src/state.rs`, `src/utils/batch_clock.rs`, `src/utils/swap_math.rs`, `src/entrypoint.rs`.

Syscalls: `sol_get_clock_sysvar`, `sol_get_last_restart_slot`.

Ghidra: no named `swap`/`tick` symbols (stripped). Largest body `FUN_ram_000099d0` (58536 B) is the likely processor.

## Tick `tickUcsEQegChaAuo9VYQQztB4ZGApY6ZT4FkULWY6N`

| | |
|---|---|
| size | 148368 B |
| arch | SBF `EM=0x107` |
| crate | `programs/market-tick` (Anchor: `market_tickv1`, `payermarket_tickv1pda`) |

Pinned errors from `programs/market-tick/src/processor.rs`:

- `Instruction slot does not match the runtime clock slot`
- `Signer is not the signer selected for this slot`
- `Timestamp must strictly increase within a slot`
- `Target interval cannot change within a slot`

`market-tick: initialized`. Syscall: `sol_get_clock_sysvar`.
