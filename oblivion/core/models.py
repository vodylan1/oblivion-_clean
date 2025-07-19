from dataclasses import dataclass

@dataclass(slots=True, frozen=True)
class PriceSample:
    timestamp_ns: int
    price: float
