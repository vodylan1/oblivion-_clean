from typing import List


class MEVDetector:
    """Detects sandwich / latency snipers on recent mempool events."""

    def detect(self, token: str, tx_hashes: List[str]) -> bool:
        # placeholder: mark true if >3 identical gas settings in block
        return len(tx_hashes) > 3
