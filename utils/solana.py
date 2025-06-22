"""
Grab current block-hash & build a System-Program transfer instruction that
works with solana-py 0.28 + solders 0.10.
"""

import asyncio, httpx
from typing import Final

# === RPCResponse fallback ===
try:
    from solana.rpc.types import RPCResponse
except ImportError:  # solana-py ≥ 0.36

    class RPCResponse(dict):  # noqa: D401
        """Minimal stub for tests – behaves like a dict."""

        @property
        def value(self):
            return self.get("result")


from solana.publickey import PublicKey
from solana.transaction import TransactionInstruction, AccountMeta
from solders.instruction import Instruction as SoldersIX
from solders.message import MessageV0
from solders.system_program import transfer, TransferParams

_RPC_URL: Final[str] = "https://api.mainnet-beta.solana.com"


async def _rpc(method: str, params: list) -> RPCResponse:
    async with httpx.AsyncClient() as cli:
        r = await cli.post(
            _RPC_URL,
            json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        )
        r.raise_for_status()
        return r.json()["result"]


async def latest_blockhash() -> str:
    res = await _rpc("getLatestBlockhash", [{"commitment": "confirmed"}])
    return res["value"]["blockhash"]


def transfer_sol_ix(
    payer: PublicKey, dest: PublicKey, lamports: int
) -> TransactionInstruction:
    solders_ix: SoldersIX = transfer(
        TransferParams(
            from_pubkey=payer.to_solders(),
            to_pubkey=dest.to_solders(),
            lamports=lamports,
        )
    )
    # convert solders → solana-py Instruction so we can still feed MessageV0
    accounts = [
        AccountMeta(
            pubkey=str(a.pubkey), is_signer=a.is_signer, is_writable=a.is_writable
        )
        for a in solders_ix.accounts
    ]
    return TransactionInstruction(
        data=bytes(solders_ix.data),
        program_id=str(solders_ix.program_id),
        keys=accounts,
    )
