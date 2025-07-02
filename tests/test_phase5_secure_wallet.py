from pipelines.secure_wallet import (
    get_wallet_balance_usd,
    sign_and_send,
    get_solana_client,
)


def test_ci_stubs():  # CI mode assumed under pytest
    assert get_wallet_balance_usd() == 10_000.0
    assert sign_and_send(b"...") == "0xDEADBEEF"
    assert "solana" in get_solana_client()
