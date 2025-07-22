"""Phase‑10: NEAT + Optuna scaffolds (no heavy compute yet)."""
import optuna
from mutation_engine.models import Genome, Gene, StrategyScore

def crossover(parent_a: Genome, parent_b: Genome) -> Genome:
    """Simple one‑point crossover."""
    split = len(parent_a.genes)//2
    return Genome(parent_a.genes[:split] + parent_b.genes[split:])

def score(genome: Genome) -> StrategyScore:
    """Stub scorer – returns dummy Sharpe/PnL."""
    base = sum(g.value for g in genome.genes)
    return StrategyScore(genome, sharpe=base/10, pnl=base)
