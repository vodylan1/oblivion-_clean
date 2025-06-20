"""
Light‑weight Solana helpers that rely only on the solders API
(compatible with solana‑py >= 0.29).

Currently exposes:
    • transfer_sol_ix(...)  -> solders.instruction.Instruction
"""

from __future__ import annotations

from typing import Union

from solders.instruction import Instruction, AccountMeta
from solders.pubkey import Pubkey
from solders.system_program import ID as SYSTEM_PROGRAM_ID, TransferParams, transfer

LAMPORTS_PER_SOL: int = 1_000_000_000


def _to_pubkey(key: Union[str, Pubkey]) -> Pubkey:
    """Accept either a base‑58 string or an existing Pubkey."""
    return key if isinstance(key, Pubkey) else Pubkey.from_string(key)


# --------------------------------------------------------------------------- #
# PUBLIC HELPERS
# --------------------------------------------------------------------------- #
def transfer_sol_ix(
    from_pubkey: Union[str, Pubkey],
    to_pubkey: Union[str, Pubkey],
    lamports: int,
) -> Instruction:
    """
    Build a SystemProgram::Transfer instruction.

    Args
    ----
    from_pubkey : sender pubkey (base‑58 str or Pubkey)
    to_pubkey   : recipient pubkey (base‑58 str or Pubkey)
    lamports    : amount in **lamports** (1 SOL = 1_000_000_000 lamports)

    Returns
    -------
    solders.instruction.Instruction
    """
    params = TransferParams(
        from_pubkey=_to_pubkey(from_pubkey),
        to_pubkey=_to_pubkey(to_pubkey),
        lamports=lamports,
    )
    return transfer(params)
