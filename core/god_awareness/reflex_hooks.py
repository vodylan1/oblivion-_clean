from typing import List
from .threat_classifier import Threat


class ReflexHooks:
    """Connects God_Awareness outputs to EGO_CORE & KillSwitch."""

    def __init__(self) -> None:
        self.last_events: List[Threat] = []

    def process(self, threats: List[Threat]) -> None:
        self.last_events = threats
        # TODO: emit events into EGO_CORE once integrated
