"""
patch_core.py

PATCHCORE module for Phase 3 (dummy version).
Calls GPT (theoretically) to propose code changes or parameter updates
based on signals from REFLECTION_ENGINE.
"""

from __future__ import annotations

# (existing imports / logic remain unchanged)


def patch_core_init():
    """Initialize PATCHCORE (placeholder)."""
    print("[PatchCore] Initialized.")


def request_autopatch():
    """Request a PatchCore suggestion (Phase 3 stub)."""

    # === SANDBOX TIMER GUARD ===
    from datetime import datetime, timedelta
    import pathlib, yaml, logging

    _pol = pathlib.Path("config/patch_policy.yaml")
    if _pol.exists():
        _cfg = yaml.safe_load(_pol.read_text()) or {}
        hrs = int(_cfg.get("sandbox_hours", 0))
        if hrs:
            _since = datetime.now() - timedelta(hours=hrs)
            ml = pathlib.Path("logs/mutation_log.md")
            if ml.exists() and ml.stat().st_mtime > _since.timestamp():
                logging.getLogger(__name__).info(
                    "Sandbox window active - autopatch delayed"
                )
                return
    # ------------------------------------------------------------------
    # Dummy body to simulate a GPT call that suggests changes.
    print("[PatchCore] Autopatch request triggered…")

    suggestion = {
        "param": "buy_threshold",
        "new_value": 18,
        "reason": "Loss streak detected. Lower buy threshold for better entry.",
    }

    print(f"[PatchCore] Suggestion: {suggestion}")
    return suggestion


# ----------------------------------------------------------------------
# TEST-ONLY helper so unit-tests can monkey-patch us
def _apply_patch(*_a, **_kw):  # noqa: D401,D103
    """Test-time stub injected so tests can monkey-patch PatchCore."""
    pass
