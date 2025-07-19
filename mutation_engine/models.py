from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Gene:
    key: str
    value: float

@dataclass
class Genome:
    genes: List[Gene] = field(default_factory=list)

@dataclass
class StrategyScore:
    genome: Genome
    sharpe: float
    pnl: float
