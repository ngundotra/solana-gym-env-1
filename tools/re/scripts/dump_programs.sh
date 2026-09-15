#!/usr/bin/env bash
# Dump HumidiFi + Tessera ELF binaries from mainnet.
set -euo pipefail
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
RPC="${SOLANA_RPC:-https://api.mainnet-beta.solana.com}"
OUT="${1:-$(dirname "$0")/../dumps}"
mkdir -p "$OUT"
solana program dump -u "$RPC" 9H6tua7jkLhdm3w8BvgpTn5LZNU7g4ZynDmCiNN3q6Rp "$OUT/humidifi.so"
solana program dump -u "$RPC" TessVdML9pBGgG9yGks7o4HewRaXVAMuoVj4x83GLQH "$OUT/tessera.so"
ls -la "$OUT"
