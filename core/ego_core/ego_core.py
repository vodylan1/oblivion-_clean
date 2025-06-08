"""
ego_core.py
────────────────────────────────────────────────────────────────────────────
EGO_CORE now supports multiple behavioural overlays (“emotional archetypes”):

    • neutral   – no change
    • rage      – BUY ⇒ BUY_MORE
    • fear      – BUY ⇒ HOLD
    • soros     – BUY ⇒ BUY_MORE  (macro conviction)
    • corleone  – BUY / SELL ⇒ HOLD  (strategic patience)

The overlay function is intentionally simple; in later phases we can make each
archetype reference richer contextual signals (volatility, macro trends,
on-chain flows, etc.).
"""

from enum import Enum


class EgoState(str, Enum):
    NEUTRAL = "neutral"
    RAGE = "rage"
    FEAR = "fear"
    SOROS = "soros"
    CORLEONE = "corleone"


def ego_core_init() -> None:
    """Initialise EGO_CORE (placeholder)."""
    print("[EGO_CORE] Initialised – archetypes: "
          f"{', '.join(e.value for e in EgoState)}")


def apply_emotional_overlay(decision: str, emotional_state: str) -> str:
    """
    Overlay the SynergyConductor decision with the current EGO archetype.

    Parameters
    ----------
    decision : str
        The raw decision from SynergyConductor (`BUY`, `SELL`, `HOLD`,
        `BUY_MORE`, `SHORT`, `CLOSE_SHORT`, …).
    emotional_state : str
        One of EgoState values (case-insensitive).

    Returns
    -------
    str
        Possibly altered trading directive.
    """
    state = emotional_state.lower()

    # Fast-path – neutral leaves the directive untouched
    if state == EgoState.NEUTRAL:
        return decision

    # ── Rage ─────────────────────────────────────────────────────────────
    if state == EgoState.RAGE:
        if decision == "BUY":
            print("[EGO_CORE] RAGE: amplifying BUY → BUY_MORE.")
            return "BUY_MORE"
        return decision

    # ── Fear ─────────────────────────────────────────────────────────────
    if state == EgoState.FEAR:
        if decision == "BUY":
            print("[EGO_CORE] FEAR: downgrading BUY → HOLD.")
            return "HOLD"
        return decision

    # ── Soros (macro conviction) ─────────────────────────────────────────
    if state == EgoState.SOROS:
        if decision == "BUY":
            print("[EGO_CORE] SOROS: doubling down BUY → BUY_MORE.")
            return "BUY_MORE"
        return decision

    # ── Corleone (strategic patience) ───────────────────────────────────
    if state == EgoState.CORLEONE:
        if decision in {"BUY", "SELL"}:
            print("[EGO_CORE] CORLEONE: patience first – forcing HOLD.")
            return "HOLD"
        return decision

    # Fallback – unknown archetype, leave untouched
    print(f"[EGO_CORE] WARNING: unknown ego state '{emotional_state}', "
          "no overlay applied.")
    return decision
