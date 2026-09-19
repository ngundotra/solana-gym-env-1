# HumidiFi + Tessera marathon journal

Climb plan: Tessera `0x10`+14acc Jupiter-only first; HumidiFi 25B taker second.
Ignore BAM MM `0x0d` / `KAM\0` and HumidiFi 65B/3acc MM updates.

## Tools enabled

| Tool | How | Used for |
|---|---|---|
| `solana program dump` 4.2.2 | Anza installer | ELF dumps (`tools/re/dumps/`) |
| rizin 0.9.1 + radare2 6.2.2 + Ghidra 12.1.3 | GitHub releases | ELF header / strings; Ghidra not needed after tick-slot gate |
| Surfpool 1.5.0 | `curl -sL https://run.surfpool.run/ \| bash` | Local clone + send |
| Jupiter lite-api | `https://lite-api.jup.ag/swap/v1` | Quote + swap-instructions |
| Morrell gist | https://gist.github.com/skynetcap/fb456a0ff0d1ab94b94ea9443e4da4aa | XOR stream cipher |
| OKX router | `okxlabs/DEX-Router-Solana-V1` `humidifi.rs` | **Stubbed** (`AdapterAbort`); XOR lived in older `ce15b2da` (git object gone from rewrite) |
| `swaps` crate | docs.rs | Stale HumidiFi marker `0x14` / Tessera 12-acc (live is 14) |

Grok CLI: **binary 1.0.30 on PATH** (`~/.local/bin/grok`). Auth install **stopped** (this turn and prior): parent markers were the literal `PLACEHOLDER` — did not write `~/.grok/auth.json`, did not invent or rewrite JWTs. Ask parent for one-shot real JSON. `expires_at` note was ~2026-09-15T06:02Z.

## Tessera H6 — Ghidra/ELF + tick program
Dumped `tickUcsEQegChaAuo9VYQQztB4ZGApY6ZT4FkULWY6N` (148368 B, SBF).
Tick ELF (`programs/market-tick/src/processor.rs`) errors:
`Instruction slot does not match the runtime clock slot`;
`Signer is not the signer selected for this slot`;
`Timestamp must strictly increase within a slot`.
Tessera ELF embeds `MRKTKV01` and `src/utils/batch_clock.rs`.
Ghidra 12 eBPF import of Tessera: **236 functions**. See `notes/ghidra/GHIDRA_PASS.md`.

### H7 — tick account layout (proven)
88 B `MRKTKV01`: signer[32] @8, **slot u64 @40**, prev/curr timestamp ns @48/@56, seq @64, target interval 30ms @72, last interval @80.
BAT1 slot u64 @0. Live tick tracks mainnet clock within ~6 slots; Surfpool slot lagged ~300+.
Parser + offline fixture: `tick_codec.py` / `tests/test_tick_codec.py`.

### H8 — recent Tessera program sigs are not 0x10
Latest `getSignaturesForAddress(Tessera)` rows are **`0x13` + 2 accounts + 800 B** (some `custom 20`). Not the Jupiter taker. Do not farm. BpZpRbuy cluster is currently quiet for Tessera CPI.

### H9 — Jupiter still quotes Tessera / BisonFi / Scorch
Fresh lite-api `onlyDirectRoutes` quotes (10M lamports SOL→USDC) all returned routes. Tessera route still 14acc CPI ending in BAT1+tick. BisonFi route has **no tick account**. Scorch route includes `ojh19oja…Scorch` (oracle-shaped). See `notes/jup_route_layouts.json`.

## Tessera

### H1 — live Jupiter parent ID
Old constant `JUP6LkbZbjS1jKKwapdHNyBwDxjC3VheXv4TtCedZH8x` missed CPI.
Live parent: `JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4`.
**Result:** 16 `0x10`+14acc Jupiter hops; 5 mainnet successes (BpZpRbuy / others).

### H2 — ix layout (proven on mainnet)
18-byte data: `0x10 \| side:u8 \| amount_in:u64le \| min_out:u64le`.
14 accounts:

| i | role | example |
|---|---|---|
| 0 | global | `8ekCy2jH...CDiF` (Tessera-owned, 10240B) |
| 1 | pool | `FLckHLGM...q2n` |
| 2 | user | fee-payer / hop user |
| 3-4 | vaults | quote vault often `9t4P5wMw...` (USDC) |
| 5-6 | user ATAs | |
| 7-8 | mints | WSOL / USDC |
| 9-10 | token programs | |
| 11 | instructions sysvar | |
| 12 | BAT1 book | `BAT1Ndpu...` Tessera-owned 2048B |
| 13 | **tick** | `4cG31VNF...` owner `tickUcsEQegChaAuo9VYQQztB4ZGApY6ZT4FkULWY6N` |

`swaps` crate omitted [12]/[13].

### H3 — Jupiter-wrapped swap on Surfpool (stale clock → 0xffff)
Fresh `dexes=TesseraV` quote + swap-instructions. Setup (ATA/wrap) succeeded. Jupiter `Route` CPI'd Tessera (~62872 CU) → **`0xffff`**.

### H10 — tick freshness fix → **WIN**
Root cause of H3/H4: Surfpool `timeTravel` leaves `SysvarC1ock.slot` as the **epoch slotIndex** (~37k) while the tick stores the **absolute slot**. Tessera compares those via `sol_get_clock_sysvar`.

Fix (`tessera_freshness.py`): clone tick+BAT1+global+pool from mainnet, `pauseClock`, then `surfnet_setAccount` the Clock sysvar to `{slot: tick.slot, unix: tick.curr_ts_ns/1e9}`.

Surfpool sig `4jZZgmg6P3dNaiGwuNjm2kYTK7VzysufPxqKkZtjvbqSPRNjdDB2Nr7iCC18vk8JhLJNtBxnpC4aCZKkLupMLr5i`
slot `448453584`, `err=null`.
Inner: Tessera `0x10` + 14acc + 18B (`side=1`, `amount_in=10_000_000`) / **71367 CU success**.
**Balances:** user USDC **+1,116,749**; pool WSOL **+10,000,000**; pool USDC **-1,116,749**.

### H4 — replay known-good mainnet tx
Sig `2AUbcsTE...` (slot 447168171, mainnet `err=null`) simulated on Surfpool with `sigVerify=false` + `replaceRecentBlockhash` → **same `0xffff`**.

### H5 — tick freshness (remaining gate)
Tick account magic `MRKTKV01`. A little-endian u64 in the body is a **slot** (observed `447169725`).
Mainnet vs Surfpool bytes diverge immediately (same 88B length). BAT1 also diverges.
Surfpool slot lagged mainnet (~100 slots) and does not stream tick updates.

**Gate (evidence):** Tessera `0x10` requires a fresh `tickUcs...` / `MRKTKV01` oracle (slot-bearing) plus BAT1 book. Surfpool one-shot clones go stale; program returns `0xffff` even under Jupiter CPI. Not a missing discriminator. BAM `0x0d` is the MM writer for that tick — out of scope per climb plan.

## HumidiFi

### H1 — XOR codec
Morrell/OKX/swaps: XOR `HUMIDIFI_IX_DATA_KEY` + rolling `0x0001000100010001` on u64 chunks. Symmetric. Layout after decode: `swap_id:u64 \| amount_in:u64 \| is_base_to_quote:u8 \| pad7 \| selector`.

### H2 — live selectors (do not use crate `0x14` only)
| Path | parent | nacc | data | selector |
|---|---|---|---|---|
| Jupiter 25B | `JUP6...V4` | 15 | 25B | **`0x14`** (crate V2) |
| DFlow 25B | `DF1ow4tspfHX...` (fp `AgmLJBMD...`) | 18 | 25B | **`0x30`** |
| Jupiter Route (this run) | `JUP6...V4` | 18 | **113B** | obfuscated blob |
| MM update | — | 3 | 65B | ignore |

`swap_id` is a nonzero u64 from the aggregator quote (unique per hop). Not slot-derived in the 25B header.

Third parent (this pass): `B3111yJCeHBcA1bizdJjUFPALfhAfSRnAbJzGUtnt56A` (Binance Wallet router) → 18acc / selector **`0x30`**.

HumidiFi ELF embeds `GIT_HASH:26ebfd833cbb015b1cd1160840f8620c24f19b67` and `contract/src/routers/{dflow,jupiter}.rs` — the program itself has router-shaped modules. Hash not found on public GitHub commit search.

### H3 — Jupiter HumidiFi on Surfpool → **WIN**
Quote `dexes=HumidiFi` SOL→USDC 10_000_000 lamports.
Surfpool sig `41wS9DHaEQLbXQB5wuHpxN8yJqp8gmaDMhJ1wLXXHaDm6thN4Vq9RjjcASMTijp8sAbPneu7VD9hbgqWJ7yqzD7T`
slot `447169617`, `err=null`.
Inner: HumidiFi invoke[2] from Jupiter Route, **81635 CU, success**.
User received `1006677` USDC; pool WSOL `+10000000`.

Inner ix: 18 accounts, 113B data (not the 25B taker packing). Jupiter emits a working `swap_id` inside the route — no local derivation required.

## Switch recommendation (if more Tessera turns)
Do **not** burn more turns on Tessera `0xffff` without a tick-stream / same-slot clone.

## BisonFi (next-pair probe, not a silent switch)

Jupiter `dexes=BisonFi` is quoteable. Taker layout from the CPI the program accepted:

- program `BiSoNHVpsVZW2F7rx2eQ59yQwKxzU5NvBcmKshCSUypi`
- **10 accounts**, **18 B** `0x02 | amount_in:u64le | min_out:u64le`
- no `tickUcs` / `MRKTKV01` on the route

Surfpool sig `22nFohKR51PbQ4zUqGyQXLkHjc4hi6EjBjhCkNmSrjaTRUVF22kSQ1p71ivBFvyQEqLhpzyk9G4H1xxvDwCWKbUg`
slot `447171125`, **tx `err=null`**, BisonFi invoke[2] **47764 CU success**.

Honest fill: **0 USDC out**. Token CPIs were `Transfer 0`. Jupiter return `0`. 300–2000 bps quotes fail Jupiter `custom 6001` / `0x1771` (min_out); 10000 bps lands because min_out is 0 and the cloned pool is stale vs quote slot (~500 slots). This is **not** a HumidiFi-class economic win — the program accepts the Jupiter-shaped ix on Surfpool, unlike Tessera `0xffff`.

Scorch still untried. Oracle-shaped `ojh19oja…Scorch` on that route.
