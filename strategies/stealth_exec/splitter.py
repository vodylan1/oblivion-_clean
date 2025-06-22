async def execute_split(signal, wallet_pool):
    """
    Dummy impl – logs the split plan; real swap logic lives in pipelines/exec_mesh.py.
    """
    parts = signal.aux.get("parts", 3)
    size = signal.size_usd / parts
    return [f"tx_mock_{i}" for i in range(parts)]
