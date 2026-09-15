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

Grok CLI: **binary 1.0.30 on PATH** (`~/.local/bin/grok`). Auth install **stopped**: parent markers were the literal `PLACEHOLDER` — did not write `~/.grok/auth.json`, did not invent JWTs. Ask parent for one-shot real JSON.

## Tessera H6 — Ghidra/ELF + tick program
Dumped `tickUcsEQegChaAuo9VYQQztB4ZGApY6ZT4FkULWY6N` (148368 B, SBF).
Tick ELF (`programs/market-tick/src/processor.rs`) errors:
`Instruction slot does not match the runtime clock slot`;
`Signer is not the signer selected for this slot`;
`Timestamp must strictly increase within a slot`.
Tessera ELF embeds `MRKTKV01` and `src/utils/batch_clock.rs`.
Ghidra 12 eBPF import of Tessera: **236 functions**. See `notes/ghidra/GHIDRA_PASS.md`.

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

### H3 — Jupiter-wrapped swap on Surfpool
Fresh `dexes=TesseraV` quote + swap-instructions. Setup (ATA/wrap) succeeded. Jupiter `Route` CPI'd Tessera (~62872 CU) → **`0xffff`**.

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

`swap_id` is a nonzero u64 from the aggregator quote (11 unique / 12 samples). Not slot-derived in the 25B header.

### H3 — Jupiter HumidiFi on Surfpool → **WIN**
Quote `dexes=HumidiFi` SOL→USDC 10_000_000 lamports.
Surfpool sig `41wS9DHaEQLbXQB5wuHpxN8yJqp8gmaDMhJ1wLXXHaDm6thN4Vq9RjjcASMTijp8sAbPneu7VD9hbgqWJ7yqzD7T`
slot `447169617`, `err=null`.
Inner: HumidiFi invoke[2] from Jupiter Route, **81635 CU, success**.
User received `1006677` USDC; pool WSOL `+10000000`.

Inner ix: 18 accounts, 113B data (not the 25B taker packing). Jupiter emits a working `swap_id` inside the route — no local derivation required.

## Switch recommendation (if more Tessera turns)
Do **not** burn more turns on Tessera `0xffff` without a tick-stream / same-slot clone. Higher odds next pair: **BisonFi → Scorch Oracle** (already seen `BiSoNHVp...` on the same jup-tagged fee-payers; Scorch is quote-provided `swap_id` like HumidiFi).
