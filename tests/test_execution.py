"""
test_execution.py

Unit-tests for Execution-Engine and Kill-Switch helper.
"""

import pytest


def test_kill_switch_triggers():
    """Kill-switch must raise the custom exception on meltdown."""
    from security.kill_switch import check_kill_switch_conditions, KillSwitchTripped

    # total PnL −60 USD  → rules say we must trip
    hist = [{"profit_loss": -20}, {"profit_loss": -40}]

    with pytest.raises(KillSwitchTripped):
        check_kill_switch_conditions(hist)


def test_kill_switch_passes():
    """No exception when recent PnL is acceptable."""
    from security.kill_switch import check_kill_switch_conditions

    hist = [{"profit_loss": +10}, {"profit_loss": -5}]
    # should silently return (== None)
    assert check_kill_switch_conditions(hist) is None
