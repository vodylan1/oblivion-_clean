"""Ultra-minimal stub for the `solders` crate – now complete for tests."""

import types, sys


# ─────────────────────────────── Keypair ────────────────────────────────
class Keypair:  # noqa: D101
    @classmethod
    def from_bytes(cls, _bytes: bytes):  # mocked constructor
        return cls()


keypair_mod = types.ModuleType("solders.keypair")
keypair_mod.Keypair = Keypair


# ─────────────────────────────── Hash ───────────────────────────────────
class Hash:  # noqa: D101
    pass


hash_mod = types.ModuleType("solders.hash")
hash_mod.Hash = Hash


# ─────────────────────────── Transaction ────────────────────────────────
class VersionedTransaction:  # noqa: D101
    pass


txn_mod = types.ModuleType("solders.transaction")
txn_mod.VersionedTransaction = VersionedTransaction


# ───────────────────────────── Instruction ──────────────────────────────
class Instruction:  # noqa: D101
    pass


instr_mod = types.ModuleType("solders.instruction")
instr_mod.Instruction = Instruction


# ────────────────────────────── Message ─────────────────────────────────
class MessageV0:  # noqa: D101
    pass


msg_mod = types.ModuleType("solders.message")
msg_mod.MessageV0 = MessageV0


# ────────────────────────────── Pubkey ──────────────────────────────────
class Pubkey:  # noqa: D101
    pass


pub_mod = types.ModuleType("solders.pubkey")
pub_mod.Pubkey = Pubkey

# ──────────────────────────── sys.modules ───────────────────────────────
sys.modules.update(
    {
        "solders": sys.modules[__name__],
        "solders.keypair": keypair_mod,
        "solders.hash": hash_mod,
        "solders.transaction": txn_mod,
        "solders.instruction": instr_mod,
    }
)
# add the extra sub-modules (Message, Pubkey) afterwards
sys.modules["solders.message"] = msg_mod
sys.modules["solders.pubkey"] = pub_mod


# ------------------------------------------------------------------ system_program
def transfer(*_a, **_kw):  # noqa: D401,D103
    """No‑op stub for tests."""
    return None


class TransferParams:  # noqa: D101
    def __init__(self, *_, **__):
        pass


sys_prog_mod = types.ModuleType("solders.system_program")
sys_prog_mod.transfer = transfer
sys_prog_mod.TransferParams = TransferParams
sys.modules["solders.system_program"] = sys_prog_mod


# ------------------------------------------------------------------ Pubkey
class Pubkey:  # noqa: D101
    def __init__(self, *_a, **_kw):
        pass

    @classmethod
    def from_string(cls, _s: str):  # mimic real API
        return cls()


pubkey_mod = types.ModuleType("solders.pubkey")
pubkey_mod.Pubkey = Pubkey
sys.modules["solders.pubkey"] = pubkey_mod
