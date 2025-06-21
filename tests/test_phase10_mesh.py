import pytest, asyncio
from pipelines.bundle_sender import send_bundle_transaction

@pytest.mark.asyncio
async def test_jito_stub_sig(monkeypatch):
    # patch env so the helper short‑circuits before hitting the network
    monkeypatch.setenv("JITO_AUTH", "Bearer TEST_TOKEN")
    async def _fake_post(*_a, **_k):
        class _Resp: status = 200
        async def json(self): return {"signature": "f"*64}
        async def __aenter__(self): return self
        async def __aexit__(self, *_): pass
        return _Resp()
    import aiohttp
    monkeypatch.setattr(aiohttp.ClientSession, "post", _fake_post)
    sig = await send_bundle_transaction([b"XX"])
    assert len(sig) == 64
