import pytest, asyncio
from pipelines.bundle_sender import send_bundle_transaction


@pytest.mark.asyncio
async def test_jito_stub_sig(monkeypatch):
    # patch env so the helper short-circuits before hitting the network
    monkeypatch.setenv("JITO_AUTH", "Bearer TEST_TOKEN")

    # ─────────── synchronous stub for aiohttp.ClientSession.post ────────────
    class _Resp:
        status = 200

        async def json(self):
            return {"signature": "f" * 64}

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_): ...

    _monkey_post = lambda *_a, **_k: _Resp()  # sync, returns object immediately

    import aiohttp

    monkeypatch.setattr(aiohttp.ClientSession, "post", _monkey_post)
    # -----------------------------------------------------------------------

    sig = await send_bundle_transaction([b"XX"])
    assert len(sig) == 64
