#!/usr/bin/env bash
# Dump HumidiFi + Tessera ELF binaries from mainnet.
set -euo pipefail
export PATH="$HOME/.local/share/solana/install/active_release/bin:$PATH"
RPC="${SOLANA_RPC:-https://api.mainnet-beta.solana.com}"
OUT="${1:-$(dirname "$0")/../dumps}"
mkdir -p "$OUT"
solana program dump -u "$RPC" 9H6tua7jkLhdm3w8BvgpTn5LZNU7g4ZynDmCiNN3q6Rp "$OUT/humidifi.so"
solana program dump -u "$RPC" TessVdML9pBGgG9yGks7o4HewRaXVAMuoVj4x83GLQH "$OUT/tessera.so"
solana program dump -u "$RPC" tickUcsEQegChaAuo9VYQQztB4ZGApY6ZT4FkULWY6N "$OUT/tick.so"
# Next-pair dumps (not in the Tessera/HumidiFi win path)
solana program dump -u "$RPC" BiSoNHVpsVZW2F7rx2eQ59yQwKxzU5NvBcmKshCSUypi "$OUT/bisonfi.so"
solana program dump -u "$RPC" SCoRcH8c2dpjvcJD6FiPbCSQyQgu3PcUAWj2Xxx3mqn "$OUT/scorch.so"
ls -la "$OUT"
