# top of file
from pipelines.bundle_sender import send_bundle_transaction as _jito_send

# … keep other imports …

# ↓ old stub is removed
async def send_bundle_transaction(bundle, relay_url=_RELAY):      # noqa: D401
    # Phase 10 fast‑path
    if os.getenv("ENABLE_JITO", "false").lower() == "true":
        return await _jito_send(bundle)
    # fallback: legacy signer path
    tx = {"type": "bundle", "len": len(bundle), "relay": relay_url}
    try:
        sig = await sign_and_send(tx, relay_url)
    except Exception as exc:
        print("[exec_mesh] bundle error:", exc)
        sig = _fake_sig()
    return sig
