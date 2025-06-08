"""
Experimental Threat‑Score stub
Enabled only if EXPERIMENTAL_THREAT_SCORE=true
"""

import os
from typing import Dict

FLAG = os.getenv("EXPERIMENTAL_THREAT_SCORE", "false").lower() == "true"


def score(snapshot: Dict) -> float:          # 0‑1 threat level


# ───────────────────────────
# 0 · checkout working branch
# ───────────────────────────
git checkout phase-7-agent-activation

# ───────────────────────────
# 1 · add / replace files
# ───────────────────────────
# A) threat_score stub  ───────────────
mkdir -p core/god_awareness
cat > core/god_awareness/threat_score.py <<'PY'
"""
Experimental Threat‑Score stub
Enabled only if EXPERIMENTAL_THREAT_SCORE=true
"""

import os
from typing import Dict

FLAG = os.getenv("EXPERIMENTAL_THREAT_SCORE", "false").lower() == "true"


def score(snapshot: Dict) -> float:          # 0‑1 threat level
    if not FLAG:
        return 0.0
    # ultra‑light heuristic until Phase‑9 matrix lands
    rug_flag = snapshot.get("rug_score", 0)
    whale_exits = snapshot.get("whale_sell_vol", 0)
    return min(1.0, 0.2 * rug_flag + 0.8 * whale_exits / 10_000)
