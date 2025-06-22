#!/usr/bin/env python
"""
Generate N stealth wallets and write wallets/stealth_pool.json
----------------------------------------------------------------
• Requires:  solana‑py 0.29  (already in requirements.txt)
• Outputs:  {
      "generated_at": "...",
      "rpc_hint":     "https://api.mainnet-beta.solana.com",
      "wallets": [
          {"name": "stealth‑0", "pubkey": "8g1c...E4d"},
          ...
      ]
  }
Private keys are printed once and then cleared from memory.
"""

from __future__ import annotations
import json, time, pathlib, sys
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from base58 import b58encode

N = 8  # <-- change 5‑10 as desired
RPC_HINT = "https://api.mainnet-beta.solana.com"

out_dir = pathlib.Path("wallets")
out_dir.mkdir(exist_ok=True)
out_file = out_dir / "stealth_pool.json"

wallets: list[dict[str, str]] = []

print("🔐  Stealth wallet keypair generation\n")

for i in range(N):
    kp = Keypair()
    pub_b58 = b58encode(bytes(kp.pubkey())).decode()
    priv_b58 = b58encode(bytes(kp)).decode()

    wallets.append({"name": f"stealth-{i}", "pubkey": pub_b58})

    print(f"[{i}] {pub_b58}")
    print(f"    secret  : {priv_b58}\n")  # record this elsewhere!

    # scrub secret from memory
    del priv_b58, kp

payload = {
    "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
    "rpc_hint": RPC_HINT,
    "wallets": wallets,
}

out_file.write_text(json.dumps(payload, indent=2))
print(f"\n✅  Wrote {out_file.relative_to(pathlib.Path.cwd())}")
