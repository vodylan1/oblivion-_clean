def test_rug_check_verdict():
    from security.rug_checker import rug_check
    from security.secure_wallet import get_solana_client
    client = get_solana_client("devnet")       # free network for CI
    verdict = rug_check("So11111111111111111111111111111111111111112", client)
    assert verdict in {"SAFE", "WARN", "BLOCK"}
