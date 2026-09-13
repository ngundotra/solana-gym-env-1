# Top-100 max fair score estimate

## Verdict

| Metric | Value |
|--------|------:|
| **theoretical_cap** (`32 × N`) | **3168** |
| N (top-100 minus Memo v1/v2) | 99 |
| Memo excluded from top-100 | 1 |
| Per-program cap | 32 |
| idl_known_cap (upper; unknowns@cap) | 3046 |
| idl_known_only (sum over cataloged) | 102 (7 programs) |
| Grok fair / raw | **66** / 70 |
| **Grok fair ÷ theoretical_cap** | **2.08%** |

## Method

Fair scoring reuses `voyager/scoring.py`:

- `+1` per unique `(program_id, first_byte_of_ix_data)` on successful txs
- Memo v1/v2 in `DEFAULT_EXCLUDED_PROGRAMS` → fair contribution **0**
- Cap `max_unique_per_program=32` (`SCORE_MAX_UNIQUE_PER_PROGRAM`)
- Zero-account spam-shaped ixs do not score when metas are present
- Per-program fair ceiling = `min(32, distinct_first_bytes_that_can_succeed)`
- **First-pass ceiling** assumes saturating the cap → `theoretical_cap = 32 × (# non-Memo programs in top 100)`

No Memo farms. Rankings are **not invented**.

## Source

- **kind:** `solana_rpc_getBlock_sample`
- **detail:** Public Solana RPC getBlock sampling of recent mainnet blocks. Ranked by successful transactions that invoke the program (top-level + inner instructions). Not invented rankings.
- **fetched_at_utc:** `2026-09-13T21:51:04.814599+00:00`
- **rpc:** `https://api.mainnet-beta.solana.com`
- **blocks_sampled:** 18
- **slot range:** 446809070 … 446809757 (tip at start `446809777`)
- **metric:** `successful_tx_count_containing_program` (secondary `instruction_invocation_count`)

Refresh:

```bash
PYTHONPATH=. python3 scripts/top100_max_fair_score.py --refresh --write-docs
# or use the checked-in snapshot only:
PYTHONPATH=. python3 scripts/top100_max_fair_score.py --snapshot docs/top100_programs_snapshot.json --write-docs
```

Checked-in snapshot: [`docs/top100_programs_snapshot.json`](./top100_programs_snapshot.json).

If live RPC refresh fails (rate limits / network), keep using the snapshot JSON;
do not invent a ranking.

## Comparison to Grok fair climb

Canonical Grok fair climb: fair **66** / raw **70** / memo **0**.

Against this top-100 first-pass ceiling (**3168**), Grok reached **2.08%** of the saturating theoretical max. That ceiling is an **upper bound** (many programs cannot expose 32 distinct successful first-bytes; Anchor discriminators also collide on byte0).

## Per-program table (top 100 by usage)

| rank | program_id | name | tx_count | fair_ceiling_32 | idl_known_cap | notes |
|-----:|------------|------|---------:|----------------:|--------------:|-------|
| 1 | `Vote111111111111111111111111111111111111111` | Vote Program | 12050 | 32 | 16 | known_first_bytes=16 |
| 2 | `ComputeBudget111111111111111111111111111111` | Compute Budget | 5315 | 32 | 5 | known_first_bytes=5 |
| 3 | `11111111111111111111111111111111` | System Program | 3633 | 32 | 13 | known_first_bytes=13 |
| 4 | `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA` | SPL Token | 2669 | 32 | 28 | known_first_bytes=28 |
| 5 | `ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL` | Associated Token Account | 2116 | 32 | 3 | known_first_bytes=3 |
| 6 | `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` | Token-2022 | 2071 | 32 | 32 | known_first_bytes=48 |
| 7 | `pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ` | Pump Fees | 1683 | 32 | — | unknown ix catalog → assume cap |
| 8 | `pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA` | Pump AMM | 1462 | 32 | — | unknown ix catalog → assume cap |
| 9 | `cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG` | Meteora DAMM v2 | 419 | 32 | — | unknown ix catalog → assume cap |
| 10 | `QuaNtZsgYRe5Z9Bk4LZ4cTD9tbkVoyCNf1R2BN9bBDv` | — | 281 | 32 | — | unknown ix catalog → assume cap |
| 11 | `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P` | pump.fun | 255 | 32 | — | unknown ix catalog → assume cap |
| 12 | `EtrnLzgbS7nMMy5fbD42kXiUzGg8XQzJ972Xtk1cjWih` | — | 232 | 32 | — | unknown ix catalog → assume cap |
| 13 | `9H6tua7jkLhdm3w8BvgpTn5LZNU7g4ZynDmCiNN3q6Rp` | — | 196 | 32 | — | unknown ix catalog → assume cap |
| 14 | `FLASHX8DrLbgeR8FcfNV1F5krxYcYMUdBkrP1EPBtxB9` | Flash Loan Aggregator | 166 | 32 | — | unknown ix catalog → assume cap |
| 15 | `TessVdML9pBGgG9yGks7o4HewRaXVAMuoVj4x83GLQH` | TesseraV | 165 | 32 | — | unknown ix catalog → assume cap |
| 16 | `JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4` | Jupiter Aggregator v6 | 148 | 32 | — | unknown ix catalog → assume cap |
| 17 | `Hd7c1kYHqYJ7dD1bLf9C61XC22JgbGp4P1PQ8UNcUH5w` | — | 141 | 32 | — | unknown ix catalog → assume cap |
| 18 | `MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr` | Memo v2 | 140 | 0 | — | excluded (Memo) |
| 19 | `9L1qqo7q7vq7sKuMsBGKPF81z6GK7N4orWGgGFwwqqDF` | — | 128 | 32 | — | unknown ix catalog → assume cap |
| 20 | `HVi6VyyLvTtFTA8f8atavxVjUKi8WjmnydfKgoZKzt7H` | — | 124 | 32 | — | unknown ix catalog → assume cap |
| 21 | `dijkbkCAKfFTCxQg3u1pg82gVU1jJGHBBRcteD11mBu` | — | 121 | 32 | — | unknown ix catalog → assume cap |
| 22 | `675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8` | Raydium AMM v4 | 107 | 32 | — | unknown ix catalog → assume cap |
| 23 | `2JR3rnJJhw5doRkFYgX8R5uXEaBLLWUwjAazxamfdh41` | — | 101 | 32 | — | unknown ix catalog → assume cap |
| 24 | `3QUnrcMqCQoiGB73s1A6uDzxziywaNFpTLiZiiZbEUoN` | — | 100 | 32 | — | unknown ix catalog → assume cap |
| 25 | `W1LDCARDa67SPBG7TFpQivHnEZXRtxCFP13ysEd1bWR` | — | 100 | 32 | — | unknown ix catalog → assume cap |
| 26 | `LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo` | Meteora DLMM | 97 | 32 | — | unknown ix catalog → assume cap |
| 27 | `FLUX6xBayGxLX9UcimVRxXFMHH6q43mAbRvDzSpCsvfK` | — | 94 | 32 | — | unknown ix catalog → assume cap |
| 28 | `ojh19ojaKduoJZuaJADhcVGp4xt1TcdAvZmpVsCorch` | — | 92 | 32 | — | unknown ix catalog → assume cap |
| 29 | `7q9uKyKWW5ddfyRiaJzFeKZTCMVToHhyZJ5sAPKK174L` | — | 90 | 32 | — | unknown ix catalog → assume cap |
| 30 | `tickUcsEQegChaAuo9VYQQztB4ZGApY6ZT4FkULWY6N` | — | 86 | 32 | — | unknown ix catalog → assume cap |
| 31 | `DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH` | — | 82 | 32 | — | unknown ix catalog → assume cap |
| 32 | `Archer8kgiavM61GyusMzaaS2ft5sALtNsD1HxkUPMhy` | — | 76 | 32 | — | unknown ix catalog → assume cap |
| 33 | `2gLMrDm6b3hCxY7UfDUERe3pmuhHWwReJ8AreVyGEF7o` | — | 71 | 32 | — | unknown ix catalog → assume cap |
| 34 | `dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN` | Dynamic Bonding Curve | 69 | 32 | — | unknown ix catalog → assume cap |
| 35 | `LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj` | Raydium LaunchLab | 65 | 32 | — | unknown ix catalog → assume cap |
| 36 | `CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK` | Raydium CLMM | 63 | 32 | — | unknown ix catalog → assume cap |
| 37 | `REALQqNEomY6cQGZJUGwywTBD2UmDT32rZcNnfxQ5N2` | — | 62 | 32 | — | unknown ix catalog → assume cap |
| 38 | `EXfkgTuTwXkH12jcuUwijZa9j29PdGktph7nKpdE8fKn` | — | 54 | 32 | — | unknown ix catalog → assume cap |
| 39 | `BYdq7NJXWHnTzzCogT6VByrPXvUQwkD5PuZQLS8JvZtw` | — | 52 | 32 | — | unknown ix catalog → assume cap |
| 40 | `whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc` | Orca Whirlpool | 46 | 32 | — | unknown ix catalog → assume cap |
| 41 | `SAGE2HAwep459SNq61LHvjxPk4pLPEJLoMETef7f7EE` | — | 44 | 32 | — | unknown ix catalog → assume cap |
| 42 | `DZNTS5ujuiyx1mazqCPdYPzEyE2VrTPPb6QbqBUftJbY` | — | 43 | 32 | — | unknown ix catalog → assume cap |
| 43 | `MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e` | — | 42 | 32 | — | unknown ix catalog → assume cap |
| 44 | `B72M6nyCLFgWiJtAN4naUTminMiTmyGcEqQHXwVeRdht` | — | 41 | 32 | — | unknown ix catalog → assume cap |
| 45 | `CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C` | Raydium CPMM | 41 | 32 | — | unknown ix catalog → assume cap |
| 46 | `6Vo3245eszAb5wuqEMw8mGdbfRUdKbHhDHP5LcaGuTAB` | — | 40 | 32 | — | unknown ix catalog → assume cap |
| 47 | `HRHjd1NCXLAvCTQERXTyTKUWUqcLGaRHKwLwGmUZ9cJq` | — | 35 | 32 | — | unknown ix catalog → assume cap |
| 48 | `99vQwtBwYtrqqD9YSXbdum3KBdxPAVxYTaQ3cfnJSrN2` | — | 34 | 32 | — | unknown ix catalog → assume cap |
| 49 | `idemJL67fKhpev5vKcxHrosuVyTat6wVC9sFfoPVg3Y` | — | 34 | 32 | — | unknown ix catalog → assume cap |
| 50 | `7kE7pY98M9hqdYjjEk6dHH7KGu6TESWfN4DWxZ1UirRu` | — | 32 | 32 | — | unknown ix catalog → assume cap |
| 51 | `term9YPb9mzAsABaqN71A4xdbxHmpBNZavpBiQKZzN3` | — | 31 | 32 | — | unknown ix catalog → assume cap |
| 52 | `Tri3NG4HkZ6DddYPKoX2ehgkqFtDuej9Aspw5BmvSo4` | — | 29 | 32 | — | unknown ix catalog → assume cap |
| 53 | `proVF4pMXVaYqmy4NjniPh4pqKNfMmsihgd4wdkCX3u` | — | 29 | 32 | — | unknown ix catalog → assume cap |
| 54 | `FD1amxhTsDpwzoVX41dxp2ygAESURV2zdUACzxM1Dfw9` | — | 26 | 32 | — | unknown ix catalog → assume cap |
| 55 | `4bwVxjN2sFQyejtoa9ieiD1rRpPY798QGTKVDcmnotWu` | — | 23 | 32 | — | unknown ix catalog → assume cap |
| 56 | `orafZ4BdfzikRRg498P23vG3EdEyMR7bYoYcD2zcwiD` | — | 23 | 32 | — | unknown ix catalog → assume cap |
| 57 | `phDEVv4w6BcfkLrLNeXr8HhhgQxnxziVGXpGPcaadMf` | — | 23 | 32 | — | unknown ix catalog → assume cap |
| 58 | `HiPMPcYjLNPgjvdzBoavzMbCeHaXWkAuDxyuE9VoPrkf` | — | 22 | 32 | — | unknown ix catalog → assume cap |
| 59 | `ALPHAQmeA7bjrVuccPsYPiCvsi428SNwte66Srvs4pHA` | — | 21 | 32 | — | unknown ix catalog → assume cap |
| 60 | `MNFSTqtC93rEfYHB6hF82sKdZpUDFWkViLByLd1k1Ms` | — | 21 | 32 | — | unknown ix catalog → assume cap |
| 61 | `jupeiUmn818Jg1ekPURTpr4mFo29p46vygyykFJ3wZC` | — | 21 | 32 | — | unknown ix catalog → assume cap |
| 62 | `HFn8GnPADiny6XqUoWE8uRPPxb29ikn4yTuPa9MF2fWJ` | — | 20 | 32 | — | unknown ix catalog → assume cap |
| 63 | `FW6zUqn4iKRaeopwwhwsquTY6ABWLLgjxtrC3VPnaWBf` | — | 19 | 32 | — | unknown ix catalog → assume cap |
| 64 | `Gt9S41PtjR58CbG9JhJ3J6vxesqrNAswbWYbLNTMZA3c` | — | 19 | 32 | — | unknown ix catalog → assume cap |
| 65 | `Point2iBvz7j5TMVef8nEgpmz4pDr7tU7v3RjAfkQbM` | — | 19 | 32 | — | unknown ix catalog → assume cap |
| 66 | `Prism8hsRo6Ww5jiN5Zeh3YDPLZHqHduCPSAV7JF7qv` | — | 19 | 32 | — | unknown ix catalog → assume cap |
| 67 | `4Qv3mbzcq1bKmrhGG4voS3EemfPd7f838FLUU7wBHSyi` | — | 18 | 32 | — | unknown ix catalog → assume cap |
| 68 | `AddressLookupTab1e1111111111111111111111111` | Address Lookup Table | 18 | 32 | 5 | known_first_bytes=5 |
| 69 | `Cargo2VNTPPTi9c1vq1Jw5d3BWUNr18MjRtSupAghKEk` | — | 18 | 32 | — | unknown ix catalog → assume cap |
| 70 | `jupgfSgfuAXv4B6R2Uxu85Z1qdzgju79s6MfZekN6XS` | — | 18 | 32 | — | unknown ix catalog → assume cap |
| 71 | `vELoC1audYbSYVRXn1vPaV8Axoa9oU6BYmNGZZBDZ1P` | — | 18 | 32 | — | unknown ix catalog → assume cap |
| 72 | `EZdpXH6LiTdUhQsZsKMKH6s1SEj1uxtrfZ3TXGr9csNS` | — | 17 | 32 | — | unknown ix catalog → assume cap |
| 73 | `3TK9D8aoBFYjYZtKCjciPrVrRStsnvo7KmpcJqDavpaU` | — | 16 | 32 | — | unknown ix catalog → assume cap |
| 74 | `M2mx93ekt1fmXSVkTrUL9xVFHkmME8HTUi5Cyc5aF7K` | — | 16 | 32 | — | unknown ix catalog → assume cap |
| 75 | `pyt2F414BA6dPttK6RddPZUdHfapoBN24GL5wbrPCou` | — | 16 | 32 | — | unknown ix catalog → assume cap |
| 76 | `rec2HHDDnjLfj4kE7VyEtFA1HPGQLK33259532cRyHp` | — | 16 | 32 | — | unknown ix catalog → assume cap |
| 77 | `9ddjzqYhSTMHaBrrKukRXRfy4WzHUPjdX88uPXZ7MXyn` | — | 14 | 32 | — | unknown ix catalog → assume cap |
| 78 | `DhpyNWkdxFh3DRPsBrwRwrK3TYC5t7Q4arnSvf3t84HY` | — | 14 | 32 | — | unknown ix catalog → assume cap |
| 79 | `HDwcJBJXjL9FpJ7UBsYBtaDjsBUhuLCUYoz3zr8SWWaQ` | — | 14 | 32 | — | unknown ix catalog → assume cap |
| 80 | `mmm3XBJg5gk8XJxEKBvdgptZz6SgK4tXvn36sodowMc` | MPL Magic Eden MMM | 14 | 32 | — | unknown ix catalog → assume cap |
| 81 | `Ax8aVosP3b55aZu3FRD3m4JCrvHBWzAkkoV4yBCWHdY1` | — | 13 | 32 | — | unknown ix catalog → assume cap |
| 82 | `FoaFt2Dtz58RA6DPjbRb9t9z8sLJRChiGFTv21EfaseZ` | — | 13 | 32 | — | unknown ix catalog → assume cap |
| 83 | `HpNfyc2Saw7RKkQd8nEL4khUcuPhQ7WwY1B2qjx8jxFq` | — | 13 | 32 | — | unknown ix catalog → assume cap |
| 84 | `goonuddtQRrWqqn5nFyczVKaie28f3kDkHWkHtURSLE` | — | 13 | 32 | — | unknown ix catalog → assume cap |
| 85 | `HDw2E7P8X1SkCyjvoGsfBGAVUutKcj874bXjHrpVYrVL` | — | 12 | 32 | — | unknown ix catalog → assume cap |
| 86 | `pythWSnswVUd12oZpeFP8e9CVaEqJg25g1Vtc2biRsT` | Pyth Oracle | 12 | 32 | — | unknown ix catalog → assume cap |
| 87 | `rec5EKMGg6MxZYaMdyBfgwp4d5rB9T1VQH5pJv5LtFJ` | Pyth Receiver | 12 | 32 | — | unknown ix catalog → assume cap |
| 88 | `AjMx5My4YUDHMiCtLpTAtgkiUJgrpJnQqd5AcQnddHQW` | — | 11 | 32 | — | unknown ix catalog → assume cap |
| 89 | `Bgo4vNe3vxRv37j8mmQarJo8vbjHEKgkhJDZzxiizBid` | — | 11 | 32 | — | unknown ix catalog → assume cap |
| 90 | `GMGNreQcJFufBiCTLDBgKhYEfEe9B454UjpDr5CaSLA1` | — | 11 | 32 | — | unknown ix catalog → assume cap |
| 91 | `riptK81hDxhe5pW5jSzSM9iRA8azgEgLJ4dXkPtBS7j` | — | 11 | 32 | — | unknown ix catalog → assume cap |
| 92 | `ExA6GYhHAeRNMWVNLrDir1SKPJZcZA2oaPq6uriSmxfJ` | — | 10 | 32 | — | unknown ix catalog → assume cap |
| 93 | `Gmso1uvJnLbawvw7yezdfCDcPydwW2s2iqG3w6MDucLo` | — | 10 | 32 | — | unknown ix catalog → assume cap |
| 94 | `HiP3dRdEbzPETVLrwu7Mht6G3XQkPVF6dUgXtDFeiRvH` | — | 10 | 32 | — | unknown ix catalog → assume cap |
| 95 | `BoobsBSMpFRBA91sNwKLYShRRQPH5GjoCH4NhLUt4yRo` | — | 9 | 32 | — | unknown ix catalog → assume cap |
| 96 | `brrnmzmsmY8codsU5kAoDpABL8CiBKejkyV5YnyykPa` | — | 9 | 32 | — | unknown ix catalog → assume cap |
| 97 | `DRVSpZ2YUYYKgZP8XtLhAGtT1zYSCKzeHfb4DgRnrgqD` | — | 8 | 32 | — | unknown ix catalog → assume cap |
| 98 | `Ed25519SigVerify111111111111111111111111111` | Ed25519 SigVerify | 7 | 32 | — | unknown ix catalog → assume cap |
| 99 | `Send9wszHjEiS3hwKcPeSLsPRu5Gb62iCrJEcG4Mq3b` | — | 7 | 32 | — | unknown ix catalog → assume cap |
| 100 | `b1oomGGqPKGD6errbyfbVMBuzSC8WtAAYo8MwNafWW1` | — | 7 | 32 | — | unknown ix catalog → assume cap |

## Notes on `idl_known_cap`

Cataloged counts come from public native/SPL instruction enums (System, Vote, Stake, ComputeBudget, ALT, Token, Token-2022, ATA) where the first data byte is the instruction tag. Token-2022 has >32 tags → capped at 32. Programs without a catalog still count as **32** in `idl_known_cap_upper` so that figure remains an upper bound, not a tight IDL sum. `idl_known_only` is the sum over cataloged programs alone.

