"""
Ultra-light stub for the `solana` SDK, just enough for unit tests.
"""

import types, sys


# ---- solana.publickey.PublicKey ------------------------------------------
class PublicKey:  # noqa: D101
    def __init__(self, *_a, **_kw):
        pass


pub_mod = types.ModuleType("solana.publickey")
pub_mod.PublicKey = PublicKey


# ---- solana.rpc.async_api.AsyncClient ------------------------------------
class AsyncClient:  # noqa: D101
    async def __aenter__(self):  # support “async with AsyncClient() as c: …”
        return self

    async def __aexit__(self, *_):  # no-op
        pass

    async def get_balance(self, *_a, **_kw):
        return {"result": {"value": 0}}

    async def get_latest_blockhash(self, *_a, **_kw):
        return {"result": {"value": {"blockhash": "0" * 44}}}


rpc_async_mod = types.ModuleType("solana.rpc.async_api")
rpc_async_mod.AsyncClient = AsyncClient

# ---- register hierarchical modules ---------------------------------------
rpc_mod = types.ModuleType("solana.rpc")
rpc_mod.async_api = rpc_async_mod

root = types.ModuleType("solana")
root.rpc = rpc_mod
root.publickey = pub_mod

sys.modules.update(
    {
        "solana": root,
        "solana.rpc": rpc_mod,
        "solana.rpc.async_api": rpc_async_mod,
        "solana.publickey": pub_mod,
    }
)


# ---- solana.transaction ---------------------------------------------------
class AccountMeta:  # noqa: D101
    def __init__(self, *_a, **_kw):
        pass


class TransactionInstruction:  # noqa: D101
    def __init__(self, *_a, **_kw):
        pass


txn_mod = types.ModuleType("solana.transaction")
txn_mod.TransactionInstruction = TransactionInstruction
txn_mod.AccountMeta = AccountMeta

root.transaction = txn_mod
sys.modules["solana.transaction"] = txn_mod

# ------------------------------------------------------------------ rpc.api.Client shim
api_mod = types.ModuleType("solana.rpc.api")


class Client:  # noqa: D101
    def __init__(self, *_a, **_kw):
        pass

    def get_token_supply(self, *_a, **_kw):
        return {}

    def get_account_info(self, *_a, **_kw):
        return {}

    def get_balance(self, *_a, **_kw):
        return {"result": {"value": 0}}


api_mod.Client = Client
root.rpc.api = api_mod  # attach to the rpc package
sys.modules["solana.rpc.api"] = api_mod
