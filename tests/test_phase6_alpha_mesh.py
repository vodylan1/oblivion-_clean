import asyncio
import pytest
from pipelines.alpha_mesh import mint_stream, MintEvent


@pytest.mark.asyncio
async def test_ci_mint_stream_stub():
    evts = [evt async for evt in mint_stream()]
    assert evts and isinstance(evts[0], MintEvent)
