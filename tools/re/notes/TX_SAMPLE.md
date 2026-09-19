# Tx sample table (2026-09-15)

RPC: `https://api.mainnet-beta.solana.com`. Tessera rows are Jupiter `0x10`+14acc only. HumidiFi rows are 25B taker swaps (65B/3acc MM skipped).

## Tessera `0x10` + 14 accounts (Jupiter)

Live Jupiter program: `JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4`.

| sig (prefix) | slot | fee-payer | err | data | notes |
|---|---|---|---|---|---|
| `2AUbcsTE…` | 447168171 | `BpZpRbuy…` | none | `1000bdfded00000000000000000000000000` | WIN on mainnet; Surfpool replay `0xffff` |
| `4QQmvGHp…` | 447168160 | `BpZpRbuy…` | none | `1000bdfded00000000000000000000000000` | same pool `FLckHLGM…` |
| `XWeESSBr…` | 447169291 | `A2R6ydBW…` | none | `1001b9f43a00000000000000000000000000` | side=1 |
| `5TzeZAoo…` | 447169291 | `9C6A9o9V…` | none | `10014ad6b200000000000000000000000000` | |
| `3MDPa1Z6…` | 447169291 | `5pj76o5P…` | none | `1001c3210000000000000000000000000000` | |
| `4Rpwd6E6…` | 447169291 | `UUAhspPg…` | Jup custom 6001 | `1001c8b861020000…` | slippage; still 14acc `0x10` |
| shakRD cluster | 4471689xx | `shakRDxy…` | 6001 / FailedToComplete | `10…` | jup-tagged; not BAM |

Constant extras on every hop: `[12]=BAT1Ndpu…` `[13]=4cG31VNF…` (tick `MRKTKV01`).

Fresh Jupiter `dexes=TesseraV` quote (this pass) still uses that 14-account CPI. Latest **program-address** sigs are `0x13`+2acc+800B (MM-style; some `custom 20`) — not taker hops. BpZpRbuy is quiet for Tessera CPI right now.

## HumidiFi 25B taker

| sig (prefix) | parent | nacc | selector | swap_id | amount_in |
|---|---|---|---|---|---|
| `sZ1ZTdfz…` | DFlow `DF1ow4…` | 18 | `0x30` | 9258209204929796804 | 320730 |
| `5bTBUTcX…` | DFlow | 18 | `0x30` | 4934971329500117497 | 761538242 |
| `FbaHTE4P…` | Jupiter `JUP6…V4` | 15 | `0x14` | 11462163793966563510 | 903321415 |
| `3Y1ueenF…` | Jupiter | 15 | `0x14` | 10580593933843700228 | 638841171 |
| `5hL79XCn…` | Jupiter `JUP6…V4` | 15 | `0x14` | 5281089746916497200 | 1277296480 |
| `mPFjy2Hu…` | DFlow | 18 | `0x30` | 3456752507807193330 | 3298493 |
| `mVPodt3x…` | Binance Wallet `B3111yJC…` | 18 | `0x30` | 16652736801701732368 | 52163827 |

Jupiter 15acc includes `jitodontfront1111111111111111JustUseJupiter` + `J1to1yuf…`. DFlow/Binance 18acc uses live marker `0x30`.

## Surfpool proof

| program | result | sig | ix |
|---|---|---|---|
| HumidiFi | **success** | `41wS9DHaEQLbXQB5wuHpxN8yJqp8gmaDMhJ1wLXXHaDm6thN4Vq9RjjcASMTijp8sAbPneu7VD9hbgqWJ7yqzD7T` | Jupiter Route → HumidiFi 18acc / 113B / 81635 CU; +10000000 WSOL in, +1006677 USDC out |
| Tessera | **0xffff** (stale Clock.slot=slotIndex) | Jupiter quote / mainnet replay | CPI 62872 CU then `custom 0xffff` |
| Tessera | **WIN** (Clock patched to tick.slot) | `4jZZgmg6P3dNaiGwuNjm2kYTK7VzysufPxqKkZtjvbqSPRNjdDB2Nr7iCC18vk8JhLJNtBxnpC4aCZKkLupMLr5i` | `0x10` 14acc 18B / 71367 CU; user USDC **+1116749**; pool WSOL **+10000000** |
| BisonFi | **program success, 0-fill** | `22nFohKR51PbQ4zUqGyQXLkHjc4hi6EjBjhCkNmSrjaTRUVF22kSQ1p71ivBFvyQEqLhpzyk9G4H1xxvDwCWKbUg` | Jupiter Route → BisonFi 10acc / 18B `0x02` / 47764 CU; token transfers were 0; Jupiter return 0 |

## BisonFi `0x02` + 10 accounts (Jupiter)

| i | role | example |
|---|---|---|
| 0 | user | ephemeral Surfpool payer |
| 1 | pool | `8FnX3xo2…FzLo` |
| 2 | vault (WSOL) | `ATRsNGv2…` |
| 3 | vault (USDC) | `2Y7HATmn…` |
| 4–5 | user ATAs | |
| 6–7 | token programs | |
| 8 | instructions sysvar | |
| 9 | jito tip | `J1to1yuf…` |
