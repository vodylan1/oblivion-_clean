"""
path_selector.py
────────────────────────────────────────────────────────────────────────────
Chooses which path to send a transaction:
  QUIC  -> if slot leader accessible
  HELIUS -> if QUIC not feasible
  FALLBACK -> private RPC #1
"""

import os
import random

def quic_slot_leader_ok() -> bool:
    # stub – realistically we'd track who the slot leader is
    # and if we have direct QUIC route to them
    return random.random() < 0.7  # 70% chance we can do QUIC

def helius_online() -> bool:
    # stub
    return True

def choose_send_path() -> str:
    # 1. QUIC if leader is known
    if quic_slot_leader_ok():
        return "QUIC"

    # 2. else staked Helius
    if helius_online():
        return "HELIUS_STAKED"

    # 3. fallback
    return "PRIVATE_RPC_1"
